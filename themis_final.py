import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 核心引擎 (100% 真實金融羅輯)
# ==========================================
st.set_page_config(page_title="COSMOS 終極全方位終端", layout="wide")

def calculate_quant_metrics(df, spy_df):
    try:
        h_aligned, m_aligned = df['Close'].align(spy_df['Close'], join='inner')
        stock_ret = h_aligned.pct_change().dropna().tail(60)
        market_ret = m_aligned.pct_change().dropna().tail(60)
        # DNA 基因
        rebel = ((stock_ret[market_ret < 0] > market_ret[market_ret < 0]).mean() - 0.4) * 166.6
        dna = max(0, min(100, rebel * 0.6 + 50))
        # RS 相對強弱
        rs = 50 + ((h_aligned.iloc[-1]/h_aligned.iloc[-63]) - (m_aligned.iloc[-1]/m_aligned.iloc[-63])) * 100
        # CX 斜率
        y = df['Close'].tail(125).values; x = np.arange(len(y))
        slope, _ = np.polyfit(x, y, 1)
        cx = 50 + (slope * 252 / y.mean() / (df['Close'].pct_change().std() * np.sqrt(252))) * 10
        return dna, rs, cx
    except: return 50.0, 50.0, 50.0

def get_real_8d_scores(info):
    def s_h(v, lims):
        if v is None: return 5
        for l, s in lims:
            if v >= l: return s
        return 1
    return {
        "🩸 血液純度 (利潤)": s_h(info.get('operatingMargins'), [(0.2, 10), (0.1, 8), (0, 4)]),
        "🛡️ 免疫系統 (ROE)": s_h(info.get('returnOnEquity'), [(0.15, 10), (0.08, 7), (0, 3)]),
        "🏗️ 心跳頻率 (營收)": s_h(info.get('revenueGrowth'), [(0.2, 10), (0.1, 7), (0, 4)]),
        "🧬 大腦潛力 (淨利)": s_h(info.get('profitMargins'), [(0.15, 10), (0.05, 7), (0, 4)]),
        "🧱 骨架重量 (PB)": s_h(info.get('priceToBook'), [(1.0, 10), (3.0, 6), (10.0, 2)]),
        "⚡ 物理底盤 (負債)": 8 if (info.get('debtToEquity', 100) or 100) < 80 else 4,
        "💰 資本配置 (派息)": s_h(info.get('dividendYield'), [(0.04, 10), (0.02, 7), (0, 3)]),
        "📈 經營拐點 (EPS)": s_h(info.get('earningsGrowth'), [(0.2, 10), (0.1, 7), (0, 4)])
    }

# ==========================================
# 2. 豪華視覺裝修 (CSS)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 2.8rem; font-weight: 900; margin-bottom: 20px; }
    .cosmos-box { background-color: #000 !important; border: 2px solid #00FFCC; border-radius: 15px; padding: 15px; text-align: center; height: 110px; }
    .cosmos-box-gold { border-color: #FFD700; }
    .label { color: #00FFCC; font-size: 0.85rem; font-weight: 600; }
    .label-gold { color: #FFD700; }
    .value { color: #FFFFFF; font-size: 1.8rem; font-weight: 900; margin-top: 5px; }
    .energy-bar-container { display: flex; gap: 3px; margin-top: 5px; }
    .energy-seg { flex: 1; height: 12px; border-radius: 2px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 實戰操作
# ==========================================
ticker = st.sidebar.text_input("輸入代號", "6869.HK").upper()
manual_target = st.sidebar.number_input("手動目標價 (0為自動)", value=0.0)

try:
    asset = yf.Ticker(ticker); info = asset.info
    df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
    spy = yf.Ticker("SPY").history(period="2y").dropna()
    
    if not df.empty:
        curr = df['Close'].iloc[-1]
        dna, rs, cx = calculate_quant_metrics(df, spy)
        cej = (df['Volume'].tail(21).mean() / (df['Volume'].tail(252).mean() + 1e-9)) * 100
        scores_8d = get_real_8d_scores(info)
        
        st.markdown(f"<div class='main-title'>🏛️ {info.get('longName', ticker)} 全方位透視</div>", unsafe_allow_html=True)
        
        # --- A. 黃金九大格 (視覺回歸) ---
        k1, k2, k3, k4 = st.columns(4)
        targets = [
            ("📁 質量 (ROE)", f"{info.get('returnOnEquity', 0)*100:.1f}%", False),
            ("📈 趨勢 (增長)", f"{info.get('earningsGrowth', 0)*100:.1f}%", False),
            ("⚡ 天體動能", f"{cx:.1f}", False),
            ("🔋 大資金 (CEJ)", f"{cej:.1f}%", False)
        ]
        for i, (l, v, g) in enumerate(targets):
            k1, k2, k3, k4 = st.columns(4) if i==0 else (None,None,None,None) # Simplified for brevity
        
        # 真正排橫 (重新排列佈局)
        row1 = st.columns(4)
        box_data = [
            ("📁 質量", f"{info.get('returnOnEquity', 0)*100:.1f}%", False),
            ("📈 趨勢", f"{info.get('earningsGrowth', 0)*100:.1f}%", False),
            ("⚡ 動能", f"{cx:.1f}", False),
            ("🔋 大資金", f"{cej:.1f}%", False)
        ]
        for i in range(4):
            row1[i].markdown(f"<div class='cosmos-box'><div class='label'>{box_data[i][0]}</div><div class='value'>{box_data[i][1]}</div></div>", unsafe_allow_html=True)
        
        st.write("")
        row2 = st.columns(4)
        target_v = manual_target if manual_target > 0 else (info.get('targetMeanPrice') or curr * 1.1)
        box_data2 = [
            ("🎭 情緒 (RS)", f"{rs:.1f}", True),
            ("🧬 DNA 基因", f"{dna:.1f}", True),
            ("🔮 明年目標", f"${target_v:.2f}", True),
            ("💰 成交比", f"{(cej/100):.1f}x", True)
        ]
        for i in range(4):
            row2[i].markdown(f"<div class='cosmos-box cosmos-box-gold'><div class='label label-gold'>{box_data2[i][0]}</div><div class='value'>{box_data2[i][1]}</div></div>", unsafe_allow_html=True)

        # --- B. 專業股價圖與蟹貨區 ---
        st.write("---")
        fig = make_subplots(rows=1, cols=2, column_widths=[0.8, 0.2], shared_yaxes=True, horizontal_spacing=0.02)
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=1)
        counts, bins = np.histogram(df['Close'], bins=50, weights=df['Volume'])
        fig.add_trace(go.Bar(x=counts, y=bins[:-1], orientation='h', marker_color='rgba(0, 255, 204, 0.3)'), row=1, col=2)
        fig.update_layout(height=500, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # --- C. 15項詳細數據 ---
        st.write("### 📜 估值與風險細節 (全實數)")
        d1, d2, d3, d4 = st.columns(4)
        d1.write(f"**PE:** {info.get('trailingPE', 'N/A')}")
        d1.write(f"**PEG:** {info.get('pegRatio', 'N/A')}")
        d2.write(f"**PS:** {info.get('priceToSalesTrailing12Months', 'N/A')}")
        d2.write(f"**PB:** {info.get('priceToBook', 'N/A')}")
        d3.write(f"**EV/EBITDA:** {info.get('enterpriseToEbitda', 'N/A')}")
        d3.write(f"**Beta:** {info.get('beta', 'N/A')}")
        d4.write(f"**股息:** {info.get('dividendYield', 0)*100:.2f}%")
        d4.write(f"**市值:** {info.get('marketCap', 0)/1e9:.1f}B")

        # --- D. 8D 能量 Bar (視覺恢復) ---
        st.write("---")
        st.write("### 🧬 投行 8D 真實財報能量檢測")
        for label, score in scores_8d.items():
            grid = '<div class="energy-bar-container">'
            for i in range(1, 11):
                color = "#00FFCC" if i <= score else "#222"
                opacity = "1" if i <= score else "0.2"
                grid += f'<div class="energy-seg" style="background-color:{color}; opacity:{opacity};"></div>'
            grid += f'</div>'
            st.markdown(f"**{label}** : {score}/10 {grid}", unsafe_allow_html=True)

except Exception as e:
    st.error(f"數據診斷中... {e}")
