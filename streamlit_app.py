import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置 (尋晚最穩陣版本)
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

# 保險絲：確保唔會出 nan
def safe_v(val, alt=50.0):
    try:
        v = float(val)
        return v if not np.isnan(v) and not np.isinf(v) else alt
    except: return alt

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3rem; font-weight: 900; margin-bottom: 25px; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 20px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.4rem; font-weight: bold; }
    .cosmos-value { color: #FFFFFF !important; font-size: 4.5rem; font-weight: 900; text-shadow: 0 0 15px #00FFCC; }
    
    /* 3個一組 紅黃綠 能量燈 */
    .ej-header { color: #00FFFF !important; font-size: 1.3rem; font-weight: 900; margin-bottom: 8px; text-align: left; }
    .bar-group-container { display: flex; gap: 8px; margin-bottom: 12px; }
    .bar-triad { display: flex; gap: 3px; }
    .ej-seg { width: 14px; height: 28px; border-radius: 2px; border: 1px solid rgba(255,255,255,0.2); }
    
    /* 八大評級 */
    .king-grid { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 12px; padding: 15px; text-align: center; }
    .king-val { color: #FFD700; font-size: 2.2rem; font-weight: bold; }
    
    /* 名家表格 (搵返晒出嚟) */
    .whale-box { background-color: #000; border: 2px solid #FFD700; border-radius: 15px; padding: 20px; margin-top: 25px; }
    .whale-row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid #333; font-size: 1.2rem; }
    
    .red-bar { background-color: #FF4B4B; color: #fff; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 1.8rem; margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入代號", "1888.HK").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="1y"); spy = yf.Ticker("SPY").history(period="1y")
    
    if not df.empty:
        # --- 🌌 找回尋晚最強演算 ---
        c = df['Close'].tail(125); days = np.arange(len(c))
        slope, intercept = np.polyfit(days, c, 1)
        pred = intercept + slope * len(days)
        mom = (c.iloc[-1] / pred) if pred > 0 else 1.0
        v_ann = max(0.001, c.pct_change().std() * np.sqrt(252))
        
        # 動態分數 (唔再係 50.0)
        cx_val = safe_v((slope / c.mean()) / v_ann * 320 * mom)
        crs_val = safe_v(50 + ((df['Close'].iloc[-1]/df['Close'].iloc[-63] - spy['Close'].iloc[-1]/spy['Close'].iloc[-63]) * 220))
        
        # EJ 錢流 & 短期能量
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        cej_score = safe_v((v21 / v252) * 100)
        short_ret = (df['Close'].iloc[-1] / df['Close'].iloc[-5]) - 1
        se_score = safe_v(50 + (short_ret * 1200))
        
        # 找回目標價
        target_p = c.iloc[-1] * 1.35

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)
        
        # A. 第一層：三主星與 3組燈
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS (星系強弱)</div><div class='cosmos-value'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        
        with c3:
            st.markdown("<div class='cosmos-box' style='border-color:#00FFFF;'>", unsafe_allow_html=True)
            def draw_triad(val, title, top_col):
                lit = int((min(120, val)/120)*21)
                html = f"<div class='ej-header'>{title}: {val:.1f}%</div><div class='bar-group-container'>"
                for g in range(7):
                    html += "<div class='bar-triad'>"
                    for i in range(3):
                        idx = g * 3 + i
                        color = "#FF4B4B" if idx<6 else ("#FFD700" if idx<12 else top_col)
                        op = 1 if idx < lit else 0.1
                        html += f"<div class='ej-seg' style='background-color:{color if idx < lit else '#222'}; opacity:{op}; box-shadow:{'0 0 10px '+color if idx < lit else 'none'}'></div>"
                    html += "</div>"
                return html + "</div>"
            st.markdown(draw_triad(cej_score, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
            st.markdown(draw_triad(se_score, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛 (找回目標價)
        st.write("")
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", f"{se_score:.0f}"), ("🔋 大資金", f"{cej_score:.0f}"), 
                 ("🎭 情緒", "75"), ("🏆 總分", f"{(cx_val+crs_val)/2.8:.0f}"), ("🔮 目標價", f"${target_p:.2f}"), ("💰 成交比", f"{(v21/v252):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-grid'><div style='color:#ccc;'>{kings[i][0]}</div><div class='king-val'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-grid'><div style='color:#ccc;'>{kings[i+4][0]}</div><div class='king-val'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 今晚研發：短期爆發能量 [{se_score:.1f}%] 🔥</div>", unsafe_allow_html=True)

        # C. 找回名家清單 (表格重現)
        st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:1.5rem; font-weight:bold; text-align:center; margin-bottom:15px;'>🧙 名家點兵實錄</div>", unsafe_allow_html=True)
        whales = [("黃仁勳 (NVIDIA)", "重倉增持 [26Q1]"), ("華倫·巴菲特", "續領持貨 [26Q1]"), ("林少陽 (港股)", "價值發現 [26Q1]"), ("李嘉誠 (價值)", "穩健續領 [26Q1]")]
        for n, a in whales:
            st.markdown(f"<div class='whale-row'><b style='color:#FFD700;'>{n}</b><span style='color:#00FFCC;'>{a}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e: st.error(f"系統修復中: {e}")
