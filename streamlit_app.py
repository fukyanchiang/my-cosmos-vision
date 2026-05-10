import streamlit as st
import pandas as pd
import time

# 從心臟檔案 (core_logic.py) 引入所有武器
from core_logic import (
    HK_STOCK_MAP, US_STOCK_MAP, HK_ETF_MAP, US_ETF_MAP,
    smart_fetch, analyze_dragon_stock
)

# ================= 1. 介面設定與全黑 CSS =================
st.set_page_config(page_title="爺孫必勝雷達", layout="centered", initial_sidebar_state="collapsed")

# 注入 CSS：黑底、白字、大字體、細字板塊
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: #FFFFFF; }
    h1, h2, h3 { color: #FFD700; font-family: 'Arial Black', sans-serif; text-align: center; }
    .big-button { width: 100%; height: 80px; font-size: 24px; font-weight: bold; border-radius: 10px; margin-bottom: 10px; }
    .result-box { background-color: #1E1E1E; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #FFD700; }
    .ticker-name { font-size: 24px; font-weight: bold; color: #00FFFF; }
    .stage-label { font-size: 18px; font-weight: bold; color: #FF4500; margin-left: 10px; }
    .sector-text { font-size: 12px; color: #AAAAAA; display: block; margin-top: 5px; }
    .score-text { font-size: 18px; color: #32CD32; font-weight: bold; margin-top: 5px;}
    .icons-text { font-size: 22px; letter-spacing: 5px; }
    .stoploss-text { font-size: 14px; color: #FF6347; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("🦅 爺孫必勝雷達 V2.0")
st.markdown("### 嚴守紀律 • 寧缺勿濫 • 一擊必殺")
st.markdown("---")

# ================= 2. 準備股票名單與板塊對照 =================
ALL_TICKERS = []
SECTOR_INFO = {}

for sector, tickers_list in {**HK_STOCK_MAP, **US_STOCK_MAP, **HK_ETF_MAP, **US_ETF_MAP}.items():
    # 爺爺修正咗呢度！tickers_list 已經切好，唔使再 split() 喇！
    for t in tickers_list:
        ALL_TICKERS.append(t)
        SECTOR_INFO[t] = sector.split(". ")[-1] # 只拎中文板塊名

ALL_TICKERS = list(set(ALL_TICKERS)) # 去除重複

# ================= 3. 三大戰術按鈕 =================
col1, col2, col3 = st.columns(3)

run_dragon = False
with col1:
    if st.button("🐲 千龍起步\n(尋找最強爆發)", use_container_width=True):
        run_dragon = True
with col2:
    if st.button("📈 VCP 形態\n(暫未開放)", use_container_width=True):
        st.info("爺孫正在建構 VCP 邏輯...")
with col3:
    if st.button("🌊 海龜回測\n(暫未開放)", use_container_width=True):
        st.info("爺孫正在建構 海龜 邏輯...")

# ================= 4. 千龍掃描執行區 =================
if run_dragon:
    st.markdown("### 🔍 啟動「🐲 龍魂」大數據掃描...")
    st.markdown("> **戰術守則**：11項死刑安檢 ➡️ RS/EJ/SE 硬指標 ➡️ 總分排位。")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    passed_stocks = []
    total_stocks = len(ALL_TICKERS)
    
    # 輸送帶開始：逐隻股票檢查
    for i, ticker in enumerate(ALL_TICKERS):
        status_text.text(f"掃描中: {ticker} ({i+1}/{total_stocks})...")
        progress_bar.progress((i + 1) / total_stocks)
        
        # 1. 下載數據
        df = smart_fetch(ticker)
        
        # 2. 丟入心臟計分
        passed, score, stage, icons, details = analyze_dragon_stock(ticker, df)
        
        # 3. 過關就加入名單
        if passed:
            passed_stocks.append({
                "Ticker": ticker,
                "Sector": SECTOR_INFO.get(ticker, "未知板塊"),
                "Score": score,
                "Stage": stage,
                "Icons": icons,
                "StopLoss": details.get("StopLoss", 0)
            })

    status_text.text("✅ 掃描完成！為您計算最終排位...")
    time.sleep(1)
    status_text.empty()
    progress_bar.empty()

    # ================= 5. 排位與顯示 =================
    if len(passed_stocks) == 0:
        st.warning("⚠️ 今日無股票能通過「11項死刑」與「龍魂門檻」。留住子彈，明日再戰！")
    else:
        # 排位邏輯：第一比 總分 (高至低)，第二比 公仔數量 (多至少)
        passed_stocks.sort(key=lambda x: (x['Score'], len(x['Icons'].split())), reverse=True)
        
        st.success(f"🎉 成功捕捉 {len(passed_stocks)} 隻真龍！請跟據階段標籤制定止損策略：")
        
        for stock in passed_stocks:
            st.markdown(f"""
            <div class="result-box">
                <span class="ticker-name">{stock['Ticker']}</span>
                <span class="stage-label">{stock['Stage']}</span>
                <span class="icons-text"> {stock['Icons']}</span>
                <span class="sector-text">📂 板塊: {stock['Sector']}</span>
                <div class="score-text">🏆 龍魂總分: {stock['Score']}</div>
                <div class="stoploss-text">🛡️ 系統防線 (10 EMA): {stock['StopLoss']}</div>
            </div>
            """, unsafe_allow_html=True)
