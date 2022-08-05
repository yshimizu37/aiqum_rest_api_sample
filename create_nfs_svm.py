# coding:utf-8
# NFS接続用SVM作成 - エントリースクリプト
# 実行時にSVM作成内容を対話形式で受け付け、メインスクリプトをキックする

# 汎用ライブラリのインポート
import os
import sys
import netaddr
import re

# 自作モジュールのインポート
sys.path.append(os.path.join(os.path.dirname(__file__), './main'))
from create_nfs_svm_main import create_nfs_svm_main

sys.path.append(os.path.join(os.path.dirname(__file__), './modules'))
from get_aggregates_info import get_aggregates_info
from get_nodes import get_nodes
from get_cluster_info import get_cluster_info
from identify_lowest_usage_cluster import identify_lowest_usage_cluster

# 作成するボリュームの内容を対話型で入力させる処理

# 対象SVM名
while True:
    # ユーザ入力の受け付け
    svm_name = input('SVM name: ')
    # 入力チェック
    if svm_name != '':
        break

# データの格納状況から推奨のクラスタ、アグリゲートを表示
recommended_cluster = identify_lowest_usage_cluster()
cluster_percentage = str(round(recommended_cluster['cluster']['usage_percentage'] * 100, 1)) + "%"
aggregate_percentage = str(round(recommended_cluster['aggregate']['usage_percentage'] * 100, 1)) + "%"

print('*****************************')
print('Recommended Cluster: ' + recommended_cluster['cluster']['name'] + '(' + cluster_percentage + ' used)')
print('Recommended Aggregate: ' + recommended_cluster['aggregate']['name'] + '(' + aggregate_percentage + ' used)')
print('*****************************')

# 推奨のクラスタ、アグリゲートを使用するかどうかを入力
while True:
    # ユーザ入力の受け付け
    use_recommended = input('Do you use this recommended cluster and aggregate?(Y/N): ')
    if use_recommended == 'Y':
        use_recommended = True
        cluster_name = recommended_cluster['cluster']['name']
        aggregate_name = recommended_cluster['aggregate']['name']
        break
    if use_recommended == 'N':
        use_recommended = False
        break

# 推奨のクラスタ、アグリゲートを使用しない場合は手動で入力
if use_recommended == False:
    # SVM作成先のクラスタ名
    while True:
        # ユーザ入力の受け付け
        cluster_name = input('ONTAP cluster name: ')
        # 指定されたクラスタがAIQUM配下に存在するかをチェック
        is_cluster_existing = get_cluster_info(cluster_name=cluster_name)
        if is_cluster_existing:
            break

    # root vol払い出し先のアグリゲート
    while True:
        # ユーザ入力の受け付け
        aggregate_name = input('aggregate name: ')
        # クラスタ内のアグリゲート一覧を取得
        aggr_list = get_aggregates_info(cluster_name=cluster_name) 
        # 指定されたアグリゲートがクラスタ内に存在するかをチェック
        for aggregate in aggr_list:
            if aggregate_name == aggregate['name']:
                is_aggregate_existing = True
                break
        if is_aggregate_existing:
            break

# VLAN IDの入力
while True:
    # ユーザ入力の受け付け
    vlan_id = input('VLAN ID: ')
    # VLAN IDの形式であるかチェック
    try:
        if int(vlan_id) >= 1 and int(vlan_id) <= 4094:
            break
        else:
            print("VLAN ID must be a number from 1 to 4094")
    except:
        print("VLAN ID must be a number from 1 to 4094")

# broadcast domainの名称
while True:
    # ユーザ入力の受け付け
    broadcast_domain_name = input('Broadcast-domain name: ')
    # 入力チェック
    if broadcast_domain_name != '':
        break

# LIF本数の入力
while True:
    # ユーザ入力の受け付け
    lif_count = input('How many LIFs do you need?(1-4): ')
    # VLAN IDの形式であるかチェック
    try:
        if int(lif_count) >= 1 and int(lif_count) <= 4:
            break
        else:
            print("LIFs must be a number from 1 to 4")
    except: 
        print("LIFs must be a number from 1 to 4")

# LIFの本数分、各LIFの内容を入力
lif_list = []
n = int(lif_count) + 1
for i in range(1, n):
    # LIFの名称
    while True:
        # ユーザ入力の受け付け
        name = input('LIF-' + str(i) + "'s name: ")
        # 入力チェック
        if name != '':
            break

    # LIFのIP
    while True:
        # ユーザ入力の受け付け
        ip = input('LIF-' + str(i) + "'s IP address: ")
        # 入力チェック
        try:
            if netaddr.IPAddress(ip).is_private():
                break
            else:
                print("It's not Private IP address")
        except:
            print('Input parameter is invalid')

    # LIFのサブネットマスク
    while True:
        # ユーザ入力の受け付け
        netmask = input('LIF-' + str(i) + "'s netmask: ")
        # 入力チェック
        try:
            if netaddr.IPAddress(netmask).is_netmask():
                break
            else:
                print('Input parameter is invalid')
        except:
            print('Input parameter is invalid')

    # LIFのhome node
    while True:
        # ユーザ入力の受け付け
        home_node = input('LIF-' + str(i) + "'s home-node: ")
        # 入力チェック
        # モジュール関数を使用してクラスタ内のノード一覧を取得
        node_list = get_nodes(cluster_name=cluster_name)
        is_node_existing = False

        # 入力されたノード名との照合
        for node in node_list:
            if node['name'] == home_node:
                is_node_existing = True
                break
        
        # クラスタ内に指定されたノード名が存在する場合は入力を受け付ける
        if is_node_existing == True:
            break
        else:
            print('node does not exist in the cluster')

    # 入力内容をLIFのリストに追加
    lif_list.append({"name":name, "ip": ip, "netmask": netmask, "home_node":home_node})

# 入力内容の最終確認
print('')
print('')
print('*****************************')
print('Summary of SVM creation')
print('*****************************')
print('SVM: ' + svm_name)
print('Cluster: ' + cluster_name)
print('Aggregate: ' + aggregate_name)
print('VLAN: ' + vlan_id)
print('Broadcast-domain: ' + broadcast_domain_name)
print('LIFs: ' + str(lif_list))
print('')
print('')

# 問題なければメイン関数をキック
while True:
    # ユーザ入力の受け付け
    is_confirmed = input('Are you sure want to create this SVM?(Y/N): ')
    if is_confirmed == 'Y':
        # メイン関数のキック
        ret = create_nfs_svm_main(cluster_name=cluster_name, svm_name=svm_name, aggregate_name=aggregate_name,
                                        vlan_id=vlan_id, broadcast_domain_name=broadcast_domain_name, lif_list=lif_list)
        break
    elif is_confirmed == 'N':
        print('Aborting SVM creation')
        break

