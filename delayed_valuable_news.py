# -*- coding: utf-8 -*-
"""
遅れても価値がある類型の判定モジュール
v5.3: インターフェース統一
"""

def is_delayed_but_valuable(entry, stock_info):
    """
    ニュースが「遅れても価値がある」類型かどうかを判定する
    
    Args:
        entry (dict): ニュースエントリ
        stock_info (dict): 銘柄情報
        
    Returns:
        tuple: (is_valuable: bool, reason: str)
    """
    title = entry.get('title', '')
    summary = entry.get('summary', '')
    text = f"{title} {summary}"
    
    # 1. 業績・ファンダメンタルズ（長期有効）
    earnings_keywords = [
        '營收', '法說會', '財測', '展望', '接單', 'CapEx', '資本支出',
        '月營收', '季報', '年報', '業績', '獲利', 'EPS', '毛利率'
    ]
    for k in earnings_keywords:
        if k in text:
            return True, f"業績・ファンダメンタルズ関連（{k}）のため、遅れても分析価値あり"
            
    # 2. 技術・構造変化（長期有効）
    tech_keywords = [
        'DRAM', 'NAND', 'HBM', 'CoWoS', 'DDR5', '先進製程', '先進封裝',
        'EUV', '液冷', 'AI伺服器', 'GB200', '產能', '擴產'
    ]
    for k in tech_keywords:
        if k in text:
            return True, f"技術・構造変化関連（{k}）のため、遅れても分析価値あり"
            
    # 3. 政策・地政学（長期有効）
    policy_keywords = [
        '關稅', '管制', '補助金', '美國廠', '地緣政治', '貿易戰', '制裁'
    ]
    for k in policy_keywords:
        if k in text:
            return True, f"政策・地政学関連（{k}）のため、遅れても分析価値あり"
            
    return False, ""
