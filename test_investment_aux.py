# -*- coding: utf-8 -*-
import json
from stock_price_analyzer import get_stock_price_data
from investment_aux_generator import generate_investment_aux_news
from email_template_v5 import create_email_body

def test_investment_aux_flow():
    print("=== 投資判断補助ニュース生成テスト ===")
    
    stock_code = "2330"
    stock_name = "台積電"
    
    # 1. 株価データ取得
    print(f"1. 株価データ取得中 ({stock_code})...")
    price_data = get_stock_price_data(stock_code)
    print(f"   取得結果: {price_data['close']} (前日比 {price_data['change_percent']}%)")
    
    # 2. ダミーニュース要約
    news_summaries = [
        "TSMCの第4四半期決算は市場予想を上回る増収増益。",
        "CoWoSパッケージング能力を倍増させる計画を発表。",
        "米国アリゾナ工場での生産開始が順調に進んでいる。"
    ]
    
    # 3. レポート生成
    print("2. レポート生成中...")
    investment_aux = generate_investment_aux_news(
        stock_code, 
        stock_name, 
        price_data, 
        news_summaries
    )
    
    print("   生成結果:")
    print(json.dumps(investment_aux, indent=2, ensure_ascii=False))
    
    # 4. メール本文生成テスト
    print("3. メール本文生成テスト...")
    results = {
        stock_code: {
            'stock_code': stock_code,
            'stock_name': stock_name,
            'news': [], # ニュースなしでも表示されるか確認
            'investment_aux': investment_aux,
            'news_count': 0
        }
    }
    
    html = create_email_body(results)
    
    if "投資判断補助（株価フェーズ整理）" in html:
        print("   ✅ メール本文にセクションが含まれています")
    else:
        print("   ❌ メール本文にセクションが含まれていません")
        
    if investment_aux['phase'] in html:
        print(f"   ✅ フェーズ「{investment_aux['phase']}」が表示されています")
        
    with open("test_email.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("   プレビュー保存: test_email.html")

if __name__ == "__main__":
    test_investment_aux_flow()
