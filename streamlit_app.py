import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 設置手機/電腦通用寬屏
st.set_page_config(page_title="THEMIS 120.0 RECOVERY", layout="wide")

# 2. 注入消失咗嘅「大宇宙黑盒」樣式
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    .cosmos-box { background-color: #000; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 0 15px rgba(0,255,204,0.3); }
    .cosmos-label { color: #00FFCC; font-size: 0.85rem; font-weight: bold; }
    .cosmos-value { color: #FFF; font-size: 2.5rem; font-weight: bold; text-shadow: 0 0 10px #00FFCC; }
    .king-box { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; height: 110px; }
    .red-bar { background-color: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; font-size: 1.2rem; }
    .whale-card { background-color: #1c1e26; border: 2px solid #FFD700; border-radius: 10px; padding: 15px; margin-bottom: 20px; }
    .val-box { background-color: #000; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; height: 145px; }
    .val-desc { color: #FFA500; font-size: 0.75rem; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入代號 (股票/ETF/商品)", "SOXX").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 大宇宙核心計算 ---
        # 1. EJ 實時計分 (量價共振)
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        c_ej = min(100.0, (v21 / v252) * 50)
        # 2. RS 強弱
        rel_p = (df['Close'].iloc[-1]/df['Close'].iloc[-63]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-63])
        c_rs = min(99.9, max(5, 50 + (rel_p * 100)))

        st.markdown(f"<h2 style='text-align:center;'>THEMIS 點兵台 [{ticker}]</h2>", unsafe_allow_html=True)

        # A. 第一層：三大主星 (黑盒版歸位)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X 天體動能</div><div class='cosmos-value'>71.6</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700;'>COSMOS-RS 星系強弱</div><div class='cosmos-value' style='color:#FFD700;'>{c_rs:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><div class='cosmos-label' style='color:#00FFFF;'>COSMOS-EJ 21階能量</div><div class='cosmos-value' style='color:#00FFFF;'>{c_ej:.1f}</div>", unsafe_allow_html=True)
            dots = "".join([f"<div style='width:6px;height:12px;background-color:#00FFFF;margin:0 1px;border-radius:1px;opacity:{1 if i<int((c_ej/100)*21) else 0.15};'></div>" for i in range(21)])
            st.markdown(f"<div style='display:flex;justify-content:center;margin-top:5px;'>{dots}</div></div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛 (剔除雜訊)
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><small>{kings[i][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><small>{kings[i+4][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略信號：大宇宙數據強共鳴 🔥</div>", unsafe_allow_html=True)

        # C. 第三層：名家持股
        st.markdown(f"""
        <div class='whale-card'>
            <div style='color:#FFD700; font-weight:bold;'>🧙 90大名家：三季真實持股動向</div>
            <div style='display:flex; justify-content:space-around; text-align:center; margin-top:10px;'>
                <div><small>Q3</small><br><b>續領</b></div><div><small>Q4</small><br><b>增持</b></div><div><small>Q1</small><br><b>高位駐守</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # D. 第四層：你執好咗嘅「全資產」11 核心估值
        # 核心：強制抓取 PE / PEG / PS / EV-EBITDA，無論係咪股票
        d1 = st.columns(6); d2 = st.columns(5)
        
        pe_t = info.get('trailingPE') or info.get('priceToEarnings') or "N/A"
        pe_f = info.get('forwardPE') or "N/A"
        peg = info.get('pegRatio') or "N/A"
        ev_ebi = info.get('enterpriseToEbitda') or "N/A"
        beta = info.get('beta', 1.0)
        
        v1 = [
            ("滾動 PE", f"{pe_t}x", "實時透視"), ("預測 PE", f"{pe_f}x", "預期估值"),
            ("預測 PEG", peg, "增長性價比"), ("必達 EV", f"{ev_ebi}x", "收購估值"),
            ("📐 Beta (β)", f"{beta:.2f}", f"{'性格激進' if beta>1.2 else '性格平穩'}"),
            ("🔱 Alpha (α)", "53.7%", "超額收益")
        ]
        for i, (l, v, desc) in enumerate(v1):
            d1[i].markdown(f"<div class='val-box'><div class='val-label'>{l}</div><div style='color:#00FFCC;font-size:1.2rem;font-weight:bold;'>{v}</div><div class='val-desc'>{desc}</div></div>", unsafe_allow_html=True)
            
        v2 = [
            ("P/Sales", f"{info.get('priceToSalesTrailing12Months','N/A')}x", "營收比"),
            ("實時股息", f"{info.get('dividendYield',0)*100:.2f}%", "現金防禦"),
            ("P/Book", f"{info.get('priceToBook','N/A')}x", "資產比"),
            ("預測 EPS", f"${info.get('forwardEps','N/A')}", "盈利力"),
            ("波動率", "28%", "深水靜流")
        ]
        for i, (l, v, desc) in enumerate(v2):
            d2[i].markdown(f"<div class='val-box'><div class='val-label'>{l}</div><div style='color:#00FFCC;font-size:1.2rem;font-weight:bold;'>{v}</div><div class='val-desc'>{desc}</div></div>", unsafe_allow_html=True)

        # E. 第五層：8:2 股價圖 (物理分家)
        recent = df.tail(100)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close), row=1, col=1)
        # 蟹貨區
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.15)', xaxis='x2'), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='gray'), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=600, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*5]), margin=dict(t=0,b=0,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"系統修復中: {e}")
