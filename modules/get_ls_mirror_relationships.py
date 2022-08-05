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
def get_ls_mirror_relationships(cluster_name, svm_name):
    print('INFO: Getting LS mirror relationships...')

    # AIQUM REST APIのURLを生成
    # 実装時点でLSミラー関係の情報を取得できるONTAP REST APIがないため、CLIパススルー機能を使用
    api_path = '/private/cli/snapmirror' # 使用するREST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # SVMルートボリュームの名称を取得
    try:
        root_vol_name = get_svm_root_volume(cluster_name=cluster_name, svm_name=svm_name)['name']
    except:
        return('ERROR: SVM roor volume is not found')
    # SnapMirrorのsource pathを生成
    source_path = cluster_name + "://" + svm_name + "/" + root_vol_name

    # リクエスト時に使用するパラメータ(対象クラスタ名)を生成
    params = {
        'type':'LS',
        'source_path': source_path,
        'fields': 'state,status'
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.get(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('ERROR: Failed getting relationships for: ' + source_path)
        return(response.text) 

    # レスポンスボディ内からLSミラー関係データを取得
    relationships = json.loads(response.text)['records']
    print('INFO: Successfully got relationships:' + source_path)
    return relationships
    
# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 get_ls_mirror_relationships.py CLUSTER_NAME SVM_NAME")
        sys.exit()

    print(get_ls_mirror_relationships(cluster_name=args[1], svm_name=args[2]))
