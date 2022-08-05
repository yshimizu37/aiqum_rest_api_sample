# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# 指定したSVM配下にexport policyとexport policy ruleを作成する関数
# AIQUMのAPI gatewayを介して、ONTAP REST API(POST /protocols/nfs/export-policies)を実行
def create_efficiency_policy(cluster_name, svm_name, policy_name, job_schedule_name):
    print('INFO: Creating efficiency policy...')

    # AIQUM REST APIのURLを生成
    api_path = '/storage/volume-efficiency-policies' # 使用するONTAP REST API

    # クラスタとSVMのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
    }

    # export policyとexport policy ruleの作成内容をリクエストボディとして生成
    request_body = {
        'name': policy_name,
        'schedule': {'name': job_schedule_name},
        'svm': {'name': svm_name}
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.post(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

    # レスポンスコードが201以外の場合はエラー出力して終了
    if response.status_code == 201:
        print('INFO: Successfully created efficiency-policy: ' + policy_name)
        return(json.loads(response.text)['records'][0])
    else:
        print('ERROR: Failed creating efficiency-policy: ' + policy_name)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 5:
        print("Usage: python3 create_efficiency_policy.py CLUSTER_NAME SVM_NAME POLICY_NAME JOB_SCHEDULE_NAME")
        sys.exit()

    print(create_efficiency_policy(cluster_name=args[1], svm_name=args[2], policy_name=args[3], job_schedule_name=args[4]))
