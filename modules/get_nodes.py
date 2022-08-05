# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
import sys

# 指定されたクラスタ内の全ノードを取得する関数
def get_nodes(cluster_name):
    # AIQUM REST APIのURLを生成
    api_path = '/datacenter/cluster/nodes' # 使用するREST API
    aiqum_request = generate_aiqum_rest_request(api_path=api_path)

    # リクエスト時に使用するパラメータ(対象クラスタ名)を生成
    params = {
        'cluster.name': cluster_name
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.get(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed getting nodes in the cluster: ' + cluster_name)
        return(response.text) 

    # レスポンスボディ内からアグリゲートの一覧データを取得
    node_list = json.loads(response.text)['records']
    return node_list
    
# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print("Usage: python3 get_nodes.py CLUSTER_NAME")
        sys.exit()

    print(get_nodes(cluster_name=args[1]))
