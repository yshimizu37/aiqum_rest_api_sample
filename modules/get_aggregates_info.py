# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
import sys

# 指定されたアグリゲートの情報を取得する関数
def get_aggregates_info(cluster_name):
    # AIQUM REST APIのURLを生成
    api_path = '/datacenter/storage/aggregates' # 使用するREST API
    aiqum_request = generate_aiqum_rest_request(api_path=api_path)

    # リクエスト時に使用するパラメータ(対象クラスタ名)を生成
    params = {
        'cluster.name': cluster_name
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.get(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed getting aggregate in the cluster: ' + cluster_name)
        return(response.text) 

    # レスポンスボディ内からAggregateオブジェクトを抽出
    aggr_info = json.loads(response.text)['records']

    # 存在しなかった場合はエラーメッセージ出力
    if aggr_info == []:
        print('ERROR: No aggregate found in the cluster: ' + cluster_name)

    return aggr_info
    
# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print("Usage: python3 get_aggregates_info.py CLUSTER_NAME")
        sys.exit()

    print(get_aggregates_info(cluster_name=args[1]))
