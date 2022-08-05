# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys

# 指定されたクラスタ内で指定されたVLANポートが存在するかどうかを判定する関数
# 存在する場合は該当のポートを使用しているLIFのリストを返却する
def check_vlan_port_existance(cluster_name, vlan_id):
    # AIQUM REST APIのURLを生成
    api_path_1 = '/datacenter/network/ethernet/ports' # 使用するREST API
    aiqum_request_1 = generate_aiqum_rest_request(api_path=api_path_1)

    # クラスタの存在確認
    if get_cluster_info(cluster_name) == []: 
        return False

    # リクエスト時に使用するパラメータ(対象クラスタ名)を生成
    params = {
        'cluster.name': cluster_name,
        'vlan.tag': vlan_id
    }

    # AIQUMに対してGETリクエスト(VLANポートの一覧取得)を発行
    response = requests.get(aiqum_request_1['url'], params=params, headers=aiqum_request_1['headers'], verify=aiqum_request_1['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed getting vlan ports in the cluster: ' + cluster_name)
        return(response.text) 

    # レスポンスボディ内からVLANポートの有無を確認
    # print(response.text)
    port_list = json.loads(response.text)['records']
    
    if len(port_list) == 0:
        print('INFO: VLAN:' + vlan_id + ' is not exist in cluster:' + cluster_name)
        return []
    else:
        print('INFO: VLAN' + vlan_id + ' is already exist in cluster:' + cluster_name)
        port_name = port_list[0]['name']
    
    # AIQUM REST APIのURLを生成
    api_path_2 = '/datacenter/network/ip/interfaces' # 使用するREST API
    aiqum_request_2 = generate_aiqum_rest_request(api_path=api_path_2)

    # リクエスト時に使用するパラメータ(対象クラスタ名)を生成
    params = {
        'cluster.name': cluster_name,
        'location.port.name': port_name,
        'state': 'up'
    }

    # AIQUMに対してGETリクエスト(該当のVLANポートに位置するLIFの一覧取得)を発行
    response = requests.get(aiqum_request_2['url'], params=params, headers=aiqum_request_2['headers'], verify=aiqum_request_2['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed getting LIFs using VLAN port:' + port_name)
        return(response.text) 

    # レスポンスボディ内からアグリゲートの一覧データを取得
    lif_list = json.loads(response.text)['records']
    if len(lif_list) == 0:
        print('WARNING: No LIFs found using VLAN port:' + port_name)
        return []
    else:
        print('INFO: LIFs found using VLAN port:' + port_name)
        return lif_list

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 check_vlan_port_existance.py CLUSTER_NAME VLAN_ID")
        sys.exit()

    print(check_vlan_port_existance(cluster_name=args[1], vlan_id=args[2]))
