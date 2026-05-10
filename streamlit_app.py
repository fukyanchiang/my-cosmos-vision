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

# ================= 1. 介面設定 (全黑白字 + 白框黑字掣) =================
st.set_page_config(page_title="🦅 爺孫必勝雷達 V2.0", layout="wide")

st.markdown("""
    <style>
    /* 全黑背景，純白文字 */
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3, h4, p, span, label, div { color: #FFFFFF !important; }
    
    /* 雷達掣：白底黑字，白框 */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 10px;
        font-size: 26px !important;
        font-weight: bold !important;
        height: 80px !important;
        width: 100% !important;
    }
    
    /* 結果卡片：白框黑底 */
    .result-card {
        border: 2px solid #FFFFFF;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 30px;
        background-color: #000000;
    }
    
    /* 細白色數據字 */
    .stats-text { font-size: 14px; color: #FFFFFF; opacity: 0.9; margin-top: 10px; }
    .sector-label { border: 1px solid #FFFFFF; padding: 3px 8px; font-size: 14px; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("🦅 爺孫必勝雷達 V2.0")

# ================= 2. 橫向四個掣 (四大天王控制台) =================
c1, c2, c3, c4 = st.columns(4)
with c1: asset_type = st.radio("1. 資產類別", ["🏢 領頭個股", "🧺 優質 ETF"], horizontal=True)
with c2: market = st.radio("2. 掃描市場", ["🇺🇸 美股", "🇭🇰 港股"], horizontal=True)
with c3: scan_range = st.selectbox("3. 選擇範圍", ["🌐 啟動全星系大規模搜索", "🎯 只看監控清單"])
with c4: tactic_title = "🐲 龍魂起步 (RS>60, EJ>85, SE>75, 11項死刑)"
st.markdown(f"#### 當前戰術：{tactic_title}")

# ================= 3. 專業重裝圖表 (修正 ValueError) =================
def plot_heavy_chart(ticker, df):
    if len(df) < 60: return None
    
    # 四層子圖：價格/重貨、成交量、三項成交指標、RS線
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.5, 0.15, 0.2, 0.15])

    # A. 價格區 + 10EMA + 重貨區
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'].ewm(span=10).mean(), line=dict(color='yellow', width=2), name='10 EMA'), row=1, col=1)
    
    # 模擬重貨區 (Volume Profile)
    recent = df.tail(100)
    bins = np.linspace(recent['Low'].min(), recent['High'].max(), 20)
    v_profile = recent.groupby(pd.cut(recent['Close'], bins))['Volume'].sum()
    max_v = v_profile.max() if not v_profile.empty else 1
    for i in range(len(bins)-1):
        price_lvl = (bins[i] + bins[i+1])/2
        v_val = v_profile.iloc[i]
        if v_val > 0:
            bar_len = int((v_val / max_v) * 20)
            fig.add_trace(go.Scatter(x=[df.index[-1], df.index[-1] + pd.Timedelta(days=bar_len)], 
                                     y=[price_lvl, price_lvl], mode='lines', 
                                     line=dict(color='rgba(255,255,255,0.3)', width=5), showlegend=False), row=1, col=1)

    # B. 成交量
    colors = ['#00FF00' if c >= o else '#FF0000' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)

    # C. 三項成交量技術指標 (5, 20, 60 SMA)
    fig.add_trace(go.Scatter(x=df.index, y=df['Volume'].rolling(5).mean(), line=dict(color='#00FFFF', width=1), name='短'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Volume'].rolling(20).mean(), line=dict(color='#FF00FF', width=1.5), name='中'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Volume'].rolling(60).mean(), line=dict(color='#FFA500', width=2), name='長'), row=3, col=1)

    # D. RS 線
    rs_data = (df['Close'] / df['Close'].iloc[0]) * 100
    fig.add_trace(go.Scatter(x=df.index, y=rs_data, line=dict(color='white', width=2), name='RS線'), row=4, col=1)

    # 修正：使用 paper_bgcolor 代替 background_color
    fig.update_layout(height=1000, template='plotly_dark', xaxis_rangeslider_visible=False, 
                      showlegend=False, paper_bgcolor='black', plot_bgcolor='black')
    return fig

# ================= 4. 執行邏輯 =================
if st.button("📡 啟動雷達掃描 (一擊必殺)"):
    # 決定清單與板塊
    if asset_type == "🏢 領頭個股": target_map = US_STOCK_MAP if market == "🇺🇸 美股" else HK_STOCK_MAP
    else: target_map = US_ETF_MAP if market == "🇺🇸 美股" else HK_ETF_MAP
    
    all_tickers = []
    sector_map = {}
    for sector, t_list in target_map.items():
        for t in t_list:
            all_tickers.append(t); sector_map[t] = sector.split(". ")[-1]

    passed_stocks = []
    sl_stocks = []
    
    prog = st.progress(0)
    status = st.empty()
    
    for i, t in enumerate(all_tickers):
        prog.progress((i+1)/len(all_tickers))
        status.text(f"掃描中: {t}...")
        df = smart_fetch(t)
        if df.empty or len(df) < 60: continue
        
        # 1. 止損監控 (現價 < 10EMA)
        ema10_now = df['Close'].ewm(span=10).mean().iloc[-1]
        if df['Close'].iloc[-1] < ema10_now:
            sl_stocks.append(t)
            
        # 2. 龍魂掃描
        passed, score, stage, icons, details = analyze_dragon_stock(t, df)
        if passed:
            passed_stocks.append({"t": t, "score": score, "stage": stage, "icons": icons, "df": df, "details": details, "sector": sector_map.get(t)})

    status.empty(); prog.empty()

    # A. 顯示止損名單 (最頂)
    if sl_stocks:
        st.markdown(f"### 🚨 近 20 日【破防止損】名單 (跌穿 10 EMA)")
        st.error(", ".join(sl_stocks[:20]))
        st.markdown("---")

    # B. 顯示掃描結果
    if passed_stocks:
        passed_stocks.sort(key=lambda x: x['score'], reverse=True)
        st.success(f"🎉 捕捉到 {len(passed_stocks)} 隻龍魂標的！")
        for s in passed_stocks:
            st.markdown(f"""
            <div class="result-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:38px; font-weight:bold; color:#00FFFF;">{s['t']} {s['stage']}</span>
                    <span class="sector-label">{s['sector']}</span>
                </div>
                <div style="font-size:35px; margin:15px 0;">{s['icons']}</div>
                <div class="stats-text">
                    RS: {round(s['score']*0.4,1)} | EJ: {round(s['score']*0.3,1)} | SE: {s['details']['SE']} | 
                    Bias: {s['details']['Bias']}% | 買入參考: {s['details']['Close']} | 止損防線(10EMA): {s['details']['StopLoss']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            # 畫專業圖表
            chart = plot_heavy_chart(s['t'], s['df'])
            if chart: st.plotly_chart(chart, use_container_width=True)
    else:
        st.warning("目前市場無符合條件標的，守住現金。")
