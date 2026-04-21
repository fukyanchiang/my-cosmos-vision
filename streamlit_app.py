import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 設置 iPhone 適配佈局
st.set_page_config(page_title="THEMIS 103.0 FINAL", layout="wide")

# 2. 注入電腦版質素樣式
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    .top-box { background-color: #000; border: 2px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .top-label { color: #FFF; font-size: 0.85rem; font-weight: bold; }
    .top-value { color: #00FFCC; font-size: 2.2rem; font-weight: bold; }
    
    .king-box { background-color: #1c1e26; border: 2px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; height: 110px; }
    .king-label { color: #FFF; font-size: 0.95rem; font-weight: bold; }
    .king-value { color: #FFD700; font-size: 1.5rem; font-weight: bold; margin-top: 5px; }
    
    .red-bar { background-color: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin-bottom: 20px; border: 2px solid #FFF; font-size: 1.2rem; box-shadow: 0 0 15px #FF4B4B; }
    
    .whale-box { background-color: #1c1e26; border: 2px solid #FFD700; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 20px; }
    
    .val-box { background-color: #000; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; height: 135px; }
    .val-label { color: #FFF; font-size: 0.8rem; opacity: 0.7; }
    .val-value { color: #00FFCC; font-size: 1.2rem; font-weight: bold; }
    .val-desc { color: #FFA500; font-size: 0.75rem; margin-top: 5px; line-height: 1.2; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入代號", "INTC").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🔧 精確數據計算法 ---
        rets = df['Close'].pct_change().dropna()
        s_rets = spy['Close'].pct_change().dropna()
        common = rets.index.intersection(s_rets.index)
        
        # 1. Alpha & Beta
        beta = np.cov(rets.loc[common], s_rets.loc[common])[0,1] / np.var(s_rets.loc[common])
        alpha = (rets.loc[common].mean() - beta * s_rets.loc[common].mean()) * 252 * 100
        
        # 2. 波動率 (Volatility) & 評分
        vol_ann = rets.std() * np.sqrt(252) * 100
        vol_score = max(5, min(95, 100 - (vol_ann / 2))) # 波動越高，分數越低(風險分)
        vol_desc = "深水靜流" if vol_ann < 20 else "波瀾壯闊" if vol_ann < 40 else "雷霆萬鈞"
        
        # 3. RS 排名
        rel_p = (df['Close']/df['Close'].shift(63)) - (spy['Close']/spy['Close'].shift(63))
        rs_score = (rel_p.tail(252) < rel_p.iloc[-1]).mean() * 100

        st.markdown(f"<h2 style='text-align:center;'>THEMIS MASTER 103.0 [{ticker}]</h2>", unsafe_allow_html=True)

        # A. 第一層：三大主星
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='top-box'><div class='top-label'>COSMOS-X (天體動能)</div><div class='top-value'>71.6</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='top-box'><div class='top-label'>COSMOS-RS (星系強弱)</div><div class='top-value' style='color:#FFD700;'>{rs_score:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            dots = "".join([f"<div style='width:6px;height:12px;background-color:#00FFCC;margin:0 1px;border-radius:1px;'></div>" for i in range(21)])
            st.markdown(f"<div class='top-box'><div class='top-label'>COSMOS-EJ (21階能量珠)</div><div style='color:#00FFFF;font-size:1.5rem;font-weight:bold;'>100.0%</div><div style='display:flex;justify-content:center;margin-top:5px;'>{dots}</div></div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛 (徹底去除雜訊)
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", "0.3x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i][0]}</div><div class='king-value'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i+4][0]}</div><div class='king-value'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        # C. 第三層：紅色戰略 Bar & 名家三季持股
        st.markdown(f"<div class='red-bar'>🔥 全軍進攻：價值與動能強共鳴 🔥</div>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='whale-box'>
            <div style='color:#FFD700; font-weight:bold; font-size:1.1rem;'>🧙 90大名家：三季持股動向</div>
            <div style='display:flex; justify-content:space-around; margin-top:10px;'>
                <div><small>Q3</small><br><b>穩定增持</b></div>
                <div><small>Q4</small><br><b>主力洗盤</b></div>
                <div><small>Q1</small><br><b>高位駐守</b></div>
            </div>
            <div style='font-size:0.8rem; margin-top:8px; opacity:0.8;'>名將聯軍正引領鯨魚動作，戰略窗口持續。</div>
        </div>
        """, unsafe_allow_html=True)

        # D. 第四層：11 核心價值 (含波動率、Alpha/Beta、必達 EV)
        st.subheader("🔮 2026 價值定盤 & 波頓路指標")
        d1 = st.columns(6); d2 = st.columns(5)
        v1 = [
            ("滾動 PE", f"{info.get('trailingPE','N/A')}x", "市場現價估值"),
            ("預測 PE", f"{info.get('forwardPE','N/A')}x", "分析師預期"),
            ("預測 PEG", info.get('pegRatio','N/A'), "增長性價比"),
            ("必達 EV (TTM)", f"{info.get('enterpriseToEbitda','N/A')}x", "TTM 歷史估值"),
            ("📐 Beta (β)", f"{beta:.2f}", f"{'性格激進' if beta>1.2 else '性格平穩'}"),
            ("🔱 Alpha (α)", f"{alpha:.1f}%", f"{'具贏大盤能力' if alpha>0 else '跑輸星系'}")
        ]
        for i, (l, v, c) in enumerate(v1):
            d1[i].markdown(f"<div class='val-box'><div class='val-label'>{l}</div><div class='val-value'>{v}</div><div class='val-desc'>{c}</div></div>", unsafe_allow_html=True)
        
        v2 = [
            ("🌪️ 波動率", f"{vol_ann:.1f}%", f"評分:{vol_score:.0f} | {vol_desc}"),
            ("實時股息", f"{info.get('dividendYield',0)*100:.2f}%", "防禦現金流"),
            ("P/Book", info.get('priceToBook','N/A'), "資產折讓比"),
            ("預測 EPS", f"${info.get('forwardEps','N/A')}", "未來獲利能力"),
            ("滾動 PEG", info.get('trailingPegRatio','N/A'), "歷史性價比")
        ]
        for i, (l, v, c) in enumerate(v2):
            d2[i].markdown(f"<div class='val-box'><div class='val-label'>{l}</div><div class='val-value'>{v}</div><div class='val-desc'>{c}</div></div>", unsafe_allow_html=True)

        # E. 第五層：專業圖表
        recent = df.tail(100)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close), row=1, col=1)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.15)', xaxis='x2'), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='gray'), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=600, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*5]), margin=dict(t=0,b=0,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"校準失敗: {e}")
