"""
遅れても価値がある類型の判定関数
v5.2-lite-v3: 30日フォールバック時に使用
"""

def is_delayed_valuable_news(title, summary):
    """
    遅れても価値がある類型のキーワードが含まれているかチェック
    
    Args:
        title: ニュースタイトル
        summary: ニュース概要
    
    Returns:
        True / False
    """
    # 業績関連キーワード
    earnings_keywords = [
        '營收', '法說會', '財測', '展望', '接單', 'CapEx', '資本支出',
        '月營收', '季報', '年報', '業績', '獲利', 'EPS', '毛利率',
        '營業利益', '淨利', '營業額', '營業收入'
    ]
    
    # 技術・需給関連キーワード
    tech_supply_keywords = [
        'DRAM', 'NAND', 'HBM', 'CoWoS', 'DDR5', 'LPDDR5',
        '價格', '供需', '產能', '瓶頸', '缺貨', '供應鏈',
        '先進製程', '先進封裝', 'EUV', '液冷', 'AI伺服器',
        'GB200', 'H200', 'AI晶片', '記憶體'
    ]
    
    # 政策・地政学関連キーワード
    policy_keywords = [
        '關稅', '管制', '補助金', '投資審查', '美國廠', '地緣政治',
        '貿易戰', '出口管制', '制裁', '投資限制', '稅收優惠',
        '政策支持', '產業政策', '國家安全', '技術封鎖'
    ]
    
    # すべてのキーワードを統合
    all_keywords = earnings_keywords + tech_supply_keywords + policy_keywords
    
    # タイトルまたは概要にキーワードが含まれているかチェック
    text = f"{title} {summary}"
    for keyword in all_keywords:
        if keyword in text:
            return True
    
    return False
