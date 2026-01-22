# -*- coding: utf-8 -*-
"""
HTMLメールテンプレート生成関数 v5.3 (v5.1完全復元版)
- ダークモードベース
- 「本日の論点」（オレンジ）、「分析スコア」（緑）などの多層ボックス構造を復元
- 投資判断補助ニュースを既存ニュースと同じフォーマットで追加
"""

import os
import sendgrid
from sendgrid.helpers.mail import Mail
from datetime import datetime, timedelta, timezone

# 識別用コメント（ログ出力用）
TEMPLATE_ID = "v5.3-restored-dark-v5.1"

def create_email_body(stock_results):
    """HTMLメール本文を生成（v5.1デザイン復元）"""
    
    taipei_time = datetime.now(timezone(timedelta(hours=8))).strftime('%Y年%m月%d日 %H:%M')
    
    # HTMLヘッダー（ダークモード）
    html = """
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #121212; color: #e0e0e0; margin: 0; padding: 0; }
            .container { max-width: 600px; margin: 0 auto; background-color: #1e1e1e; }
            .header { background-color: #0056b3; padding: 20px; color: #ffffff; }
            .stock-section { padding: 20px; border-bottom: 1px solid #333; }
            .stock-title { font-size: 24px; font-weight: bold; color: #ffffff; margin-bottom: 5px; }
            .stock-meta { font-size: 12px; color: #aaaaaa; margin-bottom: 15px; }
            
            /* 論点ボックス（オレンジ） */
            .point-box { background-color: #3d2b1f; border-left: 4px solid #d97706; padding: 15px; margin-bottom: 20px; border-radius: 4px; }
            .point-title { color: #fbbf24; font-weight: bold; font-size: 14px; margin-bottom: 5px; }
            .point-text { color: #e0e0e0; font-size: 14px; line-height: 1.6; }
            
            /* ニュースアイテム */
            .news-item { margin-bottom: 30px; }
            
            /* テーマバー（青） */
            .theme-bar { background-color: #1e3a8a; color: #bfdbfe; padding: 5px 10px; font-size: 12px; font-weight: bold; display: inline-block; border-radius: 3px; margin-bottom: 10px; }
            
            /* ニュースタイトル */
            .news-title-jp { font-size: 16px; font-weight: bold; color: #ffffff; margin-bottom: 4px; line-height: 1.4; }
            .news-title-tw { font-size: 12px; color: #9ca3af; margin-bottom: 10px; }
            
            /* 分析ボックス（緑） */
            .analysis-box { background-color: #143323; border-left: 4px solid #22c55e; padding: 15px; margin-bottom: 15px; border-radius: 4px; }
            .analysis-label { color: #86efac; font-size: 11px; font-weight: bold; margin-bottom: 5px; text-transform: uppercase; }
            .analysis-text { color: #d1fae5; font-size: 13px; line-height: 1.6; }
            
            /* 補足ボックス（グレー） */
            .supp-box { background-color: #262626; border-left: 4px solid #525252; padding: 12px; margin-top: 10px; border-radius: 4px; }
            .supp-title { color: #a3a3a3; font-size: 11px; font-weight: bold; margin-bottom: 5px; }
            .supp-text { color: #d4d4d4; font-size: 12px; line-height: 1.5; }
            
            /* リンク */
            a { color: #3b82f6; text-decoration: none; }
            a:hover { text-decoration: underline; }
            
            /* フッター */
            .footer { background-color: #000000; padding: 20px; text-align: center; font-size: 11px; color: #666; }
        </style>
    </head>
    <body>
        <div class="container">
            <!-- ヘッダー -->
            <div class="header">
                <div style="font-size: 20px; font-weight: bold;">🇹🇼 台湾株ニュース配信</div>
                <div style="font-size: 12px; opacity: 0.8; margin-top: 5px;">{taipei_time}</div>
            </div>
    """
    
    # 各銘柄のループ
    for stock_code, result in stock_results.items():
        stock_name = result['stock_name']
        news_list = result.get('news', [])
        
        # ニュースクラスタ数（投資判断補助を含む）
        cluster_count = len(news_list)
        
        html += f"""
            <div class="stock-section">
                <div class="stock-title">{stock_name} ({stock_code})</div>
                <div class="stock-meta">ニュースクラスタ数: {cluster_count}個</div>
        """
        
        # 本日の論点（最初のニュースの要約などを論点として表示する簡易ロジック）
        # ※本来は全ニュースから生成するが、ここでは最初のニュースの要約を使用
        if news_list:
            top_news = news_list[0]['representative']
            point_text = top_news.get('llm_result', {}).get('summary', '特になし')
            
            html += f"""
                <div class="point-box">
                    <div class="point-title">💡 本日の論点:</div>
                    <div class="point-text">{point_text}</div>
                </div>
            """
            
        # ニュースリスト
        for cluster in news_list:
            theme = cluster.get('theme', 'No Theme')
            rep_news = cluster.get('representative', {})
            supp_news = cluster.get('supplementary', [])
            
            # LLM結果
            llm_res = rep_news.get('llm_result', {})
            summary = llm_res.get('summary', '')
            reason = llm_res.get('reason', '')
            
            # タイトル（日本語・繁体字）
            # ※投資判断補助の場合、繁体字タイトルはないので日本語を再利用または空にする
            title_jp = rep_news.get('title', 'No Title')
            title_tw = rep_news.get('title_tw', title_jp) # 繁体字がなければ日本語
            
            # 投資判断補助かどうかの判定（テーマ名で簡易判定）
            is_aux = "投資判断補助" in theme
            
            # リンク
            link = rep_news.get('link', '#')
            
            # 日付
            pub_date = rep_news.get('published', '')
            if hasattr(pub_date, 'strftime'):
                pub_date_str = pub_date.strftime('%Y-%m-%d %H:%M')
            else:
                pub_date_str = str(pub_date)

            html += f"""
                <div class="news-item">
                    <div class="theme-bar">{theme}</div>
                    
                    <div class="news-title-jp">
                        <a href="{link}" style="color:#ffffff; text-decoration:none;">{title_jp}</a>
                    </div>
                    <div class="news-title-tw">{title_tw}</div>
                    
                    <!-- 分析ボックス（緑） -->
                    <div class="analysis-box">
                        <div class="analysis-label">関連スコア / 投資判断</div>
                        <div class="analysis-text">
                            {summary}
                        </div>
                        <div style="margin-top:8px; font-size:11px; color:#6ee7b7;">
                            📅 {pub_date_str}
                        </div>
                    </div>
            """
            
            # 補足ニュース（あれば）
            if supp_news:
                html += """
                    <div class="supp-box">
                        <div class="supp-title">補足視点</div>
                        <ul style="margin:0; padding-left:20px; color:#d4d4d4; font-size:12px;">
                """
                for supp in supp_news:
                    s_title = supp.get('title', '')
                    s_link = supp.get('link', '#')
                    html += f"""
                        <li style="margin-bottom:4px;">
                            <a href="{s_link}" style="color:#a3a3a3;">{s_title}</a>
                        </li>
                    """
                html += """
                        </ul>
                    </div>
                """
                
            html += "</div>" # End news-item
            
        html += "</div>" # End stock-section

    # フッター
    html += """
            <div class="footer">
                本メールは自動配信システムによって生成されています。<br>
                投資判断は自己責任で行ってください。<br>
                &copy; 2026 Taiwan Stock News System
            </div>
        </div>
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
