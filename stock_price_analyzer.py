#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
株価データ取得・分析モジュール
yfinanceを使用して台湾株の株価データを取得し、基本的な指標を計算する
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# 台湾時間
TW_TZ = pytz.timezone('Asia/Taipei')

def get_stock_data(stock_id, days=60):
    """
    指定された銘柄の株価データを取得する
    
    Args:
        stock_id (str): 証券コード（例: '2330'）
        days (int): 取得する過去の日数
        
    Returns:
        pandas.DataFrame: 株価データ（取得失敗時はNone）
    """
    try:
        # 台湾株のシンボル形式に変換（例: 2330 -> 2330.TW）
        ticker_symbol = f"{stock_id}.TW"
        ticker = yf.Ticker(ticker_symbol)
        
        # データを取得
        # endは明日を指定して今日を含める
        end_date = datetime.now(TW_TZ) + timedelta(days=1)
        start_date = end_date - timedelta(days=days + 20) # 移動平均計算用に少し長めに
        
        df = ticker.history(start=start_date.strftime('%Y-%m-%d'), 
                           end=end_date.strftime('%Y-%m-%d'))
        
        if df.empty:
            print(f"⚠️ 株価データ取得失敗: {stock_id} (データなし)")
            return None
            
        return df
        
    except Exception as e:
        print(f"⚠️ 株価データ取得エラー: {stock_id} - {e}")
        return None

def analyze_price_phase(df):
    """
    株価データから現在のフェーズを分析する
    
    Returns:
        dict: 分析結果
    """
    if df is None or len(df) < 20:
        return {
            "phase": "データ不足",
            "trend": "不明",
            "ma_status": "不明",
            "volatility": "不明",
            "recent_change": "不明"
        }
        
    # 最新のデータ
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    current_price = latest['Close']
    prev_price = prev['Close']
    
    # 移動平均線
    ma5 = df['Close'].rolling(window=5).mean().iloc[-1]
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    ma60 = df['Close'].rolling(window=60).mean().iloc[-1]
    
    # トレンド判定
    trend = "レンジ・方向感なし"
    if current_price > ma20 and ma20 > ma60:
        trend = "上昇トレンド"
    elif current_price < ma20 and ma20 < ma60:
        trend = "下落トレンド"
    elif current_price > ma60 and current_price < ma20:
        trend = "上昇後の調整局面"
    elif current_price < ma60 and current_price > ma20:
        trend = "下落後の反発局面"
        
    # 短期モメンタム
    momentum = "横ばい"
    if current_price > ma5 * 1.02:
        momentum = "強い"
    elif current_price < ma5 * 0.98:
        momentum = "弱い"
        
    # 直近の変化率
    daily_change_pct = ((current_price - prev_price) / prev_price) * 100
    
    # 5日間の変化率
    if len(df) >= 6:
        week_ago_price = df.iloc[-6]['Close']
        weekly_change_pct = ((current_price - week_ago_price) / week_ago_price) * 100
    else:
        weekly_change_pct = 0
        
    return {
        "current_price": current_price,
        "daily_change_pct": daily_change_pct,
        "weekly_change_pct": weekly_change_pct,
        "trend": trend,
        "momentum": momentum,
        "ma5": ma5,
        "ma20": ma20,
        "ma60": ma60
    }

def get_formatted_price_info(stock_id):
    """
    投資判断補助ニュース用のフォーマット済み情報を取得
    """
    df = get_stock_data(stock_id)
    if df is None:
        return None
        
    analysis = analyze_price_phase(df)
    
    # トレンドに応じたアイコン
    trend_icon = "➡️"
    if "上昇" in analysis['trend']:
        trend_icon = "↗️"
    elif "下落" in analysis['trend']:
        trend_icon = "↘️"
        
    # 変化率の符号
    sign = "+" if analysis['daily_change_pct'] > 0 else ""
    
    return {
        "price_str": f"{analysis['current_price']:.1f} ({sign}{analysis['daily_change_pct']:.2f}%)",
        "trend": analysis['trend'],
        "trend_icon": trend_icon,
        "weekly_change": f"{analysis['weekly_change_pct']:.1f}%",
        "raw_data": analysis
    }
