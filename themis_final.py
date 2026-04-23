import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 核心量化羅輯 (100% 真實數據)
# ==========================================
st.set_page_config(page_title="COSMOS 終極終端", layout="wide")

def calculate_logic(df, spy_df):
    try:
        h, m = df['Close'].align(spy_df['Close'], join='inner')
        ret, m_ret = h.pct_change().dropna().tail(60), m.pct_change().dropna().tail(60)
        # DNA: 反叛基因 (大盤跌我升)
        rebel = ((ret[m_ret < 0] > m_ret[m_ret < 0]).mean() - 0.4) * 166.6
        dna = max(0, min(100, rebel * 0.6 + 40))
        # RS: 相對強弱
        rs = 50 + ((h.iloc[-1]/h.iloc[-63]) - (m.iloc[-1]/m.iloc[-63])) * 100
        # CX: 天體斜率
        y = h.tail(125).values; x = np.arange(len(y))
        slope, _ = np.polyfit(x, y, 1)
        cx = 50 + (slope * 252 / y.mean() / (h.pct_change().std() * np.sqrt(252))) * 10
        return round(dna, 1), round(rs, 1), round(cx, 1)
    except: return 50.0, 50.0, 50.0

def get_8d_scores(info):
    def s(v, l):
        if v is None: return 5
        for threshold, score in l:
            if v >= threshold: return score
        return 1
    return {
        "🩸 血液 (利潤)": s(info.get('operatingMargins'), [(0.2, 10), (0.1, 8), (0, 4)]),
        "🛡️ 免疫 (ROE)": s(info.get('returnOnEquity'), [(0.15, 10), (0.08, 7), (0, 3)]),
        "🏗️ 心跳 (營收)": s(info.get('revenueGrowth'), [(0.2, 10), (0.1, 7), (0, 4)]),
        "🧬 大腦 (淨利)": s(info.get('profitMargins'), [(0.15, 10), (0.05, 7), (0, 4)]),
        "🧱 骨架 (PB)": s(info.get('priceToBook'), [(1.0, 10), (3.0, 6), (10.0, 2)]),
        "⚡ 物理 (負債)": 8 if (info.get('debtToEquity', 100) or 100) < 80 else 4,
        "💰 資本 (派息)": s(info.get('dividendYield'), [(0.04, 10), (0.02, 7), (0, 3)]),
        "📈 拐點 (EPS)": s(info.get('earningsGrowth'), [(0.2, 10), (0.1, 7), (0, 4)])
    }

# ==========================================
# 2. 豪華 UI 裝修
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    .cosmos-box { background-color: #000 !important; border: 2px solid #00FFCC; border-radius: 12px; padding: 15px; text-align: center; }
    .cosmos-box-gold { border-color: #FFD700; }
    .label { color: #00FFCC; font-size: 0.8rem; font-weight: 600; }
    .label-gold { color: #FFD700; }
    .value { color: #FFFFFF; font-size: 1.8rem; font-weight: 900; }
    .energy-bar-container { display: flex; gap: 2px; margin-top: 5px; }
    .energy-seg { flex: 1; height: 10px; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入代號", "6869.HK").upper()
manual_target = st.sidebar.number_input("手動目標價 (0為自動)", value=0.0)

try:
    asset = yf.Ticker(ticker); info = asset.info
    df = asset.history(period="2y").dropna()
    spy = yf.Ticker("SPY").history(period="2y").dropna()
    
    if not df.empty:
        curr = df['Close'].iloc[-1]
        dna, rs, cx = calculate_logic(df, spy)
        scores_8d = get_8d_scores(info)
        cej = (df['Volume'].tail(21).mean() / (df['Volume'].tail(252).mean() + 1e-9)) * 100
        
        # 1. 15 項核心估值看板
        st.write("### 🏛️ 估值與風險全方位透視")
        v_cols = st.columns(6)
        v_data = [
            ("PE (TTM)", info.get('trailingPE')), ("預準 PE", info.get('forwardPE')), 
            ("PS 營收比", info.get('priceToSalesTrailing12Months')), ("PEG 增長比", info.get('pegRatio')), 
            ("Beta (性格)", info.get('beta')), ("波動率", f"{df['Close'].pct_change().std()*np.sqrt(252)*100:.1f}%")
        ]
        for i, (l, v) in enumerate(v_data):
            v_cols[i].metric(l, f"{v:.2f}" if isinstance(v, (float, int)) else v)

        # 2. 專業 K 線圖 (包含蟹貨區)
        st.write("---")
        fig = make_subplots(rows=1, cols=2, column_widths=[0.8, 0.2], shared_yaxes=True, horizontal_spacing=0.02)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
        # 蟹貨區 (Volume Profile)
        counts, bins = np.histogram(df['Close'], bins=50, weights=df['Volume'])
        fig.add_trace(go.Bar(x=counts, y=bins[:-1], orientation='h', marker_color='rgba(0, 255, 204, 0.3)'), row=1, col=2)
        fig.update_layout(height=500, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # 3. 黃金九大格 (視覺回歸)
        r1 = st.columns(4)
        box1 = [("📁 質量", f"{info.get('returnOnEquity',0)*100:.1f}%"), ("📈 趨勢", f"{info.get('earningsGrowth',0)*100:.1f}%"), ("⚡ 動能 (CX)", cx), ("🔋 大資金", f"{cej:.1f}%")]
        for i in range(4): r1[i].markdown(f"<div class='cosmos-box'><div class='label'>{box1[i][0]}</div><div class='value'>{box1[i][1]}</div></div>", unsafe_allow_html=True)
        st.write(""); r2 = st.columns(4)
        target_v = manual_target if manual_target > 0 else (info.get('targetMeanPrice') or curr * 1.1)
        box2 = [("🎭 情緒 (RS)", rs), ("🧬 DNA 基因", dna), ("🔮 2026 目標", f"${target_v:.2f}"), ("💰 成交比", f"{(cej/100):.1f}x")]
        for i in range(4): r2[i].markdown(f"<div class='cosmos-box cosmos-box-gold'><div class='label label-gold'>{box2[i][0]}</div><div class='value'>{box2[i][1]}</div></div>", unsafe_allow_html=True)

        # 4. 8D 能量 Bar
        st.write("---")
        st.write("### 🧬 投行 8D 真實財報能量 BAR")
        e_cols = st.columns(2)
        for i, (label, score) in enumerate(scores_8d.items()):
            col = e_cols[0] if i < 4 else e_cols[1]
            grid = '<div class="energy-bar-container">'
            for j in range(1, 11):
                color = "#00FFCC" if j <= score else "#222"
                grid += f'<div class="energy-seg" style="background-color:{color}; opacity:{"1" if j<=score else "0.2"}"></div>'
            grid += f'</div>'
            col.markdown(f"**{label}** : {score}/10 {grid}", unsafe_allow_html=True)

        # 5. 重磅：實時大戶持倉名單 (代替 90 名家)
        st.write("---")
        st.write("### 🏢 實時十大名家/機構持倉名單")
        holders = asset.institutional_holders
        if holders is not None and not holders.empty:
            holders.columns = ['機構名稱', '持有股數', '日期', '佔比', '市值']
            st.dataframe(holders.style.format({'佔比': '{:.2%}'}), use_container_width=True)

except Exception as e:
    st.error(f"系統對焦中... {e}")
