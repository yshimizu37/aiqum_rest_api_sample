# coding:utf-8
import json
import requests
from pathlib import Path
import os
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

from generate_aiqum_rest_request import generate_aiqum_rest_request

# settings.jsonに記載されたクラスタの中でアグリゲート使用率が最も低いクラスタと
# そのクラスタ内で最も使用率が低いアグリゲートを特定する関数
def identify_lowest_usage_cluster():
    # 設定ファイル(settings.json)を読み込む
    abs_dir_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    abs_settings_file_path = str(abs_dir_path) + '/settings.json'

    settings_json_open = open(abs_settings_file_path, 'r')
    settings_json_load = json.load(settings_json_open)

    # 変数の初期化
    lowest_usage_cluster = {} # アグリゲート使用率が最も低いクラスタ

    # クラスタごとにアグリゲート一覧を取得し、アグリゲート使用率の平均値を計算する
    for cluster in settings_json_load['clusters']:

        # AIQUM REST APIのURLを生成
        api_path = '/datacenter/storage/aggregates'
        aiqum_request = generate_aiqum_rest_request(api_path=api_path)

        # リクエスト時に使用するパラメータ(対象クラスタ名)を生成
        params = {
            'cluster.name': cluster['name']
        }

        # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
        response = requests.get(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])
        
        # レスポンスコードが200以外の場合はエラー出力して終了
        if response.status_code != 200:
            print('error occurred while getting SVMs in the cluster: ' + cluster['name'])
            return(response.text) 

        # レスポンスボディ内からアグリゲートの一覧データを取得
        aggr_list = json.loads(response.text)['records']

        # 変数の初期化
        lowest_usage_aggregate = {} # クラスタ内で最も使用率が低いアグリゲート
        total_used = 0  # クラスタ当たりのアグリゲートサイズ合計
        total_size = 0  # クラスタ当たりのアグリゲート使用済みサイズ合計

        # クラスタ内のアグリゲート合計サイズ、合計使用済みサイズ、最も低い使用率のアグリゲートを計算
        for aggregate in aggr_list:
            total_used += aggregate['space']['block_storage']['used'] # 使用済みサイズを加算
            total_size += aggregate['space']['block_storage']['size'] # 合計サイズを加算

            # 最も使用率が低いアグリゲートを特定
            usage_percentage = aggregate['space']['block_storage']['used'] / aggregate['space']['block_storage']['size']
            if lowest_usage_aggregate == {} or lowest_usage_aggregate['usage_percentage'] >= usage_percentage:
                lowest_usage_aggregate = {'name': aggregate['name'], 'usage_percentage': usage_percentage}

        # 最も使用率が低いクラスタを特定  
        cluster_usage = total_used / total_size
    
        if lowest_usage_cluster == {} or lowest_usage_cluster['cluster']['usage_percentage'] >= cluster_usage:
            lowest_usage_cluster = {'cluster': {'name': cluster['name'], 'usage_percentage': cluster_usage},'aggregate': lowest_usage_aggregate}
    
    return(lowest_usage_cluster)

# 単体テスト用
if __name__ == "__main__":
    print(identify_lowest_usage_cluster())


