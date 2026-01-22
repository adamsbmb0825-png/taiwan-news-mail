#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投資判断補助ニュース生成モジュール
株価データと直近ニュースを組み合わせて、投資判断に役立つ補助情報を生成する
"""

import os
from openai import OpenAI
from stock_price_analyzer import get_formatted_price_info
import json

client = OpenAI()

def generate_investment_aux_news(stock_id, stock_info, recent_news_list):
    """
    投資判断補助ニュースを生成する
    
    Args:
        stock_id (str): 証券コード
        stock_info (dict): 銘柄情報
        recent_news_list (list): 直近の関連ニュースリスト
        
    Returns:
        dict: 生成されたニュースデータ（タイトル、本文など）
    """
    # 株価情報の取得
    price_info = get_formatted_price_info(stock_id)
    
    if not price_info:
        # 株価取得失敗時は生成しない（または簡易版を返す）
        return None
        
    # ニュースの要約を作成（LLMへの入力用）
    news_summary_text = ""
    if recent_news_list:
        for i, news in enumerate(recent_news_list[:5]): # 最新5件まで
            news_summary_text += f"- {news['date'][:10]}: {news['title']}\n"
    else:
        news_summary_text = "（直近の重要ニュースなし）"
        
    # プロンプト構築
    prompt = f"""
あなたはプロの株式市場アナリストです。
以下の台湾株銘柄について、株価の動きと直近ニュースを照らし合わせ、「投資判断補助情報」を作成してください。

【対象銘柄】
{stock_info['name']} ({stock_id})

【株価データ】
- 現在値: {price_info['price_str']}
- 現在のトレンド判定: {price_info['trend']}
- 直近1週間の騰落率: {price_info['weekly_change']}

【直近のニュース】
{news_summary_text}

【指示】
以下のJSONフォーマットで出力してください。
解説は客観的な事実に基づき、投資助言（「買い」「売り」など）は絶対に避けてください。
あくまで「現状の整理」に徹してください。

{{
    "phase": "現在の株価フェーズ（例：上昇トレンド継続、調整局面、底値模索など）短いフレーズで",
    "price_movement": "直近の株価の動きの簡潔な描写（例：好決算を受けて急伸後、高値圏で推移）",
    "news_correlation": "ニュースと株価の関係性（例：ニュースはポジティブだが株価は織り込み済みで反応薄、など）。ニュースがない場合は株価のテクニカルな状況のみ記述。",
    "caution_point": "投資家が今意識すべき注意点（例：過熱感、次回の月次売上発表、外資の動向など）"
}}

出力はJSONのみにしてください。
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "あなたは冷静沈着な株式市場アナリストです。JSON形式で出力します。"},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        return result
        
    except Exception as e:
        print(f"⚠️ 投資判断補助生成エラー（LLM）: {e}")
        return None
