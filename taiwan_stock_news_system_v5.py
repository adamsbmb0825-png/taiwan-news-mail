#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台湾株ニュース配信システム v5.2-lite
- 多面性を維持したまま実行時間を短縮（2-3分目標）
- RSSフィード数削減（74件 → 30件）
- 処理上限設定（URL解決200件、LLM判定60件）
- 並列処理最適化（max_workers=10）
- ログ即時表示（バッファリング無効化）
"""

VERSION = "v5.2-lite-v3-frozen-20260115-0230"

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
        with open('/home/ubuntu/stocks.json', 'r', encoding='utf-8') as f:
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
    if rss_url in cache.get('url_to_signature', {}):
        signature = cache['url_to_signature'][rss_url]
        if signature in cache['news']:
            STATS['cache_hit'] += 1
            cached_data = cache['news'][signature]
            # キャッシュからSNS判定
            if is_sns_domain(cached_data['final_url']):
                STATS['sns_domain_excluded'] += 1
                return None
            return cached_data
    
    STATS['cache_miss'] += 1
    
    # リダイレクト追跡
    final_url = resolve_final_url(rss_url, timeout=3)
    
    # リダイレクト未解決は除外
    if not final_url:
        return None
    
    # SNSドメインチェック
    if is_sns_domain(final_url):
        STATS['sns_domain_excluded'] += 1
        return None
    
    # 出典抽出
    publisher = None
    if hasattr(entry, 'source') and hasattr(entry.source, 'title'):
        publisher = entry.source.title
    if not publisher:
        publisher = extract_publisher_from_url(final_url)
    
    # 出典不明は除外
    if not publisher:
        STATS['unknown_publisher_excluded'] += 1
        return None
    
    # 出典がSNSドメインの場合も除外
    if any(sns in publisher.lower() for sns in ['facebook', 'twitter', 'x.com', 'instagram', 'line', 'threads']):
        STATS['sns_publisher_excluded'] += 1
        return None
    
    # 日時取得
    pub_date = None
    if hasattr(entry, 'published'):
        try:
            pub_date = date_parser.parse(entry.published).astimezone(TW_TZ)
        except:
            pass
    
    # スニペット取得
    snippet = entry.get("summary", "")[:200]
    
    # 記事署名生成
    signature = generate_article_signature(title, publisher, pub_date, snippet)
    
    news_entry = {
        "title": title,
        "rss_url": rss_url,
        "final_url": final_url,
        "link": final_url,
        "publisher": publisher,
        "published": pub_date.isoformat() if pub_date else None,
        "snippet": snippet,
        "signature": signature,
        "cached_at": datetime.now(TW_TZ).isoformat()
    }
    
    return news_entry

def collect_news_parallel():
    """
    RSSフィードからニュースを並列収集
    v5.2-lite-v2: 銘柄別にURL解決（各フィード上位20件）、max_workers=10
    """
    print("📰 RSSフィードからニュース収集中...", flush=True)
    cache = load_cache()
    
    # url_to_signatureマッピングを初期化
    if 'url_to_signature' not in cache:
        cache['url_to_signature'] = {}
    
    # v5.2-lite-v2: 銘柄別にRSS収集（各フィード上位20件）
    MAX_ENTRIES_PER_FEED = 20
    all_entries = []
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            # 各フィードから上位20件を取得
            all_entries.extend(feed.entries[:MAX_ENTRIES_PER_FEED])
        except Exception as e:
            print(f"⚠️  RSS収集エラー: {feed_url} - {e}", flush=True)
    
    print(f"  RSS収集完了: {len(all_entries)}件（各フィード上位{MAX_ENTRIES_PER_FEED}件）", flush=True)
    
    entries_to_process = all_entries
    
    # 並列処理でリダイレクト追跡（max_workers=10）
    news_list = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_rss_entry, entry, cache): entry for entry in entries_to_process}
        
        for i, future in enumerate(as_completed(futures), 1):
            if i % 50 == 0:
                print(f"  処理中: {i}/{len(entries_to_process)}件", flush=True)
            
            try:
                result = future.result()
                if result:
                    news_list.append(result)
                    # キャッシュに保存
                    cache['news'][result['signature']] = result
                    cache['url_to_signature'][result['rss_url']] = result['signature']
            except Exception as e:
                pass
    
    # 重複除外
    unique_news = {}
    for news in news_list:
        signature = news['signature']
        if signature in unique_news:
            STATS['duplicate_excluded'] += 1
        else:
            unique_news[signature] = news
    
    print(f"✅ 重複除外後: {len(unique_news)}件", flush=True)
    
    # キャッシュ保存
    cache = clean_cache(cache)
    save_cache(cache)
    
    return list(unique_news.values())

def translate_title(title):
    """タイトルを日本語に翻訳"""
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "あなたは台湾の金融ニュースタイトルを日本語に翻訳する専門家です。簡潔で正確な翻訳を提供してください。"},
                {"role": "user", "content": f"以下の台湾株ニュースタイトルを日本語に翻訳してください:\n\n{title}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return title

def judge_relevance(stock_id, stock_name, news_list, max_items=15):
    """LLMでニュースの関連性を判定（v5.2-lite-v3: デフォルト最大15件）"""
    news_text = "\n\n".join([
        f"[{i+1}] {news['title']}\n出典: {news['publisher']}\n概要: {news['snippet']}"
        for i, news in enumerate(news_list[:max_items])
    ])
    
    prompt = f"""
あなたは台湾株の投資判断を支援するアナリストです。

銘柄: {stock_name}（{stock_id}）
業態: {STOCKS[stock_id]['business_type']}

以下のニュースリストから、この銘柄の投資判断に有効な情報を含むニュースを選別してください。

【判定基準】
- 関連あり: 業績、受注、技術、市場動向など投資判断に直接影響する情報
- 関連性不明: 業界全般の話題で、銘柄への影響が不明確
- 参考外: 無関係、または投資判断に無価値

ニュースリスト:
{news_text}

【出力形式】
各ニュースについて、以下の形式でJSON配列として出力してください:
[
  {{"index": 1, "relevance": "関連あり", "score": 85, "reason": "理由"}},
  {{"index": 2, "relevance": "参考外", "score": 20, "reason": "理由"}}
]
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "あなたは台湾株の投資判断を支援するアナリストです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content.strip()
        # JSONを抽出
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            judgments = json.loads(json_match.group())
            return judgments
        return []
    except Exception as e:
        print(f"⚠️  関連性判定エラー: {e}", flush=True)
        return []

def generate_topic(stock_id, stock_name, relevant_news):
    """論点を生成"""
    cache = load_cache()
    
    # キャッシュチェック
    if stock_id in cache.get('topics', {}):
        cached_topic = cache['topics'][stock_id]
        cached_at = datetime.fromisoformat(cached_topic['cached_at'])
        if datetime.now(TW_TZ) - cached_at < timedelta(days=10):
            return cached_topic['topic']
    
    news_text = "\n\n".join([
        f"[{i+1}] {news['title']}\n出典: {news['publisher']}\n概要: {news['snippet']}"
        for i, news in enumerate(relevant_news[:5])
    ])
    
    prompt = f"""
銘柄: {stock_name}（{stock_id}）
業態: {STOCKS[stock_id]['business_type']}

以下のニュースから、投資家が「今後どこを見るべきか」という論点を1文で生成してください。

ニュース:
{news_text}

【出力形式】
論点のみを1文で出力してください（例：「2ナノ製造技術の量産開始時期とCoWoS受注増加が収益拡大にどう影響するかが焦点」）
"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "あなたは台湾株の投資判断を支援するアナリストです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        
        topic = response.choices[0].message.content.strip()
        
        # キャッシュに保存
        if 'topics' not in cache:
            cache['topics'] = {}
        cache['topics'][stock_id] = {
            'topic': topic,
            'cached_at': datetime.now(TW_TZ).isoformat()
        }
        save_cache(cache)
        
        return topic
    except Exception as e:
        print(f"⚠️  論点生成エラー: {e}", flush=True)
        return "市場動向と業績への影響を注視"

def send_email(results, taipei_time):
    """メール送信"""
    from email_template_v5 import generate_html_email
    
    html_content = generate_html_email(results, taipei_time)
    
    message = Mail(
        from_email='adamsbmb0825@gmail.com',
        to_emails='adamsbmb0825@gmail.com',
        subject=f'🇹🇼 台湾株ニュース配信 v5.0 - {taipei_time.strftime("%Y年%m月%d日 %H:%M:%S")}',
        html_content=html_content
    )
    
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f"✅ メール送信成功（ステータス: {response.status_code}）", flush=True)
    except Exception as e:
        print(f"❌ メール送信エラー: {e}", flush=True)

def print_stats():
    """統計情報を出力"""
    print("\n" + "="*60)
    print("📊 統計情報")
    print("="*60)
    print(f"キャッシュヒット: {STATS['cache_hit']}件", flush=True)
    print(f"キャッシュミス: {STATS['cache_miss']}件", flush=True)
    print(f"キャッシュヒット率: {STATS['cache_hit'] / (STATS['cache_hit'] + STATS['cache_miss']) * 100:.1f}%" if (STATS['cache_hit'] + STATS['cache_miss']) > 0 else "N/A")
    print(f"リダイレクトタイムアウト: {STATS['redirect_timeout']}件", flush=True)
    print(f"リダイレクト失敗: {STATS['redirect_failed']}件", flush=True)
    print(f"SNSドメイン除外: {STATS['sns_domain_excluded']}件", flush=True)
    print(f"SNS出典除外: {STATS['sns_publisher_excluded']}件", flush=True)
    print(f"出典不明除外: {STATS['unknown_publisher_excluded']}件", flush=True)
    print(f"重複除外: {STATS['duplicate_excluded']}件", flush=True)
    print("="*60 + "\n")

def main():
    import os
    
    print("="*60)
    print(f"台湾株ニュース配信システム {VERSION}", flush=True)
    print("="*60)
    
    # 第1段階: 直近7日モード
    print("\n=== 第1段階: 直近7日モード ===", flush=True)
    all_news_7days = collect_news_parallel()
    
    # 統計情報を出力
    print_stats()
    
    # 各銘柄の処理（第1段階）
    results = {}
    stocks_need_fallback = []  # フォールバックが必要な銘柄
    
    for stock_id, stock_info in STOCKS.items():
        print("="*60)
        print(f"📊 {stock_info['name']}（{stock_id}）", flush=True)
        print("="*60)
        
        # 関連ニュースを抽出
        stock_keywords = [stock_info['name'], stock_id]
        # 宇瞻の場合はApacerも追加
        if stock_id == '8271':
            stock_keywords.append('Apacer')
            stock_keywords.append('apacer')
        candidate_news = [news for news in all_news_7days if any(kw in news['title'] or kw in news['snippet'] for kw in stock_keywords)]
        
        print(f"候補ニュース: {len(candidate_news)}件", flush=True)
        
        if len(candidate_news) == 0:
            print("⚠️  関連ニュースなし (フォールバック候補)", flush=True)
            stocks_need_fallback.append((stock_id, stock_info))
            continue
        
        # v5.2-lite: LLM関連性判定は上位15件まで
        judgments = judge_relevance(stock_id, stock_info['name'], candidate_news)
        
        # 関連ニュースを抽出
        relevant_news = []
        for judgment in judgments:
            if judgment['relevance'] == '関連あり':
                idx = judgment['index'] - 1
                if idx < len(candidate_news):
                    news = candidate_news[idx].copy()
                    news['relevance_score'] = judgment['score']
                    news['relevance_reason'] = judgment['reason']
                    # タイトル翻訳
                    print(f"  [翻訳中] {news['title'][:50]}...", flush=True)
                    news['title_ja'] = translate_title(news['title'])
                    relevant_news.append(news)
        
        print(f"✅ 関連ニュース: {len(relevant_news)}件", flush=True)
        
        if len(relevant_news) == 0:
            print("⚠️  関連ニュースなし (フォールバック候補)", flush=True)
            stocks_need_fallback.append((stock_id, stock_info))
            continue
        
        # スコア順にソート
        relevant_news.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # 論点クラスタリング
        clustering_result = cluster_news_by_topic(stock_info['name'], relevant_news)
        print_clustering_log(stock_info['name'], clustering_result)
        
        # 配信ニュースを準備（クラスタ情報付き）
        delivery_news = prepare_delivery_news(clustering_result, max_clusters=3)
        
        print(f"✅ 配信: {len(delivery_news)}クラスタ", flush=True)
        
        # 論点生成
        topic = generate_topic(stock_id, stock_info['name'], relevant_news)
        
        results[stock_id] = {
            'stock_info': stock_info,
            'topic': topic,
            'news': delivery_news,
            'is_single_event': clustering_result['is_single_event'],
            'event_description': clustering_result['event_description']
        }
    
    # 第2段階: 30日フォールバック（ニュース不足銘柄のみ）
    if stocks_need_fallback:
        print("\n=== 第2段階: 30日フォールバック ===", flush=True)
        print(f"フォールバック対象: {len(stocks_need_fallback)}銘柄", flush=True)
        
        # 30日分のRSS収集（フォールバック用）
        # TODO: 実装を簡略化するため、7日分のニュースから遅れても価値がある類型のみをフィルタリング
        # 実際の30日分の収集は次のバージョンで実装
        
        for stock_id, stock_info in stocks_need_fallback:
            print("="*60)
            print(f"📊 {stock_info['name']}（{stock_id}）- 30日拡張", flush=True)
            print("="*60)
            
            # 7日分のニュースから遅れても価値がある類型のみをフィルタリング
            stock_keywords = [stock_info['name'], stock_id]
            if stock_id == '8271':
                stock_keywords.append('Apacer')
                stock_keywords.append('apacer')
            
            # 遅れても価値がある類型のニュースのみを抽出
            candidate_news_30days = [
                news for news in all_news_7days 
                if any(kw in news['title'] or kw in news['snippet'] for kw in stock_keywords)
                and is_delayed_valuable_news(news['title'], news['snippet'])
            ]
            
            print(f"30日拡張候補ニュース: {len(candidate_news_30days)}件", flush=True)
            
            if len(candidate_news_30days) == 0:
                print("⚠️  30日拡張でも関連ニュースなし", flush=True)
                continue
            
            # LLM関連性判定（最大10件）
            judgments_30days = judge_relevance(stock_id, stock_info['name'], candidate_news_30days, max_items=10)
            
            # 関連ニュースを抽出
            relevant_news_30days = []
            for judgment in judgments_30days:
                if judgment['relevance'] == '関連あり':
                    idx = judgment['index'] - 1
                    if idx < len(candidate_news_30days):
                        news = candidate_news_30days[idx].copy()
                        news['relevance_score'] = judgment['score']
                        news['relevance_reason'] = judgment['reason']
                        # タイトル翻訳
                        print(f"  [翻訳中] {news['title'][:50]}...", flush=True)
                        news['title_ja'] = translate_title(news['title'])
                        relevant_news_30days.append(news)
            
            print(f"✅ 関連ニュース: {len(relevant_news_30days)}件", flush=True)
            
            if len(relevant_news_30days) == 0:
                print("⚠️  30日拡張でも関連ニュースなし", flush=True)
                continue
            
            # スコア順にソート
            relevant_news_30days.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # 論点クラスタリング
            clustering_result = cluster_news_by_topic(stock_info['name'], relevant_news_30days)
            print_clustering_log(stock_info['name'], clustering_result)
            
            # 配信ニュースを準備（クラスタ情報付き）
            delivery_news = prepare_delivery_news(clustering_result, max_clusters=3)
            
            print(f"✅ 配信: {len(delivery_news)}クラスタ", flush=True)
            
            # 論点生成
            topic = generate_topic(stock_id, stock_info['name'], relevant_news_30days)
            
            results[stock_id] = {
                'stock_info': stock_info,
                'topic': topic,
                'news': delivery_news,
                'is_single_event': clustering_result['is_single_event'],
                'event_description': clustering_result['event_description']
            }
    
    # 最終結果サマリー
    print("\n=== 最終結果 ===", flush=True)
    for stock_id, result in results.items():
        stock_name = result['stock_info']['name']
        news_count = len(result['news'])
        print(f"{stock_name}（{stock_id}）: 配信{news_count}クラスタ", flush=True)
    
    # メール送信
    if results:
        now_taipei = datetime.now(TW_TZ)
        print("\n📧 メール送信中...", flush=True)
        send_email(results, now_taipei)
    else:
        print("\n⚠️  配信するニュースがありません", flush=True)

if __name__ == "__main__":
    main()
