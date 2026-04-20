import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. 頁面風格設定
st.set_page_config(page_title="THEMIS FINAL VISION", layout="wide")

# 核心 CSS 樣式 (極致黑金風格)
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    .header-container { display: flex; align-items: center; padding: 15px 20px; background: linear-gradient(90deg, #1c1e26, #262730); border-radius: 15px; border: 1px solid #FFD700; margin-bottom: 25px; }
    .stMetric { background-color: #1c1e26; border: 1px solid #00FFCC; border-radius: 12px; padding: 15px; }
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: bold !important; font-size: 2.2rem !important; }
    [data-testid="stMetricLabel"] { color: #00FFCC !important; font-weight: bold !important; font-size: 1.1rem !important; }
    .data-box { background-color: #1c1e26; padding: 12px; border-radius: 10px; border-left: 4px solid #FFD700; margin-bottom: 10px; height: 95px; }
    .data-label { color: #888; font-size: 0.85rem; font-weight: bold; }
    .data-value { color: #FFD700; font-size: 1.25rem; font-weight: bold; margin-top: 5px; }
    .energy-universe { display: flex; gap: 4px; justify-content: center; margin: 15px 0; }
    .energy-cluster { display: flex; gap: 2px; border: 1px solid #444; padding: 2px; }
    .energy-particle { width: 10px; height: 16px; background-color: #222; }
    .p-green { background-color: #00FFCC; box-shadow: 0 0 5px #00FFCC; }
    .p-ultra { background-color: #00FFFF; box-shadow: 0 0 10px #00FFFF; }
    </style>
    """, unsafe_allow_html=True)

ticker_input = st.sidebar.text_input("輸入代號", "ARKG").upper()
days = st.sidebar.slider("分析天數", 30, 365, 180)

# 2. 專業計算法 (手動計算，確保不報錯)
def get_analysis_res(df):
    c = df['Close']; h = df['High']; l = df['Low']; v = df['Volume']
    # 均線
    ma20 = c.rolling(20).mean(); ma50 = c.rolling(50).mean(); ma200 = c.rolling(200).mean()
    # RSI (14)
    delta = c.diff(); g = (delta.where(delta > 0, 0)).rolling(14).mean(); lo = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + g/lo))
    # ATR (14)
    tr = pd.concat([h-l, abs(h-c.shift()), abs(l-c.shift())], axis=1).max(axis=1); atr = tr.rolling(14).mean()
    # MACD (12, 26, 9)
    exp1 = c.ewm(span=12, adjust=False).mean(); exp2 = c.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2; signal = macd.ewm(span=9, adjust=False).mean()
    # 乖離率 (BIAS 20)
    bias = ((c - ma20) / ma20) * 100
    
    # 三大核心評分
    score_x = (c.iloc[-1] / ma20.iloc[-1] * 50) + (rsi.iloc[-1] * 0.5)
    score_rs = (c.pct_change(63).iloc[-1] * 100) + 50 # 3個月強弱
    
    return {
        "X": round(float(score_x), 1), "RS": round(float(score_rs), 1),
        "RSI": round(rsi.iloc[-1], 2), "ATR": round(atr.iloc[-1], 2), "MACD": round(macd.iloc[-1], 3), "BIAS": round(bias.iloc[-1], 2),
        "MA20": round(ma20.iloc[-1], 2), "MA50": round(ma50.iloc[-1], 2), "MA200": round(ma200.iloc[-1], 2), "H52": round(h.tail(252).max(), 2),
        "df_candle": df.tail(days)
    }

try:
    asset = yf.Ticker(ticker_input); df = asset.history(period="2y")
    if not df.empty:
        res = get_analysis_res(df)
        df_c = res["df_candle"]
        
        st.markdown(f"<div class='header-container'><div style='color:#FFD700; font-size:2rem; font-weight:bold; border:2px solid #FFD700; padding:5px 15px; border-radius:10px; margin-right:15px;'>THEMIS</div><div style='font-size:1.5rem;'>QUANTUM_X | {ticker_input} 完全體觀測</div></div>", unsafe_allow_html=True)

        # A. 三大天體評分
        m1, m2, m3 = st.columns(3)
        m1.metric("COSMOS-X (天體動能)", res["X"])
        m2.metric("COSMOS-RS (星系強弱)", res["RS"])
        with m3:
            # B. 21 階能量大陣
            st.markdown("<div style='color:#00FFCC; font-weight:bold; font-size:1.1rem; margin-bottom:5px;'>COSMOS-EJ (21階能量)</div>", unsafe_allow_html=True)
            total_p = int(min(21, max(1, (res["X"] / 100) * 21)))
            u_html = ""
            for i in range(7):
                p_html = "".join([f"<div class='energy-particle {('p-ultra' if i==6 and (i*3+j)<=total_p else 'p-green' if (i*3+j)<=total_p else '')}'></div>" for j in range(1,4)])
                u_html += f"<div class='energy-cluster'>{p_html}</div>"
            st.markdown(f"<div class='energy-universe'>{u_html}</div>", unsafe_allow_html=True)

        st.markdown("---")

        # C. 八大金剛觀測數據
        st.markdown("### 🌀 八大金剛護法指標")
        col1, col2, col3, col4 = st.columns(4)
        
        def box(col, lab, val): col.markdown(f"<div class='data-box'><div class='data-label'>{lab}</div><div class='data-value'>{val}</div></div>", unsafe_allow_html=True)

        box(col1, "RSI (強弱指標)", res["RSI"]); box(col2, "MACD (趨勢值)", res["MACD"]); box(col3, "ATR (波動率)", res["ATR"]); box(col4, "BIAS (乖離率)", f"{res['BIAS']}%")
        box(col1, "MA20 (生命線)", f"${res['MA20']}"); box(col2, "MA50 (趨勢線)", f"${res['MA50']}"); box(col3, "MA200 (神盾線)", f"${res['MA200']}"); box(col4, "52週最高", f"${res['H52']}")

        # D. 圖表 (還原成交量紅綠橫柱)
        # 計算紅綠顏色
        colors = ['#FF4B4B' if close < open else '#00FFCC' for open, close in zip(df_c['Open'], df_c['Close'])]
        
        fig = go.Figure()
        # 1. K 線圖
        fig.add_trace(go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name='K線', increasing_line_color='#00FFCC', decreasing_line_color='#FF4B4B'))
        # 2. 成交量橫柱 (使用 Overlay，並設置在不同的 Y 軸)
        fig.add_trace(go.Bar(x=df_c.index, y=df_c['Volume'], name='成交量', marker_color=colors, opacity=0.3, yaxis='y2'))
        
        fig.update_layout(template="plotly_dark", height=600, margin=dict(t=0,b=0,l=0,r=0), xaxis_rangeslider_visible=False, yaxis=dict(title='價格', side='right'), yaxis2=dict(title='成交量', overlaying='y', side='left', showgrid=False))
        st.plotly_chart(fig, use_container_width=True)

        st.success("✅ 完美還原完全體版本。觀測儀運行中。")
    else: st.error("找不到代號")
except Exception as e: st.error(f"連線中... ({str(e)})")
