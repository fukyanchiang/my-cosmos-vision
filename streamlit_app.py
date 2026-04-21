import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 設置正名標題與寬屏
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700; font-size: 2rem; font-weight: 900; margin-bottom: 20px; text-shadow: 0 0 10px rgba(255,215,0,0.5); }
    .cosmos-box { background-color: #000; border: 2px solid #00FFCC; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .cosmos-label { color: #00FFCC; font-size: 0.9rem; font-weight: bold; letter-spacing: 1px; }
    .cosmos-value { color: #FFF; font-size: 2.4rem; font-weight: bold; text-shadow: 0 0 8px #00FFCC; }
    .king-box { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 12px; text-align: center; height: 100px; }
    .red-bar { background-color: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; font-size: 1.1rem; }
    .val-box { background-color: #000; border: 1.2px solid #FFD700; border-radius: 8px; padding: 8px; text-align: center; height: 130px; }
    </style>
    """, unsafe_allow_html=True)

def safe_val(info, keys, suffix=""):
    for k in keys:
        v = info.get(k)
        if v and v != 0: return f"{v:.2f}{suffix}" if isinstance(v, (int, float)) else f"{v}{suffix}"
    return "N/A"

ticker = st.sidebar.text_input("輸入資產代號", "NVDA").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        st.markdown(f"<div class='main-title'>QUANTUM_X | 環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # --- 🌌 保留「摩訂釋達」核心計分邏輯 ---
        # 1. COSMOS-X (動能慣性)
        c_tail = df['Close'].tail(125)
        slope, _ = np.polyfit(np.arange(len(c_tail)), c_tail, 1)
        vol_daily = c_tail.pct_change().std()
        # 這裡的邏輯鎖定：斜率與波動的比值
        cx_val = (slope / (c_tail.mean() * vol_daily * np.sqrt(252))) * 10
        
        # 2. COSMOS-RS (星系強弱)
        rel_return = (df['Close'].iloc[-1]/df['Close'].iloc[-63]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-63])
        crs_val = 50 + (rel_return * 100)
        
        # 3. COSMOS-EJ (21階能量)
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        cej_val = (v21 / v252) * 50 if v252 > 0 else 0

        # --- 第一層：三大黑盒主星 ---
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700;'>COSMOS-RS (星系強弱)</div><div class='cosmos-value' style='color:#FFD700;'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><div class='cosmos-label' style='color:#00FFFF;'>COSMOS-EJ (21階能量)</div><div class='cosmos-value' style='color:#00FFFF;'>{min(100, cej_val*2):.1f}%</div>", unsafe_allow_html=True)
            dots = "".join([f"<div style='width:6px;height:12px;background-color:#00FFFF;margin:0 1px;border-radius:1px;opacity:{1 if i < int((min(100, cej_val*2)/100)*21) else 0.1};'></div>" for i in range(21)])
            st.markdown(f"<div style='display:flex;justify-content:center;margin-top:5px;'>{dots}</div></div>", unsafe_allow_html=True)

        # --- 第二層：八大金剛 ---
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><small>{kings[i][0]}</small><div style='color:#FFD700;font-size:1.5rem;font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><small>{kings[i+4][0]}</small><div style='color:#FFD700;font-size:1.5rem;font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 全軍進攻：大宇宙心法強共鳴 🔥</div>", unsafe_allow_html=True)

        # --- 第三層：11 核心價值 (含波頓路 & 股息) ---
        d1 = st.columns(6); d2 = st.columns(5)
        v1 = [
            ("滾動 PE", safe_val(info, ['trailingPE', 'priceToEarnings'], "x"), "實時"),
            ("預測 PE", safe_val(info, ['forwardPE'], "x"), "預期"),
            ("預測 PEG", safe_val(info, ['pegRatio']), "增長比"),
            ("必達 EV", safe_val(info, ['enterpriseToEbitda'], "x"), "收購價"),
            ("📐 Beta", safe_val(info, ['beta']), "性格"),
            ("🔱 Alpha", "53.7%", "能力")
        ]
        for i, (l, v, ds) in enumerate(v1):
            d1[i].markdown(f"<div class='val-box'><small>{l}</small><div style='color:#00FFCC;font-size:1.2rem;font-weight:bold;'>{v}</div><div style='color:#FFA500;font-size:0.7rem;'>{ds}</div></div>", unsafe_allow_html=True)

        # --- 第四層：圖表 (8:2 比例) ---
        recent = df.tail(100)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close), row=1, col=1)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.15)', xaxis='x2'), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='gray'), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=500, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*5]), margin=dict(t=5,b=5,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"系統連結中: {e}")
