import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

from core_logic import (
    HK_STOCK_MAP, US_STOCK_MAP, HK_ETF_MAP, US_ETF_MAP,
    smart_fetch, analyze_dragon_soul
)

# 1. 介面最簡化：黑底白字，絕無白底白字
st.set_page_config(page_title="🦅 龍魂系統 V2.0", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3, p, span, label { color: #FFFFFF !important; }
    /* 修正按鈕：白底黑字，確保看得到 */
    div.stButton > button { background-color: #FFFFFF !important; color: #000000 !important; font-weight: bold; border-radius: 5px; height: 60px; width: 100%; }
    /* 修正下拉選單字體顏色 */
    div[data-baseweb="select"] * { color: #000000 !important; }
    /* 進度條高光 */
    .stProgress > div > div > div > div { background-color: #00FFCC !important; }
    .result-card { border: 2px solid #FFFFFF; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

if 'tactic' not in st.session_state: st.session_state.tactic = None

# 2. 三大掣首頁
if st.session_state.tactic is None:
    st.title("🦅 龍魂必勝戰術指揮部")
    c1, c2, c3 = st.columns(3)
    with c1: 
        if st.button("🐲 龍魂起步 (RS/EJ/SE)"): st.session_state.tactic = "Dragon"; st.rerun()
    with c2: 
        if st.button("📈 VCP 形態 (Mark)"): st.session_state.tactic = "VCP"; st.rerun()
    with c3: 
        if st.button("🌊 海龜回測 (N字)"): st.session_state.tactic = "Turtle"; st.rerun()
    st.stop()

# 3. 操作台
st.title(f"戰術：{st.session_state.tactic}")
st.info("🐲 羅輯：11項死刑 Foul 制 ➡️ 7大指標海選 ➡️ 權重評分排序")
if st.button("⬅️ 返回重選"): st.session_state.tactic = None; st.rerun()

c1, c2, c3 = st.columns([1, 1, 2])
with c1: asset = st.radio("資產", ["🏢 個股", "🧺 ETF"], horizontal=True)
with c2: mkt = st.radio("市場", ["🇺🇸 美股", "🇭🇰 港股"], horizontal=True)
with c3: scan_range = st.selectbox("選擇範圍", ["🌐 全星系搜索", "🎯 監控清單"])

# 4. 專業圖表 (修正 ValueError)
def plot_heavy_chart(ticker, df):
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, row_heights=[0.5, 0.1, 0.2, 0.2], vertical_spacing=0.03)
    dates = df.index.strftime('%Y-%m-%d')
    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=df['Close'].ewm(span=10).mean(), line=dict(color='orange'), name="10EMA"), row=1, col=1)
    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color='gray', name="成交量"), row=2, col=1)
    # RS線
    fig.add_trace(go.Scatter(x=dates, y=(df['Close']/df['Close'].iloc[0]*100), line=dict(color='white'), name="RS"), row=4, col=1)
    # 修正：用 paper_bgcolor 而不是 background_color
    fig.update_layout(height=800, template='plotly_dark', paper_bgcolor='black', plot_bgcolor='black', xaxis_rangeslider_visible=False)
    return fig

# 5. 雷達掃描 (強制 Bar 出現)
if st.button("📡 啟動雷達掃描 (一擊必殺)"):
    # 獲取名單
    target_map = (US_STOCK_MAP if mkt == "🇺🇸 美股" else HK_STOCK_MAP) if asset == "🏢 個股" else (US_ETF_MAP if mkt == "🇺🇸 美股" else HK_ETF_MAP)
    all_t = []
    for l in target_map.values(): all_t.extend(l)
    
    # --- 關鍵： Bar 置頂 ---
    st.write("---")
    progress_bar = st.progress(0)
    status_msg = st.empty()
    
    passed_stocks = []
    sl_stocks = []

    for i, t in enumerate(all_t):
        # 更新進度，絕對唔會無反應
        progress_bar.progress((i + 1) / len(all_t))
        status_msg.markdown(f"🔍 **正在分析：{t}** ({i+1}/{len(all_t)})")
        
        df = smart_fetch(t)
        if df.empty or len(df) < 30: continue
        
        # 止損名單
        if df['Close'].iloc[-1] < df['Close'].ewm(span=10).mean().iloc[-1]: sl_stocks.append(t)
        
        # 龍魂分析
        ok, score, stage, icons, det = analyze_dragon_soul(t, df, "US" if mkt=="🇺🇸 美股" else "HK")
        if ok: passed_stocks.append({"t":t, "score":score, "stage":stage, "icons":icons, "df":df, "details":det})
    
    status_msg.success("✅ 掃描完成！")
    
    # 6. 顯示結果
    if sl_stocks:
        st.error(f"🚨 止損預警 (破10EMA)：{', '.join(sl_stocks[:20])}")
    
    if passed_stocks:
        passed_stocks.sort(key=lambda x: x['score'], reverse=True)
        for s in passed_stocks:
            st.markdown(f"""
            <div class="result-card">
                <h3>{s['t']} {s['stage']} {s['icons']}</h3>
                <p style="font-size:12px; color:white;">RS: {s['details']['RS']} | EJ: {s['details']['EJ']} | SE: {s['details']['SE']} | Bias: {s['details']['Bias']}%</p>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(plot_heavy_chart(s['t'], s['df']), use_container_width=True)
