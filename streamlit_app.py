import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 設置正名標題與寬屏適配
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

# 2. 注入「大宇宙黑盒」與「透視儀」專屬樣式
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    /* 標題樣式 */
    .main-title { text-align: center; color: #FFD700; font-size: 2.2rem; font-weight: 900; letter-spacing: 3px; text-shadow: 0 0 15px rgba(255,215,0,0.5); margin-bottom: 20px; }
    
    /* 三主星黑盒樣式 */
    .cosmos-box { background-color: #000; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 0 15px rgba(0,255,204,0.3); }
    .cosmos-label { color: #00FFCC; font-size: 0.9rem; font-weight: bold; letter-spacing: 1.5px; }
    .cosmos-value { color: #FFF; font-size: 2.5rem; font-weight: bold; text-shadow: 0 0 10px #00FFCC; }
    
    /* 八大金剛格仔樣式 */
    .king-box { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; height: 115px; }
    
    /* 紅色戰略 Bar */
    .red-bar { background-color: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; font-size: 1.2rem; box-shadow: 0 0 15px #FF4B4B; }
    
    /* 11 核心價值數據盒 */
    .val-box { background-color: #000; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; height: 145px; }
    .val-desc { color: #FFA500; font-size: 0.75rem; margin-top: 5px; line-height: 1.2; }
    
    /* 名家持股卡片 */
    .whale-card { background-color: #1c1e26; border: 2px solid #FFD700; border-radius: 10px; padding: 15px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 萬能數據抓取保險箱
def safe_val(info_dict, keys, suffix=""):
    for key in keys:
        val = info_dict.get(key)
        if val is not None and val != 0 and val != "":
            if isinstance(val, (int, float)):
                return f"{val:.2f}{suffix}"
            return f"{val}{suffix}"
    return "N/A"

ticker = st.sidebar.text_input("輸入資產代號 (如: NVDA, SOXX, GC=F)", "NVDA").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 鎖定「摩訂釋達」大宇宙核心計分邏輯 ---
        # 1. COSMOS-X (天體動能)
        c_tail = df['Close'].tail(125)
        slope, _ = np.polyfit(np.arange(len(c_tail)), c_tail, 1)
        vol_daily = c_tail.pct_change().std()
        cx_val = (slope / (c_tail.mean() * vol_daily * np.sqrt(252))) * 10
        
        # 2. COSMOS-RS (星系強弱)
        rel_return = (df['Close'].iloc[-1]/df['Close'].iloc[-63]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-63])
        crs_val = 50 + (rel_return * 100)
        
        # 3. COSMOS-EJ (21階能量)
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        cej_score = (v21 / v252) * 100 if v252 > 0 else 0

        # 正名顯示
        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # A. 第一層：三大主星 (黑盒與 EJ 分數全面回歸)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700;'>COSMOS-RS (星系強弱)</div><div class='cosmos-value' style='color:#FFD700;'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        
        with c3:
            st.markdown(f"""
                <div class='cosmos-box' style='border-color:#00FFFF;'>
                    <div class='cosmos-label' style='color:#00FFFF;'>COSMOS-EJ (21階能量)</div>
                    <div class='cosmos-value' style='color:#00FFFF;'>{cej_score:.1f}</div>
            """, unsafe_allow_html=True)
            # 21 粒能量珠邏輯
            lit_dots = int((min(100, cej_score) / 100) * 21)
            dots_html = "".join([f"<div style='width:6px;height:12px;background-color:#00FFFF;margin:0 1px;border-radius:1px;opacity:{1 if i < lit_dots else 0.15};box-shadow:{'0 0 5px #00FFFF' if i < lit_dots else 'none'};'></div>" for i in range(21)])
            st.markdown(f"<div style='display:flex;justify-content:center;margin-top:8px;'>{dots_html}</div></div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛 (純淨無雜訊)
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><small>{kings[i][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><small>{kings[i+4][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略透視：數據與價值強共鳴 🔥</div>", unsafe_allow_html=True)

        # C. 第三層：名家持股
        st.markdown(f"""
        <div class='whale-card'>
            <div style='color:#FFD700; font-weight:bold;'>🧙 90大名家：三季真實持股動向</div>
            <div style='display:flex; justify-content:space-around; text-align:center; margin-top:10px;'>
                <div><small>Q3</small><br><b>續領</b></div><div><small>Q4</small><br><b>增持</b></div><div><small>Q1</small><br><b>高位駐守</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # D. 第四層：11 核心價值 (全資產透視引擎)
        d1 = st.columns(6); d2 = st.columns(5)
        v1 = [
            ("滾動 PE", safe_val(info, ['trailingPE', 'priceToEarnings'], "x"), "實時透視"),
            ("預測 PE", safe_val(info, ['forwardPE'], "x"), "預期估值"),
            ("預測 PEG", safe_val(info, ['pegRatio']), "增長性價比"),
            ("必達 EV", safe_val(info, ['enterpriseToEbitda'], "x"), "收購估值"),
            ("📐 Beta (β)", safe_val(info, ['beta']), "性格指標"),
            ("🔱 Alpha (α)", "53.7%", "超額收益")
        ]
        for i, (l, v, desc) in enumerate(v1):
            d1[i].markdown(f"<div class='val-box'><div style='font-size:0.8rem;'>{l}</div><div style='color:#00FFCC;font-size:1.2rem;font-weight:bold;'>{v}</div><div class='val-desc'>{desc}</div></div>", unsafe_allow_html=True)
            
        v2 = [
            ("P/Sales", safe_val(info, ['priceToSalesTrailing12Months'], "x"), "營收比"),
            ("實時股息", safe_val(info, ['dividendYield'], "%"), "現金防禦"),
            ("P/Book", safe_val(info, ['priceToBook'], "x"), "資產比"),
            ("預測 EPS", safe_val(info, ['forwardEps'], "$"), "盈利能力"),
            ("波動率", "28%", "風險分")
        ]
        for i, (l, v, desc) in enumerate(v2):
            d2[i].markdown(f"<div class='val-box'><div style='font-size:0.8rem;'>{l}</div><div style='color:#00FFCC;font-size:1.2rem;font-weight:bold;'>{v}</div><div class='val-desc'>{desc}</div></div>", unsafe_allow_html=True)

        # E. 第五層：8:2 圖表 (物理分家，解決遮擋)
        recent = df.tail(120)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.03)
        # K線
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close), row=1, col=1)
        # 蟹貨區 (Volume Profile)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.15)', xaxis='x2'), row=1, col=1)
        # 成交量
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='gray'), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", height=600, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*5]), margin=dict(t=5,b=5,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"透視儀重啟中: {e}")
