# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# NFS接続用SVMを作成する関数

def create_svm(cluster_name, svm_name, aggregate_name):
    print('INFO: Creating SVM...')

    # AIQUM REST APIのURLを生成
    # 実装時点でONTAP REST API(POST /svm/svms)にてrootボリュームの設定ができないためCLIパススルー機能を使用
    api_path = '/private/cli/vserver' # 使用するREST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
        'return_timeout': 30
    }

    root_volume_name = svm_name + '_root'

    # svmの作成内容をリクエストボディとして生成
    request_body = {
        'vserver': svm_name,
        'aggregate': aggregate_name,
        'rootvolume': root_volume_name,
        'rootvolume-security-style': 'unix',
        'language': 'ja_JP.PCK_v2',
        'snapshot-policy': 'default',
        'ipspace': 'Default'
    }

    # AIQUMに対してPOSTリクエストを発行
    response = requests.post(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

    # レスポンスコードが201以外の場合はエラー出力して終了
    if response.status_code == 201:
        print('INFO: Successfully created svm: ' + svm_name)
        return(json.loads(response.text)['records'][0])
    else:
        print('ERROR: Failed creating svm: ' + svm_name)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 4:
        print("Usage: python3 create_svm.py CLUSTER_NAME SVM_NAME AGGREGATE_NAME")
        sys.exit()

    print(create_svm(cluster_name=args[1], svm_name=args[2], aggregate_name=args[3]))
