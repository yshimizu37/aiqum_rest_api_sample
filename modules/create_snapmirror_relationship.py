# coding:utf-8
import requests
import json
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# SnapMirror関係を新規に作成する関数
# AIQUMのAPI gatewayを介して、ONTAP REST API(POST /snapmirror/relationships)を実行
def create_snapmirror_relationship(svm_name_src, vol_name_src, cluster_name_dst, svm_name_dst, vol_name_dst):
    print('INFO: Creating SnapMirror relationship...')

    # AIQUM REST APIのURLを生成
    api_path = '/snapmirror/relationships' # 使用するONTAP REST API

    # クラスタとSVMのUUID取得（API gateway実行用）
    cluster_uuid_dst = get_cluster_info(cluster_name=cluster_name_dst)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid_dst)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
        'return_timeout': 30 # 同期処理に変更
    }

    # # SnapMirror転送先のボリューム名が指定されなかった場合は転送元ボリュームと同じ名前で新規にボリューム作成
    # if vol_name_dst == None:
    #     vol_name_dst = vol_name_src
    #     create_destination_obj =  {"enabled": "true"}
    # else:
    #     create_destination_obj =  {"enabled": "false"}

    # SnapMirrorのパスを生成
    src_path = svm_name_src + ":" + vol_name_src # 転送元
    dst_path = svm_name_dst + ":" + vol_name_dst # 転送先

    # snapmirror relationshipの作成内容をリクエストボディとして生成
    request_body = {
        "source": {"path": src_path},
        "destination": {"path": dst_path},
        # "policy": {"name": "DPDefault"}
        # "state": "snapmirrored", # relationship作成と同時にinitialize
        # "create_destination": create_destination_obj
    }

    # AIQUMに対してPOSTリクエストを発行
    response = requests.post(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

    # レスポンスコードが201以外の場合はエラー出力して終了
    if response.status_code == 201:
        print('INFO: Successfully created SnapMirror relationship: ' + src_path + ' -> ' + dst_path)
        return json.loads(response.text)['records'][0]
    else:
        print('ERROR: Failed creating SnapMirror relationship: ' + src_path + ' -> ' + dst_path)
        print(response.text) 
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    # # 宛先ボリューム名を指定しない場合
    # if len(args) == 5:
    #     print(create_snapmirror_relationship(svm_name_src=args[1], vol_name_src=args[2], cluster_name_dst=args[3], svm_name_dst=args[4]))

    # 宛先ボリューム名を指定した場合
    if len(args) == 6:
        print(create_snapmirror_relationship(svm_name_src=args[1], vol_name_src=args[2], cluster_name_dst=args[3], svm_name_dst=args[4], vol_name_dst=args[5]))

    else:
        print("Usage: python3 create_snapmirror_relationship.py SVM_NAME_SRC VOL_NAME_SRC CLUSTER_NAME_DST SVM_NAME_DST VOL_NAME_DST")
        sys.exit()
