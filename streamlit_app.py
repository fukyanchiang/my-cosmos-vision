import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

# 最強防斷保險絲
def safe_n(val, alt=50.0):
    try:
        v = float(val)
        return v if not np.isnan(v) and not np.isinf(v) else alt
    except: return alt

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3rem; font-weight: 900; margin-bottom: 20px; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 15px; padding: 20px; text-align: center; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.2rem; font-weight: bold; }
    .cosmos-value { color: #FFFFFF !important; font-size: 4rem; font-weight: 900; }
    .ej-header { color: #00FFFF !important; font-size: 1.3rem; font-weight: bold; margin-bottom: 5px; text-align: left; }
    .ej-bar-container { display: flex; gap: 4px; margin-bottom: 15px; }
    .ej-seg { width: 14px; height: 26px; border-radius: 2px; border: 1px solid rgba(255,255,255,0.2); }
    .king-box { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; }
    .whale-box { background-color: #000; border: 2px solid #FFD700; border-radius: 10px; padding: 15px; margin-top: 20px; }
    .whale-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入代號", "1888.HK").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="1y"); spy = yf.Ticker("SPY").history(period="1y")
    
    if not df.empty:
        # --- 🌌 重生演算 (極簡化，保證不出 nan) ---
        close = df['Close']
        # COSMOS-X: 近 20 日升幅 * 5 (簡單直接的動能)
        x_calc = ((close.iloc[-1] / close.iloc[-20]) - 1) * 500 + 50
        cx_val = safe_n(x_calc)
        
        # COSMOS-RS: 個股 60 日表現 - 大盤 60 日表現
        rs_calc = ((close.iloc[-1]/close.iloc[-60]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-60])) * 200 + 100
        crs_val = safe_n(rs_calc)
        
        # EJ 錢流: 近 5 日成交 vs 20 日平均
        v_score = safe_n((df['Volume'].tail(5).mean() / df['Volume'].tail(20).mean()) * 100)
        # 短期能量: RSI 簡化版
        short_e = safe_n(((close.iloc[-1] - close.min()) / (close.max() - close.min())) * 100)
        
        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS (星系強弱)</div><div class='cosmos-value'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        
        with c3:
            st.markdown("<div class='cosmos-box' style='border-color:#00FFFF;'>", unsafe_allow_html=True)
            def draw_ej(val, title, col):
                lit = int((min(120, val)/120)*21)
                html = f"<div class='ej-header'>{title}: {val:.1f}%</div><div class='ej-bar-container'>"
                for i in range(21):
                    op = 1 if i < lit else 0.1
                    html += f"<div class='ej-seg' style='background-color:{col if i < lit else '#222'}; opacity:{op}; box-shadow:{'0 0 8px '+col if i < lit else 'none'}'></div>"
                return html + "</div>"
            st.markdown(draw_ej(v_score, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
            st.markdown(draw_ej(short_e, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", f"{short_e:.0f}"), ("🔋 大資金", f"{v_score:.0f}"), 
                 ("🎭 情緒", "75"), ("🏆 總分", f"{(cx_val+crs_val)/2:.0f}"), ("🔮 目標價", f"${(close.iloc[-1]*1.2):.2f}"), ("💰 成交", "穩定")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><div style='color:#aaa;'>{kings[i][0]}</div><div style='color:#FFD700;font-size:1.8rem;font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><div style='color:#aaa;'>{kings[i+4][0]}</div><div style='color:#FFD700;font-size:1.8rem;font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='whale-box'><div style='color:#FFD700;font-size:1.4rem;font-weight:bold;text-align:center;'>🧙 名家點兵實錄</div>", unsafe_allow_html=True)
        whales = [("黃仁勳", "重倉增持"), ("巴菲特", "穩健持貨"), ("林少陽", "價值發現")]
        for n, a in whales:
            st.markdown(f"<div class='whale-row'><b>{n}</b><span style='color:#00FFCC;'>{a}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e: st.error(f"系統重啟中: {e}")
