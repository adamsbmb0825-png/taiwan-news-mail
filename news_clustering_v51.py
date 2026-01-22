#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ニュースクラスタリングモジュール v5.1
- 論点クラスタによるニュース分類
- 代表ニュース選択と補足情報統合
- イベント集中度の判定
"""

import json
import re
from openai import OpenAI

client = OpenAI()

def cluster_news_by_topic(stock_name, relevant_news):
    """
    ニュースを論点クラスタで分類
    
    Args:
        stock_name: 銘柄名
        relevant_news: 関連ニュースリスト
    
    Returns:
        dict: {
            'clusters': [クラスタリスト],
            'is_single_event': bool,
            'event_description': str (単一イベントの場合)
        }
    """
    if len(relevant_news) <= 1:
        return {
            'clusters': [{
                'cluster_id': 1,
                'theme': '単一ニュース',
                'representative': relevant_news[0] if relevant_news else None,
                'supplementary': []
            }],
            'is_single_event': False,
            'event_description': None
        }
    
    # ニューステキストを準備
    news_text = "\n\n".join([
        f"[{i+1}] タイトル: {news['title']}\n"
        f"    出典: {news['publisher']}\n"
        f"    概要: {news['snippet']}\n"
        f"    関連性スコア: {news['relevance_score']}\n"
        f"    判定理由: {news['relevance_reason']}"
        for i, news in enumerate(relevant_news)
    ])
    
    prompt = f"""
あなたは台湾株の投資判断を支援するアナリストです。

銘柄: {stock_name}

以下のニュースリストを「論点クラスタ」で分類してください。

【クラスタリング基準】
- 同じテーマ・イベントを扱うニュースは同一クラスタにまとめる
- 例：「米国工場×関税交渉」「営収発表×市場反応」「技術開発×競合動向」
- 各クラスタには明確なテーマ名を付ける

【代表ニュース選定基準（情報価値スコア）】
以下の要素を総合的に評価し、最も情報価値が高いニュースを代表として選択：
1. 情報の一次性（公式発表 > 報道 > 解説）
2. 具体性（数値・日付・固有名詞の有無）
3. 影響範囲（業績への直接影響 > 間接影響）
4. 関連性スコア（既存の判定を尊重）

【単一イベント判定】
- 全ニュースが同一の巨大イベントを扱っている場合は is_single_event: true
- その場合、event_description にイベント名を記載

ニュースリスト:
{news_text}

【出力形式】
以下の形式でJSON出力してください:
{{
  "clusters": [
    {{
      "cluster_id": 1,
      "theme": "クラスタのテーマ（例：米国工場拡大×関税交渉）",
      "representative_index": 1,
      "representative_reason": "代表として選んだ理由（情報価値スコアの根拠）",
      "supplementary_indices": [2, 3],
      "supplementary_perspectives": ["政策視点", "市場反応"]
    }}
  ],
  "is_single_event": false,
  "event_description": null
}}
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
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            clustering_result = json.loads(json_match.group())
            
            # インデックスを実際のニュースオブジェクトに変換
            clusters = []
            for cluster in clustering_result.get('clusters', []):
                rep_idx = cluster.get('representative_index', 1) - 1
                supp_indices = [idx - 1 for idx in cluster.get('supplementary_indices', [])]
                
                representative = relevant_news[rep_idx] if 0 <= rep_idx < len(relevant_news) else None
                supplementary = [relevant_news[idx] for idx in supp_indices if 0 <= idx < len(relevant_news)]
                
                clusters.append({
                    'cluster_id': cluster.get('cluster_id', 1),
                    'theme': cluster.get('theme', '不明'),
                    'representative': representative,
                    'representative_reason': cluster.get('representative_reason', ''),
                    'supplementary': supplementary,
                    'supplementary_perspectives': cluster.get('supplementary_perspectives', [])
                })
            
            return {
                'clusters': clusters,
                'is_single_event': clustering_result.get('is_single_event', False),
                'event_description': clustering_result.get('event_description')
            }
        
        # JSONパース失敗時はフォールバック
        return fallback_clustering(relevant_news)
        
    except Exception as e:
        print(f"⚠️  クラスタリングエラー: {e}")
        return fallback_clustering(relevant_news)

def fallback_clustering(relevant_news):
    """
    クラスタリング失敗時のフォールバック処理
    関連性スコア順に単純に配信
    """
    return {
        'clusters': [{
            'cluster_id': 1,
            'theme': '関連ニュース',
            'representative': relevant_news[0] if relevant_news else None,
            'representative_reason': '関連性スコアが最も高いニュース',
            'supplementary': relevant_news[1:3] if len(relevant_news) > 1 else [],
            'supplementary_perspectives': ['追加情報'] * min(2, len(relevant_news) - 1)
        }],
        'is_single_event': False,
        'event_description': None
    }

def prepare_delivery_news(clustering_result, max_clusters=3):
    """
    配信用ニュースを準備
    
    Args:
        clustering_result: クラスタリング結果
        max_clusters: 最大クラスタ数
    
    Returns:
        list: 配信用ニュースリスト（クラスタ情報付き）
    """
    delivery_news = []
    
    for cluster in clustering_result['clusters'][:max_clusters]:
        if cluster['representative']:
            news_item = cluster['representative'].copy()
            news_item['cluster_theme'] = cluster['theme']
            news_item['representative_reason'] = cluster.get('representative_reason', '理由なし')
            news_item['supplementary_news'] = cluster['supplementary']
            news_item['supplementary_perspectives'] = cluster.get('supplementary_perspectives', [])
            delivery_news.append(news_item)
    
    return delivery_news

def print_clustering_log(stock_name, clustering_result):
    """
    クラスタリング結果をログ出力
    """
    print(f"\n📊 クラスタリング結果（{stock_name}）")
    print(f"  クラスタ数: {len(clustering_result['clusters'])}個")
    
    if clustering_result['is_single_event']:
        print(f"  ⚠️  単一イベント集中: {clustering_result['event_description']}")
    
    for cluster in clustering_result['clusters']:
        print(f"\n  クラスタ {cluster['cluster_id']}: {cluster['theme']}")
        if cluster['representative']:
            print(f"    代表: {cluster['representative']['title'][:60]}...")
            print(f"    理由: {cluster.get('representative_reason', '理由なし')}")
        print(f"    補足: {len(cluster['supplementary'])}件")
        for i, supp in enumerate(cluster['supplementary']):
            perspective = cluster['supplementary_perspectives'][i] if i < len(cluster['supplementary_perspectives']) else '追加情報'
            print(f"      - [{perspective}] {supp['title'][:50]}...")
