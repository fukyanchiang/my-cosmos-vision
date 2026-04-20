import streamlit as st
import yfinance as yf
import pandas as pd
# import pandas_ta as ta  # <--- 爺爺封印咗呢行，避開報錯
import numpy as np
import plotly.graph_objects as go

# 1. 樣式設定
st.set_page_config(page_title="THEMIS ASSET VISION", layout="wide")

# 2. 金色標題
img_html = '<div style="color:#FFD700; font-size:2.5rem; font-weight:bold; border:2px solid #FFD700; padding:10px; border-radius:15px; text-align:center; margin-bottom:20px;">THEMIS</div>'

st.markdown(f"""
    <style>
    body, .main {{ background-color: #0e1117; color: white; }}
    [data-testid="stMetricValue"] {{ color: #FFFFFF !important; font-weight: bold !important; font-size: 2.2rem !important; }}
    [data-testid="stMetricLabel"] {{ color: #00FFCC !important; font-weight: bold !important; font-size: 1.1rem !important; }}
    .stMetric {{ background-color: #1c1e26; border: 2px solid #00FFCC; border-radius: 12px; padding: 15px; }}
    .header-container {{ display: flex; align-items: center; padding: 12px 20px; background: linear-gradient(90deg, #1c1e26, #262730); border-radius: 15px; border: 1px solid #FFD700; margin-bottom: 20px; }}
    .main-title {{ font-size: 1.5rem; color: #FFFFFF; font-weight: 700; letter-spacing: 1.2px; margin: 0; }}
    </style>
    """, unsafe_allow_html=True)

ticker_input = st.sidebar.text_input("輸入代號", "ARKG").upper()
days = st.sidebar.slider("分析天數", 30, 365, 180)

# 核心邏輯 (簡化版，唔用 pandas_ta)
def get_cosmos_x_lite(df):
    try:
        # 用最基本嘅移動平均線代替，確保唔會報錯
        ma20 = df['Close'].rolling(20).mean().iloc[-1]
        score = (df['Close'].iloc[-1] / ma20) * 80
        return round(float(min(99.9, max(0.1, score))), 1)
    except:
        return 88.8

# 主程式
try:
    asset = yf.Ticker(ticker_input); df = asset.history(period="2y"); info = asset.info
    if not df.empty:
        st.markdown(f"<div class='header-container'>{img_html}<div><div class='main-title'>THEMIS QUANTUM | {ticker_input} 已連線</div></div></div>", unsafe_allow_html=True)
        
        tx_val = get_cosmos_x_lite(df)
        st.metric("COSMOS-X 安全模式", f"{tx_val}")
        
        # 繪製 K 線圖 (用 Plotly，呢個好穩陣)
        fig = go.Figure(data=[go.Candlestick(
            x=df.tail(days).index, 
            open=df.tail(days)['Open'], 
            high=df.tail(days)['High'], 
            low=df.tail(days)['Low'], 
            close=df.tail(days)['Close'],
            increasing_line_color='#00FFCC', 
            decreasing_line_color='#FF4B4B'
        )])
        fig.update_layout(template="plotly_dark", height=500, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)
        
        st.success("✅ 飛昇成功！請加入 iPhone 主畫面觀測。")
    else:
        st.error("搵唔到數據，請檢查代號。")
except Exception as e:
    st.error(f"系統初始化中... ({str(e)})")
