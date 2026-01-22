#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾株ニュース配信システム v5.3 (Restored & Enhanced)
- v5.2-liteのバックアップをベースに復元
- 投資判断補助ニュース（株価フェーズ分析）を追加
- テンプレート変更なしで統合
"""

VERSION = "v5.3-restored-20260122"

import os
import feedparser
import requests
from delayed_valuable_news import is_delayed_valuable_news
from openai import OpenAI
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import json
import hashlib
import re
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import pytz
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from news_clustering_v51 import cluster_news_by_topic, prepare_delivery_news, print_clustering_log
from investment_aux_generator import generate_investment_aux_news

# OpenAI クライアント初期化
client = OpenAI()

# 台湾時間
TW_TZ = pytz.timezone('Asia/Taipei')

# 統計情報
STATS = {
    'cache_hit': 0,
    'cache_miss': 0,
    'redirect_timeout': 0,
    'redirect_failed': 0,
    'sns_domain_excluded': 0,
    'sns_publisher_excluded': 0,
    'duplicate_excluded': 0,
    'unknown_publisher_excluded': 0
}

# 銘柄情報を外部ファイルから読み込み
def load_stocks():
    """stocks.jsonから銘柄プロファイルを読み込む"""
    try:
        with open('stocks.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('stocks', {})
    except FileNotFoundError:
        print("エラー: stocks.json が見つかりません")
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
    "https://news.google.com/rss/search?q=廣達+營收&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    
    # ========================================
    # カテゴリ④ 共通業界クエリ（3件）
    # ========================================
    
    "https://news.google.com/rss/search?q=半導體&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=DRAM+OR+NAND&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
    "https://news.google.com/rss/search?q=ODM&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",
]

# SNSドメインリスト
SNS_DOMAINS = [
    'threads.net',
    'instagram.com',
    'line.me',
    'linkedin.com',
    'tiktok.com',
    'youtube.com', 'youtu.be'
]

def is_sns_domain(url):
    """URLがSNSドメインかどうかを判定"""
    url_lower = url.lower()
    return any(sns in url_lower for sns in SNS_DOMAINS)

def clean_url(url):
    """URLからトラッキングパラメータを削除"""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # 除外するパラメータ
    exclude_params = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                      'fbclid', 'gclid', 'msclkid', 'oc', '_ga', '_gl']
    
    # クリーンなクエリパラメータを作成
    clean_params = {k: v for k, v in query_params.items() if k not in exclude_params}
    clean_query = urlencode(clean_params, doseq=True)
    
    # URLを再構築
    clean_parsed = parsed._replace(query=clean_query)
    return urlunparse(clean_parsed)

def resolve_final_url(url, timeout=2):
    """
    リダイレクトを追跡して最終到達URLを取得
    タイムアウト: 2秒（v5.2-liteで短縮）
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=timeout)
        final_url = clean_url(response.url)
        return final_url
    except requests.Timeout:
        STATS['redirect_timeout'] += 1
        return None
    except Exception as e:
        STATS['redirect_failed'] += 1
        return None

def extract_publisher_from_url(url):
    """URLから出典メディア名を抽出"""
    domain_mapping = {
        'cnyes.com': '鉅亨網',
        'ctee.com.tw': '工商時報',
        'technews.tw': 'TechNews 科技新報',
        'udn.com': '聯合新聞網',
        'ltn.com.tw': '自由時報',
        'chinatimes.com': '中時新聞網',
        'cna.com.tw': '中央社 CNA',
        'moneydj.com': 'MoneyDJ',
        'eettaiwan.com': 'EE Times Taiwan',
        'digitimes.com.tw': 'DIGITIMES',
        'storm.mg': '風傳媒',
        'businessweekly.com.tw': '商業周刊',
        'cw.com.tw': '天下雜誌',
        'wealth.com.tw': '財訊',
        'mirrormedia.mg': '鏡週刊',
        'ettoday.net': 'ETtoday',
        'setn.com': '三立新聞網',
        'nownews.com': 'NOWnews',
        'yahoo.com': 'Yahoo奇摩',
        'pchome.com.tw': 'PChome',
        'cmoney.tw': 'CMoney',
        'moneysmart.tw': 'MoneySmart',
        'wealth.com.tw': '財訊',
        'businesstoday.com.tw': '今周刊',
        'smart.businessweekly.com.tw': 'Smart自學網',
        'money-link.com.tw': '理財周刊',
        'moneyweekly.com.tw': '理財周刊',
        'ctee.com.tw': '工商時報',
        'economic.com.tw': '經濟日報',
        'appledaily.com.tw': '蘋果新聞網',
        'ctwant.com': 'CTWANT',
        'sinotrade.com.tw': '永豐金證券',
        'wantgoo.com': '玩股網',
        'wantrich.chinatimes.com': '旺得富理財網',
        'knowing.asia': 'knowing',
        'newtalk.tw': '新頭殼',
        'taiwannews.com.tw': 'Taiwan News',
        'rti.org.tw': '中央廣播電台',
        'epochtimes.com': '大紀元',
        'ntdtv.com': '新唐人',
        'voacantonese.com': '美國之音',
        'rfi.fr': 'RFI',
        'bbc.com': 'BBC',
        'reuters.com': 'Reuters',
        'bloomberg.com': 'Bloomberg',
        'ft.com': 'Financial Times',
        'wsj.com': 'Wall Street Journal',
        'nikkei.com': '日經中文網',
    }
    
    parsed = urlparse(url)
    domain = parsed.netloc.lower().replace('www.', '')
    
    for key, value in domain_mapping.items():
        if key in domain:
            return value
    
    return None

def normalize_text(text):
    """テキストを正規化（全角/半角統一、記号除去、空白圧縮）"""
    # 全角→半角
    text = text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
    # 記号除去
    text = re.sub(r'[^\w\s]', '', text)
    # 空白圧縮
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def generate_article_signature(title, publisher, pub_date, snippet):
    """記事署名を生成（重複排除用）"""
    normalized_title = normalize_text(title)
    normalized_snippet = normalize_text(snippet[:120])
    date_str = pub_date.strftime('%Y-%m-%d') if pub_date else 'unknown'
    
    signature_string = f"{normalized_title}|{publisher}|{date_str}|{normalized_snippet}"
    return hashlib.md5(signature_string.encode('utf-8')).hexdigest()

def load_cache():
    """キャッシュファイルを読み込み"""
    try:
        with open('.taiwan_stock_news_cache_v5.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"news": {}, "topics": {}}

def save_cache(cache):
    """キャッシュファイルを保存"""
    with open('.taiwan_stock_news_cache_v5.json', 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def clean_cache(cache):
    """古いキャッシュをクリーニング"""
    now = datetime.now(TW_TZ)
    
    # ニュースキャッシュ: 30日間保持
    if 'news' not in cache:
        cache['news'] = {}
    news_cutoff = (now - timedelta(days=30)).isoformat()
    cache['news'] = {sig: data for sig, data in cache['news'].items() 
                     if data.get('cached_at', '') > news_cutoff}
    
    # 論点キャッシュ: 7営業日（約10日）保持
    if 'topics' not in cache:
        cache['topics'] = {}
    topic_cutoff = (now - timedelta(days=10)).isoformat()
    cache['topics'] = {stock_id: data for stock_id, data in cache['topics'].items() 
                       if data.get('cached_at', '') > topic_cutoff}
    
    return cache

def process_rss_entry(entry, cache):
    """
    RSSエントリを処理（並列処理用）
    キャッシュ優先でリダイレクト追跡をスキップ
    """
    rss_url = entry.get("link", "")
    title = entry.get("title", "")
    
    # キャッシュチェック（rss_urlベース）
    # 注: 厳密にはURL解決後のURLでチェックすべきだが、高速化のためここで一次チェック
    for sig, data in cache['news'].items():
        if data.get('url') == rss_url:
            STATS['cache_hit'] += 1
            return data

    # URL解決
    final_url = resolve_final_url(rss_url)
    if not final_url:
        return None
        
    # SNSドメイン除外
    if is_sns_domain(final_url):
        STATS['sns_domain_excluded'] += 1
        return None

    # 出版社抽出
    publisher = extract_publisher_from_url(final_url)
    if not publisher:
        # Google Newsの場合、sourceタグから取得を試みる
        if 'source' in entry:
            publisher = entry.source.get('title')
        
        if not publisher:
            STATS['unknown_publisher_excluded'] += 1
            return None

    # 日付解析
    pub_date = None
    if "published" in entry:
        try:
            pub_date = date_parser.parse(entry.published).astimezone(TW_TZ)
        except:
            pass
    
    if not pub_date:
        pub_date = datetime.now(TW_TZ)

    # 署名生成とキャッシュチェック（コンテンツベース）
    snippet = entry.get("summary", "")
    signature = generate_article_signature(title, publisher, pub_date, snippet)
    
    if signature in cache['news']:
        STATS['cache_hit'] += 1
        return cache['news'][signature]

    STATS['cache_miss'] += 1
    
    # 新規データ作成
    news_item = {
        "title": title,
        "url": final_url,
        "publisher": publisher,
        "date": pub_date.isoformat(),
        "snippet": snippet,
        "signature": signature,
        "cached_at": datetime.now(TW_TZ).isoformat()
    }
    
    # キャッシュ更新（呼び出し元で保存が必要）
    cache['news'][signature] = news_item
    
    return news_item

def collect_news_from_rss(days=7):
    """RSSフィードからニュースを収集（並列処理）"""
    print(f"📰 RSSフィードからニュース収集中... (過去{days}日分)")
    
    all_entries = []
    cutoff_date = datetime.now(TW_TZ) - timedelta(days=days)
    
    # フィード取得（I/Oバウンドなのでスレッド数多めでもOKだが、相手先負荷考慮し制限）
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(feedparser.parse, url) for url in RSS_FEEDS]
        
        for future in as_completed(futures):
            feed = future.result()
            for entry in feed.entries:
                # 日付フィルタ（一次）
                if "published" in entry:
                    try:
                        pub_date = date_parser.parse(entry.published).astimezone(TW_TZ)
                        if pub_date < cutoff_date:
                            continue
                    except:
                        pass
                all_entries.append(entry)
    
    print(f"  RSS収集完了: {len(all_entries)}件")
    
    # キャッシュ読み込み
    cache = load_cache()
    cache = clean_cache(cache)
    
    processed_news = []
    
    # URL解決とフィルタリング（並列処理）
    print(f"🔗 URL解決中（{len(all_entries)}件）...")
    
    # 処理上限設定（APIコストと時間節約）
    MAX_URL_PROCESS = 200
    if len(all_entries) > MAX_URL_PROCESS:
        print(f"  ⚠️ 件数が多いため、最新{MAX_URL_PROCESS}件のみ処理します")
        all_entries = all_entries[:MAX_URL_PROCESS]

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_rss_entry, entry, cache) for entry in all_entries]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                processed_news.append(result)
    
    # キャッシュ保存
    save_cache(cache)
    
    # 重複排除（URLベース）
    unique_news = []
    seen_urls = set()
    
    for news in processed_news:
        if news['url'] not in seen_urls:
            unique_news.append(news)
            seen_urls.add(news['url'])
        else:
            STATS['duplicate_excluded'] += 1
            
    print(f"✅ 重複除外後: {len(unique_news)}件")
    return unique_news

def filter_news_by_stock(news_list, stock_id, stock_info):
    """銘柄に関連するニュースをフィルタリング（キーワードマッチ）"""
    keywords = stock_info.get('keywords', [])
    stock_name = stock_info.get('name', '')
    
    # 銘柄名もキーワードに追加
    search_keywords = keywords + [stock_name, stock_id]
    
    relevant_news = []
    for news in news_list:
        text = (news['title'] + " " + news['snippet']).lower()
        if any(k.lower() in text for k in search_keywords):
            relevant_news.append(news)
            
    return relevant_news

def process_stock_news(stock_id, stock_info, all_news, cache, fallback_mode=False):
    """
    銘柄ごとのニュース処理フロー
    1. キーワードフィルタ
    2. LLM関連性判定（厳選）
    3. クラスタリング・要約
    4. 投資判断補助ニュース生成・追加（新規）
    """
    print(f"============================================================")
    print(f"📊 {stock_info['name']}（{stock_id}）")
    print(f"============================================================")
    
    # 1. キーワードフィルタ
    candidates = filter_news_by_stock(all_news, stock_id, stock_info)
    print(f"候補ニュース: {len(candidates)}件")
    
    if not candidates:
        print("  ❌ 候補なし")
        return None

    # 2. LLM関連性判定（コスト削減のため件数制限）
    MAX_LLM_CHECK = 15 if not fallback_mode else 30
    if len(candidates) > MAX_LLM_CHECK:
        # 日付が新しい順にソートして上位のみチェック
        candidates.sort(key=lambda x: x['date'], reverse=True)
        candidates = candidates[:MAX_LLM_CHECK]
    
    relevant_news = []
    
    # 遅延価値判定（delayed_valuable_news.py）を使用
    # LLM判定はコストがかかるため、ここも並列化したいが、
    # レートリミット考慮して直列実行（または少数の並列）
    
    # 既存のキャッシュ済み判定結果があれば利用
    # （今回は簡易実装として、news_clustering_v51.py 内のロジックに任せるか、
    #   ここで自前で呼ぶか。v5.2-liteではここで呼ぶ設計）
    
    for news in candidates:
        # キャッシュキー: signature + stock_id
        cache_key = f"{news['signature']}_{stock_id}_relevance"
        
        # キャッシュにあれば使う（判定結果は変わらないはず）
        # ※実装簡略化のため、ここでは毎回判定（delayed_valuable_news内でキャッシュ機構あればよいが）
        # 今回は直接 is_delayed_valuable_news を呼ぶ
        
        is_relevant, reason = is_delayed_valuable_news(news, stock_id, stock_info)
        
        if is_relevant:
            news['relevance_reason'] = reason
            relevant_news.append(news)
            # print(f"  ✅ 関連あり: {news['title'][:20]}...")
        else:
            pass
            # print(f"  🗑️ 除外: {news['title'][:20]}...")

    print(f"✅ 関連ニュース: {len(relevant_news)}件")
    
    if not relevant_news:
        return None

    # 3. クラスタリング・要約（v5.1のロジック再利用）
    # ここで日本語翻訳と要約が行われる
    clustered_news = cluster_news_by_topic(relevant_news, stock_id, stock_info)
    
    # 4. 投資判断補助ニュース生成・追加（新規）
    # 既存のニュースリストの末尾に、ニュースと同じフォーマットで追加する
    try:
        aux_news = generate_investment_aux_news(stock_id, stock_info, relevant_news)
        if aux_news:
            # 既存のニュース形式に合わせる
            formatted_aux_news = {
                "topic_theme": "📉 投資判断補助（株価フェーズ整理）",
                "title_ja": f"【{aux_news['phase']}】{aux_news['price_movement']}",
                "title_tw": "Market Phase Analysis", # 繁体字タイトルは英語表記で代用（または空文字）
                "summary_ja": f"{aux_news['news_correlation']}\n\n💡 注意点: {aux_news['caution_point']}",
                "representative_reason": aux_news['news_correlation'], # 分析ボックス用
                "source": "Market Analysis",
                "pub_date": datetime.now(TW_TZ).strftime('%Y-%m-%d %H:%M'),
                "url": "#", # リンクなし
                "related_score": 0, # スコアなし
                "sentiment": "neutral"
            }
            clustered_news.append(formatted_aux_news)
            print("  ✅ 投資判断補助ニュースを追加しました")
    except Exception as e:
        print(f"  ⚠️ 投資判断補助ニュース生成エラー: {e}")

    return {
        'stock_id': stock_id,
        'stock_name': stock_info['name'],
        'news': clustered_news
    }

def main():
    print(f"🚀 台湾株ニュース配信システム {VERSION} 起動")
    start_time = time.time()
    
    # 1. ニュース収集（過去7日）
    all_news = collect_news_from_rss(days=7)
    
    # キャッシュ読み込み（プロセス内で共有）
    cache = load_cache()
    
    results = {}
    
    # 2. 銘柄ごとに処理
    for stock_id, stock_info in STOCKS.items():
        # _commentなどはスキップ
        if stock_id.startswith('_') or stock_id == 'stocks':
            continue
            
        res = process_stock_news(stock_id, stock_info, all_news, cache)
        
        if res:
            results[stock_id] = res
        else:
            # フォールバックモード（過去30日）
            print(f"⚠️ {stock_info['name']}: 直近7日間のニュースなし。フォールバックモード(30日)を実行します。")
            
            # 30日分のニュースを再収集（全件は重いので、対象銘柄のクエリだけ叩くのが理想だが、
            # 実装簡略化のため、既存関数で30日指定で再収集。ただしキャッシュ効くので2回目は速い）
            # ※最適化: 本当はここで「この銘柄専用のRSS」だけ叩くべきだが、
            # RSS_FEEDSリストがフラットなので、全件叩いてしまう。
            # v5.2-liteでは許容範囲（30件程度なら）
            
            fallback_news = collect_news_from_rss(days=30)
            res = process_stock_news(stock_id, stock_info, fallback_news, cache, fallback_mode=True)
            
            if res:
                results[stock_id] = res
            else:
                print(f"❌ {stock_info['name']}: 30日間でも関連ニュースなし")
                # ニュースなしでも投資判断補助だけは出したい場合、ここで生成する手もあるが、
                # 今回の要件は「企業ニュース0件を防ぐ」ではなく「以前の挙動に戻す」なので、
                # ニュースがなければメールにも載せない（または空で載せる）
                # ただし、投資判断補助は「必ず1本」という要件があるため、
                # ニュースがなくても投資判断補助だけ生成して返す
                try:
                    aux_news = generate_investment_aux_news(stock_id, stock_info, [])
                    if aux_news:
                        formatted_aux_news = {
                            "topic_theme": "📉 投資判断補助（株価フェーズ整理）",
                            "title_ja": f"【{aux_news['phase']}】{aux_news['price_movement']}",
                            "title_tw": "Market Phase Analysis",
                            "summary_ja": f"{aux_news['news_correlation']}\n\n💡 注意点: {aux_news['caution_point']}",
                            "representative_reason": aux_news['news_correlation'],
                            "source": "Market Analysis",
                            "pub_date": datetime.now(TW_TZ).strftime('%Y-%m-%d %H:%M'),
                            "url": "#",
                            "related_score": 0,
                            "sentiment": "neutral"
                        }
                        results[stock_id] = {
                            'stock_id': stock_id,
                            'stock_name': stock_info['name'],
                            'news': [formatted_aux_news]
                        }
                        print("  ✅ ニュースなしのため、投資判断補助のみ生成しました")
                except Exception as e:
                    print(f"  ⚠️ 投資判断補助生成エラー(フォールバック): {e}")

    # 3. メール作成・送信
    if results:
        from email_template_v5 import create_email_body
        
        # テンプレートに渡すデータを整形
        # email_template_v5.py は {stock_id: {'news': [...]}} を期待しているはず
        # 確認: email_template_v5.py の create_email_body(news_data)
        
        html_content = create_email_body(results)
        
        # プレビュー保存
        with open('email_preview.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("💾 プレビューを保存しました: email_preview.html")
        
        # 送信
        recipient = os.environ.get('RECIPIENT_EMAIL')
        if recipient:
            message = Mail(
                from_email=recipient, # 自分自身に送る（SendGrid Sender Identity回避）
                to_emails=recipient,
                subject=f"🇹🇼 台湾株ニュース配信 {datetime.now(TW_TZ).strftime('%Y/%m/%d')}",
                html_content=html_content
            )
            
            try:
                sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
                response = sg.send(message)
                print(f"✅ 送信成功！ ステータスコード: {response.status_code}")
            except Exception as e:
                print(f"❌ 送信エラー: {e}")
        else:
            print("⚠️ RECIPIENT_EMAIL が設定されていないため送信スキップ")
            
    else:
        print("❌ 配信対象ニュースがありませんでした")

    elapsed = time.time() - start_time
    print(f"⏱️ 処理時間: {elapsed:.2f}秒")

if __name__ == "__main__":
    main()
