# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
import sys
from get_cluster_info import get_cluster_info


# 既存のSnapMirror関係に対して初期転送を行う関数
def initialize_snapmirror_relationship(cluster_name_dst, snapmirror_relationship_uuid):
    print('INFO: Initializing SnapMirror relationship...')

    # AIQUM REST APIのURLを生成
    api_path = '/snapmirror/relationships/' + snapmirror_relationship_uuid # 使用するREST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name_dst)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
        'return_timeout': 30 # 非同期型で実行
    }

    request_body = {"state":"snapmirrored"}

    # AIQUMに対してPOSTリクエストを発行
    response = requests.patch(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed initializing relationships for: ' + snapmirror_relationship_uuid)
        print(response.text)
        return False 

    # レスポンスボディ内からアグリゲートの一覧データを取得
    print('INFO: Successfully started initializing relationships for: ' + snapmirror_relationship_uuid)
    return response.text
    
# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 modify_snapmirror_relationship.py CLUSTER_NAME_DST SNAPMIRROR_UUID")
        sys.exit()

    print(initialize_snapmirror_relationship(cluster_name_dst=args[1], snapmirror_relationship_uuid=args[2]))
