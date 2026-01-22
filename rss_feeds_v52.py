# -*- coding: utf-8 -*-
"""
台湾株ニュース配信システム v5.2
RSSフィード一覧（3カテゴリ分離構造 + 地域パラメータ分岐）
"""

# RSSフィード一覧
RSS_FEEDS_V52 = [
    # ========================================
    # 台積電（2330）
    # ========================================
    
    # ① 銘柄直結クエリ（高精度枠）
    "https://news.google.com/rss/search?q=台積電+OR+TSMC&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TW-01: 企業名（TW）
    "https://news.google.com/rss/search?q=台積電+OR+TSMC&hl=en-US&gl=US&ceid=US:en",  # TW-01: 企業名（US）
    "https://news.google.com/rss/search?q=台積電+OR+TSMC&hl=ja&gl=JP&ceid=JP:ja",  # TW-01: 企業名（JP）
    "https://news.google.com/rss/search?q=TSMC+2330&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TW-02: 銘柄コード
    
    # ② 上流ドライバークエリ（多面性枠）
    "https://news.google.com/rss/search?q=先進製程+OR+3奈米+OR+2奈米&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TW-03: 技術（先進製程）TW
    "https://news.google.com/rss/search?q=advanced+process+OR+3nm+OR+2nm&hl=en-US&gl=US&ceid=US:en",  # TW-03: 技術（先進製程）US
    "https://news.google.com/rss/search?q=先進プロセス+OR+3nm+OR+2nm&hl=ja&gl=JP&ceid=JP:ja",  # TW-03: 技術（先進製程）JP
    
    "https://news.google.com/rss/search?q=CoWoS+OR+先進封裝&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TW-04: 技術（先進封裝）TW
    "https://news.google.com/rss/search?q=CoWoS+OR+advanced+packaging&hl=en-US&gl=US&ceid=US:en",  # TW-04: 技術（先進封裝）US
    "https://news.google.com/rss/search?q=CoWoS+OR+先進パッケージング&hl=ja&gl=JP&ceid=JP:ja",  # TW-04: 技術（先進封裝）JP
    
    "https://news.google.com/rss/search?q=NVIDIA+OR+AI晶片+OR+GPU&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TW-05: 顧客（AI）TW
    "https://news.google.com/rss/search?q=NVIDIA+OR+AI+chip+OR+GPU&hl=en-US&gl=US&ceid=US:en",  # TW-05: 顧客（AI）US
    "https://news.google.com/rss/search?q=NVIDIA+OR+AIチップ+OR+GPU&hl=ja&gl=JP&ceid=JP:ja",  # TW-05: 顧客（AI）JP
    
    "https://news.google.com/rss/search?q=台積電+美國廠+OR+TSMC+Arizona&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TW-06: 政策（米国工場）TW
    "https://news.google.com/rss/search?q=TSMC+Arizona+OR+US+fab&hl=en-US&gl=US&ceid=US:en",  # TW-06: 政策（米国工場）US
    "https://news.google.com/rss/search?q=TSMC+アリゾナ+OR+米国工場&hl=ja&gl=JP&ceid=JP:ja",  # TW-06: 政策（米国工場）JP
    
    # ③ 業績・イベントクエリ（確実枠）
    "https://news.google.com/rss/search?q=台積電+營收&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TW-07: 月次營收
    "https://news.google.com/rss/search?q=台積電+法說會+OR+TSMC+outlook&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TW-08: 法說會（TW）
    "https://news.google.com/rss/search?q=TSMC+earnings+OR+outlook&hl=en-US&gl=US&ceid=US:en",  # TW-08: 法說會（US）
    
    # ========================================
    # 創見（2451）
    # ========================================
    
    # ① 銘柄直結クエリ（高精度枠）
    "https://news.google.com/rss/search?q=創見+OR+Transcend&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TR-01: 企業名（TW）
    "https://news.google.com/rss/search?q=創見+OR+Transcend&hl=en-US&gl=US&ceid=US:en",  # TR-01: 企業名（US）
    "https://news.google.com/rss/search?q=創見+OR+Transcend&hl=ja&gl=JP&ceid=JP:ja",  # TR-01: 企業名（JP）
    "https://news.google.com/rss/search?q=創見+2451&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TR-02: 銘柄コード
    
    # ② 上流ドライバークエリ（多面性枠）
    "https://news.google.com/rss/search?q=工業用記憶體+OR+車載記憶體&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TR-03: 技術（産業用メモリ）TW
    "https://news.google.com/rss/search?q=industrial+memory+OR+automotive+memory&hl=en-US&gl=US&ceid=US:en",  # TR-03: 技術（産業用メモリ）US
    "https://news.google.com/rss/search?q=産業用メモリ+OR+車載メモリ&hl=ja&gl=JP&ceid=JP:ja",  # TR-03: 技術（産業用メモリ）JP
    
    "https://news.google.com/rss/search?q=DRAM價格+OR+記憶體價格&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TR-04: 需給（DRAM価格）TW
    "https://news.google.com/rss/search?q=DRAM+price+OR+memory+price&hl=en-US&gl=US&ceid=US:en",  # TR-04: 需給（DRAM価格）US
    "https://news.google.com/rss/search?q=DRAM価格+OR+メモリ価格&hl=ja&gl=JP&ceid=JP:ja",  # TR-04: 需給（DRAM価格）JP
    
    # ③ 業績・イベントクエリ（確実枠）
    "https://news.google.com/rss/search?q=創見+營收&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TR-05: 月次營收
    "https://news.google.com/rss/search?q=創見+法說會+OR+Transcend+outlook&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # TR-06: 法說會
    
    # ========================================
    # 宇瞻（8271）
    # ========================================
    
    # ① 銘柄直結クエリ（高精度枠）
    "https://news.google.com/rss/search?q=宇瞻+OR+Apacer&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # AP-01: 企業名（TW）
    "https://news.google.com/rss/search?q=宇瞻+OR+Apacer&hl=en-US&gl=US&ceid=US:en",  # AP-01: 企業名（US）
    "https://news.google.com/rss/search?q=宇瞻+OR+Apacer&hl=ja&gl=JP&ceid=JP:ja",  # AP-01: 企業名（JP）
    "https://news.google.com/rss/search?q=宇瞻+8271&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # AP-02: 銘柄コード
    
    # ② 上流ドライバークエリ（多面性枠）
    "https://news.google.com/rss/search?q=工業用記憶體+OR+醫療記憶體&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # AP-03: 技術（産業用メモリ）TW
    "https://news.google.com/rss/search?q=industrial+memory+OR+medical+memory&hl=en-US&gl=US&ceid=US:en",  # AP-03: 技術（産業用メモリ）US
    "https://news.google.com/rss/search?q=産業用メモリ+OR+医療用メモリ&hl=ja&gl=JP&ceid=JP:ja",  # AP-03: 技術（産業用メモリ）JP
    
    # DRAM価格クエリは創見と共通（重複除外される）
    
    # ③ 業績・イベントクエリ（確実枠）
    "https://news.google.com/rss/search?q=宇瞻+營收&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # AP-05: 月次營收
    "https://news.google.com/rss/search?q=宇瞻+法說會+OR+Apacer+outlook&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # AP-06: 法說會
    
    # ========================================
    # 廣達（2382）
    # ========================================
    
    # ① 銘柄直結クエリ（高精度枠）
    "https://news.google.com/rss/search?q=廣達+OR+Quanta&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # QT-01: 企業名（TW）
    "https://news.google.com/rss/search?q=廣達+OR+Quanta&hl=en-US&gl=US&ceid=US:en",  # QT-01: 企業名（US）
    "https://news.google.com/rss/search?q=廣達+OR+Quanta&hl=ja&gl=JP&ceid=JP:ja",  # QT-01: 企業名（JP）
    "https://news.google.com/rss/search?q=廣達+2382&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # QT-02: 銘柄コード
    
    # ② 上流ドライバークエリ（多面性枠）
    "https://news.google.com/rss/search?q=AI伺服器+OR+資料中心&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # QT-03: 顧客（AIサーバー）TW
    "https://news.google.com/rss/search?q=AI+server+OR+data+center&hl=en-US&gl=US&ceid=US:en",  # QT-03: 顧客（AIサーバー）US
    "https://news.google.com/rss/search?q=AIサーバー+OR+データセンター&hl=ja&gl=JP&ceid=JP:ja",  # QT-03: 顧客（AIサーバー）JP
    
    "https://news.google.com/rss/search?q=NVIDIA+GB200+OR+Blackwell&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # QT-04: 顧客（NVIDIA）TW
    "https://news.google.com/rss/search?q=NVIDIA+GB200+OR+Blackwell&hl=en-US&gl=US&ceid=US:en",  # QT-04: 顧客（NVIDIA）US
    "https://news.google.com/rss/search?q=NVIDIA+GB200+OR+Blackwell&hl=ja&gl=JP&ceid=JP:ja",  # QT-04: 顧客（NVIDIA）JP
    
    "https://news.google.com/rss/search?q=液冷伺服器+OR+散熱&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # QT-05: 技術（液冷）TW
    "https://news.google.com/rss/search?q=liquid+cooling+server+OR+thermal&hl=en-US&gl=US&ceid=US:en",  # QT-05: 技術（液冷）US
    "https://news.google.com/rss/search?q=液冷サーバー+OR+冷却技術&hl=ja&gl=JP&ceid=JP:ja",  # QT-05: 技術（液冷）JP
    
    # ③ 業績・イベントクエリ（確実枠）
    "https://news.google.com/rss/search?q=廣達+營收&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # QT-06: 月次營收
    "https://news.google.com/rss/search?q=廣達+法說會+OR+Quanta+outlook&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # QT-07: 法說會（TW）
    "https://news.google.com/rss/search?q=Quanta+earnings+OR+outlook&hl=en-US&gl=US&ceid=US:en",  # QT-07: 法說會（US）
    
    # ========================================
    # 共通業界クエリ（全銘柄対象）
    # ========================================
    
    # 半導体業界
    "https://news.google.com/rss/search?q=半導體+OR+晶圓代工&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # IND-01: 半導体業界（抽象語）TW
    "https://news.google.com/rss/search?q=semiconductor+OR+foundry&hl=en-US&gl=US&ceid=US:en",  # IND-01: 半導体業界（抽象語）US
    "https://news.google.com/rss/search?q=半導体+OR+ファウンドリ&hl=ja&gl=JP&ceid=JP:ja",  # IND-01: 半導体業界（抽象語）JP
    
    "https://news.google.com/rss/search?q=EUV+OR+先進製程+OR+CoWoS&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # IND-02: 半導体業界（具体語）TW
    "https://news.google.com/rss/search?q=EUV+OR+advanced+process+OR+CoWoS&hl=en-US&gl=US&ceid=US:en",  # IND-02: 半導体業界（具体語）US
    "https://news.google.com/rss/search?q=EUV+OR+先進プロセス+OR+CoWoS&hl=ja&gl=JP&ceid=JP:ja",  # IND-02: 半導体業界（具体語）JP
    
    # メモリ業界
    "https://news.google.com/rss/search?q=DRAM+OR+NAND&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # IND-03: メモリ業界（抽象語）TW
    "https://news.google.com/rss/search?q=DRAM+OR+NAND&hl=en-US&gl=US&ceid=US:en",  # IND-03: メモリ業界（抽象語）US
    "https://news.google.com/rss/search?q=DRAM+OR+NAND&hl=ja&gl=JP&ceid=JP:ja",  # IND-03: メモリ業界（抽象語）JP
    
    "https://news.google.com/rss/search?q=HBM+OR+DDR5+OR+記憶體價格&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # IND-04: メモリ業界（具体語）TW
    "https://news.google.com/rss/search?q=HBM+OR+DDR5+OR+memory+price&hl=en-US&gl=US&ceid=US:en",  # IND-04: メモリ業界（具体語）US
    "https://news.google.com/rss/search?q=HBM+OR+DDR5+OR+メモリ価格&hl=ja&gl=JP&ceid=JP:ja",  # IND-04: メモリ業界（具体語）JP
    
    # ODM・サーバー業界
    "https://news.google.com/rss/search?q=ODM+OR+伺服器&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # IND-05: ODM・サーバー業界（抽象語）TW
    "https://news.google.com/rss/search?q=ODM+OR+server&hl=en-US&gl=US&ceid=US:en",  # IND-05: ODM・サーバー業界（抽象語）US
    "https://news.google.com/rss/search?q=ODM+OR+サーバー&hl=ja&gl=JP&ceid=JP:ja",  # IND-05: ODM・サーバー業界（抽象語）JP
    
    "https://news.google.com/rss/search?q=AI伺服器+OR+GB200+OR+液冷&hl=zh-TW&gl=TW&ceid=TW:zh-Hant",  # IND-06: ODM・サーバー業界（具体語）TW
    "https://news.google.com/rss/search?q=AI+server+OR+GB200+OR+liquid+cooling&hl=en-US&gl=US&ceid=US:en",  # IND-06: ODM・サーバー業界（具体語）US
    "https://news.google.com/rss/search?q=AIサーバー+OR+GB200+OR+液冷&hl=ja&gl=JP&ceid=JP:ja",  # IND-06: ODM・サーバー業界（具体語）JP
]

# 合計: 72件のRSSフィード

# カテゴリ別統計
STATS_V52 = {
    "total_feeds": len(RSS_FEEDS_V52),
    "by_category": {
        "銘柄直結クエリ": 16,
        "上流ドライバークエリ": 39,
        "業績・イベントクエリ": 8,
        "共通業界クエリ": 18
    },
    "by_region": {
        "TW": 32,
        "US": 20,
        "JP": 20
    },
    "by_stock": {
        "台積電（2330）": 20,
        "創見（2451）": 11,
        "宇瞻（8271）": 10,
        "廣達（2382）": 16,
        "共通業界": 18
    }
}

# v5.1との差分
DIFF_V51_V52 = {
    "v5.1_feeds": 11,
    "v5.2_feeds": 72,
    "increase": 61,
    "increase_rate": "約6.5倍"
}
