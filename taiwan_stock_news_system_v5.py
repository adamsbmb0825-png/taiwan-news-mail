# -*- coding: utf-8 -*-
"""
台湾株ニュース配信システム v5.3 (GitHub正本)
- 投資判断補助ニュース（株価フェーズ分析）の追加
- SendGrid送信元アドレスの修正
- 企業ニュース強制採用ロジック（0件防止）の追加
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

# バージョン情報
VERSION = "v5.3-20260122-forced-pick"

# 環境変数
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# タイムゾーン設定
JST = timezone(timedelta(hours=9))

# 銘柄リスト読み込み
try:
    with open("stocks.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
        STOCKS = json_data.get("stocks", {})
except FileNotFoundError:
    print("❌ stocks.json が見つかりません。")
    sys.exit(1)

# RSSフィードリスト
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=台積電+when:7d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=創見+when:7d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=宇瞻+when:7d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=廣達+when:7d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://money.udn.com/rssfeed/news/1001/5590", # 産業
    "https://money.udn.com/rssfeed/news/1001/5591", # 証券
]

client = OpenAI(api_key=OPENAI_API_KEY)

def fetch_rss_feeds(days_back=7):
    """RSSフィードからニュースを収集"""
    print(f"📰 RSSフィードからニュース収集中... (過去{days_back}日分)", flush=True)
    all_entries = []
    seen_links = set()
    
    cutoff_date = datetime.now(JST) - timedelta(days=days_back)
    
    for feed_url in RSS_FEEDS:
        # 30日フォールバック時はGoogle Newsのクエリパラメータを変更
        if days_back > 7 and "when:7d" in feed_url:
            feed_url = feed_url.replace("when:7d", "when:30d")
            
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            # 日付パース
            published = None
            if hasattr(entry, 'published_parsed'):
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).astimezone(JST)
            
            if published and published > cutoff_date:
                if entry.link not in seen_links:
                    all_entries.append({
                        'title': entry.title,
                        'link': entry.link,
                        'summary': getattr(entry, 'summary', ''),
                        'published': published,
                        'source': getattr(entry, 'source', {}).get('title', 'Unknown')
                    })
                    seen_links.add(entry.link)
                    
    print(f"  RSS収集完了: {len(all_entries)}件", flush=True)
    return all_entries

def resolve_redirects(entries):
    """Google NewsなどのリダイレクトURLを解決（並列処理）"""
    print(f"🔗 URL解決中（{len(entries)}件）...", flush=True)
    
    # 件数が多い場合は最新のものに絞る（API制限回避）
    if len(entries) > 100:
        print("  ⚠️ 件数が多いため、最新100件のみ処理します", flush=True)
        entries = sorted(entries, key=lambda x: x['published'], reverse=True)[:100]
        
    def resolve_url(entry):
        try:
            # Google Newsのリダイレクト解決
            if "news.google.com" in entry['link']:
                response = requests.get(entry['link'], timeout=5, allow_redirects=True)
                entry['link'] = response.url
        except:
            pass
        return entry

    with ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(resolve_url, entries))
        
    # 重複排除（URL解決後）
    unique_entries = []
    seen_urls = set()
    for entry in entries:
        if entry['link'] not in seen_urls:
            unique_entries.append(entry)
            seen_urls.add(entry['link'])
            
    print(f"✅ 重複除外後: {len(unique_entries)}件", flush=True)
    return unique_entries

def analyze_relevance_with_llm(entry, stock_code, stock_info, is_fallback_mode=False):
    """LLMを使用してニュースの関連性と重要度を判定"""
    prompt = f"""
    以下のニュース記事が、台湾の銘柄「{stock_info['name']} ({stock_code})」の株価や業績に直接影響を与える重要なニュースかどうか判定してください。
    
    タイトル: {entry['title']}
    要約: {entry['summary']}
    
    以下のJSON形式で回答してください:
    {{
        "is_relevant": true/false,
        "reason": "判定理由（日本語）",
        "summary": "投資家向けの簡潔な要約（日本語、50文字以内）",
        "importance": 1-5の整数（5が最高）
    }}
    
    判定基準:
    - 銘柄名が明記されている、または主要製品・サプライチェーンに深く関わる場合はTrue
    - 単なる市況概況や、名前が羅列されているだけの記事はFalse
    - {stock_info.get('keywords', [])} に関連する具体的な動向があればTrue
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

def force_pick_news(candidates, stock_info):
    """
    【強制採用ロジック】
    LLM判定で0件になった場合、候補の中から最も適切なニュースを1つ強制的に選ぶ。
    優先順位:
    1. 重要キーワード（營收, 法說會, 展望など）を含む記事
    2. タイトルに銘柄名が含まれる記事
    3. 最も新しい記事
    """
    if not candidates:
        return None

    # 重要キーワード
    priority_keywords = ["營收", "法說會", "財測", "展望", "接單", "CapEx", "DRAM", "NAND", "HBM", "CoWoS", "關稅", "管制", "EPS", "獲利"]
    
    # 1. 重要キーワードを含むものを探す
    for entry in candidates:
        text = (entry['title'] + entry['summary']).lower()
        for kw in priority_keywords:
            if kw.lower() in text:
                print(f"  ⚠️ FORCED PICK used: {stock_info['name']} reason=Keyword match ({kw}) url={entry['link']}", flush=True)
                return {
                    **entry,
                'llm_result': {
                    'is_relevant': True,
                    'reason': f"【自動補完】重要キーワード「{kw}」を含むため強制採用",
                    'summary': f"【自動補完】{entry['title']}（{kw}関連）",
                    'importance': 3,
                    'representative_reason': f"重要キーワード「{kw}」を含むため"
                },
                'forced_pick': True
            }

    # 2. タイトルに銘柄名が含まれるものを探す
    for entry in candidates:
        if stock_info['name'] in entry['title']:
            print(f"  ⚠️ FORCED PICK used: {stock_info['name']} reason=Title match url={entry['link']}", flush=True)
            return {
                **entry,
                'llm_result': {
                    'is_relevant': True,
                    'reason': "【自動補完】タイトルに銘柄名を含むため強制採用",
                    'summary': f"【自動補完】{entry['title']}",
                    'importance': 3,
                    'representative_reason': "タイトルに銘柄名を含むため"
                },
                'forced_pick': True
            }

    # 3. なければ最新のものを採用
    entry = candidates[0] # candidatesは既に日付順でソートされている前提
    print(f"  ⚠️ FORCED PICK used: {stock_info['name']} reason=Newest fallback url={entry['link']}", flush=True)
    return {
        **entry,
        'llm_result': {
            'is_relevant': True,
            'reason': "【自動補完】関連ニュース不足のため最新記事を採用",
            'summary': f"【自動補完】{entry['title']}",
            'importance': 1,
            'representative_reason': "最新記事のため"
        },
        'forced_pick': True
    }

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
                
    # 【強制採用ロジック】関連ニュースが0件の場合、候補から強制的に1つ選ぶ
    if not relevant_news and candidates:
        print("  ⚠️ 関連ニュースが0件のため、強制採用ロジックを実行します...", flush=True)
        forced_news = force_pick_news(candidates, stock_info)
        if forced_news:
            relevant_news.append(forced_news)
            news_summaries_for_aux.append(forced_news['llm_result']['summary'])

    print(f"✅ 関連ニュース: {len(relevant_news)}件", flush=True)
    
    # 3. ニュースクラスタリング（v5.1機能）
    clustered_news = []
    if relevant_news:
        # 引数順序修正: (stock_name, relevant_news)
        clusters = cluster_news_by_topic(stock_info['name'], relevant_news)
        print_clustering_log(stock_info['name'], clusters)
        # テンプレートはクラスタ構造を期待しているため、prepare_delivery_newsを通さず直接渡す
        clustered_news = clusters['clusters']
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
    
    # 第1段階: 直近7日
    print("\n=== 第1段階: 直近7日モード ===", flush=True)
    entries = fetch_rss_feeds(days_back=7)
    entries = resolve_redirects(entries)
    
    results = {}
    stocks_needing_fallback = []
    
    for stock_code, stock_info in STOCKS.items():
        result = process_stock_news(stock_code, stock_info, entries, is_fallback_mode=False)
        results[stock_code] = result
        
        # ニュースが0件の場合はフォールバック対象に追加
        # ※強制採用ロジックが入ったので、candidatesが0件の場合のみここに来るはず
        if result['news_count'] == 0:
            stocks_needing_fallback.append(stock_code)
            
    # 第2段階: 30日フォールバック（ニュース0件の銘柄のみ）
    if stocks_needing_fallback:
        print("\n=== 第2段階: 30日フォールバックモード ===", flush=True)
        print(f"対象銘柄: {', '.join(stocks_needing_fallback)}", flush=True)
        
        # 過去30日分のRSSを取得
        fallback_entries = fetch_rss_feeds(days_back=30)
        fallback_entries = resolve_redirects(fallback_entries)
        
        for stock_code in stocks_needing_fallback:
            stock_info = STOCKS[stock_code]
            print(f"🔄 {stock_info['name']} のフォールバック処理を開始...", flush=True)
            
            # フォールバックモードで再処理
            result = process_stock_news(stock_code, stock_info, fallback_entries, is_fallback_mode=True)
            
            # 結果を上書き
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
