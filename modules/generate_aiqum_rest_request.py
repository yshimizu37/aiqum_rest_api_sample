# coding:utf-8
import json
import sys
import os
from pathlib import Path

# 設定ファイルからAIQUM REST API実行時に共通で使用するベースURLと認証情報を生成する
def generate_aiqum_rest_request(api_path, cluster_uuid=None):
    # 設定ファイル(settings.json)を読み込む
    abs_dir_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    abs_settings_file_path = str(abs_dir_path) + '/settings.json'

    settings_json_open = open(abs_settings_file_path, 'r')
    settings_json_load = json.load(settings_json_open)

    # 設定ファイルの内容からリクエスト先URLを生成
    base_url = "https://" + settings_json_load['aiqum']['ip'] +"/api"

    # cluster_uuidの指定があった場合は、API gateway(AIQUM経由でONTAP REST API実行)のリクエスト用URLを生成
    if cluster_uuid != None:
        url = base_url + '/gateways/' + cluster_uuid + api_path
    # cluster_uuidの指定がなかった場合は、AIQUM REST APIのリクエスト用URLを生成
    else:
        url = base_url + api_path

    # 設定ファイルの内容からHTTPSのヘッダを生成
    authorization = 'Basic ' + settings_json_load['aiqum']['cred']
    headers = {
        'accept': 'application/json',
        'authorization': authorization,
    }

    # 設定ファイルの内容から証明書の検証有無を生成
    verify = bool(settings_json_load['aiqum']['verify'])

    return { "url": url, "headers": headers, "verify": verify}

# 単体テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) == 2:
        print(generate_aiqum_rest_request(api_path=args[1]))
    elif len(args) == 3:
        print(generate_aiqum_rest_request(api_path=args[1], cluster_uuid=args[2]))
    else:
        print("Usage: python3 generate_aiqum_rest_request.py API_PATH [CLUSTER_UUID]")
        sys.exit()