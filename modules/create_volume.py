# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# NFS接続用ボリュームを作成する関数

def create_volume(cluster_name, svm_name, aggregate_name, vol_name, vol_size_byte, export_policy_name, type):
    if type == 'rw': print('INFO: Creating source volume...')
    if type == 'dp': print('INFO: Creating destination volume...')

    # AIQUM REST APIのURLを生成
    api_path = '/storage/volumes' # 使用するONTAP REST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
        'return_timeout': 30,  # 同期処理に変更
    }

    # dp volumeの作成内容をリクエストボディとして生成
    request_body = {
        "aggregates": [
            {
                "name": aggregate_name,
            }
        ],
        "autosize": {
            "grow_threshold": 98,
            "mode": "grow_shrink",
            "shrink_threshold": 50
        },
        "guarantee": {
            "type": "none"
        },
        "language": "ja_JP.PCK_v2",
        "name": vol_name,
        "nas": {
            "export_policy": {
                "name": export_policy_name
            },
            "security_style": "unix"
        },
        "size": vol_size_byte,
        "snapshot_policy": {
            "name": "none"
        },
        "space": {
            "snapshot": {
                "reserve_percent": 5
            },
        },
        "state": "online",
        "svm": {
            "name": svm_name
        },
        "type": type,
    }

    # RWボリュームの場合はリクエストボディにjunction-path設定を追加
    if type == 'rw':
        request_body['nas']['path'] = '/' + vol_name


    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.post(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

    # レスポンスコードが201以外の場合はエラー出力して終了
    if response.status_code == 201:
        print('INFO: Successfully created volume: ' + vol_name)
        return(json.loads(response.text)['records'][0])
    else:
        print('ERROR: Failed creating volume: ' + vol_name)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 8:
        print("Usage: python3 create_volume.py CLUSTER_NAME SVM_NAME AGGREGATE_NAME VOL_NAME VOL_SIZE EXPORT_POLICY_NAME TYPE")
        sys.exit()

    print(create_volume(cluster_name=args[1], svm_name=args[2], aggregate_name=args[3], vol_name=args[4], vol_size_byte=args[5], export_policy_name=args[6], type=args[7]))
