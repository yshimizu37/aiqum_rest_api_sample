# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys

# 指定されたクラスタ内のjob schedule一覧を取得する関数
def get_job_schedules(cluster_name):
    # AIQUM REST APIのURLを生成
    api_path = '/cluster/schedules' # 使用するREST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.get(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed getting job schedules in the cluster: ' + cluster_name)
        return(response.text) 

    # レスポンスボディ内からjobスケジュールの一覧データを取得
    schedule_list = json.loads(response.text)['records']
    return schedule_list
    
# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 2:
        print("Usage: python3 get_job_schedules.py CLUSTER_NAME")
        sys.exit()

    print(get_job_schedules(cluster_name=args[1]))
