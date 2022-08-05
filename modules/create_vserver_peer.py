# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# 指定したSVM間でsnapmirror用のピア関係を作成する関数
# AIQUMのAPI gatewayを介して、ONTAP REST API(POST /svm/peers)を実行
def create_vserver_peer(cluster_name_src, svm_name_src, cluster_name_dst, svm_name_dst):
    print('INFO: Creating vserver peer relationship for SnapMirror...')

    api_path = '/svm/peers' # 使用するONTAP REST API

    # クラスタのUUID取得（API gateway実行用）
    cluster_uuid_src = get_cluster_info(cluster_name=cluster_name_src)['uuid']
    cluster_uuid_dst = get_cluster_info(cluster_name=cluster_name_dst)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request_src = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid_src)
    aiqum_request_dst = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid_dst)

    # リクエスト時に使用するパラメータを生成
    params_post_patch = {
        'return_records': "false",
        'return_timeout': 30 # 同期処理に変更
    }

    # peer relationshipの作成内容をリクエストボディとして生成
    request_body = {
        'applications': [
            "snapmirror"
        ],
        'peer':
            {
                'cluster': {
                    'name': cluster_name_dst
                },
                'svm': {
                    'name': svm_name_dst
                }
            },
        'svm': {
            'name': svm_name_src
        }
    }

    # SnapMirror元のSVMからピア関係作成
    response = requests.post(
        aiqum_request_src['url'], params=params_post_patch, headers=aiqum_request_src['headers'], verify=aiqum_request_src['verify'], json=request_body)

    # レスポンスコードが201以外の場合はエラー出力して終了
    if response.status_code == 201:
        print('INFO: Successfully created verver peer relationship: ' + svm_name_src + ' -> ' + svm_name_dst)
    else:
        print('ERROR: Failed creating verver peer relationship: ' + svm_name_src + ' -> ' + svm_name_dst)
        print(response.text) 
        return False

    # SnapMirrorの宛先クラスタ上でピア関係をacceptする
    # pendingとなっているピア関係のUUIDを取得
    params_get = {
        'svm.name': svm_name_dst,
        'peer.svm.name': svm_name_src
    }
    response = requests.get(
        aiqum_request_dst['url'], params=params_get, headers=aiqum_request_dst['headers'], verify=aiqum_request_dst['verify'])

    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code == 200:
        print('INFO: Successfully getting pending relationship: ' + svm_name_src + ' -> ' + svm_name_dst)
        pending_relationship_uuid = json.loads(response.text)['records'][0]['uuid']
    else:
        print('ERROR: Failed getting pending relationship: ' + svm_name_src + ' -> ' + svm_name_dst)
        print(response.text) 
        return False

    # pendingとなっているピア関係をaccept

    api_path_patch = api_path + '/' + pending_relationship_uuid
    aiqum_request_dst_patch = generate_aiqum_rest_request(api_path=api_path_patch, cluster_uuid=cluster_uuid_dst)
    request_body = {"state":"peered"}

    response = requests.patch(
        aiqum_request_dst_patch['url'], params=params_post_patch, headers=aiqum_request_dst_patch['headers'], verify=aiqum_request_dst_patch['verify'], json=request_body)

    # レスポンスコードが200以外の場合はエラー出力して終了
    if response.status_code == 200:
        print('INFO: Successfully accepted verver peer relationship: ' + svm_name_src + ' -> ' + svm_name_dst)
        return True
    else:
        print('ERROR: Failed accepting verver peer relationship: ' + svm_name_src + ' -> ' + svm_name_dst)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) != 5:
        print("Usage: python3 create_vserver_peer.py CLUSTER_NAME_SRC SVM_NAME_SRC CLUSTER_NAME_DST SVM_NAME_DST")
        sys.exit()

    print(create_vserver_peer(cluster_name_src=args[1], svm_name_src=args[2], cluster_name_dst=args[3], svm_name_dst=args[4]))
