# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys

# 指定されたSVMのSSL証明書一覧を取得する関数
def create_ssl_certification(cluster_name, svm_name):
    print('INFO: Creating a new SSL certification...')

    # AIQUM REST APIのURLを生成
    api_path = '/security/certificates' # 使用するONTAP REST API

    # クラスタとSVMのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        "return_records": "true"
    }

    request_body = {
        "svm": {
            "name": svm_name
        },
        "common_name": svm_name,
        "expiry_time": "P3650DT",
        "hash_function": "sha256",
        "key_size": 2048,
        "type": "server"
    }

    # AIQUMに対してGETリクエストを発行
    response = requests.post(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 201:
        print('ERROR: Failed creating SSL certification for SVM:' + svm_name)
        print(response.text)
        return False 

    # レスポンスボディ内を返却
    print('INFO: Successfully created SSL certification for SVM:' + svm_name)
    return json.loads(response.text)['records'][0]

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 create_ssl_certification.py CLUSTER_NAME SVM_NAME")
        sys.exit()

    print(create_ssl_certification(cluster_name=args[1], svm_name=args[2]))
