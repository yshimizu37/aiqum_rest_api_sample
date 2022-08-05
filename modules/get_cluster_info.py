# coding:utf-8
import sys
from generate_aiqum_rest_request import generate_aiqum_rest_request
import json
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

# 引数で指定されたONTAPクラスタの情報を取得する関数
def get_cluster_info(cluster_name):
    # AIQUM REST APIのURLを生成
    api_path = '/datacenter/cluster/clusters' # 使用するREST API
    aiqum_request = generate_aiqum_rest_request(api_path=api_path)

    # リクエスト時に使用するパラメータ(対象SVMの親クラスタ名)を生成
    params = {
        'name': cluster_name
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.get(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])

    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('error occurred while getting clusters')
        return(response.text)

    # レスポンスボディ内からClusterオブジェクトを抽出
    cluster_info = json.loads(response.text)['records']

    # 存在しなかった場合はエラーメッセージ出力
    if cluster_info == []:
        print('ERROR: Cluster: ' + cluster_name + ' does not exist')
    else:
        cluster_info = cluster_info[0]

    return cluster_info


# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print("Usage: python3 get_cluster_info.py CLUSTER_NAME")
        sys.exit()

    print(get_cluster_info(cluster_name=args[1]))
