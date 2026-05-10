import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import time

# 從心臟檔案 (core_logic.py) 引入武器
from core_logic import (
    HK_STOCK_MAP, US_STOCK_MAP, HK_ETF_MAP, US_ETF_MAP,
    smart_fetch, analyze_dragon_stock
)

# ================= 1. 介面設定 (全黑背景 + 純白文字 + 白框黑字雷達) =================
st.set_page_config(page_title="🦅 爺孫必勝雷達 V2.0", layout="wide")

st.markdown("""
    <style>
    /* 全黑背景，文字純白 */
    .stApp { background-color: #000000; color: #FFFFFF; }
    h1, h2, h3, h4, p, span, label, div { color: #FFFFFF !important; }
    
    /* 雷達掣：白底黑字，要有白框 */
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
        margin-bottom: 35px;
        background-color: #000000;
    }
    
    /* 細白色指標字 */
    .stats-text { font-size: 14px; color: #FFFFFF !important; opacity: 0.9; margin-top: 12px; }
    .sector-tag { border: 1px solid #FFFFFF; padding: 4px 10px; font-size: 14px; border-radius: 5px; float: right; }
    </style>
""", unsafe_allow_html=True)

st.title("🦅 爺孫必勝雷達 V2.0")

# ================= 2. 橫向控制台 (四個大掣) =================
# 第一行：四大控制項
c1, c2, c3, c4 = st.columns(4)
with c1: asset_type = st.radio("1. 資產類別", ["🏢 領頭個股", "🧺 優質 ETF"], horizontal=True)
with c2: market = st.radio("2. 掃描市場", ["🇺🇸 美股", "🇭🇰 港股"], horizontal=True)
with c3: scan_range = st.selectbox("3. 選擇範圍", ["🌐 啟動全星系大規模搜索", "🎯 只看監控清單"])
with c4: tactic_title = "🐲 龍魂起步 (RS>60, EJ>85, SE>75, 11項死刑過濾)"
st.markdown(f"#### 當前戰術：{tactic_title}")

# ================= 3. 專業重裝圖表 (修正 ValueError) =================
def plot_heavy_chart(ticker, df):
    if df.empty or len(df) < 20: return None
    
    # 建立四層子圖
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.5, 0.15, 0.2, 0.15])

    # A. 價格區 + 10EMA + 模擬重貨區
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Close'].ewm(span=10).mean(), line=dict(color='yellow', width=2), name='10 EMA'), row=1, col=1)
    
    # 模擬重貨區 (橫條)
    recent = df.tail(100)
    price_bins = np.linspace(recent['Low'].min(), recent['High'].max(), 15)
    vol_by_price = recent.groupby(pd.cut(recent['Close'], price_bins))['Volume'].sum()
    max_v = vol_by_price.max() if not vol_by_price.empty else 1
    for i in range(len(price_bins)-1):
        p_mid = (price_bins[i] + price_bins[i+1])/2
        v_val = vol_by_price.iloc[i]
        if v_val > 0:
            bar_len = int((v_val / max_v) * 20)
            fig.add_trace(go.Scatter(x=[df.index[-1], df.index[-1] + pd.Timedelta(days=bar_len)], 
                                     y=[p_mid, p_mid], mode='lines', 
                                     line=dict(color='rgba(255,255,255,0.25)', width=6), showlegend=False), row=1, col=1)

    # B. 成交量
    colors = ['#00FF00' if c >= o else '#FF0000' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)

    # C. 三項成交量技術指標 (5, 20, 60 SMA)
    fig.add_trace(go.Scatter(x=df.index, y=df['Volume'].rolling(5).mean(), line=dict(color='#00FFFF', width=1), name='短線'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Volume'].rolling(20).mean(), line=dict(color='#FF00FF', width=1.5), name='中線'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Volume'].rolling(60).mean(), line=dict(color='#FFA500', width=2), name='長線'), row=3, col=1)

    # D. RS 線 (相對自身基準)
    rs_line = (df['Close'] / df['Close'].iloc[0]) * 100
    fig.add_trace(go.Scatter(x=df.index, y=rs_line, line=dict(color='white', width=2), name='RS線'), row=4, col=1)

    # 重要：修正後的背景顏色設定 (去除 background_color 錯誤)
    fig.update_layout(height=900, template='plotly_dark', xaxis_rangeslider_visible=False, 
                      showlegend=False, paper_bgcolor='black', plot_bgcolor='black',
                      margin=dict(l=10, r=10, t=30, b=10))
    return fig

# ================= 4. 掃描執行按鈕 =================
if st.button("📡 啟動雷達掃描 (一擊必殺)"):
    # 載入名單
    if asset_type == "🏢 領頭個股": target_map = US_STOCK_MAP if market == "🇺🇸 美股" else HK_STOCK_MAP
    else: target_map = US_ETF_MAP if market == "🇺🇸 美股" else HK_ETF_MAP
    
    all_tickers = []
    sector_info = {}
    for sector, t_list in target_map.items():
        for t in t_list:
            all_tickers.append(t); sector_info[t] = sector.split(". ")[-1]

    passed_stocks = []
    sl_stocks = [] # 止損名單
    
    prog = st.progress(0)
    status = st.empty()
    
    for i, t in enumerate(all_tickers):
        prog.progress((i+1)/len(all_tickers))
        status.text(f"正在掃描: {t}...")
        df = smart_fetch(t)
        if df.empty or len(df) < 30: continue
        
        # A. 止損監控 (現價 < 10EMA)
        ema10 = df['Close'].ewm(span=10).mean().iloc[-1]
        if df['Close'].iloc[-1] < ema10:
            sl_stocks.append(t)
            
        # B. 龍魂戰術過濾
        passed, score, stage, icons, details = analyze_dragon_stock(t, df)
        if passed:
            passed_stocks.append({"t": t, "score": score, "stage": stage, "icons": icons, "df": df, "details": details, "sector": sector_info.get(t)})

    status.empty(); prog.empty()

    # 1. 顯示止損名單 (最頂，白色背景紅色字體警示)
    if sl_stocks:
        st.markdown(f"### 🚨 近 20 日【破防止損】監控名單 (跌穿 10 EMA)")
        st.error(f"建議處理：{', '.join(sl_stocks[:25])}")
        st.markdown("---")

    # 2. 顯示掃描出的神股
    if passed_stocks:
        passed_stocks.sort(key=lambda x: x['score'], reverse=True)
        st.success(f"🎉 捕捉到 {len(passed_stocks)} 隻龍魂標的！由高分至低分排序：")
        
        for s in passed_stocks:
            st.markdown(f"""
            <div class="result-card">
                <span class="sector-tag">板塊: {s['sector']}</span>
                <div style="font-size:38px; font-weight:bold; color:#00FFFF;">{s['t']} {s['stage']}</div>
                <div style="font-size:32px; margin:15px 0;">{s['icons']}</div>
                <div class="stats-text">
                    RS 指標: {round(s['score']*0.4,1)} | EJ 底氣: {round(s['score']*0.3,1)} | SE 加速度: {s['details']['SE']} | 
                    Bias 乖離: {s['details']['Bias']}% | 現價: {s['details']['Close']} | 🛡️ 10EMA 止損線: {s['details']['StopLoss']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            chart = plot_heavy_chart(s['t'], s['df'])
            if chart: st.plotly_chart(chart, use_container_width=True)
    else:
        st.warning("目前市場無標的符合龍魂條件，請保本守候。")
