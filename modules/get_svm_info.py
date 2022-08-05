# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)
import json
from generate_aiqum_rest_request import generate_aiqum_rest_request
import sys

# 指定されたクラスタ名のkeyとUUIDを取得する関数
def get_svm_info(cluster_name, svm_name):
    # AIQUM REST APIのURLを生成
    api_path = '/datacenter/svm/svms' # 使用するREST API
    aiqum_request = generate_aiqum_rest_request(api_path=api_path)

    # リクエスト時に使用するパラメータ(対象SVMの親クラスタ名)を生成
    params = {
        'name': svm_name,
        'cluster.name': cluster_name
    }

    # AIQUMに対してGETリクエスト(SVMの一覧取得)を発行
    response = requests.get(aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'])
    
    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code != 200:
        print('error occurred while getting SVMs in the cluster: ' + cluster_name)
        return(response.text) 

    # レスポンスボディ内からSVMオブジェクトを抽出
    svm_info = json.loads(response.text)['records']

    # 存在しなかった場合はエラーメッセージ出力
    if svm_info == []:
        print('ERROR: SVM: ' + svm_name + ' does not exist')
    else:
        svm_info = svm_info[0]

    return svm_info

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 3:
        print("Usage: python3 get_svm_info.py CLUSTER_NAME SVM_NAME")
        sys.exit()

    print(get_svm_info(cluster_name=args[1], svm_name=args[2]))
