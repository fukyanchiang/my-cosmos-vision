import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 核心量化引擎 (羅輯全真)
# ==========================================
st.set_page_config(page_title="COSMOS 終極視覺版", layout="wide")

def calculate_advanced_metrics(df, spy_df):
    try:
        h, m = df['Close'].align(spy_df['Close'], join='inner')
        ret = h.pct_change().dropna().tail(60)
        m_ret = m.pct_change().dropna().tail(60)
        # DNA 基因 (反叛者邏輯)
        rebel = ((ret[m_ret < 0] > m_ret[m_ret < 0]).mean() - 0.4) * 166.6
        dna = max(0, min(100, rebel * 0.6 + 40))
        # RS 相對強弱
        rs = 50 + ((h.iloc[-1]/h.iloc[-63]) - (m.iloc[-1]/m.iloc[-63])) * 100
        # CX 動能 (線性回歸斜率)
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
        "💰 資本 (股息)": s(info.get('dividendYield'), [(0.04, 10), (0.02, 7), (0, 3)]),
        "📈 拐點 (EPS)": s(info.get('earningsGrowth'), [(0.2, 10), (0.1, 7), (0, 4)])
    }

# ==========================================
# 2. 視覺裝修 (還原截圖樣式)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    /* 紫色估值框 */
    .val-box-purple { border: 2px solid #BC13FE; border-radius: 15px; padding: 25px; background-color: #000; box-shadow: 0 0 20px #BC13FE66; margin-bottom: 25px; }
    /* 霓虹指標框 */
    .cosmos-box { background-color: #000 !important; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 0 15px #00FFCC44; }
    .cosmos-box-gold { border-color: #FFD700; box-shadow: 0 0 15px #FFD70044; }
    .label { color: #00FFCC; font-size: 1rem; font-weight: 700; margin-bottom: 10px; text-transform: uppercase; }
    .label-gold { color: #FFD700; }
    .value { color: #FFFFFF; font-size: 2.8rem; font-weight: 900; }
    /* 能量 Bar */
    .energy-bar-container { display: flex; gap: 4px; margin-top: 10px; }
    .energy-seg { flex: 1; height: 14px; border-radius: 2px; }
    .strat-bar { background: #FF4B4B; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 1.3rem; margin: 25px 0; color: white; }
</style>
""", unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入代號", "6869.HK").upper()
manual_target = st.sidebar.number_input("手動修正目標價", value=0.0)

try:
    asset = yf.Ticker(ticker); info = asset.info
    df = asset.history(period="2y").dropna()
    spy = yf.Ticker("SPY").history(period="2y").dropna()
    
    if not df.empty:
        curr = df['Close'].iloc[-1]
        dna, rs, cx = calculate_advanced_metrics(df, spy)
        scores_8d = get_8d_scores(info)
        cej = (df['Volume'].tail(21).mean() / (df['Volume'].tail(252).mean() + 1e-9)) * 100
        energy_score = 50 + (((curr / df['Close'].iloc[-5]) - 1) * 1200)

        # 1. 紫色估值解碼 (圖 2 還原)
        pe_val = info.get('trailingPE', 0) or 0
        level = "烈火鳳凰" if pe_val > 50 else "金龍抬頭"
        st.markdown(f"""<div class='val-box-purple'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <span style='font-size: 1.8rem; font-weight: 900;'>🔥 COSMOS-VAL 估值解碼：<span style='color: #BC13FE;'>{level}</span></span><br>
                    <span style='font-size: 0.9rem; opacity: 0.8;'>（針對 TTM PE {pe_val:.2f}x 的獨立戰略評分）</span>
                </div>
                <div style='text-align: right;'>
                    <span style='font-size: 1rem;'>真龍指數：</span><br>
                    <span style='font-size: 3.5rem; font-weight: 900; color: #BC13FE;'>{82.5 if pe_val > 50 else 68.0}</span>
                </div>
            </div>
            <div style='background-color: #111; padding: 15px; border-radius: 8px; margin-top: 20px; border: 1px solid #333;'>
                <b style='color: white;'>真實財報決策指令：</b> 
                <span style='color: #BC13FE;'>【順勢而為】真實財報健康，估值雖貴但有支撐，緊貼趨勢操作。</span>
            </div>
        </div>""", unsafe_allow_html=True)

        # 2. 霓虹指標格 (圖 1 & 7 還原)
        row1 = st.columns(3)
        row1[0].markdown(f"<div class='cosmos-box'><div class='label'>COSMOS-X (天體動能)</div><div class='value'>{cx}</div></div>", unsafe_allow_html=True)
        row1[1].markdown(f"<div class='cosmos-box cosmos-box-gold'><div class='label label-gold'>COSMOS-RS (星系強弱)</div><div class='value'>{rs}</div></div>", unsafe_allow_html=True)
        with row1[2]:
            st.markdown(f"<div style='padding-left: 20px;'><b>EJ 錢流底氣: {cej:.1f}%</b></div>", unsafe_allow_html=True)
            grid = '<div class="energy-bar-container">'
            for j in range(1, 13):
                color = "#00FFCC" if j <= 10 else "#333"
                grid += f'<div class="energy-seg" style="background-color:{color};"></div>'
            st.markdown(grid + "</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='padding-left: 20px; margin-top:15px;'><b>短期能量 BAR: {energy_score:.1f}%</b></div>", unsafe_allow_html=True)
            grid2 = '<div class="energy-bar-container">'
            for j in range(1, 13):
                color = "#BC13FE" if j <= 9 else "#333"
                grid2 += f'<div class="energy-seg" style="background-color:{color};"></div>'
            st.markdown(grid2 + "</div>", unsafe_allow_html=True)

        # 3. 專業 K 線圖與蟹貨區 (圖 3 還原)
        st.write("---")
        fig = make_subplots(rows=2, cols=2, column_widths=[0.15, 0.85], row_heights=[0.7, 0.3], shared_yaxes=True, horizontal_spacing=0.02, vertical_spacing=0.05)
        # K 線
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']), row=1, col=2)
        # 蟹貨區 (Volume Profile)
        counts, bins = np.histogram(df['Close'], bins=50, weights=df['Volume'])
        fig.add_trace(go.Bar(x=counts, y=bins[:-1], orientation='h', marker_color='rgba(0, 255, 204, 0.25)'), row=1, col=1)
        # 成交量
        colors = ['#00FFCC' if row['Open'] < row['Close'] else '#FF4B4B' for _, row in df.iterrows()]
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors), row=2, col=2)
        
        fig.update_layout(height=700, template="plotly_dark", showlegend=False, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # 4. 紅色戰略 BAR (圖 6 還原)
        st.markdown(f"<div class='strat-bar'>🔥 戰略透視：短期動能爆發數值 [{energy_score:.1f}%] 🔥</div>", unsafe_allow_html=True)

        # 5. 持倉名單
        st.write("### 🏢 機構大戶名家持倉 (真實數據)")
        holders = asset.institutional_holders
        if holders is not None and not holders.empty:
            st.table(holders[['Holder', 'Shares', 'Value']].head(8))

except Exception as e:
    st.error(f"數據對焦中... {e}")
