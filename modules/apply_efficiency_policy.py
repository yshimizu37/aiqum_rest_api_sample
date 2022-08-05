# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# 指定したefficiency policyをボリュームに適用する関数
# AIQUMのAPI gatewayを介して、ONTAP REST API(PATCH /storage/volumes/{vol_uuid})を実行
def apply_efficiency_policy(cluster_name, svm_name, policy_name, vol_name, vol_uuid):
    print('INFO: Apppling efficiency policy...')

    # クラスタとボリュームのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']
    
    # AIQUM REST APIのURLを生成
    api_path_1 = '/private/cli/volume/efficiency/on' # 使用するREST API

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request_1 = generate_aiqum_rest_request(api_path=api_path_1, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
        'return_timeout': 30 # 同期処理に変更
    }

    # efficiency policyの適用内容をリクエストボディとして生成
    request_body = {
        "vserver": svm_name,
        "volume": vol_name
    }

    # AIQUMに対してPATCHリクエストを発行
    response = requests.post(
        aiqum_request_1['url'], params=params, headers=aiqum_request_1['headers'], verify=aiqum_request_1['verify'], json=request_body)

    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code == 200:
        print('INFO: Successfully enabled volume efficiency:' + vol_name)
    else:
        print('ERROR: Failed enabling volume efficiency:' + vol_name)
        print(response.text) 
        return False

    api_path_2 = '/storage/volumes/' + vol_uuid # 使用するONTAP REST API

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request_2 = generate_aiqum_rest_request(api_path=api_path_2, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
        'return_timeout': 30 # 同期処理に変更
    }

    # efficiency policyの適用内容をリクエストボディとして生成
    request_body = {
        "efficiency": {
            "policy": {
                "name": policy_name
            }
        }
    }

    # AIQUMに対してPATCHリクエストを発行
    response = requests.patch(
        aiqum_request_2['url'], params=params, headers=aiqum_request_2['headers'], verify=aiqum_request_2['verify'], json=request_body)

    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code == 200:
        print('INFO: Successfully applied efficiency-policy:' + policy_name + ' to volume:' + vol_name)
        # print(response.text)         
        return(response.text)
    else:
        print('ERROR: Failed appling efficiency-policy:' + policy_name + ' to volume:' + vol_name)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 5:
        print("Usage: python3 apply_efficiency_policy.py CLUSTER_NAME SVM_NAME POLICY_NAME VOL_NAME")
        sys.exit()

    print(apply_efficiency_policy(cluster_name=args[1], svm_name=args[2], policy_name=args[3], vol_name=args[4]))
