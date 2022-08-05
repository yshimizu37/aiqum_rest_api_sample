# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
from get_svm_root_volume import get_svm_root_volume
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# LSミラー関係の初期転送を行う関数
def initialize_ls_mirror_relationships(cluster_name, svm_name):
    print('INFO: Initializing load-sharing mirror relationships...')

    # AIQUM REST APIのURLを生成
    # 実装時点でLSミラーの初期転送ができるONTAP REST APIがないため、CLIパススルー機能を使用
    api_path = '/private/cli/snapmirror/initialize-ls-set' # 使用するREST API

    # クラスタとSVMのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # SVMルートボリュームの名称を取得
    try:
        root_vol_name = get_svm_root_volume(cluster_name=cluster_name, svm_name=svm_name)['name']
    except:
        return('ERROR: SVM roor volume is not found')

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
        'return_timeout': 30 # 同期処理に変更
    }

    # SnapMirrorのパスを生成
    src_path = svm_name + ":" + root_vol_name # 転送元

    # snapmirror relationshipの作成内容をリクエストボディとして生成
    request_body = {
        "source-path": src_path
    }

    # AIQUMに対してPOSTリクエストを発行
    response = requests.post(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

    # レスポンスコードが200以外の場合はエラー出力して終了
    # print(response.status_code)
    if response.status_code == 200:
        print('INFO: Successfully initialized SnapMirror relationships for :' + src_path)
        return(response.text)
    else:
        print('ERROR: Failed initializing SnapMirror relationships for:' + src_path)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) == 3:
        print(initialize_ls_mirror_relationships(cluster_name=args[1], svm_name=args[2]))

    else:
        print("Usage: python3 initialize_ls_mirror_relationships.py CLUSTER_NAME SVM_NAME")
        sys.exit()
