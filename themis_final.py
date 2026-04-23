import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 核心量化引擎 (真實數據)
# ==========================================
st.set_page_config(page_title="COSMOS 終極靈魂終端", layout="wide")

def calculate_real_logic(df, spy_df):
    try:
        h, m = df['Close'].align(spy_df['Close'], join='inner')
        ret, m_ret = h.pct_change().dropna().tail(60), m.pct_change().dropna().tail(60)
        rebel = ((ret[m_ret < 0] > m_ret[m_ret < 0]).mean() - 0.4) * 166.6
        dna = round(max(0, min(100, rebel * 0.6 + 40)), 1)
        rs = round(50 + ((h.iloc[-1]/h.iloc[-63]) - (m.iloc[-1]/m.iloc[-63])) * 100, 1)
        y = h.tail(125).values; x = np.arange(len(y))
        slope, _ = np.polyfit(x, y, 1)
        cx = round(50 + (slope * 252 / y.mean() / (h.pct_change().std() * np.sqrt(252))) * 10, 1)
        return dna, rs, cx
    except: return 50.0, 50.0, 50.0

def get_real_8d_scores(info):
    def s(v, l):
        if v is None: return 5
        for threshold, score in l:
            if v >= threshold: return score
        return 1
    return {
        "🩸 血液 (利潤Margins)": s(info.get('operatingMargins'), [(0.2, 10), (0.1, 8), (0, 4)]),
        "🛡️ 免疫 (核心ROE)": s(info.get('returnOnEquity'), [(0.15, 10), (0.08, 7), (0, 3)]),
        "🏗️ 心跳 (營收增長)": s(info.get('revenueGrowth'), [(0.2, 10), (0.1, 7), (0, 4)]),
        "🧬 大腦 (淨利潛力)": s(info.get('profitMargins'), [(0.15, 10), (0.05, 7), (0, 4)]),
        "🧱 骨架 (PB估值)": s(info.get('priceToBook'), [(1.0, 10), (3.0, 6), (10.0, 2)]),
        "⚡ 物理 (資產負債)": 8 if (info.get('debtToEquity', 100) or 100) < 80 else 4,
        "💰 資本 (股息派息)": s(info.get('dividendYield'), [(0.04, 10), (0.02, 7), (0, 3)]),
        "📈 經營 (EPS拐點)": s(info.get('earningsGrowth'), [(0.2, 10), (0.1, 7), (0, 4)])
    }

# ==========================================
# 2. 視覺裝修 (CSS 復刻)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    .cosmos-box { background-color: #000 !important; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 0 15px #00FFCC44; }
    .cosmos-box-gold { border-color: #FFD700; box-shadow: 0 0 15px #FFD70044; }
    .cosmos-box-red { border-color: #FF4B4B; box-shadow: 0 0 15px #FF4B4B44; }
    .val-box-purple { border: 2px solid #BC13FE; border-radius: 15px; padding: 25px; background-color: #000; box-shadow: 0 0 20px #BC13FE66; margin-bottom: 25px; }
    .energy-bar-container { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 10px; }
    .energy-seg { flex: 1; height: 14px; border-radius: 2px; }
    .strat-bar { background: #FF4B4B; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 1.3rem; margin: 25px 0; color: white; }
    .label { color: #00FFCC; font-size: 0.9rem; font-weight: 700; text-transform: uppercase; }
    .label-gold { color: #FFD700; }
    .value { color: #FFFFFF; font-size: 2.5rem; font-weight: 900; }
    .holder-name-cn { color: #FFD700; font-size: 2.5rem; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

ticker = st.sidebar.text_input("🚀 代號", "6869.HK").upper()
manual_target = st.sidebar.number_input("🔮 手動目標價", value=0.0)

try:
    asset = yf.Ticker(ticker); info = asset.info
    df = asset.history(period="2y").dropna()
    spy = yf.Ticker("SPY").history(period="2y").dropna()
    
    if not df.empty:
        curr = df['Close'].iloc[-1]
        dna, rs, cx = calculate_real_logic(df, spy)
        scores_8d = get_real_8d_scores(info)
        cej = (df['Volume'].tail(21).mean() / (df['Volume'].tail(252).mean() + 1e-9)) * 100
        energy_score = 50 + (((curr / df['Close'].iloc[-5]) - 1) * 1200)

        # --- 第一部分：三大核心 (圖 1 復刻) ---
        c1, c2, c3 = st.columns([1, 1, 1.2])
        c1.markdown(f"<div class='cosmos-box'><div class='label'>COSMOS-X (天體動能)</div><div class='value'>{cx}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box cosmos-box-gold'><div class='label label-gold'>COSMOS-RS (星系強弱)</div><div class='value'>{rs}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<b>EJ 錢流底氣: {cej:.1f}%</b>", unsafe_allow_html=True)
            st.markdown('<div class="energy-bar-container">' + "".join([f'<div class="energy-seg" style="background-color:{"#00FFCC" if j<=8 else "#333"}; opacity:{"1" if j<=8 else "0.2"};"></div>' for j in range(1,13)]) + '</div>', unsafe_allow_html=True)
            st.markdown(f"<b>短期能量 BAR: {energy_score:.1f}%</b>", unsafe_allow_html=True)
            st.markdown('<div class="energy-bar-container">' + "".join([f'<div class="energy-seg" style="background-color:{"#BC13FE" if j<=10 else "#333"};"></div>' for j in range(1,13)]) + '</div>', unsafe_allow_html=True)

        # --- 第二部分：紅色戰略 Bar (圖 2 頂部復刻) ---
        st.markdown(f"<div class='strat-bar'>🔥 戰略透視：短期動能爆發數值 [{energy_score:.1f}%] 🔥</div>", unsafe_allow_html=True)

        # --- 第三部分：估值與風險九大格 (圖 2 復刻) ---
        st.write("### 🏛️ 估值與風險全方位透視")
        v_cols = st.columns(3)
        v_metrics = [
            ("PE 獲利比", f"TTM: {info.get('trailingPE',0):.2f}x\n2026預準: {info.get('forwardPE',0):.2f}x"),
            ("PEG 增長比", f"TTM: {info.get('pegRatio',0):.2f}\n2026預準: N/A"),
            ("PS 營收比", f"TTM: {info.get('priceToSalesTrailing12Months',0):.2f}x\n營收規模: {info.get('totalRevenue',0)/1e9:.1f}B"),
            ("PB 淨資產", f"TTM: {info.get('priceToBook',0):.2f}x\n賬面價值"),
            ("EV/EBITDA", f"TTM: {info.get('enterpriseToEbitda',0):.2f}x\n企業估值"),
            ("股息率", f"TTM: {info.get('dividendYield',0)*100:.2f}%\n現金流回報"),
            ("Beta (性格)", f"{info.get('beta',0):.2f}\n市場同步率"),
            ("Alpha (超額)", "N/A\n贏過大盤之能力"),
            ("波動率 (情緒)", f"{df['Close'].pct_change().std()*np.sqrt(252)*100:.1f}%\n年化震盪頻率")
        ]
        for i, (l, v) in enumerate(v_metrics):
            v_cols[i%3].markdown(f"<div class='cosmos-box' style='height:150px; margin-bottom:10px;'><div class='label'>{l}</div><div style='font-size:1.1rem; font-weight:700;'>{v.splitlines()[0]}</div><div style='font-size:0.7rem; opacity:0.6;'>{v.splitlines()[1]}</div></div>", unsafe_allow_html=True)

        # --- 第四部分：專業 K 線與左側蟹貨區 (圖 3 復刻) ---
        st.write("### 🕯️ 專業 K 線與蟹貨區 (Visible Range Volume Profile)")
        fig = make_subplots(rows=2, cols=2, column_widths=[0.15, 0.85], row_heights=[0.7, 0.3], shared_yaxes=True, horizontal_spacing=0.02, vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=2)
        counts, bins = np.histogram(df['Close'], bins=50, weights=df['Volume'])
        fig.add_trace(go.Bar(x=counts, y=bins[:-1], orientation='h', marker_color='rgba(0, 255, 204, 0.3)'), row=1, col=1)
        v_colors = ['#00FFCC' if r['Open'] < r['Close'] else '#FF4B4B' for _, r in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=v_colors), row=2, col=2)
        fig.update_layout(height=700, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # --- 第五部分：紫色估值解碼 & DNA & 8D Bar (新組件大融合) ---
        st.write("---")
        st.markdown(f"""<div class='val-box-purple'><div style='display:flex; justify-content:space-between;'><div><span style='font-size:1.8
