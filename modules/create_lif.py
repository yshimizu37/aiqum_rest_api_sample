# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# NFS接続用のLIFを作成する関数

def create_lif(cluster_name, svm_name, lif_name, home_node, home_port, ip, netmask):
    print('INFO: Creating a LIF...')

    # AIQUM REST APIのURLを生成
    api_path = '/network/ip/interfaces' # 使用するONTAP REST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true'
    }

    # dp volumeの作成内容をリクエストボディとして生成
    request_body = {
        "ip": {
            "address": ip,
            "netmask": netmask
        },
        "location": {
            "auto_revert": 'false',
            "home_node": {
                "name": home_node
            },
            "home_port": {
                "name": home_port
            },
            "failover": "broadcast_domain_only",
        },
        "service_policy": {
            "name": "default-data-files"
        },
        "name": lif_name,
        "svm": {
            "name": svm_name
        },
    }

    # AIQUMに対してPOSTリクエストを発行
    response = requests.post(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

    # レスポンスコードが201以外の場合はエラー出力して終了
    if response.status_code == 201:
        print('INFO: Successfully created LIF: ' + lif_name)
        return(json.loads(response.text)['records'][0])
    else:
        print('ERROR: Failed creating LIF: ' + lif_name)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 8:
        print("Usage: python3 create_lif.py CLUSTER_NAME SVM_NAME LIF_NAME HOME_NODE HOME_PORT IP_ADDR NETMASK")
        sys.exit()

    print(create_lif(cluster_name=args[1], svm_name=args[2], lif_name=args[3], home_node=args[4], home_port=args[5], ip=args[6], netmask=args[7]))
