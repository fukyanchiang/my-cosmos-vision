import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 基礎設定
st.set_page_config(page_title="THEMIS ASSET VISION", layout="wide")

# 2. CSS 樣式 (維持大宇宙金黑風格)
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: bold !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] { color: #00FFCC !important; font-weight: bold !important; font-size: 1.1rem !important; }
    .stMetric { background-color: #1c1e26; border: 2px solid #00FFCC; border-radius: 12px; padding: 15px; }
    .header-container { display: flex; align-items: center; padding: 15px 20px; background: linear-gradient(90deg, #1c1e26, #262730); border-radius: 15px; border: 1px solid #FFD700; margin-bottom: 25px; }
    .main-title { font-size: 1.6rem; color: #FFFFFF; font-weight: 700; letter-spacing: 1.2px; margin: 0; }
    
    /* 能量珠樣式 */
    .energy-universe { display: flex; gap: 6px; justify-content: center; margin-top: 10px; align-items: center; }
    .energy-cluster { display: flex; gap: 2px; border: 1px solid #444; padding: 2px; border-radius: 3px; }
    .energy-particle { width: 10px; height: 16px; border-radius: 1px; background-color: #222; }
    .p-green { background-color: #00FFCC; box-shadow: 0 0 5px #00FFCC; }
    .p-ultra { background-color: #00FFFF; box-shadow: 0 0 10px #00FFFF; }
    .energy-label { color: #00FFFF; font-weight: bold; font-size: 1.1rem; text-align: center; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 側邊欄輸入
ticker_input = st.sidebar.text_input("輸入代號", "ARKG").upper()
days = st.sidebar.slider("分析天數", 30, 365, 180)

# 3. 核心功能 (手動計算法)
def get_cosmos_x_score(df):
    try:
        c = df['Close']
        ma20 = c.rolling(20).mean()
        ma200 = c.rolling(200).mean()
        # 動能評分：現價與20日線及200日線的關係
        score = ((c.iloc[-1] / ma20.iloc[-1] * 0.7) + (c.iloc[-1] / ma200.iloc[-1] * 0.3)) * 85
        return round(float(min(99.9, max(0.1, score))), 1)
    except:
        return 50.0

try:
    # 獲取數據
    asset = yf.Ticker(ticker_input); df = asset.history(period="2y")
    
    if not df.empty:
        # 金色標題
        img_title = '<div style="color:#FFD700; font-size:2.2rem; font-weight:bold; border:2px solid #FFD700; padding:10px 20px; border-radius:15px; margin-right:20px;">THEMIS</div>'
        st.markdown(f"<div class='header-container'>{img_title}<div><div class='main-title'>QUANTUM_X | {ticker_input} 21階能量觀測儀</div></div></div>", unsafe_allow_html=True)

        # 計算評分與能量珠
        tx_val = get_cosmos_x_score(df)
        
        # 21 粒珠算法：根據分數分配
        total_particles = int(min(21, max(1, (tx_val / 100) * 21)))
        
        u_html = ""
        for cluster in range(1, 8): # 7 組
            c_content = ""
            for particle in range(1, 4): # 每組 3 粒
                p_idx = (cluster - 1) * 3 + particle
                p_cls = ""
                if p_idx <= total_particles:
                    p_cls = "p-ultra" if cluster == 7 else "p-green"
                c_content += f"<div class='energy-particle {p_cls}'></div>"
            u_html += f"<div class='energy-cluster'>{c_content}</div>"

        # 頂部儀表板
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("COSMOS-X 動能評分", f"{tx_val}")
        with col2:
            st.markdown("<div class='energy-label'>COSMOS-EJ 21階能量大陣</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='energy-universe'>{u_html}</div>", unsafe_allow_html=True)

        st.markdown("---")

        # 繪圖
        df_plot = df.tail(days)
        fig = go.Figure(data=[go.Candlestick(
            x=df_plot.index, open=df_plot['Open'], high=df_plot['High'], 
            low=df_plot['Low'], close=df_plot['Close'],
            increasing_line_color='#00FFCC', decreasing_line_color='#FF4B4B'
        )])
        fig.update_layout(template="plotly_dark", height=550, margin=dict(t=10, b=10, l=10, r=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.success("✅ 數據對齊成功。觀測儀運行中。")

    else:
        st.error("找不到該資產數據，請檢查代號是否正確。")

except Exception as e:
    st.error(f"系統觀測中... 請稍後。({str(e)})")
