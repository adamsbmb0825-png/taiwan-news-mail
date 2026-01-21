# -*- coding: utf-8 -*-
"""
株価データ取得・分析モジュール (v5.3)
yfinanceを使用して直近の株価データを取得し、トレンド分析を行う
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_stock_price_data(ticker_symbol, days=30):
    """
    指定された銘柄の直近株価データを取得し、分析結果を返す
    
    Args:
        ticker_symbol (str): 銘柄コード（例: "2330"）
        days (int): 取得する過去の日数
        
    Returns:
        dict: 株価分析結果
    """
    # 台湾株のシンボル形式に変換（例: 2330 -> 2330.TW）
    symbol = f"{ticker_symbol}.TW"
    
    try:
        # 株価データ取得
        stock = yf.Ticker(symbol)
        # 直近のデータを取得（少し多めに取得して移動平均などを計算可能にする）
        history = stock.history(period="3mo")
        
        if history.empty:
            return {"error": "No data found"}
            
        # 直近データ
        latest = history.iloc[-1]
        latest_date = history.index[-1].strftime('%Y-%m-%d')
        latest_close = latest['Close']
        
        # 前日比
        if len(history) >= 2:
            prev_close = history.iloc[-2]['Close']
            change = latest_close - prev_close
            change_percent = (change / prev_close) * 100
        else:
            change = 0
            change_percent = 0
            
        # 直近5営業日の変動
        if len(history) >= 6:
            week_ago_close = history.iloc[-6]['Close']
            week_change = latest_close - week_ago_close
            week_change_percent = (week_change / week_ago_close) * 100
        else:
            week_change_percent = 0
            
        # 直近20営業日（約1ヶ月）の変動
        if len(history) >= 21:
            month_ago_close = history.iloc[-21]['Close']
            month_change = latest_close - month_ago_close
            month_change_percent = (month_change / month_ago_close) * 100
        else:
            month_change_percent = 0
            
        # 移動平均線
        ma5 = history['Close'].rolling(window=5).mean().iloc[-1]
        ma20 = history['Close'].rolling(window=20).mean().iloc[-1]
        ma60 = history['Close'].rolling(window=60).mean().iloc[-1]
        
        # トレンド判定（簡易ロジック）
        trend = "レンジ・方向感なし"
        if latest_close > ma20 and ma20 > ma60:
            trend = "上昇トレンド"
        elif latest_close < ma20 and ma20 < ma60:
            trend = "下落トレンド"
        elif latest_close < ma20 and ma20 > ma60:
            trend = "上昇後の調整局面"
        elif latest_close > ma20 and ma20 < ma60:
            trend = "下落後の反発局面"
            
        # 急騰・急落検知（直近5営業日以内で3%以上の変動があったか）
        recent_volatility = []
        recent_data = history.tail(5)
        for i in range(1, len(recent_data)):
            daily_change = (recent_data.iloc[i]['Close'] - recent_data.iloc[i-1]['Close']) / recent_data.iloc[i-1]['Close'] * 100
            if abs(daily_change) >= 3.0:
                date_str = recent_data.index[i].strftime('%Y-%m-%d')
                direction = "急騰" if daily_change > 0 else "急落"
                recent_volatility.append(f"{date_str}に{abs(daily_change):.1f}%の{direction}")
        
        volatility_msg = "なし"
        if recent_volatility:
            volatility_msg = "、".join(recent_volatility)
            
        return {
            "symbol": ticker_symbol,
            "date": latest_date,
            "close": round(latest_close, 2),
            "change_percent": round(change_percent, 2),
            "week_change_percent": round(week_change_percent, 2),
            "month_change_percent": round(month_change_percent, 2),
            "trend": trend,
            "ma5": round(ma5, 2),
            "ma20": round(ma20, 2),
            "ma60": round(ma60, 2),
            "volatility": volatility_msg,
            "history_summary": _format_history_summary(history.tail(10))
        }
        
    except Exception as e:
        return {"error": str(e)}

def _format_history_summary(df):
    """
    直近の株価推移をテキスト形式で整形
    """
    summary = []
    for date, row in df.iterrows():
        date_str = date.strftime('%m/%d')
        close = row['Close']
        summary.append(f"{date_str}: {close:.1f}")
    return ", ".join(summary)

if __name__ == "__main__":
    # テスト実行
    print("Testing with TSMC (2330)...")
    result = get_stock_price_data("2330")
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
