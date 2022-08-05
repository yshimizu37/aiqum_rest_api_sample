# coding:utf-8
# NFS接続用SVM作成 - エントリースクリプト
# 実行時にSVM作成内容を対話形式で受け付け、メインスクリプトをキックする

# 汎用ライブラリのインポート
import os
import sys
import netaddr
import re
import json
from pathlib import Path

# 自作モジュールのインポート
sys.path.append(os.path.join(os.path.dirname(__file__), './main'))
from create_nfs_volume_main import create_nfs_volume_main

sys.path.append(os.path.join(os.path.dirname(__file__), './modules'))
from get_aggregates_info import get_aggregates_info
from get_svm_info import get_svm_info
from get_cluster_info import get_cluster_info
from get_volume_info import get_volume_info

# 作成するボリュームの内容を対話型で入力させる処理

# 対象クラスタ名
while True:
    # ユーザ入力の受け付け
    cluster_name = input('ONTAP cluster name: ')
    # 指定されたクラスタがAIQUM配下に存在するかをチェック
    is_cluster_existing = get_cluster_info(cluster_name=cluster_name)
    if is_cluster_existing:
        # 設定ファイル(settings.json)を読み込む
        abs_dir_path = Path(os.path.dirname(os.path.abspath(__file__)))
        abs_settings_file_path = str(abs_dir_path) + '/settings.json'

        settings_json_open = open(abs_settings_file_path, 'r')
        settings_json_load = json.load(settings_json_open)

        # 引数で指定されたクラスタ名がsettings.json内に存在するか確認
        # 存在する場合はsettings.jsonからDR用のクラスタ/SVMを特定
        is_cluster_in_settings_file = False
        for cluster in settings_json_load['clusters']:
            if cluster_name == cluster['name']:
                peer_cluster_name = cluster['snapmirror_destination']['peer_cluster_name']
                backup_svm_name = cluster['snapmirror_destination']['backup_svm_name']
                is_cluster_in_settings_file = True
                break
        if is_cluster_in_settings_file:
            break

# 対象SVM名
while True:
    # ユーザ入力の受け付け
    svm_name = input('SVM name: ')
    # 指定されたSVMが上記クラスタ内に存在するかをチェック
    is_svm_existing = get_svm_info(
        cluster_name=cluster_name, svm_name=svm_name)
    if is_svm_existing:
        break

# ボリュームの使用用途
while True:
    # ユーザ入力の受け付け（選択式）
    vol_type = input('volume type(1: NFS datastore for vSphere, 2: other): ')
    # 入力チェック
    if vol_type == '1' or vol_type == '2':
        break

# ボリューム名
while True:
    # ユーザ入力の受け付け
    vol_name = input('volume name: ')
    # 入力チェック
    if vol_name != '':
        # 対象ボリュームがソース側SVMに存在しないことを確認
        vol_info = get_volume_info(cluster_name=cluster_name, svm_name=svm_name, vol_name=vol_name)
        if vol_info == []:
            is_vol_in_source_svm = False            
        else:
            is_vol_in_source_svm = True
            print('volume is already existing in the SVM')

        # 対象ボリュームがバックアップ用SVM内に存在しないことを確認
        vol_info = get_volume_info(cluster_name=peer_cluster_name, svm_name=backup_svm_name, vol_name=vol_name)
        if vol_info == []:
            is_vol_in_backup_svm = False            
        else:
            is_vol_in_backup_svm = True
            print('volume is already existing in the backup SVM')

        # ソース側、バックアップ側双方にボリュームが存在しない場合に入力OKとする
        print("source existing:" + str(is_vol_in_source_svm))
        print("destination existing:" + str(is_vol_in_backup_svm))
        if (not is_vol_in_source_svm) and (not is_vol_in_backup_svm):
            break

# ボリュームサイズ
while True:
    # ユーザ入力の受け付け
    vol_size = input('volume size(unit: GB/TB): ')
    # MB/GB/TBいずれかの単位で記載されているかチェック
    res = re.search("(GB|TB)$", vol_size)
    # 単位より前の文字列が整数値であるかをチェック
    if res:
        try:
            # 入力されたボリュームから数字部分のみを抽出
            n = int(re.split("(GB|TB)$", vol_size)[0])
                
            # ボリュームサイズをバイト単位に変換
            if re.split("(GB|TB)$", vol_size)[1] == 'GB':
                vol_size_byte = n * 1024 ** 3
            elif re.split("(GB|TB)$", vol_size)[1] == 'TB':
                vol_size_byte = n * 1024 ** 4

            break
        except:
            print('Input parameter is invalid')

    else:
        print('Input parameter is invalid')

# vol払い出し先のアグリゲート
while True:
    # ユーザ入力の受け付け
    aggregate_name = input('aggregate name: ')
    # クラスタ内のアグリゲート一覧を取得
    aggr_list = get_aggregates_info(cluster_name=cluster_name) 
    is_aggregate_existing = None
    # 指定されたアグリゲートがクラスタ内に存在するかをチェック
    for aggregate in aggr_list:
        if aggregate_name == aggregate['name']:
            is_aggregate_existing = True
            break
    if is_aggregate_existing:
        break
    else:
        print('Aggregate:' + aggregate_name + ' does not exist in the cluster')

# データストア用の場合、export policy作成とWindowsクライアント向け設定は不要
if vol_type == '1':
    client_cidr = None
    is_windows_client = False

elif vol_type == '2':
    # export policyの作成内容(データストア用でない場合のみ)
    while True:
        # ユーザ入力の受け付け
        client_cidr = input(
            'client CIDR for export policy rule(example: 192.168.0.0/24): ')
        # netaddrを使用して入力内容がCIDRの形式か否かをチェック
        try:
            ip = netaddr.IPNetwork(client_cidr)
            break
        except:
            print('Input parameter is invalid')

    # マウント元がWindowsクライアントか否か(データストア用でない場合のみ)
    while True:
        # ユーザ入力の受け付け
        is_windows_client = input('Windows client(Y/N): ')
        if is_windows_client == 'Y':
            is_windows_client = True
            break
        elif is_windows_client == 'N':
            is_windows_client = False
            break

# # snapmirror同期の開始時刻
# while True:
#     # ユーザ入力の受け付け
#     is_snapmirror = input('Create SnapMirror relationship(Y/N): ')
#     if is_snapmirror == 'Y':
#         break
#     elif is_snapmirror == 'N':
#         break

while True:
    # ユーザ入力の受け付け
    start_hours_for_job_schedule = input(
        'start hour for dedupelication and snapmirror sync(0-11)): ')
    # 0~12時までの時刻が整数値で入力されているかをチェック
    try:
        if int(start_hours_for_job_schedule) >= 0 and int(start_hours_for_job_schedule) <= 11:
            break
        print('Schedule must be specified from 0 to 11')
    except:
        print('Schedule must be specified from 0 to 11')

# 入力内容の最終確認
print('')
print('')
print('*****************************')
print('Summary of volume creation')
print('*****************************')
print('Cluster: ' + cluster_name)
print('SVM: ' + svm_name)
print('Volume: ' + vol_name)
print('Volume size: ' + vol_size)
print('Aggregate: ' + aggregate_name)
if vol_type == '2': 
    print('Client match: ' + str(client_cidr))
    print('Windows client: ' + str(is_windows_client))
print('Start hour for job schedule: ' + str(start_hours_for_job_schedule))
print('')
print('')

# 問題なければメイン関数をキック
while True:
    # ユーザ入力の受け付け
    is_confirmed = input('Are you sure want to create this volume?(Y/N): ')
    if is_confirmed == 'Y':
        # メイン関数のキック
        ret = create_nfs_volume_main(cluster_name=cluster_name, svm_name=svm_name, vol_name=vol_name, vol_size_byte=vol_size_byte, aggregate_name=aggregate_name,
                                        is_windows_client=is_windows_client, client_cidr=client_cidr, start_hours_for_job_schedule=start_hours_for_job_schedule)
        break
    elif is_confirmed == 'N':
        print('Aborting volume creation')
        break

