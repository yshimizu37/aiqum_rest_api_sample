
# AIQUM REST API/ONTAP REST APIを活用したサンプルスクリプト
## はじめに
- 本スクリプトはActive IQ Unified Manager(以下、AIQUM)ならびにONTAPのREST APIに関して、実践的な活用例を示す目的で作成しております
    1. NFS接続用ボリューム作成
    1. NFS接続用SVM作成
- お客様環境での動作を保証するものではなく、本スクリプトを実行したことによるいかなる不具合やトラブル等については責任を負いかねます
- 開発/動作確認に使用した環境
    - ストレージ装置
        - FAS-2650/AFF-A200
        - ONTAP 9.9.1
        - AIQUM 9.10
    - スクリプト実行環境
        - macOS Monterey, Ubuntu 18.04.5 LTS
        - python 3.6.9, 3.8.2

## スクリプト実行における前提条件
### 共通
- スクリプトを実行する端末にpython3がインストールされていること
    - インストールが必要なサードパーティライブラリ(動作確認したバージョン)
        - netaddr(0.8.0)
        - requests(2.25.1)
- スクリプトを実行する端末からAIQUMにアクセス可能であること
- 作業対象のONTAPクラスタがsettings.jsonに記載したAIQUM配下に登録されていること
- AIQUMのAPI gateway機能が有効化されていること
- 作業対象のONTAPクラスタにてhttp/httpsアクセスが有効化されていること
- 作業対象のONTAPクラスタにてsettings.jsonに記載のSnapMirror転送先クラスタとのクラスタピア関係が作成済みであること
- SnapMirror先クラスタにてsettings.jsonに記載のバックアップ用のSVMが作成済みであること

### 1. NFS接続用ボリューム作成
- ボリューム作成先のSVMが作成済みであること
- ボリューム作成先のSVMとsettings.jsonに記載のSnapMirror転送先のバックアップ用SVMの間でSVMピア関係が作成済みであること
- 作成するボリュームに関して以下の情報が揃っていること
    - クラスタ名
    - SVM名
    - ボリューム名
    - ボリュームサイズ
    - アグリゲート名
    - 重複排除ならびにSnapMirrorの開始時刻(0-11時の間で指定)
        - job scheduleは12時間インターバルで設定
            - 重複排除は15分開始、SnapMirrorは45分開始の設定
        - 例：5時を指定した場合
            - 重複排除: 5:15, 17:15に実行
            - SnapMirror: 5:45, 17:45に実行
    - ボリューム用途(NFSデータストア用かそれ以外か)
    - データストア用以外の場合
        - アクセスを許可するクライアントのCIDR
        - Windowsクライアント向け設定の必要有無

### 2. NFS接続用SVM作成
- 作成するSVMに関して以下の情報が揃っていること
    - SVM名
    - クラスタ名(手動で設定する場合)
    - アグリゲート名(手動で設定する場合)
    - VLAN ID
    - Broadcast Domain名
    - LIFの情報
        - LIF名
        - IPアドレス
        - サブネットマスク
        - home-node


## スクリプト実行前の初期設定
初回のスクリプト実行時のみ、お使いの環境に合わせてsetting.jsonのパラメータを変更してください
- aiqum: AIQUMサーバに関する情報を記載
    - ip: AIQUMの管理IP
    - cred: AIQUMの認証情報(例：admin:P@ssw0rd)をBase64でエンコーディングした文字列
    - verify: AIQUMにて自己証明書を利用している場合は0を指定
- clusters: SVMならびにボリュームの払い出し対象となるクラスタを記載(複数指定可)
    - name: クラスタ名を記載
    - base_port: SVMのデータ通信用ポートとして使用する物理ポート名(例：e0a, a0a)を記載
    - mtu: 作成するVLANポートに設定するMTUの値を記載
    - snapmirror_destination: SnapMirror転送先クラスタに関する情報を記載
        - peer_cluster_name: SnapMirror転送先のクラスタ名を記載(※要クラスタピア関係)
        - backup_svm_name: SnapMirror転送先クラスタ内に作成済みのバックアップ用SVMの名称を記載
        - backup_aggregate_name: DPボリュームを作成する先のアグリゲート名を記載
- export_policy_name_for_vm_datastore: データストア用NFSボリュームに設定するexport policyの名称を指定


## 基本的な使用方法
sample_codeディレクトリ直下にあるpythonスクリプトを実行してください
###  1. NFS接続用ボリューム作成
```
# スクリプトの実行
# 以下、対話式で作成するボリュームの内容を入力する
yshimizu@yshimizu-mac-0 sample_code % python3 create_nfs_volume.py
ONTAP cluster name: ps-2650-cl
SVM name: rest_test_09
volume type(1: NFS datastore for vSphere, 2: other): 1
volume name: test1
volume size(unit: GB/TB): 100GB
aggregate name: aggr1_node2
start hour for dedupelication and snapmirror sync(0-11)): 0

# 入力内容の確認が促されるため、問題なければ"Y"を入力
*****************************
Summary of volume creation
*****************************
cluster_name: ps-2650-cl
svm_name: rest_test_09
vol_name: test1
vol_size_byte: 100GB
aggregate_name: aggr1_node2
start_time_for_snapmirror_sync: 0


Are you sure want to create this volume?(Y/N): Y

# 以下、メインスクリプトの実行ログ
INFO: Starting NFS volume creation...
INFO: Job schedule for deduplication is not found
INFO: Job schedule for SnapMirror is not found
INFO: Creating job schedule...
INFO: Successfully created job shedule: dedupe0015_start_12h_interval
INFO: Creating job schedule...
INFO: Successfully created job shedule: mirror0045_start_12h_interval
INFO: Creating source volume...
INFO: Successfully created volume: test1
INFO: Creating efficiency policy...
INFO: Successfully created efficiency-policy: test1
INFO: Apppling efficiency policy...
INFO: Successfully enabled volume efficiency:test1
INFO: Successfully applied efficiency-policy:test1 to volume:test1
INFO: Getting LS mirror relationships...
INFO: Successfully found svm root volume for: rest_test_09
INFO: Successfully got relationships:ps-2650-cl://rest_test_09/rest_test_09_root
INFO: Updating LS mirror relationships...
INFO: Successfully found svm root volume for: rest_test_09
INFO: Successfully updated relationships for: ps-2650-cl://rest_test_09/rest_test_09_root
INFO: Creating destination volume...
INFO: Successfully created volume: test1
INFO: Creating SnapMirror relationship...
INFO: Successfully created SnapMirror relationship: rest_test_09:test1 -> s3test:test1
INFO: Modifying SnapMirror relationship...
INFO: Successfully modified relationships for: s3test:test1
INFO: Initializing SnapMirror relationship...
INFO: Successfully started initializing relationships for: de61e3f9-13ed-11ed-ad45-00a098f0b86b
INFO: Monitoring SnapMirror transfer status...
INFO: Successfully got relationships for: de61e3f9-13ed-11ed-ad45-00a098f0b86b
INFO: Transfering status: transferring
INFO: Remaining retry count:10
INFO: Waiting 30 seconds for next check
INFO: Successfully got relationships for: de61e3f9-13ed-11ed-ad45-00a098f0b86b
INFO: Transfering status: transferring
INFO: Remaining retry count:9
INFO: Waiting 30 seconds for next check
INFO: Successfully got relationships for: de61e3f9-13ed-11ed-ad45-00a098f0b86b
INFO: Transfering status: transferring
INFO: Remaining retry count:8
INFO: Waiting 30 seconds for next check
INFO: Successfully got relationships for: de61e3f9-13ed-11ed-ad45-00a098f0b86b
INFO: Transfering status: transferring
INFO: Remaining retry count:7
INFO: Waiting 30 seconds for next check
INFO: Successfully got relationships for: de61e3f9-13ed-11ed-ad45-00a098f0b86b
INFO: Transfering status: transferring
INFO: Remaining retry count:6
INFO: Waiting 30 seconds for next check
INFO: Successfully got relationships for: de61e3f9-13ed-11ed-ad45-00a098f0b86b
INFO: Transfering status: success
INFO: Snapmirror transfer has been completed
INFO: Volume creation has been sunccessfully finished
```


###  2. NFS接続用SVM作成
```
# スクリプトの実行
# 以下、対話式で作成するSVMの内容を入力する
yshimizu@yshimizu-mac-0 sample_code % python3 create_nfs_svm.py
SVM name: rest_test_10

# 現在のアグリゲート空き容量をもとにSVM作成先として推奨されるクラスタ、アグリゲートが表示される
# 手動でクラスタ名、アグリゲート名を指定する場合は"N"を入力
*****************************
Recommended Cluster: PS-A220(2.7% used)
Recommended Aggregate: aggr1_node1(1.3% used)
*****************************
Do you use this recommended cluster and aggregate?(Y/N): Y
VLAN ID: 2000
Broadcast-domain name: vlan2000
How many LIFs do you need?(1-4): 1
LIF-1's name: lif1
LIF-1's IP address: 10.aa
Input parameter is invalid
LIF-1's IP address: 192.168.0.30
LIF-1's netmask: 255.255.255.0
LIF-1's home-node: ps-2650-cl-01
LIF-1's home-node: PS-A220-01

# 入力内容の確認が促されるため、問題なければ"Y"を入力
*****************************
Summary of SVM creation
*****************************
svm_name: rest_test_10
cluster_name: PS-A220
aggregate_name: aggr1_node1
vlan_id: 2000
broadcast-domain: vlan2000
LIFs: [{'name': 'lif1', 'ip': '192.168.0.30', 'netmask': '255.255.255.0', 'home_node': 'PS-A220-01'}]


Are you sure want to create this SVM?(Y/N): Y

# 以下、メインスクリプトの実行ログ
# SVM内にボリュームを作成する場合は本スクリプトの完了後に"create_nfs_volumes.py"を実行すること

INFO: Starting NFS volume creation...
INFO: VLAN:2000 is not exist in cluster:PS-A220
INFO: Creating broadcast domain...
INFO: Successfully created broadcast domain: vlan2000
INFO: Creating VLAN enabled port...
INFO: Creating VLAN enabled port for node: PS-A220-01
INFO: Successfully created port:a0a-2000 on node:PS-A220-01
INFO: Creating VLAN enabled port for node: PS-A220-02
INFO: Successfully created port:a0a-2000 on node:PS-A220-02
INFO: Creating SVM...
INFO: Successfully created svm: rest_test_10
INFO: Creating NFS service...
INFO: Successfully created nfs service on the svm: rest_test_10
INFO: Searching default export-policy id...
INFO: Successfully got default export-policy id: 154618822657
INFO: Creating export-policy rule for default export-policy...
INFO: Successfully created export-policy rule
INFO: Creating DP volume for load-sharing mirror...
INFO: Successfully found svm root volume for: rest_test_10
INFO: Creating dp volume:rest_test_10_root_m1 on aggregate:aggr1_node1
INFO: Successfully created dp volume: rest_test_10_root_m1
INFO: Creating dp volume:rest_test_10_root_m2 on aggregate:aggr1_node2
INFO: Successfully created dp volume: rest_test_10_root_m2
INFO: Creating load-sharing mirror relationships...
INFO: Successfully found svm root volume for: rest_test_10
INFO: Successfully created SnapMirror relationship: rest_test_10:rest_test_10_root -> rest_test_10:rest_test_10_root_m1
INFO: Successfully created SnapMirror relationship: rest_test_10:rest_test_10_root -> rest_test_10:rest_test_10_root_m2
INFO: Successfully finished creating all load-sharing mirror relationships
INFO: Initializing load-sharing mirror relationships...
INFO: Successfully found svm root volume for: rest_test_10
INFO: Successfully initialized SnapMirror relationships for :rest_test_10:rest_test_10_root
INFO: Modifying SnapMirror relationship...
INFO: Successfully modified relationships for: rest_test_10:rest_test_10_root_m1
INFO: Modifying SnapMirror relationship...
INFO: Successfully modified relationships for: rest_test_10:rest_test_10_root_m2
INFO: Creating a LIF...
INFO: Successfully created LIF: lif1
INFO: Creating vserver peer relationship for SnapMirror...
INFO: Successfully created verver peer relationship: rest_test_10 -> opt-test
INFO: Successfully getting pending relationship: rest_test_10 -> opt-test
INFO: Successfully accepted verver peer relationship: rest_test_10 -> opt-test
INFO: Getting SSL certification...
INFO: Finished getting SSL certification for SVM:rest_test_10
INFO: Deleting original SSL certification...
INFO: Successfully deleted SSL certification for :34c26b7b-13f8-11ed-ad45-00a098f0b86b
INFO: Creating a new SSL certification...
INFO: Successfully created SSL certification for SVM:rest_test_10
INFO: SVM creation has been sunccessfully finished
INFO: If you need NFS volumes, execute "python3 create_nfs_volumes.py"
```

## その他仕様、制限事項等
- REST API実行中に何らかのエラーが発生した時点でスクリプト全体を停止します
    - レスポンスコードが"200"または"201"以外の場合にエラーとみなします
    - 異常終了時も途中経過で作成されたストレージオブジェクト(例：jobスケジュール, export-policy)は自動で削除されませんので、スクリプトを再実行する際は事前にこれらのオブジェクトを削除してください