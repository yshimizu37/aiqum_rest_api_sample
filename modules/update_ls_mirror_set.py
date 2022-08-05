# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
import sys
from get_svm_root_volume import get_svm_root_volume
from get_cluster_info import get_cluster_info


# 指定されたSVMのLSミラー関係を取得する関数
def update_ls_mirror_set(cluster_name, svm_name):
    print('INFO: Updating LS mirror relationships...')

    # AIQUM REST APIのURLを生成
    # 実装時点でLSミラーのupdateができるONTAP REST APIがないため、CLIパススルー機能を使用
    api_path = '/private/cli/snapmirror/update-ls-set' # 使用するREST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # SVMルートボリュームの名称を取得
    root_vol_name = get_svm_root_volume(cluster_name=cluster_name, svm_name=svm_name)['name']

    # SnapMirrorのsource pathを生成
    source_path = cluster_name + "://" + svm_name + "/" + root_vol_name

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
        'return_timeout': 30
    }

    request_body = {
        'source_path': source_path
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.post(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed updating relationships for: ' + source_path)
        print(response.text)
        return False 

    # レスポンスボディ内からアグリゲートの一覧データを取得
    print('INFO: Successfully updated relationships for: ' + source_path)
    relationships = json.loads(response.text)
    return relationships
    
# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 update_ls_mirror_set.py CLUSTER_NAME SVM_NAME")
        sys.exit()

    print(update_ls_mirror_set(cluster_name=args[1], svm_name=args[2]))
