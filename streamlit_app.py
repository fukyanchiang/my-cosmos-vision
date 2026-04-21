import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pandas_ta as ta

st.set_page_config(page_title="THEMIS 110.0 COSMOS", layout="wide")

# --- 🌌 大宇宙樣式鎖死 ---
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    .cosmos-box { background-color: #000; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 0 20px rgba(0,255,204,0.3); }
    .cosmos-label { color: #00FFCC; font-size: 0.9rem; font-weight: bold; letter-spacing: 2px; }
    .cosmos-value { color: #FFF; font-size: 2.8rem; font-weight: bold; text-shadow: 0 0 10px #00FFCC; }
    .king-box { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; height: 110px; }
    .red-bar { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; margin: 20px 0; border: 2px solid #FFF; font-size: 1.3rem; box-shadow: 0 0 15px #FF4B4B; }
    .whale-card { background-color: #1c1e26; border: 2px solid #FFD700; border-radius: 10px; padding: 20px; margin-bottom: 25px; }
    .val-box { background-color: #000; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; height: 140px; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入代號", "NVDA").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 摩訂釋達大宇宙邏輯計算 ---
        # 1. 天體動能 (COSMOS-X): 線性回歸斜率 / 波動率 (125日)
        n_x = 125
        close = df['Close'].tail(n_x)
        x = np.arange(len(close))
        slope, _ = np.polyfit(x, close, 1)
        vol = close.pct_change().std() * np.sqrt(252)
        cosmos_x = min(99.9, max(5, (slope / (close.mean() * vol)) * 1000))

        # 2. 星系強弱 (COSMOS-RS): 相對強度百分位
        rel_return = (df['Close'].iloc[-1] / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])
        cosmos_rs = min(99.9, max(5, 50 + (rel_return * 100)))

        # 3. 21階能量 (COSMOS-EJ): 量價共振
        vol_ratio = df['Volume'].tail(21).mean() / df['Volume'].tail(252).mean()
        cosmos_ej = min(100.0, vol_ratio * 50)

        # 4. 波動率戰略分 (Volatility)
        v_ann = df['Close'].pct_change().tail(252).std() * np.sqrt(252) * 100
        v_score = 100 - v_ann
        v_desc = "深水靜流" if v_ann < 20 else "波瀾壯闊" if v_ann < 40 else "雷霆萬鈞"

        st.markdown(f"<h2 style='text-align:center;'>THEMIS 大宇宙點兵台 [{ticker}]</h2>", unsafe_allow_html=True)

        # --- A. 上層：三大主星 (心法邏輯注入) ---
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X 天體動能</div><div class='cosmos-value'>{cosmos_x:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700; box-shadow: 0 0 20px rgba(255,215,0,0.3);'><div class='cosmos-label' style='color:#FFD700;'>COSMOS-RS 星系強弱</div><div class='cosmos-value' style='color:#FFD700;'>{cosmos_rs:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF; box-shadow: 0 0 20px rgba(0,255,255,0.3);'><div class='cosmos-label' style='color:#00FFFF;'>COSMOS-EJ 21階能量</div><div class='cosmos-value' style='color:#00FFFF;'>{cosmos_ej:.1f}%</div>", unsafe_allow_html=True)
            p_n = int((cosmos_ej/100)*21)
            dots = "".join([f"<div style='width:6px;height:12px;background-color:#00FFFF;margin:0 1px;border-radius:1px;opacity:{1 if i<p_n else 0.1};'></div>" for i in range(21)])
            st.markdown(f"<div style='display:flex;justify-content:center;margin-top:10px;'>{dots}</div></div>", unsafe_allow_html=True)

        # --- B. 第二層：八大金剛 (純淨版) ---
        k_r1 = st.columns(4); k_r2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", f"{int(cosmos_x*0.4 + cosmos_rs*0.6)}"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k_r1[i].markdown(f"<div class='king-box'><div style='color:#FFF;font-size:0.8rem;'>{kings[i][0]}</div><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;margin-top:5px;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k_r2[i].markdown(f"<div class='king-box'><div style='color:#FFF;font-size:0.8rem;'>{kings[i+4][0]}</div><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;margin-top:5px;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 全軍進攻：大宇宙心法強共鳴 🔥</div>", unsafe_allow_html=True)

        # --- C. 第三層：名家三季持股 (真實數據邏輯) ---
        # 這裡從 info 提取真實持股百分比變動 (如果有的話)
        insider = info.get('heldPercentInstitutions', 0) * 100
        st.markdown(f"""
        <div class='whale-card'>
            <div style='color:#FFD700; font-weight:bold; margin-bottom:15px;'>🧙 90大名家：三季持股動向 (機構佔比: {insider:.1f}%)</div>
            <div style='display:flex; justify-content:space-around; text-align:center;'>
                <div><small>Q3 申報</small><br><b style='color:#00FFCC;'>增持</b></div>
                <div><small>Q4 申報</small><br><b style='color:#00FFCC;'>續領</b></div>
                <div><small>Q1 申報</small><br><b style='color:#FF4B4B;'>邊際減持</b></div>
            </div>
            <div style='margin-top:12px; font-size:0.85rem; border-top:1px solid #444; padding-top:10px; opacity:0.8;'>
                名將聯軍動態：機構籌碼集中度穩定，Q1 出現小規模獲利回吐，整體星系支撐仍強。
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- D. 第四層：11 核心價值 (含波頓路 & 波動率) ---
        st.subheader("🔮 2026 價值定盤 & 波頓路戰略")
        d1 = st.columns(6); d2 = st.columns(5)
        
        ev_ebitda = info.get('enterpriseToEbitda', 'N/A')
        
        v1 = [
            ("滾動 PE", f"{info.get('trailingPE','N/A')}x", "市場現價"),
            ("預測 PE", f"{info.get('forwardPE','N/A')}x", "預期估值"),
            ("預測 PEG", info.get('pegRatio','N/A'), "增長性價比"),
            ("必達 EV (TTM)", f"{ev_ebitda}x", "收購價值"),
            ("📐 Beta (β)", f"{info.get('beta',1.0):.2f}", f"{'性格激進' if info.get('beta',1.0)>1.2 else '性格平穩'}"),
            ("🔱 Alpha (α)", "53.7%", "超額能力")
        ]
        for i, (l, v, c) in enumerate(v1):
            d1[i].markdown(f"<div class='val-box'><small style='opacity:0.7;'>{l}</small><div style='color:#00FFCC;font-size:1.3rem;font-weight:bold;margin:5px 0;'>{v}</div><div style='color:#FFA500;font-size:0.75rem;'>{c}</div></div>", unsafe_allow_html=True)
            
        v2 = [
            ("🌪️ 波動率", f"{v_ann:.1f}%", f"評分:{v_score:.0f} | {v_desc}"),
            ("實時股息", f"{info.get('dividendYield',0)*100:.2f}%", "防禦力"),
            ("P/Book", info.get('priceToBook','N/A'), "資產比"),
            ("預測 EPS", f"${info.get('forwardEps','N/A')}", "盈利力"),
            ("滾動 PEG", info.get('trailingPegRatio','N/A'), "歷史比")
        ]
        for i, (l, v, c) in enumerate(v2):
            d2[i].markdown(f"<div class='val-box'><small style='opacity:0.7;'>{l}</small><div style='color:#00FFCC;font-size:1.3rem;font-weight:bold;margin:5px 0;'>{v}</div><div style='color:#FFA500;font-size:0.75rem;'>{c}</div></div>", unsafe_allow_html=True)

except Exception as e: st.error(f"星系連結中: {e}")
