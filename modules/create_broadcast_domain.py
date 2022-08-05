# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
from get_nodes import get_nodes
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# 指定したクラスタ配下にbroadcast domainを作成する関数
# AIQUMのAPI gatewayを介して、ONTAP REST API(POST /network/ethernet/broadcast-domains)を実行
def create_broadcast_domain(cluster_name, broadcast_domain_name, mtu, ipspace='Default'):
    print('INFO: Creating broadcast domain...')

    # AIQUM REST APIのURLを生成
    api_path = '/network/ethernet/broadcast-domains' # 使用するONTAP REST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
    }

    # VLANポートの作成内容をリクエストボディとして生成
    request_body = {
        "ipspace": {
            "name": ipspace
        },
        "mtu": mtu,
        "name": broadcast_domain_name
    }

    # AIQUM(API gateway)に対してPOSTリクエスト(VLANポートの作成)を発行
    response = requests.post(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

    # レスポンスコードが201以外の場合はエラー出力して終了
    if response.status_code == 201:
        print('INFO: Successfully created broadcast domain: ' + broadcast_domain_name)
        return True
    else:
        print('ERROR: Failed creating broadcast domain: ' + broadcast_domain_name)
        print(response.text) 
        return False


# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 4:
        print("Usage: python3 create_broadcast_domain.py CLUSTER_NAME BROADCAST_DOMAIN_NAME MTU")
        sys.exit()

    print(create_broadcast_domain(cluster_name=args[1], broadcast_domain_name=args[2], mtu=args[3]))
