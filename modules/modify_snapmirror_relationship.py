# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
import sys
from get_cluster_info import get_cluster_info


# 既存のSnapMirror関係に対してポリシー変更とスケジュール設定を行う関数
def modify_snapmirror_relationship(cluster_name_dst, svm_name_dst, vol_name_dst, job_schedule_name, policy_name=None):
    print('INFO: Modifying SnapMirror relationship...')

    # AIQUM REST APIのURLを生成
    # 実装時点でLSミラーのupdateができるONTAP REST APIがないため、CLIパススルー機能を使用
    api_path = '/private/cli/snapmirror' # 使用するREST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name_dst)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # SnapMirrorのdestination pathを生成
    destination_path = svm_name_dst + ':' + vol_name_dst

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
        'return_timeout': 30,
        'destination-path': destination_path
    }

    request_body = {
        'schedule': job_schedule_name,
    }

    # SnapMirror policyの指定があった場合はリクエストボディへ追加
    if policy_name != None:
        request_body['policy'] = policy_name

    # AIQUMに対してPOSTリクエストを発行
    response = requests.patch(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed modifying relationships for: ' + destination_path)
        print(response.text)
        return False 

    # レスポンスボディ内からアグリゲートの一覧データを取得
    print('INFO: Successfully modified relationships for: ' + destination_path)
    relationships = json.loads(response.text)
    return relationships
    
# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) == 5:
        print(modify_snapmirror_relationship(cluster_name_dst=args[1], svm_name_dst=args[2], vol_name_dst=args[3], job_schedule_name=args[4]))
    elif len(args) == 6:
        print(modify_snapmirror_relationship(cluster_name_dst=args[1], svm_name_dst=args[2], vol_name_dst=args[3], policy_name=args[4], job_schedule_name=args[5]))
    else:
        print("Usage: python3 modify_snapmirror_relationship.py CLUSTER_NAME_DST SVM_NAME_DST VOL_NAME_DST POLICY_NAME SCHEDULE_NAME")
        sys.exit()
