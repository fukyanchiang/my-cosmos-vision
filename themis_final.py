import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 核心量化引擎 (羅輯全真 + 穩定過濾)
# ==========================================
st.set_page_config(page_title="COSMOS 終極終端", layout="wide")

def calculate_advanced_metrics(df, spy_df):
    try:
        h_aligned, m_aligned = df['Close'].align(spy_df['Close'], join='inner')
        stock_ret = h_aligned.pct_change().dropna().tail(60)
        market_ret = m_aligned.pct_change().dropna().tail(60)
        rebel = max(0, min(100, ((stock_ret[market_ret < 0] > market_ret[market_ret < 0]).mean() - 0.4) * 166.6))
        dna = round(rebel * 0.6 + 40, 1)
        rs = 50 + ((h_aligned.iloc[-1]/h_aligned.iloc[-63]) - (m_aligned.iloc[-1]/m_aligned.iloc[-63])) * 100
        y = df['Close'].tail(125).values
        x = np.arange(len(y))
        slope, _ = np.polyfit(x, y, 1)
        cx = (slope * 252 / y.mean() / (df['Close'].pct_change().std() * np.sqrt(252))) * 25
        return dna, rs, cx
    except: return 50.0, 50.0, 50.0

def calculate_filtered_energy(df):
    try:
        change_5d = (df['Close'].iloc[-1] / df['Close'].iloc[-5]) - 1
        atr = (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
        if abs(df['Close'].iloc[-1] - df['Close'].iloc[-5]) < (atr * 1.5): return 50.0
        return max(0, min(250, 50 + (change_5d * 1200)))
    except: return 50.0

# ==========================================
# 2. UI 渲染
# ==========================================
st.sidebar.markdown("### 🕹️ 核心控制")
ticker = st.sidebar.text_input("輸入代號 (例如: 6869.HK)", "6869.HK").upper()
manual_target = st.sidebar.number_input("手動修正目標價 (0為自動)", value=0.0)

try:
    asset = yf.Ticker(ticker); info = asset.info
    df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
    spy = yf.Ticker("SPY").history(period="2y").dropna()
    
    if not df.empty:
        curr = df['Close'].iloc[-1]
        dna, rs, cx = calculate_advanced_metrics(df, spy)
        energy = calculate_filtered_energy(df)
        
        # A. 頂部看板 (修復小數點)
        st.markdown(f"## 🏛️ {info.get('longName', ticker)} 全方位透視")
        v1, v2, v3, v4 = st.columns(4)
        pe = info.get('trailingPE')
        pb = info.get('priceToBook')
        v1.metric("PE (TTM)", f"{pe:.2f}" if pe else "N/A")
        v2.metric("PB", f"{pb:.2f}" if pb else "N/A")
        v3.metric("機構持倉", f"{info.get('heldPercentInstitutions', 0)*100:.1f}%")
        v4.metric("內幕持倉", f"{info.get('heldPercentInsiders', 0)*100:.1f}%")

        # B. 專業 K 線與蟹貨區 (穩定修正版)
        st.write("### 🕯️ 專業 K 線與蟹貨區 (Visible Range Volume Profile)")
        fig = make_subplots(rows=1, cols=2, column_widths=[0.85, 0.15], shared_yaxes=True, horizontal_spacing=0.01)
        
        # 主 K 線
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
        
        # 蟹貨區 (Volume Profile) - 增加穩定性處理
        clean_vol_df = df[['Close', 'Volume']].dropna()
        if not clean_vol_df.empty:
            counts, bins = np.histogram(clean_vol_df['Close'], bins=50, weights=clean_vol_df['Volume'])
            fig.add_trace(go.Bar(x=counts, y=bins[:-1], orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name="成交分佈"), row=1, col=2)
        
        fig.update_layout(height=500, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # C. 核心量化指標
        st.write("---")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("🧬 DNA 基因", f"{dna}")
        k2.metric("🎭 情緒 (RS)", f"{rs:.1f}")
        k3.metric("⚡ 天體動能", f"{cx:.1f}")
        target_val = manual_target if manual_target > 0 else (info.get('targetMeanPrice') or curr * (1 + (info.get('earningsGrowth', 0) or 0.1)))
        k4.metric("🔮 明年目標", f"${target_val:.2f}")

        # D. 詳細數據與能量條
        st.write("---")
        m1, m2, m3 = st.columns(3)
        m1.write(f"**PEG:** {info.get('pegRatio', 'N/A')}")
        m2.write(f"**EV/EBITDA:** {info.get('enterpriseToEbitda', 'N/A')}")
        m3.write(f"**股息率:** {info.get('dividendYield', 0)*100:.2f}%")
        
        st.markdown(f"<div style='background-color:#FF4B4B; padding:15px; border-radius:10px; text-align:center; font-weight:900; margin-top:20px;'>🔥 真實短期爆發能量：{energy:.1f}% (ATR 防震啟動) 🔥</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"⚠️ 診斷中：{e}。請檢查代號或稍後再試。")
