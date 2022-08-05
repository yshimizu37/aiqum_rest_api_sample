# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
import sys
from get_cluster_info import get_cluster_info


# SSLサービスの有効化
def enable_ssl_server(cluster_name, svm_name):
    print('INFO: Enabling SSL Server...')

    # AIQUM REST APIのURLを生成
    # 実装時点で"-v3-ms-dos-client"の設定変更ができるONTAP REST APIがないため、CLIパススルー機能を使用
    api_path = '/private/cli/security/ssl' # 使用するREST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'vserver': svm_name,
        'return_records': "true"
    }

    request_body = {
        'server-enabled': 'true'
    }

    # Windowsクライアント向けNFSサービス設定
    response = requests.patch(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed enabling SSL service for: ' + svm_name)
        return(response.text) 

    # レスポンスボディ内からNFSサービスの設定値を取得
    print('INFO: Successfully enabling SSL service for: ' + svm_name)
    return json.loads(response.text)['records'][0]
    
# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 enable_ssl_server.py CLUSTER_NAME SVM_NAME")
        sys.exit()

    print(enable_ssl_server(cluster_name=args[1], svm_name=args[2]))
