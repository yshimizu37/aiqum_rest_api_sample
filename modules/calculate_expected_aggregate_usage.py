# coding:utf-8
import json
import sys
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

from generate_aiqum_rest_request import generate_aiqum_rest_request

# 作成するボリュームサイズ(byte単位)をもとに、
# ボリュームを払い出し後における対象アグリゲートの想定使用率と使用済みサイズを計算する関数
def calculate_expected_aggregate_usage(cluster_name, aggregate_name, vol_size_byte):
    # AIQUM REST APIのURLを生成
    api_path = '/datacenter/storage/aggregates' # 使用するREST API
    aiqum_request = generate_aiqum_rest_request(api_path=api_path)

    # リクエスト時に使用するパラメータ(対象クラスタ名)を生成
    params = {
        'name': aggregate_name,
        'cluster.name': cluster_name
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.get(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('error occurred while getting SVMs in the cluster: ' + cluster_name)
        return(response.text) 

    # レスポンスボディ内からアグリゲートの使用状況に関するデータを抽出
    aggr_info = json.loads(response.text)['records'][0]['space']['block_storage']
 
    # 現在のアグリゲート使用状況を計算
    before_usage_percentage = aggr_info['used'] / aggr_info['size'] * 100
    before_prov = {'size': aggr_info['size'], 'used': aggr_info['used'], 'usage_percentage': before_usage_percentage}

    # ボリューム払い出し後の使用状況を試算
    after_used = aggr_info['used'] + int(vol_size_byte)
    after_usage_percentage = after_used / aggr_info['size'] * 100
    after_prov = {'size': aggr_info['size'], 'used': after_used, 'usage_percentage': after_usage_percentage}

    # ボリューム払い出し前後のアグリゲート使用状況を返却
    return {'before': before_prov, 'after': after_prov}
    
# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 4:
        print("Usage: python3 calculate_expected_aggregate_usage.py CLUSTER_NAME AGGREGATE_NAME VOL_SIZE_BYTE")
        sys.exit()

    print(calculate_expected_aggregate_usage(cluster_name=args[1], aggregate_name=args[2], vol_size_byte=args[3]))
