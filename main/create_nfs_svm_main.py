# coding:utf-8
import json
import sys
import os
from pathlib import Path

# 自作モジュールのインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '../modules'))
from check_vlan_port_existance import check_vlan_port_existance
from check_ip_duplication import check_ip_duplication
from create_vlan_port import create_vlan_port
from create_svm import create_svm
from create_export_policy_rule_for_default import create_export_policy_rule_for_default
from create_ls_volumes import create_ls_volumes
from create_ls_mirror_relationships import create_ls_mirror_relationships
from initialize_ls_mirror_relationships import initialize_ls_mirror_relationships
from modify_snapmirror_relationship import modify_snapmirror_relationship
from create_lif import create_lif
from create_vserver_peer import create_vserver_peer
from create_ssl_certification import create_ssl_certification
from create_broadcast_domain import create_broadcast_domain
from create_nfs_service import create_nfs_service
from delete_ssl_certification import delete_ssl_certification
from get_ssl_certification import get_ssl_certification

def create_nfs_svm_main(cluster_name, svm_name, vlan_id, broadcast_domain_name, aggregate_name, lif_list):
    print('INFO: Starting NFS volume creation...')
    error_message = 'ERROR: Aborting SVM creation...'

    """
    0. 設定ファイルの読み込み
    """
    # 設定ファイル(settings.json)を読み込む
    abs_dir_path = Path(os.path.dirname(os.path.abspath(__file__))).parent
    abs_settings_file_path = str(abs_dir_path) + '/settings.json'

    settings_json_open = open(abs_settings_file_path, 'r')
    settings_json_load = json.load(settings_json_open)

    # 引数で指定されたSVM名とsettings.jsonからDR用のクラスタ/SVMを特定
    for cluster in settings_json_load['clusters']:
        if cluster_name == cluster['name']:
            peer_cluster_name = cluster['snapmirror_destination']['peer_cluster_name']
            backup_svm_name = cluster['snapmirror_destination']['backup_svm_name']
            home_port = cluster['base_port'] + '-' + vlan_id
            mtu = cluster['mtu']
    
    """
    1. ポートVLAN、broadcast-domain作成
    """
    # 指定されたVLAN IDを持つポートがクラスタ内に存在するかを確認
    ping_lif_list = check_vlan_port_existance(cluster_name=cluster_name, vlan_id=vlan_id)
    if ping_lif_list == False:
        return error_message
    # VLANが存在しない場合
    elif len(ping_lif_list) == 0:
        is_new_vlan = True
    # 既にVLANが存在する場合
    else:
        is_new_vlan = False

    # 既存VLANの場合はIPアドレスの重複確認を行う
    if is_new_vlan == False:
        ping_svm_name = ping_lif_list[0]['svm']['name']  # ping送信テスト用のSVM
        ping_lif_name = ping_lif_list[0]['name']  # ping送信テスト用のLIF

        # LIF設定用のIPのいずれか1つでも応答が返ってきたら処理を中断する
        for lif in lif_list:
            is_duplicated_ip = check_ip_duplication(cluster_name=cluster_name, svm_name=ping_svm_name, lif_name=ping_lif_name, ip=lif['ip'])
            if is_duplicated_ip:
                print("ERROR: IP Address:" + lif['ip'] + " is already assigned other interface")
                return error_message

    # 新規VLANの場合、VLANポートの作成を行う
    else:
        # broadcast-domainの作成
        ret = create_broadcast_domain(cluster_name=cluster_name, broadcast_domain_name=broadcast_domain_name, mtu=mtu, ipspace='Default')
        # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
        if ret == False:
            return error_message

        # VLANポートの作成
        ret = create_vlan_port(cluster_name=cluster_name, vlan_id=vlan_id, broadcast_domain=broadcast_domain_name, ipspace='Default')
        # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
        if ret == False:
            return error_message

    """
    2. SVM作成
    """
    # SVMの作成
    ret = create_svm(cluster_name=cluster_name, svm_name=svm_name, aggregate_name=aggregate_name)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return error_message

    # NFSサービスの作成
    ret = create_nfs_service(cluster_name=cluster_name, svm_name=svm_name)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return error_message

    # export policy(default)ルール作成
    ret = create_export_policy_rule_for_default(cluster_name=cluster_name, svm_name=svm_name)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return error_message

    # LSミラーボリュームの作成
    ls_volume_list = create_ls_volumes(cluster_name=cluster_name, svm_name=svm_name)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ls_volume_list == False:
        return error_message

    # LSミラー関係の作成用にLSボリュームのリストを作成
    ls_volume_name_list = []
    for ls_volume in ls_volume_list:
        ls_volume_name_list.append(ls_volume['name']) 

    # LSミラー用SnapMirror関係の作成
    ret = create_ls_mirror_relationships(cluster_name=cluster_name, svm_name=svm_name, ls_volume_name_list=ls_volume_name_list)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return error_message

    # LSミラー用SnapMirror関係の初期化
    ret = initialize_ls_mirror_relationships(cluster_name=cluster_name, svm_name=svm_name)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return error_message

    # LSミラーのスケジュール設定
    job_schedule_name = 'hourly' # LSミラーに適用するjobスケジュール
    for ls_volume_name in ls_volume_name_list:
        ret = modify_snapmirror_relationship(cluster_name_dst=cluster_name, svm_name_dst=svm_name, vol_name_dst=ls_volume_name, job_schedule_name=job_schedule_name)
        # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
        if ret == False:
            return error_message

    """
    3. LIF作成
    """
    # LIFの作成
    for lif in lif_list:
        ret = create_lif(cluster_name=cluster_name, svm_name=svm_name, lif_name=lif['name'], home_node=lif['home_node'], home_port=home_port, ip=lif['ip'], netmask=lif['netmask'])
        # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
        if ret == False:
            return error_message

    """
    4. Vserver peer作成
    """
    # バックアップ用SVMとのピア関係作成
    ret = create_vserver_peer(cluster_name_src=cluster_name, svm_name_src=svm_name, cluster_name_dst=peer_cluster_name, svm_name_dst=backup_svm_name)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return error_message

    """
    5. デジタル証明書削除・再作成
    """
    # SVMデフォルトのSSL証明書のUUIDを取得
    ret = get_ssl_certification(cluster_name=cluster_name, svm_name=svm_name)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return error_message
    cert_uuid = ret['uuid']

    # SVMデフォルトのSSL証明書を削除
    ret = delete_ssl_certification(cluster_name=cluster_name, cert_uuid=cert_uuid)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return error_message

    # 再作成する
    ret = create_ssl_certification(cluster_name=cluster_name, svm_name=svm_name)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return error_message
    
    # 正常終了の場合のメッセージ
    print('INFO: SVM creation has been sunccessfully finished')
    print('INFO: If you need NFS volumes, execute "python3 create_nfs_volumes.py"')

# 結合テスト用
if __name__ == "__main__":
    args = sys.argv
    try:
        lif_list = eval(args[6])
    except:
        print('error1')
        sys.exit()

    if len(args) == 7:
        create_nfs_svm_main(cluster_name=args[1], svm_name=args[2], vlan_id=args[3], broadcast_domain_name=args[4], aggregate_name=args[5], lif_list=lif_list)

    else:
        print('error2')
        sys.exit()
