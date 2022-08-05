# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# 指定したSVM配下にexport policyとexport policy ruleを作成する関数
# AIQUMのAPI gatewayを介して、ONTAP REST API(POST /protocols/nfs/export-policies)を実行
def create_job_schedule_12h_interval(cluster_name, start_hour, start_minute, prefix_for_schedule_name):
    print('INFO: Creating job schedule...')

    # AIQUM REST APIのURLを生成
    api_path = '/cluster/schedules' # 使用するONTAP REST API

    # クラスタとSVMのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
    }

    # job sheduleの名称を引数で受け取った接頭辞とjobの開始時刻から計算
    if len(str(start_hour)) == 1:
        # 時刻が一桁だった場合は２桁に直す
        start_hour_str = '0' + str(start_hour)
    else:        
        # 時刻が二桁だった場合はそのまま
        start_hour_str = str(start_hour)
    
    if len(str(start_minute)) == 1:
        # 分が一桁だった場合は２桁に直す
        start_minute_str = '0' + str(start_minute)
    else:        
        # 分が二桁だった場合はそのまま
        start_minute_str = str(start_minute)

    schedule_name = prefix_for_schedule_name + start_hour_str + start_minute_str + '_start_12h_interval'

    # インターバル12時間後のjob開始時刻を計算
    start_time_after_12h = int(start_hour) + 12

    # job scheduleの作成内容をリクエストボディとして生成
    request_body = {
        'name': schedule_name,
        'cron': {
            'hours': [start_hour, start_time_after_12h],
            'minutes': [start_minute]
        }
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.post(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

    # レスポンスコードが201以外の場合はエラー出力して終了
    if response.status_code == 201:
        print('INFO: Successfully created job shedule: ' + schedule_name)
        return json.loads(response.text)['records'][0]
    else:
        print('ERROR: Failed creating job shedule: ' + schedule_name)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 5:
        print("Usage: python3 create_job_schedule_12h_interval.py CLUSTER_NAME START_HOUR START_MINUTE SCHEDULE_NAME_PREFIX")
        sys.exit()

    print(create_job_schedule_12h_interval(cluster_name=args[1], start_hour=args[2], start_minute=args[3], prefix_for_schedule_name=args[4]))
