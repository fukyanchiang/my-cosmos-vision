import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="COSMOS 戰略指揮部 V42", layout="wide")

# --- 基礎工具函數 ---
def safe_n(val, alt=50.0):
    try:
        v = float(val)
        return v if not np.isnan(v) and not np.isinf(v) else alt
    except: return alt

def safe_s(info, keys, suffix="", alt="N/A"):
    for k in keys:
        v = info.get(k)
        if v is not None and v != "" and str(v).lower() not in ['nan', 'inf', 'none']: 
            try: return f"{float(v):.2f}{suffix}"
            except: pass
    return alt

def get_beta(info, df, spy_df):
    b = info.get('beta')
    if b is not None and str(b).lower() not in ['nan', 'none', '']: return f"{float(b):.2f}"
    try:
        df_aligned, spy_aligned = df['Close'].align(spy_df['Close'], join='inner')
        asset_ret = df_aligned.pct_change().dropna().tail(252)
        spy_ret = spy_aligned.pct_change().dropna().tail(252)
        if len(asset_ret) > 30:
            covar = np.cov(asset_ret, spy_ret)[0][1]
            var = np.var(spy_ret)
            if var > 0: return f"{(covar / var):.2f}"
    except: pass
    return "1.00"

def draw_triad_bar(val, title, color):
    lit = int((min(120, val)/120)*21)
    html = f"<div class='ej-header'>{title}: {val:.1f}%</div><div class='bar-group-container'>"
    for g in range(7):
        html += "<div class='bar-triad'>"
        for i in range(3):
            idx = g*3+i; c_code = "#FF4B4B" if idx<6 else ("#FFD700" if idx<12 else color)
            op = 1 if idx < lit else 0.1; sh = f"box-shadow: 0 0 10px {c_code};" if idx < lit else ""
            html += f"<div class='ej-seg' style='background-color:{c_code if idx < lit else '#222'}; opacity:{op}; {sh}'></div>"
        html += "</div>"
    return html + "</div>"

# --- 乖孫的美股版塊地圖 ---
US_SECTOR_MAP = {
    "太陽能 (TAN)": "TAN", "公用事業 (XLU)": "XLU", "油服 (OIH)": "OIH",
    "工業 (XLI)": "XLI", "必消 (XLP)": "XLP", "房地產 (XLRE)": "XLRE",
    "銀行 (KRE)": "KRE", "建築 (ITB)": "ITB", "半導體 (SMH)": "SMH",
    "能源 (XLE)": "XLE", "醫療 (XLV)": "XLV", "通訊 (XLC)": "XLC",
    "金融 (XLF)": "XLF", "可選消費 (XLY)": "XLY", "科技 (XLK)": "XLK",
    "生技 (IBB)": "IBB", "黃金礦工 (GDX)": "GDX"
}

# 2. 視覺裝修 (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 25px; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 20px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 5rem; font-weight: 900; }
    .ej-header { color: #00FFFF !important; font-size: 1.8rem; font-weight: 900; margin-bottom: 8px; }
    .bar-group-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .bar-triad { display: flex; gap: 3px; }
    .ej-seg { width: 16px; height: 35px; border-radius: 2px; border: 1.2px solid rgba(255,255,255,0.4); }
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; min-height: 200px; }
    .val-label { color: #FFFFFF !important; font-size: 1.6rem; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 12px; }
    .val-text { font-size: 1.3rem; color: #ccc; margin: 8px 0; }
    .val-focus { color: #FFD700; font-weight: bold; font-size: 1.8rem; }
    .red-bar { background-color: #FF4B4B; color: #fff; padding: 20px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 2.5rem; margin: 30px 0; border: 3px solid #fff; }
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700; font-weight: bold; font-size: 2.5rem; }
    .whale-a { color: #00FFCC; font-size: 1.6rem; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# 3. 側邊欄控制
st.sidebar.markdown("## 🛰️ 模式選擇")
app_mode = st.sidebar.selectbox("切換戰術視角", ["📡 版塊強勢熱力圖", "🚀 個股 DNA 深度透視"])

# --- 模式 A：版塊掃描 ---
if app_mode == "📡 版塊強勢熱力圖":
    st.markdown("<h1 class='main-title'>🛰️ 全美星系版塊能量分布</h1>", unsafe_allow_html=True)
    spy_data = yf.Ticker("SPY").history(period="60d")['Close']
    results = []
    with st.spinner('爺爺正在掃描全美版塊...'):
        for name, sym in US_SECTOR_MAP.items():
            try:
                d = yf.Ticker(sym).history(period="60d")['Close
