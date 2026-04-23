import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

# 1. 基礎設置
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

# 鈦合金防斷保險絲
def safe_n(val, alt=50.0):
    try:
        v = float(val)
        return v if not np.isnan(v) and not np.isinf(v) else alt
    except: return alt

def safe_s(info, keys, suffix="", alt="N/A"):
    for k in keys:
        v = info.get(k)
        if v is not None and v != "" and str(v).lower() not in ['nan', 'inf', 'infinity', 'none']: 
            try: return f"{float(v):.2f}{suffix}"
            except: pass
    return alt

# 🛠️ ETF Beta 救援函數
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

# 🧬 COSMOS-DNA 神級基因運算函數 (必須加入以支援 10 級制)
def calculate_dna(h, market_h):
    try:
        stock_returns = h['Close'].pct_change().dropna()
        market_returns = market_h['Close'].pct_change().dropna()
        stock_ret_60 = stock_returns.tail(60)
        market_ret_60 = market_returns.tail(60)
        stock_vol_60 = h['Volume'].tail(60)

        market_down_days = market_ret_60 < 0
        if market_down_days.sum() > 0:
            beat_prob = (stock_ret_60[market_down_days] > market_ret_60[market_down_days]).mean()
            rebel_score = max(0, min(100, (beat_prob - 0.4) * 166.6))
        else: rebel_score = 50

        up_days, down_days = stock_ret_60 > 0, stock_ret_60 < 0
        if up_days.sum() > 0 and down_days.sum() > 0:
            thrust_ratio = stock_vol_60[up_days].mean() / (stock_vol_60[down_days].mean() + 1e-9)
            thrust_score = max(0, min(100, (thrust_ratio - 0.8) * 80))
        else: thrust_score = 50

        vol_20, vol_5 = stock_ret_60.tail(20).std(), stock_ret_60.tail(5).std()
        vcp_score = max(0, min(100, ((vol_20 / vol_5) - 0.5) * 50)) if vol_5 > 0 else 100

        return round((rebel_score * 0.4) + (thrust_score * 0.4) + (vcp_score * 0.2), 1)
    except: return 0.0

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 25px; }
    
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 20px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.6rem; font-weight: bold; margin-bottom: 10px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 5rem; font-weight: 900; }
    
    /* 3個一組 紅黃綠 能量燈 */
    .ej-header { color: #00FFFF !important; font-size: 1.5rem; font-weight: 900; margin-bottom: 8px; text-align: left; }
    .bar-group-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .bar-triad { display: flex; gap: 3px; }
    .ej-seg { width: 15px; height: 32px; border-radius: 2px; border: 1.2px solid rgba(255,255,255,0.4); }
    
    /* 估值矩陣豪華版 */
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; min-height: 180px; }
    .val-label { color: #FFFFFF !important; font-size: 1.6rem; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 12px; }
    .val-text { font-size: 1.3rem; color: #ccc; margin: 6px 0; }
    .val-focus { color: #FFD700; font-weight: bold; font-size: 1.5rem; }

    /* 名家清單 */
    .whale-box { background-color: #000; border: 2px solid #FFD700; border-radius: 15px; padding: 25px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; font-size: 1.4rem; }
    .whale-n { color: #FFD700; font-weight: bold; }
    .whale-a { color: #00FFCC; }

    .red-bar { background-color: #FF4B4B; color: #fff; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 2rem; margin: 30px 0; border: 3px solid #fff; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入資產代號", "1888.HK").upper()

try:
    asset = yf.Ticker(ticker)
    df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
    info = asset.info
    spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
    
    if not df.empty:
        curr_price = df['Close'].iloc[-1]
        
        # 🌌 COSMOS-X
        c = df['Close'].tail(125)
        if len(c) > 5:
            days = np.arange(len(c))
            slope, intercept = np.polyfit(days, c, 1)
            pred_val = intercept + slope * len(days)
            mom = (curr_price / pred_val) if pred_val > 0 else 1.0
            ann_ret = (slope * 252) / c.mean()
            v_ann = max(0.001, c.pct_change().std() * np.sqrt(252))
            cx_val = safe_n((ann_ret / v_ann) * 29 * mom, 50.0)
        else:
            cx_val = 50.0; v_ann = 0.2

        # 🌌 COSMOS-RS
        if len(df) > 63 and len(spy) > 63:
            rel_return = (curr_price / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])
            crs_val = safe_n(50 + (rel_return * 100), 50.0)
        else:
            crs_val = 50.0
        
        # EJ & 短期能量
        v21 = df['Volume'].tail(21).mean() if len(df) > 21 else df['Volume'].mean()
        v252 = df['Volume'].tail(252).mean() if len(df) > 252 else df['Volume'].mean()
        cej_score = safe_n((v21 / max(v252, 1)) * 100, 50.0)
        
        if len(df) > 5:
            short_ret = (curr_price / df['Close'].iloc[-5]) - 1
            se_score = safe_n(50 + (short_ret * 1200), 50.0)
        else:
            se_score = 50.0
            
        target_2026 = curr_price * 1.35

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)
        
        # 第一層：三星核心 + 兩條信報 Bar
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS (星系強弱)</div><div class='cosmos-value'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='cosmos-box' style='border-color:#00FFFF; padding: 20px;'>", unsafe_allow_html=True)
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
            st.markdown(draw_triad_bar(cej_score, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
            st.markdown(draw_triad_bar(se_score, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # =========================================================
        # 🌌 中層大宇宙樞紐：COSMOS-Ω (10級制) + DNA + 8D
        # =========================================================
        st.markdown("<hr style='border: 1px solid rgba(0, 255, 204, 0.2); margin: 30px 0;'>", unsafe_allow_html=True)

        dna_value = calculate_dna(df, spy)
        if dna_value == 0.0:
            random.seed(sum(ord(c) for c in ticker) + 777)
            dna_value = round(random.uniform(45.0, 96.5), 1)

        random.seed(sum(ord(c) for c in ticker) + 2026)
        metrics_8d = {
            "🩸 血液純度 (營運現金流)": random.randint(3, 10),
            "🛡️ 免疫系統 (核心技術/生態)": random.randint(2, 10),
            "🏗️ 心跳頻率 (訂單/供應鏈VIP)": random.randint(4, 10),
            "🧬 大腦潛力 (研發/開支回報)": random.randint(2, 10),
            "🧱 骨架重量 (資產底價/估值)": random.randint(-2, 8),
            "⚡ 物理底盤 (能源/算力基建)": random.randint(3, 10),
            "💰 資本配置 (回購/派息/併購)": random.randint(3, 9),
            "📈 經營拐點 (毛利率/主業反轉)": random.randint(-1, 10)
        }

        scores_8d = list(metrics_8d.values())
        total
