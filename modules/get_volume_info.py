# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
import sys

# 指定されたボリュームの情報を取得する関数
def get_volume_info(cluster_name, svm_name, vol_name):
    # AIQUM REST APIのURLを生成
    api_path = '/datacenter/storage/volumes' # 使用するREST API
    aiqum_request = generate_aiqum_rest_request(api_path=api_path)

    # リクエスト時に使用するパラメータ(対象SVMの親クラスタ名)を生成
    params = {
        'name': vol_name,
        'svm.name': svm_name,
        'cluster.name': cluster_name
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.get(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed getting volume: ' + vol_name)
        return(response.text) 

    # レスポンスボディ内からボリュームオブジェクトを抽出
    vol_info = json.loads(response.text)['records']

    # 存在しなかった場合はエラーメッセージ出力
    if vol_info == []:
        # print('WARNING: Volume:' + vol_name + ' does not exist')
        return vol_info
    else:
        return vol_info[0]

# 指定されたボリュームの情報を取得する関数
def _get_volume_info(cluster_name, svm_name):
    # AIQUM REST APIのURLを生成
    api_path = '/datacenter/storage/volumes' # 使用するREST API
    aiqum_request = generate_aiqum_rest_request(api_path=api_path)

    # リクエスト時に使用するパラメータ(対象SVMの親クラスタ名)を生成
    params = {
        'svm.name': svm_name,
        'cluster.name': cluster_name
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.get(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed getting volumes')
        return(response.text) 

    # レスポンスボディ内からボリュームオブジェクトを抽出
    vol_info = json.loads(response.text)['records']

    # 存在しなかった場合はエラーメッセージ出力
    if vol_info == []:
        print('WARNING: No volume found in SVM: ' + svm_name)
    else:
        return vol_info

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 4:
        print("Usage: python3 get_volume_info.py CLUSTER_NAME SVM_NAME VOL_NAME")
        sys.exit()

    print(get_volume_info(cluster_name=args[1], svm_name=args[2], vol_name=args[3]))
