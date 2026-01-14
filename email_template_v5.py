"""
HTMLメールテンプレート生成関数 v5.1（ニュースクラスタリング対応）
"""

VERSION = "v5.1-frozen-20260113-0320"

def generate_html_email(stock_results, taipei_time):
    """tableベースでiOS Mailのダークモードに完全対応したHTMLメール本文を生成"""
    
    # HTMLヘッダー
    html = """
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; background-color:#ffffff;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#ffffff">
            <tr>
                <td align="center" style="padding:20px;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:800px;">
    """
    
    # ヘッダー
    html += f"""
                        <!-- ヘッダー -->
                        <tr>
                            <td bgcolor="#0ea5e9" style="padding:20px; border-bottom:3px solid #0284c7;">
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td>
                                            <font face="Arial, sans-serif" size="6" color="#ffffff" style="font-weight:bold;">
                                                🇹🇼 台湾株ニュース配信
                                            </font>
                                            <font face="Arial, sans-serif" size="3" color="#ffffff" style="background-color:#16a34a; padding:4px 12px; border-radius:4px; margin-left:10px; font-weight:bold;">
                                                {VERSION}
                                            </font>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-top:10px;">
                                            <font face="Arial, sans-serif" size="2" color="#e0f2fe">
                                                配信日時: {taipei_time}
                                            </font>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr><td style="height:30px;"></td></tr>
    """
    
    # 各銘柄のセクション
    for stock_id, data in stock_results.items():
        # 単一イベント集中の警告
        single_event_warning = ""
        if data.get('is_single_event', False):
            single_event_warning = f"""
                        <!-- 単一イベント警告 -->
                        <tr>
                            <td bgcolor="#dc2626" style="padding:12px 20px; border-radius:8px; border-left:4px solid #991b1b;">
                                <font face="Arial, sans-serif" size="2" color="#ffffff" style="font-weight:bold;">
                                    ⚠️ 本日は重要イベントが集中しています: {data.get('event_description', '詳細不明')}
                                </font>
                            </td>
                        </tr>
                        <tr><td style="height:15px;"></td></tr>
            """
        
        html += f"""
                        <!-- 銘柄セクション: {data['stock_info']['name']} -->
                        <tr>
                            <td style="border-left:4px solid #0ea5e9; padding-left:20px;">
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td>
                                            <font face="Arial, sans-serif" size="5" color="#000000" style="font-weight:bold;">
                                                {data['stock_info']['name']} ({stock_id})
                                            </font>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-top:8px;">
                                            <font face="Arial, sans-serif" size="2" color="#64748b">
                                                {data['stock_info']['business_type']}
                                            </font>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-top:5px;">
                                            <font face="Arial, sans-serif" size="2" color="#64748b">
                                                ニュースクラスタ数: {len(data['news'])}個
                                            </font>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr><td style="height:15px;"></td></tr>
                        
                        {single_event_warning}
                        
                        <!-- 論点ボックス -->
                        <tr>
                            <td bgcolor="#78350f" style="padding:15px 20px; border-radius:8px;">
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td>
                                            <font face="Arial, sans-serif" size="3" color="#fbbf24" style="font-weight:bold;">
                                                💡 本日の論点：
                                            </font>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-top:8px;">
                                            <font face="Arial, sans-serif" size="3" color="#ffffff" style="line-height:1.6;">
                                                {data['topic']}
                                            </font>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr><td style="height:25px;"></td></tr>
        """
        
        # ニュース一覧（クラスタ対応）
        if data['news']:
            for item in data['news']:
                pub_date = item.get('published', '日時不明')
                source = item.get('publisher', '')
                title_ja = item.get('title_ja', item['title'])
                cluster_theme = item.get('cluster_theme', '関連ニュース')
                representative_reason = item.get('representative_reason', '')
                supplementary_news = item.get('supplementary_news', [])
                supplementary_perspectives = item.get('supplementary_perspectives', [])
                
                html += f"""
                        <!-- ニュースクラスタ: {cluster_theme} -->
                        <tr>
                            <td bgcolor="#f1f5f9" style="padding:15px; border-left:4px solid #0ea5e9; border-radius:8px;">
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <!-- クラスタテーマ -->
                                    <tr>
                                        <td bgcolor="#0284c7" style="padding:8px 12px; border-radius:4px;">
                                            <font face="Arial, sans-serif" size="2" color="#ffffff" style="font-weight:bold;">
                                                📌 {cluster_theme}
                                            </font>
                                        </td>
                                    </tr>
                                    <tr><td style="height:12px;"></td></tr>
                                    
                                    <!-- 代表ニュース -->
                                    <tr>
                                        <td>
                                            <font face="Arial, sans-serif" size="2" color="#16a34a" style="font-weight:bold;">
                                                ▶ 主要ニュース
                                            </font>
                                        </td>
                                    </tr>
                                    <tr><td style="height:5px;"></td></tr>
                                    
                                    <!-- 日本語タイトル -->
                                    <tr>
                                        <td>
                                            <font face="Arial, sans-serif" size="3" color="#1e40af" style="font-weight:bold;">
                                                🇯🇵 <a href="{item['link']}" style="color:#1e40af; text-decoration:none;">{title_ja}</a>
                                            </font>
                                        </td>
                                    </tr>
                                    <!-- 中国語タイトル -->
                                    <tr>
                                        <td style="padding-top:8px;">
                                            <font face="Arial, sans-serif" size="2" color="#475569">
                                                🇹🇼 <a href="{item['link']}" style="color:#475569; text-decoration:none;">{item['title']}</a>
                                            </font>
                                        </td>
                                    </tr>
                                    <!-- メタ情報 -->
                                    <tr>
                                        <td style="padding-top:10px;">
                                            <table cellpadding="0" cellspacing="0" border="0">
                                                <tr>
                                                    <td bgcolor="#0284c7" style="padding:4px 10px; border-radius:4px;">
                                                        <font face="Arial, sans-serif" size="1" color="#ffffff" style="font-weight:bold;">
                                                            関連スコア: {item['relevance_score']}
                                                        </font>
                                                    </td>
                                                    <td style="width:10px;"></td>
                                                    {'<td bgcolor="#64748b" style="padding:4px 10px; border-radius:4px;"><font face="Arial, sans-serif" size="1" color="#ffffff" style="font-weight:bold;">' + source + '</font></td>' if source else ''}
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <!-- 代表選定理由 -->
                                    {'<tr><td bgcolor="#065f46" style="padding:8px 12px; border-radius:4px; margin-top:8px;"><font face="Arial, sans-serif" size="2" color="#ffffff">✓ 選定理由: ' + representative_reason + '</font></td></tr>' if representative_reason else ''}
                                    <!-- 関連理由 -->
                                    <tr>
                                        <td bgcolor="#065f46" style="padding:8px 12px; border-radius:4px; margin-top:8px;">
                                            <font face="Arial, sans-serif" size="2" color="#ffffff">
                                                ✓ {item['relevance_reason']}
                                            </font>
                                        </td>
                                    </tr>
                                    <!-- 日時 -->
                                    <tr>
                                        <td style="padding-top:8px;">
                                            <font face="Arial, sans-serif" size="2" color="#64748b">
                                                📅 {pub_date}
                                            </font>
                                        </td>
                                    </tr>
                """
                
                # 補足ニュース
                if supplementary_news:
                    html += """
                                    <tr><td style="height:15px;"></td></tr>
                                    <tr>
                                        <td>
                                            <font face="Arial, sans-serif" size="2" color="#64748b" style="font-weight:bold;">
                                                ▶ 補足視点
                                            </font>
                                        </td>
                                    </tr>
                                    <tr><td style="height:5px;"></td></tr>
                    """
                    
                    for i, supp_news in enumerate(supplementary_news):
                        perspective = supplementary_perspectives[i] if i < len(supplementary_perspectives) else '追加情報'
                        supp_title_ja = supp_news.get('title_ja', supp_news['title'])
                        
                        html += f"""
                                    <tr>
                                        <td bgcolor="#f8fafc" style="padding:10px; border-left:2px solid #cbd5e1; border-radius:4px;">
                                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                                <tr>
                                                    <td>
                                                        <font face="Arial, sans-serif" size="1" color="#ffffff" style="background-color:#64748b; padding:2px 8px; border-radius:4px; font-weight:bold;">
                                                            {perspective}
                                                        </font>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="padding-top:5px;">
                                                        <font face="Arial, sans-serif" size="2" color="#475569">
                                                            <a href="{supp_news['link']}" style="color:#475569; text-decoration:none;">{supp_title_ja}</a>
                                                        </font>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                    <tr><td style="height:8px;"></td></tr>
                        """
                
                html += """
                                </table>
                            </td>
                        </tr>
                        <tr><td style="height:20px;"></td></tr>
                """
        else:
            html += """
                        <tr>
                            <td bgcolor="#f1f5f9" style="padding:15px; border-radius:8px;">
                                <font face="Arial, sans-serif" size="3" color="#000000">
                                    本日は関連ニュースがありませんでした。
                                </font>
                            </td>
                        </tr>
                        <tr><td style="height:20px;"></td></tr>
            """
        
        # 銘柄間の余白
        html += """
                        <tr><td style="height:40px;"></td></tr>
        """
    
    # HTMLフッター（バージョン情報付き）
    html += f"""
                        <!-- フッター -->
                        <tr><td style="height:40px;"></td></tr>
                        <tr>
                            <td bgcolor="#f1f5f9" style="padding:20px; border-radius:8px; text-align:center;">
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td>
                                            <font face="Arial, sans-serif" size="2" color="#64748b" style="font-weight:bold;">
                                                台湾株ニュース配信システム {VERSION}
                                            </font>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-top:8px;">
                                            <font face="Arial, sans-serif" size="1" color="#94a3b8">
                                                build: {VERSION} | 仕様書: v5.1-20260113
                                            </font>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-top:5px;">
                                            <font face="Arial, sans-serif" size="1" color="#94a3b8">
                                                配信銘柄: 台積電（2330）、創見（2451）、宇瞻（8271）、廣達（2382）
                                            </font>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding-top:5px;">
                                            <font face="Arial, sans-serif" size="1" color="#94a3b8">
                                                新機能: ニュース多様性改善（論点クラスタリング）
                                            </font>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return html
