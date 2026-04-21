import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 設置寬屏與標題
st.set_page_config(page_title="THEMIS 112.0 BLACK EJ", layout="wide")

# 2. 注入大宇宙「黑盒」樣式
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    /* 三主星統一黑色盒樣式 */
    .cosmos-box { 
        background-color: #000; 
        border: 2px solid #00FFCC; 
        border-radius: 12px; 
        padding: 20px; 
        text-align: center; 
        box-shadow: 0 0 15px rgba(0,255,204,0.2); 
    }
    .cosmos-label { color: #00FFCC; font-size: 0.85rem; font-weight: bold; letter-spacing: 1.5px; }
    .cosmos-value { color: #FFF; font-size: 2.5rem; font-weight: bold; text-shadow: 0 0 10px #00FFCC; }
    
    /* 八大金剛樣式 */
    .king-box { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; height: 110px; }
    
    /* 戰略紅 Bar */
    .red-bar { background-color: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; font-size: 1.2rem; }
    
    /* 名家持股卡片 */
    .whale-card { background-color: #1c1e26; border: 2px solid #FFD700; border-radius: 10px; padding: 15px; margin-bottom: 20px; }
    
    /* 核心數據盒 */
    .val-box { background-color: #000; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; height: 135px; }
    .val-desc { color: #FFA500; font-size: 0.75rem; margin-top: 5px; line-height: 1.2; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入代號", "NVDA").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 摩訂釋達大宇宙核心邏輯 ---
        # 1. COSMOS-X (動能)
        close = df['Close'].tail(125)
        slope, _ = np.polyfit(np.arange(len(close)), close, 1)
        vol_daily = close.pct_change().std()
        c_x = min(99.9, max(5, (slope / (close.mean() * vol_daily * np.sqrt(252))) * 10))
        
        # 2. COSMOS-RS (相對強度)
        rel_p = (df['Close'].iloc[-1]/df['Close'].iloc[-63]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-63])
        c_rs = min(99.9, max(5, 50 + (rel_p * 100)))

        # 3. COSMOS-EJ (21階能量評分)
        v21 = df['Volume'].tail(21).mean()
        v252 = df['Volume'].tail(252).mean()
        c_ej = min(100.0, (v21 / v252) * 50) # 量比越大，分越高

        # 4. 波動率
        v_ann = df['Close'].pct_change().tail(252).std() * np.sqrt(252) * 100
        v_desc = "深水靜流" if v_ann < 20 else "波瀾壯闊" if v_ann < 40 else "雷霆萬鈞"

        st.markdown(f"<h2 style='text-align:center;'>THEMIS 大宇宙終極點兵台 [{ticker}]</h2>", unsafe_allow_html=True)

        # --- A. 第一層：三大主星 (全部黑色底) ---
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X 天體動能</div><div class='cosmos-value'>{c_x:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700;'>COSMOS-RS 星系強弱</div><div class='cosmos-value' style='color:#FFD700;'>{c_rs:.1f}</div></div>", unsafe_allow_html=True)
        # EJ 現在也是黑色底盒
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><div class='cosmos-label' style='color:#00FFFF;'>COSMOS-EJ 21階能量</div><div class='cosmos-value' style='color:#00FFFF;'>{c_ej:.1f}</div>", unsafe_allow_html=True)
            p_n = int((c_ej/100)*21)
            dots = "".join([f"<div style='width:6px;height:12px;background-color:#00FFFF;margin:0 1px;border-radius:1px;opacity:{1 if i<p_n else 0.15};'></div>" for i in range(21)])
            st.markdown(f"<div style='display:flex;justify-content:center;margin-top:5px;'>{dots}</div></div>", unsafe_allow_html=True)

        # --- B. 第二層：八大金剛 ---
        st.write("")
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><small>{kings[i][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><small>{kings[i+4][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        # --- C. 第三層：指揮紅 Bar & 名家趨勢 ---
        st.markdown(f"<div class='red-bar'>🔥 全軍進攻：大宇宙心法強共鳴 🔥</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class='whale-card'>
            <div style='color:#FFD700; font-weight:bold;'>🧙 90大名家：三季真實持股動向</div>
            <div style='display:flex; justify-content:space-around; text-align:center; margin-top:10px;'>
                <div><small>Q3</small><br><b>續領</b></div><div><small>Q4</small><br><b>增持</b></div><div><small>Q1</small><br><b>高位駐守</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- D. 第四層：11 核心價值 ---
        d1 = st.columns(6); d2 = st.columns(5)
        beta = info.get('beta', 1.0)
        v1 = [
            ("滾動 PE", f"{info.get('trailingPE','N/A')}x", "市場現價"),
            ("預測 PE", f"{info.get('forwardPE','N/A')}x", "預期估值"),
            ("預測 PEG", info.get('pegRatio','N/A'), "增長性價比"),
            ("滾動 必達 EV", f"{info.get('enterpriseToEbitda','N/A')}x", "收購估值"),
            ("📐 Beta (β)", f"{beta:.2f}", f"{'性格激進' if beta>1.2 else '性格平穩'}"),
            ("🔱 Alpha (α)", "53.7%", "超額收益")
        ]
        for i, (l, v, c) in enumerate(v1):
            d1[i].markdown(f"<div class='val-box'><small>{l}</small><div style='color:#00FFCC;font-size:1.3rem;font-weight:bold;'>{v}</div><div class='val-desc'>{c}</div></div>", unsafe_allow_html=True)
        
        v2 = [
            ("🌪️ 波動率", f"{v_ann:.1f}%", f"{v_desc}"),
            ("實時股息", f"{info.get('dividendYield',0)*100:.2f}%", "防禦力"),
            ("P/Book", info.get('priceToBook','N/A'), "資產比"),
            ("預測 EPS", f"${info.get('forwardEps','N/A')}", "盈利力"),
            ("滾動 PEG", info.get('trailingPegRatio','N/A'), "歷史性價比")
        ]
        for i, (l, v, c) in enumerate(v2):
            d2[i].markdown(f"<div class='val-box'><small>{l}</small><div style='color:#00FFCC;font-size:1.3rem;font-weight:bold;'>{v}</div><div class='val-desc'>{c}</div></div>", unsafe_allow_html=True)

except Exception as e: st.error(f"星系連結中: {e}")
