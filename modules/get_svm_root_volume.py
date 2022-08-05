# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
urllib3.disable_warnings(InsecureRequestWarning)
import sys

# SVM名からルートボリューム名を取得する処理
def get_svm_root_volume(cluster_name, svm_name):
    # AIQUM REST APIのURLを生成
    api_path = '/storage/volumes' # 使用するONTAP REST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params1 = {
        'svm.name': svm_name,
        'is_svm_root': 'true'
    }
    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.get(
        aiqum_request['url'], params=params1, headers=aiqum_request['headers'], verify=aiqum_request['verify'])

    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code == 200:
        print('INFO: Successfully found svm root volume for: ' + svm_name)
        return json.loads(response.text)['records'][0]
    else:
        print('ERROR: Failed getting svm root volume for: ' + svm_name)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 get_svm_root_volume.py CLUSTER_NAME SVM_NAME")
        sys.exit()

    print(get_svm_root_volume(cluster_name=args[1], svm_name=args[2]))
