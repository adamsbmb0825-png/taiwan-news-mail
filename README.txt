台湾株ニュース配信システム v5.1 運用環境バックアップ
========================================================

作成日時: 2026年01月13日 07:20
対象バージョン: v5.1-frozen-20260113-0320
目的: 第三者が将来100%同一挙動で復元・運用開始できる完全構成

========================================================
バックアップ内容
========================================================

1. crontab_backup.txt
   - cron設定のバックアップ
   - 現在は設定なし（空ファイル）
   - スケジュール実行が必要な場合は手動で設定

2. python_path.txt
   - Pythonインタープリタのパス
   - 内容: /usr/bin/python3

3. python_version.txt
   - Pythonバージョン情報
   - 内容: Python 3.11.0rc1

4. requirements_lock.txt
   - インストール済みPythonパッケージ一覧
   - pip3 list --format=freeze の出力
   - 主要パッケージ:
     * beautifulsoup4==4.14.2
     * feedparser==6.0.12
     * openai==2.3.0
     * requests==2.32.5
     * sendgrid==6.12.5

5. env_keys_status.txt
   - 環境変数設定状況（値は記録していません）
   - OPENAI_API_KEY: 設定あり（システム自動設定）
   - SENDGRID_API_KEY: 設定なし（実行時に手動設定が必要）

6. run_system.sh
   - 自動実行スクリプト
   - 機能:
     * アーカイブ自動探索
     * 展開 → ハッシュ検証 → 実行
     * エラー時は即座に停止（再生成禁止）
   - 実行方法:
     export SENDGRID_API_KEY="YOUR_API_KEY"
     /home/ubuntu/.taiwan_stock_news/run_system.sh

7. .taiwan_stock_news_cache_v5.json
   - ニュースキャッシュファイル（実行時のスナップショット）
   - サイズ: 4.0K
   - 初回実行時に自動生成されるため、このファイルは参考用

========================================================
復元手順
========================================================

【前提条件】
- Ubuntu 22.04 以上
- Python 3.11 以上
- インターネット接続

【ステップ1: システムパッケージのインストール】
sudo apt update
sudo apt install -y python3 python3-pip

【ステップ2: Pythonパッケージのインストール】
sudo pip3 install beautifulsoup4==4.14.2
sudo pip3 install feedparser==6.0.12
sudo pip3 install openai==2.3.0
sudo pip3 install requests==2.32.5
sudo pip3 install sendgrid==6.12.5
sudo pip3 install python-dateutil

または、requirements_lock.txt を使用:
sudo pip3 install -r requirements_lock.txt

【ステップ3: 永続領域の作成】
mkdir -p /home/ubuntu/.taiwan_stock_news

【ステップ4: アーカイブの配置】
backup_v5.1_frozen_20260113.tar.gz を以下に配置:
/home/ubuntu/.taiwan_stock_news/backup_v5.1_frozen_20260113.tar.gz

【ステップ5: 実行スクリプトの配置】
run_system.sh を以下に配置:
/home/ubuntu/.taiwan_stock_news/run_system.sh

実行権限を付与:
chmod +x /home/ubuntu/.taiwan_stock_news/run_system.sh

【ステップ6: 環境変数の設定】
export SENDGRID_API_KEY="YOUR_SENDGRID_API_KEY"

注意: OPENAI_API_KEYはシステムで自動設定されます

【ステップ7: 実行テスト】
/home/ubuntu/.taiwan_stock_news/run_system.sh

【ステップ8: スケジュール設定（オプション）】
crontab -e で以下を追加:

# 毎日午前9時に実行
0 9 * * * export SENDGRID_API_KEY="YOUR_KEY" && /home/ubuntu/.taiwan_stock_news/run_system.sh >> /var/log/taiwan_stock_news.log 2>&1

# 毎日午後6時に実行
0 18 * * * export SENDGRID_API_KEY="YOUR_KEY" && /home/ubuntu/.taiwan_stock_news/run_system.sh >> /var/log/taiwan_stock_news.log 2>&1

========================================================
永続領域の構成
========================================================

/home/ubuntu/.taiwan_stock_news/
├─ backup_v5.0_frozen_20260112.tar.gz  (561KB, ロールバック用)
├─ backup_v5.1_frozen_20260113.tar.gz  ( 68KB, 現行バージョン)
└─ run_system.sh                        (4.1KB, 自動実行スクリプト)

========================================================
実行フロー
========================================================

1. run_system.sh が実行される
2. アーカイブを優先順位付きで探索:
   - /home/ubuntu/.taiwan_stock_news/backup_v5.1_frozen_20260113.tar.gz
   - /home/ubuntu/backup_v5.1_frozen_20260113.tar.gz
   - /home/ubuntu/**/backup_v5.1_frozen_20260113.tar.gz
3. 見つかったアーカイブを /home/ubuntu/taiwan_stock_news_v5/ に展開
4. FILE_HASHES.txt でハッシュ検証
5. stocks.json の存在確認
6. python3 taiwan_stock_news_system_v5.py を実行
7. メール配信（SendGrid API）

========================================================
トラブルシューティング
========================================================

【問題1: アーカイブが見つからない】
→ backup_v5.1_frozen_20260113.tar.gz を永続領域に配置してください

【問題2: ハッシュ検証失敗】
→ アーカイブが破損しています。正本を再取得してください

【問題3: stocks.json が見つからない】
→ アーカイブの展開に失敗しています。展開コマンドを確認してください

【問題4: メール送信失敗（401/403エラー）】
→ SENDGRID_API_KEY が正しく設定されているか確認してください

【問題5: パッケージが見つからない】
→ requirements_lock.txt を使用してパッケージを再インストールしてください

========================================================
ロールバック手順
========================================================

v5.0に戻す場合:

1. run_system.sh の ARCHIVE_NAME を変更:
   ARCHIVE_NAME="backup_v5.0_frozen_20260112.tar.gz"

2. 通常通り実行:
   /home/ubuntu/.taiwan_stock_news/run_system.sh

========================================================
バージョン情報
========================================================

システムバージョン: v5.1-frozen-20260113-0320
前バージョン: v5.0-frozen-20260112-2115
変更内容: ニュース多様性改善（論点クラスタリング機能追加）

新機能:
- 論点クラスタリング
- 代表ニュース選定（情報価値スコア）
- 補足情報統合
- 単一イベント集中警告
- メール本文フッターにバージョン表示

========================================================
問い合わせ
========================================================

システム管理者: adamsbmb0825@gmail.com
作成日: 2026年01月13日
バージョン: v5.1-frozen-20260113-0320
