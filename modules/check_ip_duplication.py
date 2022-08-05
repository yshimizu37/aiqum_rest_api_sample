# coding:utf-8
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from generate_aiqum_rest_request import generate_aiqum_rest_request
from get_cluster_info import get_cluster_info
import sys
urllib3.disable_warnings(InsecureRequestWarning)

# 指定したIPアドレスにpingを実行し、応答の有無を確認する関数
# 応答あり = True, 応答なし = False
def check_ip_duplication(cluster_name, svm_name, lif_name, ip):
    print('INFO: Checking IP address duplication...')

    # AIQUM REST APIのURLを生成
    # 実装時点でPingが実行できるONTAP REST APIがないため、CLIパススルー機能を使用
    api_path = '/private/cli/network/ping' # 使用するREST API

    # クラスタとSVMのUUID取得（API gateway実行用）
    cluster_uuid = get_cluster_info(cluster_name=cluster_name)['uuid']

    # APIリクエスト先のURLを生成（API gateway）
    aiqum_request = generate_aiqum_rest_request(api_path=api_path, cluster_uuid=cluster_uuid)

    # リクエスト時に使用するパラメータを生成
    params = {
        'return_records': 'true',
    }

    # snapmirror relationshipの作成内容をリクエストボディとして生成
    request_body = {
        'vserver': svm_name,
        'destination': ip,
        'lif': lif_name
    }

    # AIQUMに対してPOSTリクエストを発行
    response = requests.post(
        aiqum_request['url'], params=params, headers=aiqum_request['headers'], verify=aiqum_request['verify'], json=request_body)

    # レスポンスコードが200の場合はping応答あり
    # print(response.status_code)
    if response.status_code == 200:
        print('INFO: ' + ip + ' is alive')
        return True
    else:
        print('INFO: Destination unreachable:' + ip)
        return False

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) == 5:
        print(check_ip_duplication(cluster_name=args[1], svm_name=args[2], lif_name=args[3], ip=args[4]))

    else:
        print("Usage: python3 check_ip_duplication.py CLUSTER_NAME SVM_NAME LIF_NAME IP_ADDR")
        sys.exit()
