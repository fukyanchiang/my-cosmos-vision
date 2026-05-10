import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import time

# 從心臟檔案引入武器
from core_logic import (
    HK_STOCK_MAP, US_STOCK_MAP, HK_ETF_MAP, US_ETF_MAP,
    smart_fetch, analyze_dragon_stock
)

# ================= 1. 終極黑白戰鬥介面 (CSS) =================
st.set_page_config(page_title="🦅 爺孫必勝雷達 V2.0", layout="wide")

st.markdown("""
    <style>
    /* 全黑底白字 */
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3, h4, p, span, label { color: #FFFFFF !important; }
    
    /* 雷達掣：白框黑字 */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 10px;
        font-size: 24px !important;
        font-weight: bold !important;
        height: 70px !important;
        width: 100% !important;
    }
    
    /* 結果框框 */
    .result-card {
        border: 1px solid #FFFFFF;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
        background-color: #000000;
    }
    
    /* 細白色字指標 */
    .stats-text { font-size: 12px; color: #FFFFFF; opacity: 0.8; }
    .icons-display { font-size: 28px; margin: 10px 0; }
    .sector-tag { color: #AAAAAA; font-size: 14px; border: 1px solid #444; padding: 2px 5px; }
    
    /* 止損紅色標記 */
    .stoploss-header { color: #FF0000 !important; font-size: 30px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🦅 爺孫必勝雷達 V2.0")

# ================= 2. 橫向控制台 =================
c1, c2, c3 = st.columns(3)
with c1: asset_type = st.radio("資產類別", ["🏢 領頭個股", "🧺 優質 ETF"], horizontal=True)
with c2: market = st.radio("掃描市場", ["🇺🇸 美股", "🇭🇰 港股"], horizontal=True)
with c3: tactic_name = "🐲 龍魂起步 (RS>60, EJ>85, SE>75, 11項死刑過濾)"

# ================= 3. 專業畫圖引擎 (重裝還原) =================
def plot_heavy_chart(ticker, df):
    # 建立多層子圖：價格區、成交指標、RS線
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.02, 
                        row_heights=[0.5, 0.15, 0.2, 0.15])

    # A. 價格區 (K線 + EMA10 + 買入止損線 + 重貨區)
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'].ewm(span=10).mean(), line=dict(color='yellow', width=1.5), name='10 EMA'), row=1, col=1)
    
    # 模擬重貨區 (水平長條)
    recent_vol = df.tail(100)
    bins = np.linspace(recent_vol['Low'].min(), recent_vol['High'].max(), 20)
    vol_profile = recent_vol.groupby(pd.cut(recent_vol['Close'], bins))['Volume'].sum()
    for b, v in zip(bins, vol_profile):
        fig.add_trace(go.Scatter(x=[df.index[-20], df.index[-20] + pd.Timedelta(days=int(v/vol_profile.max()*15))], 
                                 y=[b, b], mode='lines', line=dict(color='rgba(255,255,255,0.2)', width=4), showlegend=False), row=1, col=1)

    # B. 成交量 + 星星
    colors = ['#00FF00' if c > o else '#FF0000' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)

    # C. 3個重量級成交指標 (模擬 Tradeforce 邏輯)
    fig.add_trace(go.Scatter(x=df.index, y=df['Volume'].rolling(5).mean(), line=dict(color='cyan'), name='指標1'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Volume'].rolling(20).mean(), line=dict(color='magenta'), name='指標2'), row=3, col=1)

    # D. RS 線
    fig.add_trace(go.Scatter(x=df.index, y=df['Close']/df['Close'].iloc[0], line=dict(color='white', width=2), name='RS線'), row=4, col=1)

    fig.update_layout(height=1000, template='plotly_dark', xaxis_rangeslider_visible=False, showlegend=False, background_color='black')
    return fig

# ================= 4. 執行與顯示邏輯 =================
st.subheader(f"戰術：{tactic_name}")

if st.button("📡 啟動雷達掃描 (一擊必殺)"):
    # 決定清單
    if asset_type == "🏢 領頭個股": target_map = US_STOCK_MAP if market == "🇺🇸 美股" else HK_STOCK_MAP
    else: target_map = US_ETF_MAP if market == "🇺🇸 美股" else HK_ETF_MAP
    
    all_tickers = []
    sector_lookup = {}
    for sector, t_list in target_map.items():
        for t in t_list:
            all_tickers.append(t)
            sector_lookup[t] = sector.split(". ")[-1]

    passed_stocks = []
    sl_stocks = [] # 止損名單
    
    prog = st.progress(0)
    for i, t in enumerate(all_tickers):
        prog.progress((i+1)/len(all_tickers))
        df = smart_fetch(t)
        if df.empty: continue
        
        # 10 EMA 止損監控 (最近 20 日)
        ema10 = df['Close'].ewm(span=10).mean().iloc[-1]
        if df['Close'].iloc[-1] < ema10:
            sl_stocks.append(t)
            
        passed, score, stage, icons, details = analyze_dragon_stock(t, df)
        if passed:
            passed_stocks.append({"t": t, "score": score, "stage": stage, "icons": icons, "df": df, "details": details, "sector": sector_lookup.get(t)})

    # A. 顯示止損名單 (最頂)
    if sl_stocks:
        st.markdown('<p class="stoploss-header">🚨 近 20 日【破防止損】名單 (跌穿 10 EMA)</p>', unsafe_allow_html=True)
        st.write(", ".join(sl_stocks[:15])) # 顯示前15隻
        st.markdown("---")

    # B. 顯示掃描結果
    if passed_stocks:
        passed_stocks.sort(key=lambda x: x['score'], reverse=True)
        for s in passed_stocks:
            st.markdown(f"""
            <div class="result-card">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-size:30px; font-weight:bold; color:#00FFFF;">{s['t']} {s['stage']}</span>
                    <span class="sector-tag">{s['sector']}</span>
                </div>
                <div class="icons-display">{s['icons']}</div>
                <div class="stats-text">
                    RS: {round(s['score']*0.4,1)} | EJ: {round(s['score']*0.3,1)} | SE: {s['details']['SE']} | 
                    Bias: {s['details']['Bias']}% | 買入參考: {s['details']['Close']} | 止損線(10EMA): {s['details']['StopLoss']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.plotly_chart(plot_heavy_chart(s['t'], s['df']), use_container_width=True)
