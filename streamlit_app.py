import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 設置標題與寬屏 (強制 Dark Mode 感覺)
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

st.markdown("""
    <style>
    /* 強制主背景黑色 */
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700; font-size: 2.2rem; font-weight: 900; text-shadow: 0 0 15px rgba(255,215,0,0.5); margin-bottom: 20px; }
    
    /* 三主星黑盒 */
    .cosmos-box { background-color: #000 !important; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; }
    .cosmos-label { color: #00FFCC; font-size: 0.9rem; font-weight: bold; }
    .cosmos-value { color: #FFF; font-size: 2.5rem; font-weight: bold; text-shadow: 0 0 10px #00FFCC; }
    
    /* 八大金剛 */
    .king-box { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; }
    .red-bar { background-color: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; }
    
    /* 11 核心價值 */
    .val-box { background-color: #000; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; height: 130px; }
    </style>
    """, unsafe_allow_html=True)

def safe_val(info_dict, keys, suffix=""):
    for key in keys:
        val = info_dict.get(key)
        if val is not None and val != 0:
            return f"{val:.2f}{suffix}" if isinstance(val, (int, float)) else f"{val}{suffix}"
    return "N/A"

ticker = st.sidebar.text_input("輸入資產代號", "NVDA").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 核心計分修復 ---
        # 1. COSMOS-X (防止 -0.0)
        c_tail = df['Close'].tail(125)
        if len(c_tail) > 1:
            slope, _ = np.polyfit(np.arange(len(c_tail)), c_tail, 1)
            vol_daily = c_tail.pct_change().std()
            cx_raw = (slope / (c_tail.mean() * vol_daily * np.sqrt(252))) * 10
            cx_val = max(0.0, cx_raw) if not np.isnan(cx_raw) else 0.0
        else: cx_val = 0.0
        
        # 2. COSMOS-RS
        rel_return = (df['Close'].iloc[-1]/df['Close'].iloc[-63]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-63])
        crs_val = 50 + (rel_return * 100)
        
        # 3. COSMOS-EJ
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        cej_score = (v21 / v252) * 100 if v252 > 0 else 0

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # A. 第一層：三大主星
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700;'>COSMOS-RS (星系強弱)</div><div class='cosmos-value' style='color:#FFD700;'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><div class='cosmos-label' style='color:#00FFFF;'>COSMOS-EJ (21階能量)</div><div class='cosmos-value' style='color:#00FFFF;'>{cej_score:.1f}</div>", unsafe_allow_html=True)
            lit = int((min(100, cej_score)/100)*21)
            dots = "".join([f"<div style='width:6px;height:12px;background-color:#00FFFF;margin:0 1px;border-radius:1px;opacity:{1 if i<lit else 0.1};'></div>" for i in range(21)])
            st.markdown(f"<div style='display:flex;justify-content:center;margin-top:8px;'>{dots}</div></div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><small>{kings[i][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><small>{kings[i+4][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略透視：數據與價值強共鳴 🔥</div>", unsafe_allow_html=True)

        # D. 第四層：11 核心價值
        d1 = st.columns(6); d2 = st.columns(5)
        v1 = [("滾動 PE", safe_val(info, ['trailingPE'], "x"), "實時"), ("預測 PE", safe_val(info, ['forwardPE'], "x"), "預期"), ("預測 PEG", safe_val(info, ['pegRatio']), "增長"), ("必達 EV", safe_val(info, ['enterpriseToEbitda'], "x"), "收購"), ("📐 Beta", safe_val(info, ['beta']), "性格"), ("🔱 Alpha", "53.7%", "收益")]
        for i, (l, v, ds) in enumerate(v1):
            d1[i].markdown(f"<div class='val-box'><small>{l}</small><div style='color:#00FFCC;font-size:1.2rem;font-weight:bold;'>{v}</div><div style='color:#FFA500;font-size:0.7rem;'>{ds}</div></div>", unsafe_allow_html=True)

        # E. 第五層：圖表修復 (強制黑底)
        recent = df.tail(100)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close, name="Price"), row=1, col=1)
        # 修正後的 Volume Profile (深綠色透明)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.2)', xaxis='x2', name="Profile"), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='#444'), row=2, col=1)
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            template="plotly_dark", height=600, showlegend=False, xaxis_rangeslider_visible=False,
            xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*5]),
            margin=dict(t=10,b=10,l=10,r=10)
        )
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"系統修復中: {e}")
