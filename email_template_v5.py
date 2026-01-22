# -*- coding: utf-8 -*-
"""
HTMLメールテンプレート生成関数 v5.3（投資判断補助ニュース対応・デザイン修正版）
"""

import os
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime, timedelta, timezone

VERSION = "v5.3-20260121-fix"

def create_email_body(stock_results):
    """HTMLメール本文を生成"""
    
    taipei_time = datetime.now(timezone(timedelta(hours=8))).strftime('%Y/%m/%d %H:%M')
    
    # HTMLヘッダー
    html = """
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin:0; padding:0; background-color:#f3f4f6;">
        <table width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="#f3f4f6">
            <tr>
                <td align="center" style="padding:20px;">
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:800px; background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
    """
    
    # ヘッダー
    html += f"""
                        <!-- ヘッダー -->
                        <tr>
                            <td bgcolor="#1e293b" style="padding:24px;">
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td>
                                            <font face="Helvetica, Arial, sans-serif" size="5" color="#ffffff" style="font-weight:bold; letter-spacing:0.5px;">
                                                🇹🇼 台湾株 投資判断レポート
                                            </font>
                                        </td>
                                        <td align="right">
                                            <font face="Helvetica, Arial, sans-serif" size="2" color="#94a3b8">
                                                {taipei_time} (TST)
                                            </font>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
    """
    
    # 各銘柄のループ
    for stock_code, result in stock_results.items():
        stock_name = result['stock_name']
        news_list = result.get('news', [])
        investment_aux = result.get('investment_aux', {})
        
        html += f"""
                        <!-- 銘柄セクション: {stock_name} -->
                        <tr>
                            <td style="padding:24px 24px 0 24px;">
                                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td style="border-bottom:2px solid #e2e8f0; padding-bottom:12px;">
                                            <font face="Helvetica, Arial, sans-serif" size="5" color="#0f172a" style="font-weight:bold;">
                                                {stock_name} <span style="color:#64748b; font-size:18px;">({stock_code})</span>
                                            </font>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
        """
        
        # ① 企業ニュース（クラスタリング表示） - 先に表示
        if news_list:
            html += """
                        <tr>
                            <td style="padding:16px 24px 0 24px;">
                                <font face="Helvetica, Arial, sans-serif" size="2" color="#64748b" style="font-weight:bold; text-transform:uppercase; letter-spacing:1px;">
                                    Latest News
                                </font>
            """
            
            for cluster in news_list:
                theme = cluster.get('theme', 'No Theme')
                rep_news = cluster.get('representative', {})
                supp_news = cluster.get('supplementary', [])
                
                html += f"""
                                <div style="margin-top:12px; margin-bottom:24px;">
                                    <font face="Helvetica, Arial, sans-serif" size="3" color="#0f172a" style="font-weight:bold; background:linear-gradient(to right, #e0f2fe, #ffffff); padding:4px 8px; border-radius:4px;">
                                        📌 {theme}
                                    </font>
                                    <div style="margin-top:8px;">
                                        <a href="{rep_news.get('link', '#')}" style="text-decoration:none; color:#0284c7; font-weight:bold; font-family:Helvetica, Arial, sans-serif; font-size:16px;">
                                            {rep_news.get('title', 'No Title')}
                                        </a>
                                        <div style="margin-top:4px;">
                                            <font face="Helvetica, Arial, sans-serif" size="2" color="#64748b">
                                                {rep_news.get('source', 'Unknown')} • {rep_news.get('published', '').strftime('%m/%d %H:%M') if hasattr(rep_news.get('published'), 'strftime') else '-'}
                                            </font>
                                        </div>
                                        <div style="margin-top:8px; line-height:1.6;">
                                            <font face="Helvetica, Arial, sans-serif" size="3" color="#334155">
                                                {rep_news.get('llm_result', {}).get('summary', '')}
                                            </font>
                                        </div>
                                    </div>
                """
                
                # 補足ニュース
                if supp_news:
                    html += """
                                    <div style="margin-top:12px; padding-left:12px; border-left:2px solid #e2e8f0;">
                                        <font face="Helvetica, Arial, sans-serif" size="2" color="#64748b">関連情報:</font>
                                        <ul style="margin:4px 0 0 0; padding-left:20px; color:#475569; font-family:Helvetica, Arial, sans-serif; font-size:13px;">
                                    """
                    for supp in supp_news:
                        html += f"""
                                            <li style="margin-bottom:4px;">
                                                {supp.get('llm_result', {}).get('summary', supp.get('title', ''))}
                                                <a href="{supp.get('link', '#')}" style="color:#94a3b8; text-decoration:none;">[Link]</a>
                                            </li>
                        """
                    html += """
                                        </ul>
                                    </div>
                    """
                
                html += "</div>"
                
            html += """
                            </td>
                        </tr>
            """
        else:
            # ニュースがない場合もスペースを空ける（あるいはメッセージを表示）
            html += """
                        <tr>
                            <td style="padding:16px 24px 0 24px;">
                                <font face="Helvetica, Arial, sans-serif" size="2" color="#64748b" style="font-weight:bold; text-transform:uppercase; letter-spacing:1px;">
                                    Latest News
                                </font>
                                <div style="margin-top:12px; margin-bottom:24px;">
                                    <font face="Helvetica, Arial, sans-serif" size="3" color="#94a3b8">
                                        ※ 直近の重要ニュースはありませんでした。
                                    </font>
                                </div>
                            </td>
                        </tr>
            """

        # ② 投資判断補助ニュース（v5.3新機能） - 後に表示、デザインをフラット化
        if investment_aux:
            phase_color = "#16a34a" # デフォルト緑
            if "下落" in investment_aux.get('phase', ''):
                phase_color = "#dc2626" # 赤
            elif "調整" in investment_aux.get('phase', ''):
                phase_color = "#ca8a04" # 黄
                
            html += f"""
                        <tr>
                            <td style="padding:0 24px 24px 24px;">
                                <div style="border-top:1px solid #e2e8f0; margin-bottom:16px;"></div>
                                <font face="Helvetica, Arial, sans-serif" size="2" color="#64748b" style="font-weight:bold; text-transform:uppercase; letter-spacing:1px;">
                                    Market Phase Analysis
                                </font>
                                <div style="margin-top:12px;">
                                    <div style="margin-bottom:12px; border-left:4px solid {phase_color}; padding-left:12px;">
                                        <font face="Helvetica, Arial, sans-serif" size="4" color="#0f172a" style="font-weight:bold;">
                                            {investment_aux.get('phase', '判定不能')}
                                        </font>
                                    </div>
                                    
                                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:12px;">
                                        <tr>
                                            <td width="30%" valign="top" style="padding-right:12px;">
                                                <font face="Helvetica, Arial, sans-serif" size="2" color="#64748b">直近変動</font><br>
                                                <font face="Helvetica, Arial, sans-serif" size="3" color="#0f172a">{investment_aux.get('change_summary', '-')}</font>
                                            </td>
                                            <td width="70%" valign="top">
                                                <font face="Helvetica, Arial, sans-serif" size="2" color="#64748b">ニュースとの関係性</font><br>
                                                <font face="Helvetica, Arial, sans-serif" size="3" color="#0f172a">{investment_aux.get('news_relation', '-')}</font>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <div style="margin-top:12px; padding-top:12px;">
                                        <font face="Helvetica, Arial, sans-serif" size="2" color="#15803d">
                                            <b>💡 注意点:</b> {investment_aux.get('caution', '-')}
                                        </font>
                                    </div>
                                </div>
                            </td>
                        </tr>
            """

    # フッター
    html += """
                        <tr>
                            <td bgcolor="#f8fafc" style="padding:24px; border-top:1px solid #e2e8f0; text-align:center;">
                                <font face="Helvetica, Arial, sans-serif" size="2" color="#94a3b8">
                                    本メールは自動配信システムによって生成されています。<br>
                                    投資判断は自己責任で行ってください。<br>
                                    &copy; 2026 Taiwan Stock News System
                                </font>
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

def send_email_via_sendgrid(api_key, from_email, to_email, subject, html_content):
    """SendGridを使用してメールを送信"""
    message = Mail(
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    try:
        sg = sendgrid.SendGridAPIClient(api_key)
        response = sg.send(message)
        return response.status_code
    except Exception as e:
        print(f"SendGrid Error: {e}")
        return 500
