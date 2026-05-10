import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# 從心臟檔案引入武器
from core_logic import (
    HK_STOCK_MAP, US_STOCK_MAP, HK_ETF_MAP, US_ETF_MAP,
    smart_fetch, analyze_dragon_stock
)

# ================= 1. 介面設定 =================
st.set_page_config(page_title="爺孫必勝雷達 V2.0", layout="wide")

# 注入 CSS：戰鬥黑金風格
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; height: 100px; font-size: 28px !important; font-weight: bold; border-radius: 15px; border: 2px solid #FFD700; background-color: #1e2129; color: #FFD700; transition: 0.3s; }
    .stButton>button:hover { background-color: #FFD700; color: #000000; }
    .control-panel { background-color: #161a24; padding: 20px; border-radius: 10px; border: 1px solid #444; margin-top: 20px; }
    .result-box { background-color: #1e2129; padding: 25px; border-radius: 15px; border-left: 10px solid #FFD700; margin-bottom: 30px; }
    .ticker-name { font-size: 36px; font-weight: bold; color: #00FFFF; }
    </style>
""", unsafe_allow_html=True)

st.title("🦅 爺孫必勝雷達 V2.0")
st.markdown("<h4 style='text-align: center; color: #888;'>—— 戰術先行 • 數據奪路 ——</h4>", unsafe_allow_html=True)

# ================= 2. 三大核心戰術大掣 (第一層) =================
# 使用 Session State 嚟記住揀咗邊個戰術
if 'tactic' not in st.session_state:
    st.session_state.tactic = None

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🐲 龍魂起步\n(千龍雷達)"):
        st.session_state.tactic = "Dragon"
with col2:
    if st.button("📈 VCP 形態\n(爆發鎖定)"):
        st.session_state.tactic = "VCP"
with col3:
    if st.button("🌊 海龜回測\n(強勢回補)"):
        st.session_state.tactic = "Turtle"

# ================= 3. 戰略指揮塔 (第二層：根據戰術顯示選項) =================
if st.session_state.tactic:
    st.markdown(f"### 🎯 已選戰術：{'🐲 龍魂' if st.session_state.tactic=='Dragon' else '📈 VCP' if st.session_state.tactic=='VCP' else '🌊 海龜'}")
    
    with st.container():
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            market = st.radio("掃描市場", ["🇺🇸 美股", "🇭🇰 港股"], horizontal=True)
        with c2:
            asset_type = st.radio("資產類別", ["🏢 個股", "🧺 ETF"], horizontal=True)
        with c3:
            tactical_filter = st.radio("戰術過濾", ["🔥 極致新高 (ATH)", "🐉 潛龍伏躍"], horizontal=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 準備名單
    if asset_type == "🏢 個股":
        target_map = US_STOCK_MAP if market == "🇺🇸 美股" else HK_STOCK_MAP
    else:
        target_map = US_ETF_MAP if market == "🇺🇸 美股" else HK_ETF_MAP

    # ================= 4. 專業圖表函數 (Plotly) =================
    def plot_professional_chart(ticker, df):
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_width=[0.3, 0.7])
        # 蠟燭圖
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
        # 均線
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'].ewm(span=10).mean(), line=dict(color='yellow', width=1.5), name='10 EMA'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'].rolling(50).mean(), line=dict(color='cyan', width=1.5), name='50 SMA'), row=1, col=1)
        # 成交量
        colors = ['green' if df['Close'].iloc[i] > df['Open'].iloc[i] else 'red' for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='成交量'), row=2, col=1)
        fig.update_layout(height=600, template='plotly_dark', showlegend=False, xaxis_rangeslider_visible=False)
        return fig

    # ================= 5. 掃描執行 =================
    if st.button(f"🔍 啟動 {market} 掃描", type="primary"):
        all_tickers = []
        for s_list in target_map.values(): all_tickers.extend(s_list)
        
        prog = st.progress(0)
        status = st.empty()
        passed_stocks = []

        for i, t in enumerate(all_tickers):
            status.text(f"正在掃描: {t} ({i+1}/{len(all_tickers)})")
            prog.progress((i+1)/len(all_tickers))
            df = smart_fetch(t)
            if df.empty: continue
            
            # 戰術邏輯
            if st.session_state.tactic == "Dragon":
                passed, score, stage, icons, details = analyze_dragon_stock(t, df)
                if passed:
                    passed_stocks.append({"t": t, "score": score, "stage": stage, "icons": icons, "df": df, "details": details})
            else:
                # VCP 與 海龜 邏輯暫未開放，先預留
                st.warning("此戰術邏輯正在開發中...")
                break

        status.empty()
        prog.empty()

        if passed_stocks:
            passed_stocks.sort(key=lambda x: x['score'], reverse=True)
            for s in passed_stocks:
                st.markdown(f"""
                <div class="result-box">
                    <div class="ticker-name">{s['t']} <span style="font-size: 20px; color:#FF4500;">{s['stage']}</span></div>
                    <div style="font-size: 24px; margin: 10px 0;">{s['icons']}</div>
                    <p style="color: #32CD32; font-size: 18px; font-weight: bold;">🏆 龍魂分: {round(s['score'],2)} | 🛡️ 止損參考: {s['details']['StopLoss']}</p>
                </div>
                """, unsafe_allow_html=True)
                st.plotly_chart(plot_professional_chart(s['t'], s['df']), use_container_width=True)
        else:
            st.warning("今日無股票符合條件，請守好資金。")
