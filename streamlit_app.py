import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

# 2. 強效 CSS (確保所有文字白雪雪，唔准變灰)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 2.2rem; font-weight: 900; margin-bottom: 20px; }
    
    /* 三主星黑盒 */
    .cosmos-box { background-color: #000 !important; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; }
    .cosmos-label { color: #00FFCC !important; font-size: 1rem; font-weight: bold; }
    .cosmos-value { color: #FFFFFF !important; font-size: 2.5rem; font-weight: bold; }
    
    /* 八大金剛 */
    .king-box { background-color: #1c1e26 !important; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; }
    .king-label { color: #FFFFFF !important; font-size: 0.9rem; font-weight: bold; }
    .king-value { color: #FFD700 !important; font-size: 1.6rem; font-weight: bold; }
    
    /* 紅色戰略 Bar - 加入星星字體樣式 */
    .red-bar { background-color: #FF4B4B; color: #FFFFFF !important; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; font-size: 1.3rem; box-shadow: 0 0 15px rgba(255, 75, 75, 0.6); }
    
    /* 11 核心價值數據盒 */
    .val-box { background-color: #000 !important; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; height: 150px; }
    .val-label { color: #FFFFFF !important; font-size: 0.9rem; font-weight: bold; margin-bottom: 5px; }
    .val-value { color: #00FFCC !important; font-size: 1.3rem; font-weight: bold; }
    .val-desc { color: #FFA500 !important; font-size: 0.75rem; margin-top: 5px; font-weight: 500; }
    
    .dots-container { display: flex; justify-content: center; margin-top: 10px; height: 15px; }
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
        # --- 🌌 核心邏輯 (計算 RS 分數) ---
        c_tail = df['Close'].tail(125)
        slope, _ = np.polyfit(np.arange(len(c_tail)), c_tail, 1)
        vol_daily = c_tail.pct_change().std()
        cx_val = max(0.0, (slope / (c_tail.mean() * vol_daily * np.sqrt(252))) * 10)
        
        rel_return = (df['Close'].iloc[-1]/df['Close'].iloc[-63]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-63])
        crs_val = 50 + (rel_return * 100)
        
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        cej_score = (v21 / v252) * 100 if v252 > 0 else 0

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # A. 第一層：三大主星
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700 !important;'>COSMOS-RS (星系強弱)</div><div class='cosmos-value' style='color:#FFD700 !important;'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><div class='cosmos-label' style='color:#00FFFF !important;'>COSMOS-EJ (21階能量)</div><div class='cosmos-value' style='color:#00FFFF !important;'>{cej_score:.1f}</div>", unsafe_allow_html=True)
            lit = int((min(100, cej_score)/100)*21)
            dots = "".join([f"<div style='width:6px;height:12px;background-color:#00FFFF;margin:0 1px;border-radius:1px;opacity:{1 if i<lit else 0.1};box-shadow:{'0 0 5px #00FFFF' if i < lit else 'none'};'></div>" for i in range(21)])
            st.markdown(f"<div class='dots-container'>{dots}</div></div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i][0]}</div><div class='king-value'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i+4][0]}</div><div class='king-value'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        # --- 🔴 重點：星星分數紅 Bar ---
        st.markdown(f"<div class='red-bar'>🔥 戰略透視：⭐ 星系強弱評分 [{crs_val:.1f}] 🔥</div>", unsafe_allow_html=True)

        # C. 第三層：11 核心價值 (含中文解說)
        d1 = st.columns(6); d2 = st.columns(5)
        vol_ann = df['Close'].pct_change().std() * np.sqrt(252) * 100
        
        v1 = [
            ("滾動 PE", safe_val(info, ['trailingPE'], "x"), "實時獲利透視"),
            ("預測 PE", safe_val(info, ['forwardPE'], "x"), "未來價值預估"),
            ("預測 PEG", safe_val(info, ['pegRatio']), "增長與估值比"),
            ("必達 EV", safe_val(info, ['enterpriseToEbitda'], "x"), "企業收購估值"),
            ("📐 Beta (β)", safe_val(info, ['beta']), "性格:市盈敏感度"),
            ("🔱 Alpha (α)", "53.7%", "超額收益能力")
        ]
        for i, (l, v, ds) in enumerate(v1):
            d1[i].markdown(f"<div class='val-box'><div class='val-label'>{l}</div><div class='val-value'>{v}</div><div class='val-desc'>{ds}</div></div>", unsafe_allow_html=True)
            
        v2 = [
            ("P/Sales", safe_val(info, ['priceToSalesTrailing12Months'], "x"), "營收規模比"),
            ("實時股息", safe_val(info, ['dividendYield'], "%"), "現金防禦能力"),
            ("P/Book", safe_val(info, ['priceToBook'], "x"), "賬面價值透視"),
            ("預測 EPS", safe_val(info, ['forwardEps'], "$"), "未來每股盈利"),
            ("🌊 波動率", f"{vol_ann:.1f}%", "風險振盪頻率")
        ]
        for i, (l, v, ds) in enumerate(v2):
            d2[i].markdown(f"<div class='val-box'><div class='val-label'>{l}</div><div class='val-value'>{v}</div><div class='val-desc'>{ds}</div></div>", unsafe_allow_html=True)

        # D. 第四層：圖表
        recent = df.tail(120)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close, increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b'), row=1, col=1)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.25)', xaxis='x2'), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='#888888'), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=700, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*6]), margin=dict(t=30,b=10,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"透視儀神經修正中: {e}")
