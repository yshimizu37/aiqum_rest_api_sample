# coding:utf-8
import requests
import json
import time
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
import sys
from get_cluster_info import get_cluster_info

# SnapMirror転送が完了するまで待機する関数
def check_snapmirror_status(cluster_name_dst, snapmirror_relationship_uuid, interval=30, retry_count=10):
    print('INFO: Monitoring SnapMirror transfer status...')

    # 最大retry_countの数だけ繰り返しチェックする
    for i in range(retry_count, 0, -1):
        # SnapMirror relationshipの状態を取得
        transfer_status = get_snapmirror_status(cluster_name_dst=cluster_name_dst, snapmirror_relationship_uuid=snapmirror_relationship_uuid)

        # SnapMirror転送が完了の状態だったら終了
        if transfer_status == 'success':
            print('INFO: Snapmirror transfer has been completed')
            return True
        
        # SnapMirror転送中の場合はintervalの時間だけ待って再チェック
        elif transfer_status == 'transferring':
            print('INFO: Remaining retry count:' + str(i))
            print('INFO: Waiting ' + str(interval) + ' seconds for next check')
            time.sleep(interval)
        
        # その他のステータスの場合は異常終了
        else:
            print('ERROR: Transferring status is invalid')
            return False

    # retry countがゼロになったら終了
    print('WARNING: Reached max retry count but the SnapMirror transfer does not end yet')
    return False

# SnapMirror転送の状態を確認する関数
def get_snapmirror_status(cluster_name_dst, snapmirror_relationship_uuid):
    # AIQUM REST APIのURLを生成
    api_path = '/snapmirror/relationships/' + snapmirror_relationship_uuid # 使用するREST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name_dst)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {}

    # AIQUMに対してPOSTリクエストを発行
    response = requests.get(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed getting relationships for: ' + snapmirror_relationship_uuid)
        print(response.text)
        return False 

    # レスポンスボディ内からアグリゲートの一覧データを取得
    # print(response.text)
    print('INFO: Successfully got relationships for: ' + snapmirror_relationship_uuid)

    transfer_status = json.loads(response.text)['transfer']['state']
    print('INFO: Transfering status: ' + transfer_status)
    return transfer_status
    
# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 modify_snapmirror_relationship.py CLUSTER_NAME_DST SNAPMIRROR_UUID")
        sys.exit()

    print(check_snapmirror_status(cluster_name_dst=args[1], snapmirror_relationship_uuid=args[2]))
