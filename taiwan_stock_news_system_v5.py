#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾株ニュース配信システム v5.3
- 2段階フォールバック方式（直近7日 -> 30日）
- 遅延価値判定モジュール統合
- ニュースクラスタリング機能（v5.1）
- 投資判断補助ニュース（株価フェーズ整理）機能（v5.3新機能）
"""

import os
import sys
import json
import time
import feedparser
import requests
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from openai import OpenAI
from email_template_v5 import create_email_body, send_email_via_sendgrid
from news_clustering import cluster_news_by_topic, prepare_delivery_news, print_clustering_log
from delayed_valuable_news import is_delayed_but_valuable
from stock_price_analyzer import get_stock_price_data
from investment_aux_generator import generate_investment_aux_news

# ============================================================
# 設定・定数
# ============================================================

VERSION = "v5.3-20260121"

# タイムゾーン設定 (JST)
JST = timezone(timedelta(hours=9))

# APIキー設定
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL")

if not SENDGRID_API_KEY or not RECIPIENT_EMAIL:
    print("エラー: 環境変数 SENDGRID_API_KEY または RECIPIENT_EMAIL が設定されていません。", flush=True)
    sys.exit(1)

# OpenAI クライアント初期化
client = OpenAI()

# 銘柄リスト読み込み
def load_stocks():
    try:
        with open('stocks.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # "stocks" キーがある場合はその中身を返す、なければそのまま返す（互換性維持）
            return data.get('stocks', data)
    except FileNotFoundError:
        print("エラー: stocks.json が見つかりません。", flush=True)
        return {}
    except json.JSONDecodeError as e:
        print(f"エラー: stocks.json の形式が不正です: {e}", flush=True)
        return {}

STOCKS = load_stocks()

# RSSフィード（v5.2-lite: 30件に削減、多面性維持）
RSS_FEEDS = [
    # ========================================
    # カテゴリ① 銘柄直結クエリ（10件）
    # ========================================
    
    # 台積電（2330） - 3件
    "https://news.google.com/rss/search?q=台積電+OR+TSMC&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=TSMC&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=TSMC&hl=ja&gl=JP&ceid=JP:ja",
    
    # 創見（2451） - 2件
    "https://news.google.com/rss/search?q=創見+OR+Transcend&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=創見+OR+Transcend&hl=ja&gl=JP&ceid=JP:ja",
    
    # 宇瞻（8271） - 2件
    "https://news.google.com/rss/search?q=宇瞻+OR+Apacer&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=Apacer&hl=en-US&gl=US&ceid=US:en",
    
    # 廣達（2382） - 3件
    "https://news.google.com/rss/search?q=廣達+OR+Quanta&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=Quanta+Computer&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=廣達+OR+Quanta&hl=ja&gl=JP&ceid=JP:ja",
    
    # ========================================
    # カテゴリ② 上流ドライバークエリ（13件）
    # ========================================
    
    # 技術キーワード（6件）
    "https://news.google.com/rss/search?q=EUV&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=CoWoS&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=HBM&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=液冷&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=先進製程&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=先進封裝&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    
    # 顧客・プラットフォーム（3件）
    "https://news.google.com/rss/search?q=NVIDIA&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=AI伺服器&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=GB200&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    
    # 政策・地政学（2件）
    "https://news.google.com/rss/search?q=美國廠&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=關稅&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    
    # 需給・供給制約（2件）
    "https://news.google.com/rss/search?q=DRAM價格&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=產能&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    
    # ========================================
    # カテゴリ③ 業績・イベントクエリ（4件）
    # ========================================
    
    "https://news.google.com/rss/search?q=台積電+營收&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=創見+營收&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=宇瞻+營收&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=廣達+營收&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
]

# 除外ドメイン・キーワード設定
EXCLUDED_DOMAINS = [
    'ptt.cc', 'dcard.tw', 'mobile01.com', 'facebook.com', 'instagram.com',
    'youtube.com', 'wikipedia.org', 'amazon.com', 'ruten.com.tw', 'shopee.tw'
]

EXCLUDED_KEYWORDS = [
    '股市爆料同學會', '討論區', '懶人包', '優惠', '折扣', '開箱', '評測',
    '謠言', '八卦', 'PTT', 'Dcard', 'Mobile01'
]

# ============================================================
# 関数定義
# ============================================================

def fetch_rss_feeds(days_back=7):
    """RSSフィードからニュースを収集"""
    all_entries = []
    seen_links = set()
    
    cutoff_date = datetime.now(JST) - timedelta(days=days_back)
    print(f"📰 RSSフィードからニュース収集中... (過去{days_back}日分)", flush=True)
    
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # 日付フィルタリング
                published = None
                if hasattr(entry, 'published_parsed'):
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(JST)
                
                if published and published < cutoff_date:
                    continue
                
                # 重複チェック
                if entry.link in seen_links:
                    continue
                
                seen_links.add(entry.link)
                
                # 必要な情報を抽出
                all_entries.append({
                    'title': entry.title,
                    'link': entry.link,
                    'published': published,
                    'source': entry.source.title if hasattr(entry, 'source') else 'Unknown',
                    'summary': entry.summary if hasattr(entry, 'summary') else ''
                })
                
        except Exception as e:
            print(f"  ⚠️ フィード取得エラー: {url} - {e}", flush=True)
            
    print(f"  RSS収集完了: {len(all_entries)}件", flush=True)
    return all_entries

def resolve_redirects(entries):
    """Google Newsの短縮URLを展開"""
    print(f"🔗 URL解決中（{len(entries)}件）...", flush=True)
    
    # 件数が多い場合は最新のものに絞る
    if len(entries) > 100:
        print("  ⚠️ 件数が多いため、最新100件のみ処理します", flush=True)
        entries = sorted(entries, key=lambda x: x['published'] or datetime.min, reverse=True)[:100]
    
    resolved_entries = []
    
    # セッションの再利用
    session = requests.Session()
    
    for entry in entries:
        try:
            # Google Newsのリンクかどうかチェック
            if 'news.google.com' in entry['link']:
                # HEADリクエストでリダイレクト先を取得（高速化）
                response = session.head(entry['link'], allow_redirects=True, timeout=5)
                entry['link'] = response.url
            
            # 除外ドメインチェック
            domain = entry['link'].split('/')[2] if len(entry['link'].split('/')) > 2 else ''
            if any(ex in domain for ex in EXCLUDED_DOMAINS):
                continue
                
            resolved_entries.append(entry)
            
        except Exception:
            # エラー時は元のリンクのまま追加（または除外）
            resolved_entries.append(entry)
            
    print(f"✅ 重複除外後: {len(resolved_entries)}件", flush=True)
    return resolved_entries

def analyze_relevance_with_llm(entry, stock_code, stock_info, is_fallback_mode=False):
    """LLMを使用してニュースの関連性を判定"""
    
    # 判定基準の構築
    criteria = f"""
    1. 銘柄「{stock_info['name']}」({stock_code}) の業績、製品、技術、受注、提携に直接関係するか。
    2. 競合他社や業界全体の動向で、この銘柄に重大な影響を与えるか。
    3. 単なる市況概況や、名前が出ているだけの記事は除外する。
    """
    
    if is_fallback_mode:
        criteria += """
    4. 【重要】記事の日付が古くても、現在も有効な情報（技術解説、長期展望、構造的な変化など）は「関連あり」とする。
    5. 短期的な株価変動や、すでに終了したイベントの速報は除外する。
        """
    
    prompt = f"""
    以下のニュース記事が、投資家にとって「{stock_info['name']}」の分析に役立つ重要な情報を含んでいるか判定してください。
    
    タイトル: {entry['title']}
    ソース: {entry['source']}
    概要: {entry['summary']}
    
    判定基準:
    {criteria}
    
    JSON形式で回答してください:
    {{
        "is_relevant": true/false,
        "reason": "判定理由（日本語、50文字以内）",
        "summary": "記事の要約（日本語、100文字以内。投資判断に役立つ具体的な事実を中心に）"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "あなたは台湾株の専門アナリストです。厳格に情報の価値を判定します。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # フォールバックモードかつ「関連なし」の場合、遅延価値判定を試行
        if is_fallback_mode and not result['is_relevant']:
            is_valuable, reason = is_delayed_but_valuable(entry, stock_info)
            if is_valuable:
                result['is_relevant'] = True
                result['reason'] = f"【遅延価値あり】{reason}"
                
        return result
        
    except Exception as e:
        return {"is_relevant": False, "reason": f"エラー: {e}", "summary": ""}

def process_stock_news(stock_code, stock_info, all_entries, is_fallback_mode=False):
    """特定の銘柄に関するニュースを処理"""
    print(f"============================================================", flush=True)
    print(f"📊 {stock_info['name']}（{stock_code}）", flush=True)
    print(f"============================================================", flush=True)
    
    # キーワードフィルタリング（1次選別）
    keywords = [stock_info['name'], stock_code]
    if 'keywords' in stock_info:
        keywords.extend(stock_info['keywords'])
        
    candidates = []
    for entry in all_entries:
        text = (entry['title'] + ' ' + entry['summary']).lower()
        if any(k.lower() in text for k in keywords):
            candidates.append(entry)
            
    print(f"候補ニュース: {len(candidates)}件", flush=True)
    
    # 候補が多すぎる場合は絞り込み（LLMコスト削減）
    # フォールバックモード時は上限を厳しくする（10件）、通常時は60件
    limit = 10 if is_fallback_mode else 60
    if len(candidates) > limit:
        candidates = sorted(candidates, key=lambda x: x['published'] or datetime.min, reverse=True)[:limit]
    
    # 2. LLMによる関連性判定
    relevant_news = []
    news_summaries_for_aux = [] # 投資判断補助用の要約リスト
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_entry = {
            executor.submit(analyze_relevance_with_llm, entry, stock_code, stock_info, is_fallback_mode): entry 
            for entry in candidates
        }
        
        for future in as_completed(future_to_entry):
            entry = future_to_entry[future]
            try:
                result = future.result()
                if result['is_relevant']:
                    entry['llm_result'] = result
                    relevant_news.append(entry)
                    news_summaries_for_aux.append(result['summary'])
                    print(f"  ✅ {entry['title'][:30]}...", flush=True)
                else:
                    # print(f"  ❌ {entry['title'][:30]}...", flush=True)
                    pass
            except Exception:
                pass
                
    print(f"✅ 関連ニュース: {len(relevant_news)}件", flush=True)
    
    # 3. ニュースクラスタリング（v5.1機能）
    clustered_news = []
    if relevant_news:
        # 引数順序修正: (stock_name, relevant_news)
        clusters = cluster_news_by_topic(stock_info['name'], relevant_news)
        print_clustering_log(stock_info['name'], clusters)
        clustered_news = prepare_delivery_news(clusters)
        print(f"✅ 配信: {len(clustered_news)}クラスタ", flush=True)
    
    # 4. 投資判断補助ニュース生成（v5.3新機能）
    # ニュースがなくても株価データはあるので必ず生成する
    print(f"📉 投資判断補助レポート生成中...", flush=True)
    
    # 株価データ取得
    price_data = get_stock_price_data(stock_code)
    
    # レポート生成
    investment_aux = generate_investment_aux_news(
        stock_code, 
        stock_info['name'], 
        price_data, 
        news_summaries_for_aux
    )
    print(f"✅ 投資判断補助レポート生成完了", flush=True)
    
    return {
        'stock_code': stock_code,
        'stock_name': stock_info['name'],
        'news': clustered_news,
        'investment_aux': investment_aux, # 追加
        'news_count': len(relevant_news)
    }

def main():
    print("============================================================", flush=True)
    print(f"台湾株ニュース配信システム {VERSION}", flush=True)
    print("============================================================", flush=True)
    
    # 第1段階: 直近7日モード
    print("=== 第1段階: 直近7日モード ===", flush=True)
    all_entries = fetch_rss_feeds(days_back=7)
    all_entries = resolve_redirects(all_entries)
    
    results = {}
    stocks_needing_fallback = []
    
    for stock_code, stock_info in STOCKS.items():
        result = process_stock_news(stock_code, stock_info, all_entries, is_fallback_mode=False)
        results[stock_code] = result
        
        # ニュースが0件の場合はフォールバック対象に追加
        if result['news_count'] == 0:
            stocks_needing_fallback.append(stock_code)
            
    # 第2段階: 30日フォールバックモード（対象銘柄のみ）
    if stocks_needing_fallback:
        print("\n=== 第2段階: 30日フォールバックモード ===", flush=True)
        print(f"対象銘柄: {', '.join(stocks_needing_fallback)}", flush=True)
        
        # 過去30日分のRSSを取得（コスト削減のため、対象銘柄のクエリに絞るのが理想だが、今回は簡易的に全取得）
        # ※本来はここでクエリを絞るべきだが、RSS_FEEDSの構造上、全取得してフィルタリングする
        fallback_entries = fetch_rss_feeds(days_back=30)
        fallback_entries = resolve_redirects(fallback_entries)
        
        for stock_code in stocks_needing_fallback:
            stock_info = STOCKS[stock_code]
            print(f"🔄 {stock_info['name']} のフォールバック処理を開始...", flush=True)
            
            # フォールバックモードで再処理
            result = process_stock_news(stock_code, stock_info, fallback_entries, is_fallback_mode=True)
            
            # 結果を上書き（ニュースが見つかった場合のみ、あるいは0件でも投資判断補助はあるので更新）
            results[stock_code] = result

    # メール作成と送信
    print("\n📧 メール作成中...", flush=True)
    email_body = create_email_body(results)
    
    # ファイルに保存（デバッグ用）
    with open("email_preview.html", "w", encoding="utf-8") as f:
        f.write(email_body)
    print("  プレビュー保存: email_preview.html", flush=True)
    
    print("🚀 メール送信中...", flush=True)
    status_code = send_email_via_sendgrid(
        api_key=SENDGRID_API_KEY,
        from_email=RECIPIENT_EMAIL,
        to_email=RECIPIENT_EMAIL,
        subject=f"【台湾株】本日の投資判断レポート ({datetime.now(JST).strftime('%Y/%m/%d')})",
        html_content=email_body
    )
    
    if 200 <= status_code < 300:
        print("✅ 送信成功！", flush=True)
    else:
        print(f"❌ 送信失敗: ステータスコード {status_code}", flush=True)

if __name__ == "__main__":
    main()
