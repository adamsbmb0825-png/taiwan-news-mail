#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾株ニュース配信システム v5.0 キャッシュクリアスクリプト

【重要】
- このスクリプトはニュースキャッシュと論点キャッシュのみをクリアします
- HTMLテンプレート、銘柄プロファイル、除外ルール、デザイン設定は一切変更しません
- キャッシュクリア後の初回配信は通常通り v5.0 仕様で出力されます
"""

import json
import os
from datetime import datetime

CACHE_FILE = "/home/ubuntu/.taiwan_stock_news_cache_v5.json"

def clear_cache():
    """ニュースキャッシュと論点キャッシュをクリア"""
    
    print("=" * 60)
    print("台湾株ニュース配信システム v5.0 - キャッシュクリア")
    print("=" * 60)
    
    # 既存キャッシュの確認
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            news_count = len(cache.get('news', {}))
            topic_count = len(cache.get('topics', {}))
            url_count = len(cache.get('url_to_signature', {}))
            
            print(f"\n現在のキャッシュ:")
            print(f"  ニュースキャッシュ: {news_count}件")
            print(f"  論点キャッシュ: {topic_count}件")
            print(f"  URLマッピング: {url_count}件")
            
        except Exception as e:
            print(f"⚠️  キャッシュ読み込みエラー: {e}")
            cache = {}
    else:
        print("\nキャッシュファイルが存在しません")
        cache = {}
    
    # キャッシュをクリア
    new_cache = {
        "news": {},
        "topics": {},
        "url_to_signature": {},
        "cleared_at": datetime.now().isoformat(),
        "cleared_by": "clear_cache.py"
    }
    
    # 保存
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_cache, f, ensure_ascii=False, indent=2)
        
        print("\n✅ キャッシュクリア完了")
        print(f"  クリア日時: {new_cache['cleared_at']}")
        print("\n【確認事項】")
        print("  ✓ HTMLテンプレート: 変更なし")
        print("  ✓ 銘柄プロファイル: 変更なし")
        print("  ✓ 除外ルール: 変更なし")
        print("  ✓ デザイン設定: 変更なし")
        print("\n次回実行時は通常通り v5.0 仕様で配信されます。")
        
    except Exception as e:
        print(f"❌ キャッシュクリア失敗: {e}")

if __name__ == "__main__":
    clear_cache()
