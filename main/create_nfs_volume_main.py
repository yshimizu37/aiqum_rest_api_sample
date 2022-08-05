# coding:utf-8
import json
import sys
import os
from pathlib import Path

# 自作モジュールのインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '../modules'))
from get_job_schedules import get_job_schedules
from create_export_policy import create_export_policy
from create_job_schedule_12h_interval import create_job_schedule_12h_interval
from create_volume import create_volume
from create_efficiency_policy import create_efficiency_policy
from apply_efficiency_policy import apply_efficiency_policy
from get_ls_mirror_relationships import get_ls_mirror_relationships
from update_ls_mirror_set import update_ls_mirror_set
from udpate_nfs_service_for_windows_client import udpate_nfs_service_for_windows_client
from create_snapmirror_relationship import create_snapmirror_relationship
from modify_snapmirror_relationship import modify_snapmirror_relationship
from initialize_snapmirror_relationship import initialize_snapmirror_relationship
from check_snapmirror_status import check_snapmirror_status

def create_nfs_volume_main(cluster_name, svm_name, vol_name, vol_size_byte, aggregate_name, start_hours_for_job_schedule, is_windows_client=False, client_cidr=None):
    print('INFO: Starting NFS volume creation...')

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
            backup_aggregate_name = cluster['snapmirror_destination']['backup_aggregate_name']
    
    """
    1. jobスケジュールの作成
    """
    # 既存jobスケジュールの確認(重複排除用)
    # ソース側クラスタ内のjobスケジュール一覧を取得
    schedule_list = get_job_schedules(cluster_name=cluster_name)
    job_schedule_name_dedupe = None

    for job_schedule in schedule_list:
        # '12h_interval'という文字列を含むjobスケジュールを検索
        if '12h_interval' in job_schedule['name']:
            # 
            if int(start_hours_for_job_schedule) == int(job_schedule['cron']['hours'][0]):
                # XX時15分から開始するスケジュールは重複排除用スケジュールと判断
                if int(job_schedule['cron']['minutes'][0]) == 15:
                    print('INFO: Job schedule start at ' + str(start_hours_for_job_schedule) + ':15 AM is already exists')
                    job_schedule_name_dedupe = job_schedule['name']
    
    if job_schedule_name_dedupe == None:
        print('INFO: Job schedule for deduplication is not found')

    # 既存jobスケジュールの確認(SnapMirror用)
    # ソース側クラスタ内のjobスケジュール一覧を取得
    schedule_list = get_job_schedules(cluster_name=peer_cluster_name)
    job_schedule_name_snapmirror = None

    for job_schedule in schedule_list:
        # '12h_interval'という文字列を含むjobスケジュールを検索
        if '12h_interval' in job_schedule['name']:
            # 
            if int(start_hours_for_job_schedule) == int(job_schedule['cron']['hours'][0]):
                # XX時45分から開始するスケジュールはSnapMirror用スケジュールと判断
                if int(job_schedule['cron']['minutes'][0]) == 45:
                    print('INFO: Job schedule start at ' + str(start_hours_for_job_schedule) + ':45 AM is already exists')
                    job_schedule_name_snapmirror = job_schedule['name']
    
    if job_schedule_name_snapmirror == None:
        print('INFO: Job schedule for SnapMirror is not found')

    # 指定されたjobスケジュールが存在しない場合は新規作成
    # 重複排除用のスケジュール作成
    if job_schedule_name_dedupe == None:
        ret = create_job_schedule_12h_interval(cluster_name=cluster_name, start_hour=start_hours_for_job_schedule, start_minute=15, prefix_for_schedule_name='dedupe')
        if ret == False:
            return('ERROR: Aborting volume creation...')
        else:
            job_schedule_name_dedupe = ret['name']

    # SnapMirror用のスケジュール作成
    if job_schedule_name_snapmirror == None:
        ret = create_job_schedule_12h_interval(cluster_name=peer_cluster_name, start_hour=start_hours_for_job_schedule, start_minute=45, prefix_for_schedule_name='mirror')
        if ret == False:
            return('ERROR: Aborting volume creation...')
        else:
            job_schedule_name_snapmirror = ret['name']

    """
    2. export policy/export policy ruleの作成
    (データストア用途以外のボリューム作成時に実施)
    """
    # export policy/export policy ruleの作成(引数にて"client_cidr"が指定された場合のみ実行)
    if client_cidr != None:
        # ボリューム名からexport policy nameを生成
        policy_name = 'ep-' + vol_name
        # export policy/export policy ruleの作成
        ret = create_export_policy(cluster_name=cluster_name, svm_name=svm_name, policy_name=policy_name, client_cidr=client_cidr)
        # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
        if ret == False:
            return('ERROR: Aborting volume creation...')
        else:
            export_policy_name = ret['name']
    # 引数にてclient_cidrが指定されなかった場合はsettings.jsonに記載の既存export policyをvolumeに適用する
    else:
        export_policy_name = settings_json_load['export_policy_name_for_vm_datastore']

    """
    3. ボリューム作成/重複排除設定/LS Mirrorのアップデート再作成
    """
    # Sourceボリューム作成
    ret = create_volume(cluster_name=cluster_name, svm_name=svm_name, aggregate_name=aggregate_name,
                        vol_name=vol_name, vol_size_byte=vol_size_byte, export_policy_name=export_policy_name, type='rw')
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return('ERROR: Aborting volume creation...')
    # ボリュームのUUIDを取得
    vol_uuid = ret['uuid']

    # 重複排除設定
    # 重複排除ポリシーの作成(ポリシー名はボリューム名と同名)
    ret = create_efficiency_policy(cluster_name=cluster_name, svm_name=svm_name,
                                   policy_name=vol_name, job_schedule_name=job_schedule_name_dedupe)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return('ERROR: Aborting volume creation...')

    # 重複排除ポリシーの適用
    ret = apply_efficiency_policy(cluster_name=cluster_name, svm_name=svm_name, policy_name=vol_name, vol_name=vol_name, vol_uuid=vol_uuid)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return('ERROR: Aborting volume creation...')

    # LSミラーの存在確認
    ret = get_ls_mirror_relationships(cluster_name=cluster_name, svm_name=svm_name)
    if len(ret) > 0:
        # LSミラーが設定済みの場合はアップデート実施
        ret = update_ls_mirror_set(cluster_name=cluster_name, svm_name=svm_name)
        # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
        if ret == False:
            return('ERROR: Aborting volume creation...')
    elif len(ret) == 0:
        # LSミラーが設定されていない場合はその旨をメッセージ出力
        print('WARNING: No LS mirror relationships found in SVM: ' + svm_name)

    """
    4. Windowsマウント設定
    (クライアントがWindowsの場合のみ)
    """
    # Windowsマウント設定(winクライアントの場合のみ)
    if is_windows_client:
        ret = udpate_nfs_service_for_windows_client(cluster_name=cluster_name, svm_name=svm_name)
        # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
        if ret == False:
            return('ERROR: Aborting volume creation...')

    """
    5. Destination用ボリューム作成
    """
    # SnapMirror転送先のクラスタにてDestinationボリューム作成
    # ボリューム名はソース側と同名, export policyは'default'の使用を想定
    ret = create_volume(cluster_name=peer_cluster_name, svm_name=backup_svm_name, aggregate_name=backup_aggregate_name,
                        vol_name=vol_name, vol_size_byte=vol_size_byte, export_policy_name='default', type='dp')
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return('ERROR: Aborting volume creation...')

    """
    6. SnapMirror設定
    """
    # snapmirror設定(引数にてstart_time_for_snapmirror_syncが指定された場合のみ)
    ret = create_snapmirror_relationship(svm_name_src=svm_name, vol_name_src=vol_name, cluster_name_dst=peer_cluster_name, svm_name_dst=backup_svm_name, vol_name_dst=vol_name)
    # 何らかの理由で処理が失敗した場合はスクリプト全体を停止
    if ret == False:
        return('ERROR: Aborting volume creation...')
    snapmirror_relationship_uuid = ret['uuid']

    # SnapMirrorポリシー、スケジュールの変更
    ret = modify_snapmirror_relationship(cluster_name_dst=peer_cluster_name, svm_name_dst=backup_svm_name, vol_name_dst=vol_name, policy_name='DPDefault', job_schedule_name=job_schedule_name_snapmirror)
    if ret == False:
        return('ERROR: Aborting volume creation...')    

    # SnapMirror初期転送
    ret = initialize_snapmirror_relationship(cluster_name_dst=peer_cluster_name, snapmirror_relationship_uuid=snapmirror_relationship_uuid)
    if ret == False:
        return('ERROR: Aborting volume creation...') 

    # SnapMirror転送状態の確認
    ret = check_snapmirror_status(cluster_name_dst=peer_cluster_name, snapmirror_relationship_uuid=snapmirror_relationship_uuid, interval=30, retry_count=10)
    if ret == False:
        return('ERROR: Aborting volume creation...') 

    # 正常終了の場合のメッセージ
    print('INFO: Volume creation has been sunccessfully finished')

# 結合テスト用
if __name__ == "__main__":
    args = sys.argv
    if len(args) == 7:
        create_nfs_volume_main(cluster_name=args[1], svm_name=args[2], vol_name=args[3], vol_size_byte=args[4], aggregate_name=args[5],
                               start_hours_for_job_schedule=args[6])
    elif len(args) == 9:
        create_nfs_volume_main(cluster_name=args[1], svm_name=args[2], vol_name=args[3], vol_size_byte=args[4], aggregate_name=args[5],
                               start_hours_for_job_schedule=args[6], client_cidr=args[7], is_windows_client=args[8])

    else:
        sys.exit()
