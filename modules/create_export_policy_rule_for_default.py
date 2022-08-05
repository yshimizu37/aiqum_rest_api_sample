# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# 指定したSVMのデフォルトのexport policy上にruleを作成する関数
# AIQUMのAPI gatewayを介して、ONTAP REST API(POST /protocols/nfs/export-policies)を実行
def create_export_policy_rule_for_default(cluster_name, svm_name):
    # デフォルトのexport-policyのIDを取得
    print('INFO: Searching default export-policy id...')

    # AIQUM REST APIのURLを生成
    api_path_1 = '/protocols/nfs/export-policies' # 使用するONTAP REST API
    # クラスタとSVMのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']
    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request_1 = generate_aiqum_rest_request(api_path=api_path_1, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params_1 = {
        'svm.name': svm_name,
        'name': 'default'
    }

    # AIQUMに対してGETリクエストを発行
    response = requests.get(
        aiqum_request_1['url'], params=params_1, headers=aiqum_request_1['headers'], verify=aiqum_request_1['verify'])

    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code == 200:
        default_policy_id = str(json.loads(response.text)['records'][0]['id'])
        print('INFO: Successfully got default export-policy id: ' + default_policy_id)
    else:
        print('ERROR: Failed getting default export-policy')
        print(response.text) 
        return False

    # export-policyのIDを使用してexport-policy ruleを作成
    print('INFO: Creating export-policy rule for default export-policy...')

    # AIQUM REST APIのURLを生成
    api_path_2 = '/protocols/nfs/export-policies/' + default_policy_id + '/rules' # 使用するONTAP REST API
    # クラスタとSVMのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']
    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request_2 = generate_aiqum_rest_request(api_path=api_path_2, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params_2 = {
        'return_records': 'true'
    }

    # export policy ruleの作成内容をリクエストボディとして生成
    request_body = {
        'allow_device_creation': 'true',
        'allow_suid': 'true',
        'anonymous_user': '0',
        'clients': [
            {
                'match': '0.0.0.0/0',
            },
        ],
        'protocols': [
            'any'
        ],
        'ro_rule': [
            'any'
        ],
        'rw_rule': [
            'any'
        ],
        'superuser': [
            'any'
        ]
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.post(
        aiqum_request_2['url'], params=params_2, headers=aiqum_request_2['headers'], verify=aiqum_request_2['verify'], json=request_body)

    # レスポンスコードが201以外の場合はエラー出力して終了
    if response.status_code == 201:
        print('INFO: Successfully created export-policy rule')
        return json.loads(response.text)['records'][0]
    else:
        print('ERROR: Failed creating export-policy rule')
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 create_export_policy_rule_for_default.py CLUSTER_NAME SVM_NAME")
        sys.exit()

    print(create_export_policy_rule_for_default(cluster_name=args[1], svm_name=args[2]))
