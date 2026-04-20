import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta  # 注意：呢度一定要用底線
import numpy as np
import plotly.graph_objects as go

# 1. 樣式設定
st.set_page_config(page_title="THEMIS ASSET VISION", layout="wide")

# 2. 金色標題 (取代報錯圖片)
img_html = '<div style="color:#FFD700; font-size:2.5rem; font-weight:bold; border:2px solid #FFD700; padding:10px; border-radius:15px; text-align:center; margin-bottom:20px;">THEMIS</div>'

st.markdown(f"""
    <style>
    body, .main {{ background-color: #0e1117; color: white; }}
    [data-testid="stMetricValue"] {{ color: #FFFFFF !important; font-weight: bold !important; font-size: 2.2rem !important; }}
    [data-testid="stMetricLabel"] {{ color: #00FFCC !important; font-weight: bold !important; font-size: 1.1rem !important; }}
    .stMetric {{ background-color: #1c1e26; border: 2px solid #00FFCC; border-radius: 12px; padding: 15px; }}
    .detail-box {{ background-color: #262730; padding: 12px; border-radius: 8px; border-left: 4px solid #FFD700; margin-top: 5px; min-height: 145px; }}
    .detail-text {{ font-size: 1.2rem; color: #FFD700 !important; font-weight: bold; }}
    .label-text {{ font-size: 0.9rem; color: #FFFFFF !important; opacity: 0.8; }}
    .header-container {{ display: flex; align-items: center; padding: 12px 20px; background: linear-gradient(90deg, #1c1e26, #262730); border-radius: 15px; border: 1px solid #FFD700; margin-bottom: 20px; }}
    .main-title {{ font-size: 1.5rem; color: #FFFFFF; font-weight: 700; letter-spacing: 1.2px; margin: 0; }}
    .energy-universe {{ display: flex; gap: 6px; justify-content: center; margin-top: 10px; align-items: center; }}
    .energy-cluster {{ display: flex; gap: 2px; border: 1px solid #444; padding: 2px; border-radius: 3px; }}
    .energy-particle {{ width: 8px; height: 12px; border-radius: 1px; background-color: #222; }}
    .p-red {{ background-color: #FF4B4B; box-shadow: 0 0 3px #FF4B4B; }}
    .p-yellow {{ background-color: #FFD700; box-shadow: 0 0 3px #FFD700; }}
    .p-green {{ background-color: #00FFCC; box-shadow: 0 0 3px #00FFCC; }}
    .p-ultra {{ background-color: #00FFFF; box-shadow: 0 0 8px #00FFFF; }}
    </style>
    """, unsafe_allow_html=True)

ticker_input = st.sidebar.text_input("輸入代號", "ARKG").upper()
days = st.sidebar.slider("分析天數", 30, 365, 180)

# 核心邏輯
def get_cosmos_x(df):
    try:
        c = df['Close']; h = df['High']; l = df['Low']; v = df['Volume']
        vwap = (v * (h+l+c)/3).rolling(20).sum() / (v.rolling(20).sum() + 1e-9)
        gravity = (c.iloc[-1] / vwap.iloc[-1])
        mfi = ta.mfi(h, l, c, v, length=14).iloc[-1]
        ema200 = ta.ema(c, length=200).iloc[-1]
        score = ((c.iloc[-1]/ema200 - 1) * 50) + (mfi * 0.3) + (gravity * 20)
        return round(float(min(99.9, max(0.1, score + 20))), 1)
    except: return 50.0

# 主程式
try:
    asset = yf.Ticker(ticker_input); df = asset.history(period="2y"); info = asset.info
    if not df.empty:
        st.markdown(f"<div class='header-container'>{img_html}<div><div class='main-title'>THEMIS QUANTUM | {ticker_input} 觀測中</div></div></div>", unsafe_allow_html=True)
        
        tx_val = get_cosmos_x(df)
        st.metric("COSMOS-X 天體動能", f"{tx_val}")
        
        fig = go.Figure(data=[go.Candlestick(x=df.tail(days).index, open=df.tail(days)['Open'], high=df.tail(days)['High'], low=df.tail(days)['Low'], close=df.tail(days)['Close'])])
        fig.update_layout(template="plotly_dark", height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.success("飛昇成功！請加入 iPhone 主畫面。")
    else:
        st.error("找不到代號，請檢查輸入。")
except Exception as e:
    st.error(f"系統啟動中... 請稍後重試。({str(e)})")
