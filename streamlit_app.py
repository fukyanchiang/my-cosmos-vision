import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 基礎設定
st.set_page_config(page_title="THEMIS ASSET VISION", layout="wide")

# 2. CSS 樣式 (極致黑金風格)
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: bold !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] { color: #00FFCC !important; font-weight: bold !important; font-size: 1.1rem !important; }
    .stMetric { background-color: #1c1e26; border: 2px solid #00FFCC; border-radius: 12px; padding: 15px; }
    .header-container { display: flex; align-items: center; padding: 15px 20px; background: linear-gradient(90deg, #1c1e26, #262730); border-radius: 15px; border: 1px solid #FFD700; margin-bottom: 25px; }
    .main-title { font-size: 1.6rem; color: #FFFFFF; font-weight: 700; letter-spacing: 1.2px; margin: 0; }
    .energy-universe { display: flex; gap: 6px; justify-content: center; margin-top: 10px; align-items: center; }
    .energy-cluster { display: flex; gap: 2px; border: 1px solid #444; padding: 2px; border-radius: 3px; }
    .energy-particle { width: 10px; height: 16px; border-radius: 1px; background-color: #222; }
    .p-green { background-color: #00FFCC; box-shadow: 0 0 5px #00FFCC; }
    .p-ultra { background-color: #00FFFF; box-shadow: 0 0 10px #00FFFF; }
    .data-box { background-color: #1c1e26; padding: 15px; border-radius: 10px; border-left: 5px solid #FFD700; margin-bottom: 10px; }
    .data-label { color: #888; font-size: 0.9rem; }
    .data-value { color: #FFD700; font-size: 1.3rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

ticker_input = st.sidebar.text_input("輸入代號", "ARKG").upper()
days = st.sidebar.slider("分析天數", 30, 365, 180)

# 核心計算法
def calc_metrics(df):
    c = df['Close']; h = df['High']; l = df['Low']
    ma20 = c.rolling(20).mean(); ma200 = c.rolling(200).mean()
    
    # 1. COSMOS-X (動能)
    score_x = round(float((c.iloc[-1] / ma20.iloc[-1]) * 95), 1)
    
    # 2. STCR (天體結構 - 趨勢穩定度)
    stcr = round(float((c.rolling(50).mean().iloc[-1] / ma200.iloc[-1]) * 100), 1)
    
    # 3. RS (相對強度 - 模擬計算)
    rs_val = round(float((c.pct_change(60).iloc[-1] * 100) + 50), 1)
    
    return score_x, stcr, rs_val

try:
    asset = yf.Ticker(ticker_input); df = asset.history(period="2y")
    if not df.empty:
        img_title = '<div style="color:#FFD700; font-size:2.2rem; font-weight:bold; border:2px solid #FFD700; padding:10px 20px; border-radius:15px; margin-right:20px;">THEMIS</div>'
        st.markdown(f"<div class='header-container'>{img_title}<div><div class='main-title'>QUANTUM_X | {ticker_input} 大圓滿觀測</div></div></div>", unsafe_allow_html=True)

        score_x, stcr, rs_val = calc_metrics(df)
        
        # 第一排：三大評分
        m1, m2, m3 = st.columns(3)
        m1.metric("COSMOS-X 動能", f"{score_x}")
        m2.metric("STCR 結構評分", f"{stcr}")
        m3.metric("RS 相對強度", f"{rs_val}")

        # 第二排：21 階能量珠
        total_p = int(min(21, max(1, (score_x / 100) * 21)))
        u_html = ""
        for cluster in range(1, 8):
            c_content = "".join([f"<div class='energy-particle {'p-ultra' if cluster==7 and (cluster-1)*3+p<=total_p else 'p-green' if (cluster-1)*3+p<=total_p else ''}'></div>" for p in range(1, 4)])
            u_html += f"<div class='energy-cluster'>{c_content}</div>"
        st.markdown(f"<div style='text-align:center; color:#00FFFF; margin-bottom:5px;'>COSMOS-EJ 21階能量大陣</div><div class='energy-universe'>{u_html}</div>", unsafe_allow_html=True)

        # 第三排：八大金剛 (詳細數據)
        st.markdown("### 🌀 八大金剛觀測數據")
        k1, k2, k3, k4 = st.columns(4)
        k1.markdown(f"<div class='data-box'><div class='data-label'>現價</div><div class='data-value'>${round(df['Close'].iloc[-1],2)}</div></div>", unsafe_allow_html=True)
        k2.markdown(f"<div class='data-box'><div class='data-label'>20日平均</div><div class='data-value'>${round(df['Close'].rolling(20).mean().iloc[-1],2)}</div></div>", unsafe_allow_html=True)
        k3.markdown(f"<div class='data-box'><div class='data-label'>52週最高</div><div class='data-value'>${round(df['High'].tail(252).max(),2)}</div></div>", unsafe_allow_html=True)
        k4.markdown(f"<div class='data-box'><div class='data-label'>成交量</div><div class='data-value'>{int(df['Volume'].iloc[-1]/1000)}K</div></div>", unsafe_allow_html=True)

        # 繪圖
        fig = go.Figure(data=[go.Candlestick(x=df.tail(days).index, open=df.tail(days)['Open'], high=df.tail(days)['High'], low=df.tail(days)['Low'], close=df.tail(days)['Close'])])
        fig.update_layout(template="plotly_dark", height=500, margin=dict(t=0,b=0,l=0,r=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        st.success("✅ 大圓滿版本已部署。八大金剛護法中。")
    else: st.error("找不到代號")
except Exception as e: st.error(f"連線中: {e}")
