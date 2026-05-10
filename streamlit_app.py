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

# ================= 1. 終極黑白高對比 CSS =================
st.set_page_config(page_title="🦅 龍魂掃股 V2.0", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    div.stButton > button {
        background-color: #FFFFFF !important; color: #000000 !important;
        border: 3px solid #FFFFFF !important; border-radius: 12px;
        font-size: 26px !important; font-weight: 900 !important;
        height: 100px !important; width: 100% !important;
    }
    div[data-baseweb="select"] { background-color: #FFFFFF !important; border-radius: 8px; }
    div[data-baseweb="select"] span { color: #000000 !important; font-weight: bold !important; }
    .stProgress > div > div > div > div { background-color: #00FFCC !important; }
    .result-card { border: 2px solid #FFFFFF; padding: 25px; border-radius: 15px; margin-bottom: 25px; }
    .stats-text { font-size: 13px; color: #FFFFFF !important; opacity: 0.9; }
    </style>
""", unsafe_allow_html=True)

if 'tactic' not in st.session_state: st.session_state.tactic = None

# ================= 2. 第一步：三大掣首頁 =================
if st.session_state.tactic is None:
    st.markdown("<h1 style='text-align:center;'>🦅 爺孫必勝戰術指揮部</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🐲 龍魂起步\n(尋找最強爆發)"): st.session_state.tactic = "Dragon Soul"; st.rerun()
    with c2:
        if st.button("📈 VCP 形態\n(Mark Minervini)"): st.session_state.tactic = "VCP Pattern"; st.rerun()
    with c3:
        if st.button("🌊 海龜回測\n(N字型加注)"): st.session_state.tactic = "Turtle Strategy"; st.rerun()
    st.stop()

# ================= 3. 第二步：操作台與 100% 羅輯 =================
st.markdown(f"## 🛠️ 戰術模式：{st.session_state.tactic}")
st.info("🐲 羅輯：11項死刑 Foul 制 ➡️ 7大指標海選 (RS>60, EJ>85, SE>75, OBV 1/7, NetFlow>0, 兵力勝, 集中度<70%) ➡️ 權重評分排序")
if st.button("⬅️ 返回首頁"): st.session_state.tactic = None; st.rerun()

st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 1.5])
with c1: asset = st.radio("1. 資產類別", ["🏢 個股", "🧺 ETF"], horizontal=True)
with c2: mkt = st.radio("2. 市場", ["🇺🇸 美股", "🇭🇰 港股"], horizontal=True)
with c3: scan_range = st.selectbox("3. 選擇範圍", ["🌐 啟動全星系大規模搜索", "🎯 監控清單"])

# ================= 4. V188.0 重裝圖表 =================
def plot_heavy_chart(ticker, df):
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.5, 0.1, 0.25, 0.15])
    dates = df.index.strftime('%Y-%m-%d')
    # A. 價格 + 10 EMA + 重貨區
    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=df['Close'].ewm(span=10).mean(), line=dict(color='orange', width=2), name='10 EMA'), row=1, col=1)
    counts, bins = np.histogram(df['Close'].tail(100), bins=20, weights=df['Volume'].tail(100))
    for i in range(len(counts)):
        if counts[i]>0:
            fig.add_trace(go.Scatter(x=[dates[-1], dates[-max(1, int(counts[i]/max(counts)*25))]], y=[(bins[i]+bins[i+1])/2]*2, mode='lines', line=dict(color='rgba(255,255,255,0.2)', width=4), showlegend=False), row=1, col=1)
    # B. 成交量 + 星星
    v_colors = ['#00FF00' if c >= o else '#FF0000' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors), row=2, col=1)
    # C. 3個重量級指標
    fig.add_trace(go.Scatter(x=dates, y=df['Volume'].rolling(5).mean(), line=dict(color='#00FFFF')), row=3, col=1)
    fig.add_trace(go.Scatter(x=dates, y=df['Volume'].rolling(20).mean(), line=dict(color='#FF00FF')), row=3, col=1)
    fig.add_trace(go.Scatter(x=dates, y=df['Volume'].rolling(60).mean(), line=dict(color='#FFA500')), row=3, col=1)
    # D. RS 線
    fig.add_trace(go.Scatter(x=dates, y=(df['Close']/df['Close'].iloc[0]*100), line=dict(color='white', width=2)), row=4, col=1)
    fig.update_layout(height=950, template='plotly_dark', paper_bgcolor='black', plot_bgcolor='black', xaxis_rangeslider_visible=False, showlegend=False)
    return fig

# ================= 5. 開火掃描 =================
if st.button("📡 啟動雷達掃描 (一擊必殺)"):
    if asset == "🏢 個股": target_map = US_STOCK_MAP if mkt == "🇺🇸 美股" else HK_STOCK_MAP
    else: target_map = US_ETF_MAP if mkt == "🇺🇸 美股" else HK_ETF_MAP
    all_t = []; sector_info = {}
    for s, l in target_map.items():
        for t in l: all_t.append(t); sector_info[t] = s.split(". ")[-1]
    
    st.markdown("### 🔍 掃描條 (正在搜尋真龍...)")
    pb = st.progress(0); status = st.empty(); passed = []; sl_list = []
    for i, t in enumerate(all_t):
        pb.progress((i+1)/len(all_t)); status.text(f"分析標的: {t}")
        df = smart_fetch(t)
        if df.empty or len(df) < 30: continue
        if df['Close'].iloc[-1] < df['Close'].ewm(span=10).mean().iloc[-1]: sl_list.append(t)
        ok, score, stage, icons, d = analyze_dragon_soul(t, df, "US" if mkt=="🇺🇸 美股" else "HK")
        if ok: passed.append({"t":t, "score":score, "stage":stage, "icons":icons, "df":df, "details":d, "sector":sector_info.get(t,"未知")})
    status.empty(); pb.empty()

    if sl_list: st.error(f"🚨 止損預警 (跌穿 10EMA)：{', '.join(sl_list[:25])}")
    if passed:
        passed.sort(key=lambda x: x['score'], reverse=True)
        for s in passed:
            st.markdown(f"""<div class="result-card"><span style="float:right; border:1px solid #FFF; padding:2px 8px;">📂 {s['sector']}</span><div style="font-size:32px; font-weight:bold; color:#00FFFF;">{s['t']} {s['stage']}</div><div style="font-size:30px; margin:10px 0;">{s['icons']}</div><div class="stats-text">RS:{s['details']['RS']} | EJ:{s['details']['EJ']} | SE:{s['details']['SE']} | Bias:{s['details']['Bias']}% | 🛡️ 止損:{s['details']['StopLoss']}</div></div>""", unsafe_allow_html=True)
            st.plotly_chart(plot_heavy_chart(s['t'], s['df']), use_container_width=True)
