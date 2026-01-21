# -*- coding: utf-8 -*-
"""
投資判断補助ニュース生成モジュール (v5.3)
株価データとニュース要約を入力とし、株価フェーズ整理レポートを生成する
"""
from openai import OpenAI
import json

def generate_investment_aux_news(stock_code, stock_name, price_data, news_summaries):
    """
    投資判断補助ニュース（株価フェーズ整理）を生成する
    
    Args:
        stock_code: 銘柄コード
        stock_name: 銘柄名
        price_data: stock_price_analyzer.get_stock_price_data() の戻り値
        news_summaries: 収集したニュースの要約リスト（文字列のリスト）
        
    Returns:
        dict: {
            'phase': '上昇トレンド継続' | '上昇後の調整局面' | '下落トレンド' | 'レンジ・方向感なし',
            'change_summary': '直近の株価推移要約',
            'news_relation': 'ニュースと株価の関係性',
            'caution': '注意点'
        }
    """
    client = OpenAI()
    
    # 株価データの整形
    if "error" in price_data:
        price_info = "株価データ取得失敗"
    else:
        price_info = f"""
        - 現在値: {price_data['close']} (前日比 {price_data['change_percent']}%)
        - 直近1週間の変化: {price_data['week_change_percent']}%
        - 直近1ヶ月の変化: {price_data['month_change_percent']}%
        - トレンド判定: {price_data['trend']}
        - 移動平均線: 5日={price_data['ma5']}, 20日={price_data['ma20']}, 60日={price_data['ma60']}
        - 直近の急騰・急落: {price_data['volatility']}
        - 直近10日の推移: {price_data['history_summary']}
        """
        
    # ニュース要約の結合
    news_text = "\n".join([f"- {s}" for s in news_summaries[:10]]) if news_summaries else "直近の関連ニュースなし"
    
    system_prompt = """
    あなたはプロの株式市場アナリストです。
    提供された「株価データ」と「直近ニュース」に基づき、投資家が冷静に現状を把握するための「投資判断補助レポート（株価フェーズ整理）」を作成してください。
    
    【重要な制約・禁止事項】
    1. 売買判断、投資助言、推奨表現（「買い時」「売るべき」「上がる見込み」など）は絶対に使用しないこと。
    2. 目標株価や将来予測は記述しないこと。
    3. 断定的な投資行動の誘導は行わないこと。
    4. あくまで「事実の整理」と「現状のフェーズ認識」に徹すること。
    5. ニュースがポジティブでも株価が下がっている場合は、その乖離（織り込み済み、地合い悪化など）を客観的に指摘すること。
    
    【出力フォーマット】
    必ず以下のJSON形式で出力してください。
    {
        "phase": "現在のフェーズ（'上昇トレンド継続', '上昇後の調整局面', '下落トレンド', 'レンジ・方向感なし' のいずれか）",
        "change_summary": "直近5〜10営業日の動き、トレンド、騰落率などを簡潔に要約（50文字以内）",
        "news_relation": "ニュース内容と株価動向が一致しているか、乖離しているか、材料出尽くしかなどを分析（50文字以内）",
        "caution": "現在の局面で投資家が留意すべき事実（過熱感、移動平均線との乖離、出来高など）（50文字以内）"
    }
    """
    
    user_prompt = f"""
    対象銘柄: {stock_name} ({stock_code})
    
    【株価データ】
    {price_info}
    
    【直近の関連ニュース】
    {news_text}
    
    上記に基づき、投資判断補助レポートをJSON形式で作成してください。
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {
            "phase": "判定不能",
            "change_summary": "エラーが発生しました",
            "news_relation": "-",
            "caution": str(e)
        }

if __name__ == "__main__":
    # テスト用
    dummy_price = {
        "close": 100.0,
        "change_percent": -2.5,
        "week_change_percent": -5.0,
        "month_change_percent": 10.0,
        "trend": "上昇後の調整局面",
        "ma5": 102.0,
        "ma20": 98.0,
        "ma60": 90.0,
        "volatility": "なし",
        "history_summary": "100, 101, 103, 102, 100"
    }
    
    dummy_news = ["利益が予想を上回る"]
    
    print("Generating test report...")
    report = generate_investment_aux_news("0000", "テスト銘柄", dummy_price, dummy_news)
    print(json.dumps(report, indent=2, ensure_ascii=False))
