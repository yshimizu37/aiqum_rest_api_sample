# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# SVM上にNFSサービスを作成する関数

def create_nfs_service(cluster_name, svm_name):
    print('INFO: Creating NFS service...')

    # AIQUM REST APIのURLを生成
    api_path = '/protocols/nfs/services' # 使用するREST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true'
    }

    # svmの作成内容をリクエストボディとして生成
    request_body = {
        'svm': {
            'name': svm_name
        },
        'enabled': 'true',
        'protocol': {
            "v3_enabled": 'true',
        },
        'vstorage_enabled': 'true'
    }

    # AIQUMに対してPOSTリクエストを発行
    response = requests.post(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

    # レスポンスコードが201以外の場合はエラー出力して終了
    if response.status_code == 201:
        print('INFO: Successfully created nfs service on the svm: ' + svm_name)
        return(json.loads(response.text)['records'][0])
    else:
        print('ERROR: Failed creating nfs service on the svm: ' + svm_name)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 create_nfs_service.py CLUSTER_NAME SVM_NAME")
        sys.exit()

    print(create_nfs_service(cluster_name=args[1], svm_name=args[2]))
