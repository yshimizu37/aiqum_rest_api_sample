# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
from get_aggregates_info import get_aggregates_info
from get_svm_root_volume import get_svm_root_volume
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# LSミラー用のボリューム作成
def create_ls_volumes(cluster_name, svm_name):
    print('INFO: Creating DP volume for load-sharing mirror...')

    # AIQUM REST APIのURLを生成
    api_path = '/storage/volumes' # 使用するONTAP REST API

    # クラスタ/SVM/アグリゲートのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # SVMルートボリュームの名称を取得
    try:
        root_vol_name = get_svm_root_volume(cluster_name=cluster_name, svm_name=svm_name)['name']
    except:
        return('ERROR: SVM roor volume is not found')

    # アグリゲートのリストを取得
    aggr_list = get_aggregates_info(cluster_name=cluster_name)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
        'return_timeout': 30,  # 同期処理に変更
    }

    # LSミラーボリュームの末尾に付与する連番
    vol_number = 0

    # 作成完了したvolumeの情報が入る配列
    dp_volume_list = []

    # クラスタ内の全アグリゲートに対してdpボリュームを作成
    for aggregate in aggr_list:
        # LSミラーボリュームの末尾に付与する連番をカウントアップ
        vol_number += 1
        vol_name = root_vol_name + '_m' + str(vol_number)

        print('INFO: Creating dp volume:' + vol_name + ' on aggregate:' + aggregate['name'])

        # dp volumeの作成内容をリクエストボディとして生成
        request_body = {
            'name': vol_name,
            'aggregates': [
                {
                    'name': aggregate['name']
                }
            ],
            'svm': {
                'name': svm_name
            },
            'size': '1GB',
            'type': 'dp'
        }

        # AIQUMに対してPOSTリクエストを発行
        response = requests.post(
            aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

        # レスポンスコードが201以外の場合はエラー出力して終了
        if response.status_code == 201:
            print('INFO: Successfully created dp volume: ' + vol_name)
            dp_volume_info = json.loads(response.text)['records'][0]
            dp_volume_list.append(dp_volume_info)
        else:
            print('ERROR: Failed creating dp volume: ' + vol_name)
            print(response.text) 
            return False

    return dp_volume_list

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 create_ls_volumes.py CLUSTER_NAME SVM_NAME")
        sys.exit()

    print(create_ls_volumes(cluster_name=args[1], svm_name=args[2]))
