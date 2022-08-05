# coding:utf-8
import requests
import json
import os
from pathlib import Path
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
from get_nodes import get_nodes
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# 指定したクラスタ配下の全ノードに指定されたVLANポートを作成する関数
# AIQUMのAPI gatewayを介して、ONTAP REST API(POST /network/ethernet/ports)を実行
def create_vlan_port(cluster_name, vlan_id, broadcast_domain, ipspace='Default'):
    print('INFO: Creating VLAN enabled port...')

    # AIQUM REST APIのURLを生成
    api_path = '/network/ethernet/ports' # 使用するONTAP REST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # VLANポート作成先となる物理ポート(LAG含む)をsettings.jsonから取得
    # 設定ファイル(settings.json)を読み込む
    abs_dir_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    abs_settings_file_path = str(abs_dir_path) + '/settings.json'

    settings_json_open = open(abs_settings_file_path, 'r')
    settings_json_load = json.load(settings_json_open)

    # 引数で指定されたクラスタ名とsettings.jsonからbase portを特定
    for cluster in settings_json_load['clusters']:
        if cluster_name == cluster['name']:
            base_port = cluster['base_port']

    # クラスタ内に存在する全ノードを取得
    node_list = get_nodes(cluster_name=cluster_name)


    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
    }

    # ノードごとにVLANポート作成
    for node in node_list:
        print('INFO: Creating VLAN enabled port for node: ' + node['name'])

        # VLANポートの作成内容をリクエストボディとして生成
        request_body = {
            'broadcast_domain': {
                'ipspace':{
                    'name': ipspace
                },
                'name': broadcast_domain
            },
            'node': {
                'uuid': node['uuid']
            },
            'type': 'vlan',
            'vlan': {
                'base_port': {
                    'name': base_port
                },
                'tag': vlan_id
            }
        }

        # AIQUM(API gateway)に対してPOSTリクエスト(VLANポートの作成)を発行
        response = requests.post(
            aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

        # レスポンスコードが201以外の場合はエラー出力して終了
        if response.status_code == 201:
            print('INFO: Successfully created port:' + base_port + '-' + vlan_id + ' on node:' + node['name'])
        else:
            print('ERROR: Failed creating port: ' + base_port + '-' + vlan_id + ' on node:' + node['name'])
            print(response.text) 
            return False

    # 全ノード作成完了したら終了
    return True

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 4:
        print("Usage: python3 create_vlan_port.py CLUSTER_NAME VLAN_ID BROADCAST_DOMAIN")
        sys.exit()

    print(create_vlan_port(cluster_name=args[1], vlan_id=args[2], broadcast_domain=args[3]))
