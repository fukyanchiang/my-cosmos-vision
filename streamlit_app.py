import streamlit as st
import pandas as pd
import time

# 從心臟檔案 (core_logic.py) 引入武器
from core_logic import (
    HK_STOCK_MAP, US_STOCK_MAP, HK_ETF_MAP, US_ETF_MAP,
    smart_fetch, analyze_dragon_stock
)

# ================= 1. 介面設定與全黑 CSS =================
st.set_page_config(page_title="爺孫必勝雷達 V2", layout="wide") # 轉 Wide 方便睇圖

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stSelectbox label, .stRadio label { color: #FFD700 !important; font-weight: bold !important; }
    .result-box { background-color: #1E1E1E; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #FFD700; }
    .ticker-header { display: flex; justify-content: space-between; align-items: center; }
    .ticker-name { font-size: 28px; font-weight: bold; color: #00FFFF; }
    .stoploss-tag { background-color: #FF4B4B; color: white; padding: 2px 8px; border-radius: 5px; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

st.title("🦅 爺孫必勝雷達 V2.0")

# ================= 2. 戰略指揮塔 (Sidebar) =================
with st.sidebar:
    st.header("🎮 戰略指揮塔")
    
    asset_type = st.radio("1. 資產類別", ["🏢 領頭個股", "🧺 優質 ETF"])
    market = st.radio("2. 掃描市場", ["🇺🇸 美股", "🇭🇰 港股"])
    
    st.markdown("---")
    st.header("📜 歷史監控")
    show_sl_list = st.checkbox("顯示近 20 日止損名單")

# 根據選擇決定名單
if asset_type == "🏢 領頭個股":
    target_map = US_STOCK_MAP if market == "🇺🇸 美股" else HK_STOCK_MAP
else:
    target_map = US_ETF_MAP if market == "🇺🇸 美股" else HK_ETF_MAP

# 準備清單
ALL_TICKERS = []
SECTOR_INFO = {}
for sector, t_list in target_map.items():
    for t in t_list:
        ALL_TICKERS.append(t)
        SECTOR_INFO[t] = sector.split(". ")[-1]

# ================= 3. 執行按鈕 =================
st.markdown(f"### 目前目標：{market} - {asset_type}")
if st.button(f"🚀 開始掃描 {len(ALL_TICKERS)} 隻標的", use_container_width=True):
    
    progress_bar = st.progress(0)
    passed_stocks = []
    
    for i, ticker in enumerate(ALL_TICKERS):
        progress_bar.progress((i + 1) / len(ALL_TICKERS))
        df = smart_fetch(ticker)
        passed, score, stage, icons, details = analyze_dragon_stock(ticker, df)
        
        if passed:
            # 爺爺喺呢度幫你預留埋「圖表連結」
            passed_stocks.append({
                "Ticker": ticker, "Score": score, "Stage": stage, 
                "Icons": icons, "Sector": SECTOR_INFO.get(ticker),
                "Details": details, "DF": df
            })

    # ================= 4. 結果顯示 =================
    if not passed_stocks:
        st.warning("戰友，目前市場未達標，請耐心等待。")
    else:
        passed_stocks.sort(key=lambda x: x['Score'], reverse=True)
        
        for s in passed_stocks:
            with st.container():
                st.markdown(f"""
                <div class="result-box">
                    <div class="ticker-header">
                        <span class="ticker-name">{s['Ticker']} {s['Stage']}</span>
                        <span class="icons-text">{s['Icons']}</span>
                    </div>
                    <p style="color: #AAAAAA;">板塊: {s['Sector']} | 龍魂總分: {round(s['Score'],2)}</p>
                    <p style="color: #32CD32; font-weight: bold;">🛡️ 10EMA 防線: {s['Details']['StopLoss']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 這裡就是你要的圖表資料 (先用 Streamlit 自帶圖表，下一步再教你畫專業 RS 圖)
                st.line_chart(s['DF']['Close'].tail(60))
