# 台湾株ニュース配信システム v5.0 完全凍結バックアップ

**バージョン名:** v5.0-frozen-20260112-2115  
**作成日時:** 2026年1月12日 21:15（台湾時間）  
**状態:** 本番運用で正常動作していた状態を凍結したバックアップである

---

## このバックアップについて

このバックアップは、2026年1月12日時点で本番運用中の台湾株ニュース配信システム v5.0 の完全な状態を凍結したものです。

**重要:** このバックアップに含まれるファイルは、すべて実際に動作していた正本をそのままコピーしたものです。再生成・書き換え・最適化・補完・推測による変更は一切行っていません。

---

## 復元手順

### 前提条件

- Ubuntu 22.04 以上
- Python 3.11 以上
- 以下のパッケージがインストール済み:
  - `feedparser`
  - `requests`
  - `python-dateutil`
  - `sendgrid`
  - `pytz`
  - `openai`

### ステップ1: バックアップの展開

```bash
cd /home/ubuntu
tar -xzf backup_v5.0_frozen_20260112.tar.gz
cd backup_v5.0_frozen_20260112
```

### ステップ2: ファイルの配置

```bash
# メインスクリプト
cp taiwan_stock_news_system_v5.py /home/ubuntu/

# HTMLテンプレート
cp email_template_v5.py /home/ubuntu/

# 銘柄プロファイル
cp stocks.json /home/ubuntu/

# システム設定
cp system_config.json /home/ubuntu/

# キャッシュクリアスクリプト
cp clear_cache.py /home/ubuntu/
chmod +x /home/ubuntu/clear_cache.py

# キャッシュファイル（オプション）
cp .taiwan_stock_news_cache_v5.json /home/ubuntu/
```

### ステップ3: 環境変数の設定

```bash
export SENDGRID_API_KEY="YOUR_SENDGRID_API_KEY"
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

### ステップ4: 実行

```bash
cd /home/ubuntu
python3 taiwan_stock_news_system_v5.py
```

---

## ファイル検証

復元後、以下のハッシュ値と一致することを確認してください:

```
f11060943f785545adf2e82e869c05d022058d97a6f0d57549bba840b5029aa1  taiwan_stock_news_system_v5.py
4cffb73cfd4f181af92cf39b9b415af0bc776dba7d0c6f6a670835f378daed8b  email_template_v5.py
d0a78a4f4ff3a880b27a922241c5006baf8eb26fd9ffd779dd6d0136fd9f6dd2  stocks.json
```

検証コマンド:

```bash
sha256sum taiwan_stock_news_system_v5.py email_template_v5.py stocks.json
```

---

## キャッシュクリア

ニュースキャッシュと論点キャッシュをクリアする場合:

```bash
python3 /home/ubuntu/clear_cache.py
```

**重要:** このスクリプトは、ニュースキャッシュと論点キャッシュのみをクリアします。HTMLテンプレート、銘柄プロファイル、除外ルール、デザイン設定は一切変更しません。

---

## トラブルシューティング

### メール送信エラー

**エラー:** `Unauthorized`

**原因:** SendGrid API キーが未設定または無効

**解決方法:**
1. SendGrid API キーを確認
2. 環境変数 `SENDGRID_API_KEY` を設定
3. 送信元アドレス（FROM）が SendGrid で認証済みであることを確認

### 宇瞻（8271）のニュースが0件

**原因:** RSSフィードまたはキーワードマッチングの問題

**解決方法:**
1. このバックアップの `taiwan_stock_news_system_v5.py` を使用していることを確認
2. 宇瞻専用のRSSフィード3本が含まれていることを確認（118-120行目）
3. キーワードマッチングに「Apacer」が含まれていることを確認（567-570行目）

### 「出典不明」が表示される

**原因:** 古いテンプレートを使用している

**解決方法:**
1. このバックアップの `email_template_v5.py` を使用していることを確認
2. 112行目が `source = item.get('publisher', '')` であることを確認
3. 147行目が条件付き表示になっていることを確認

---

## 注意事項

1. **再生成禁止:** このバックアップのファイルを再生成しないでください。既存のファイルをそのまま使用してください。

2. **変更禁止:** 動作に問題がない限り、ファイルの内容を変更しないでください。

3. **キャッシュとスクリプトの分離:** キャッシュクリアはスクリプト・テンプレートに影響しません。

4. **バージョン管理:** メールフッターにバージョン情報が表示されます。問題発生時に即座に特定可能です。

---

## サポート

このバックアップに関する質問や問題がある場合は、プロジェクト管理者に連絡してください。

**バックアップ作成者:** Manus AI Agent  
**バックアップ日時:** 2026年1月12日 21:15  
**バージョン:** v5.0-frozen-20260112-2115
