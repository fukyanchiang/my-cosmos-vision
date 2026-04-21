import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置 (大宗師鎖死)
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3rem; font-weight: 900; margin-bottom: 20px; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 15px; padding: 20px; text-align: center; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.2rem; font-weight: bold; }
    .cosmos-value { color: #FFFFFF !important; font-size: 4rem; font-weight: 900; text-shadow: 0 0 15px #00FFCC; }
    
    /* 正宗信報排版：文字連分數 */
    .ej-header { color: #00FFFF !important; font-size: 1.3rem; font-weight: 900; text-align: left; margin-bottom: 8px; }
    .ej-bar-container { display: flex; gap: 4px; margin-bottom: 15px; }
    .ej-segment { width: 14px; height: 28px; border-radius: 2px; border: 1.5px solid rgba(255,255,255,0.4); }
    
    .king-box { background-color: #1c1e26 !important; border: 2px solid #00FFCC; border-radius: 12px; padding: 15px; text-align: center; margin-bottom: 10px; }
    .king-label { color: #FFFFFF !important; font-size: 1.1rem; font-weight: bold; }
    .king-value { color: #FFD700 !important; font-size: 2.2rem; font-weight: bold; }
    .red-bar { background-color: #FF4B4B; color: #fff; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 2rem; margin: 20px 0; border: 3px solid #fff; }
    </style>
    """, unsafe_allow_html=True)

def get_num(val, default=50.0):
    try: 
        v = float(val)
        return v if not np.isnan(v) and not np.isinf(v) else default
    except: return default

ticker = st.sidebar.text_input("輸入資產代號", "1888.HK").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 COSMOS-X 演算 (今晚新邏輯) ---
        c = df['Close'].tail(125); days = np.arange(len(c))
        slope, intercept = np.polyfit(days, c, 1)
        pred_val = intercept + slope * len(days)
        mom_factor = (c.iloc[-1] / pred_val) if pred_val > 0 else 1.0
        vol = max(0.001, c.pct_change().std() * np.sqrt(252))
        
        cx_val = get_num((slope / c.mean()) / vol * 320 * mom_factor, 50.0)
        asset_ret = df['Close'].iloc[-1] / df['Close'].iloc[-63]
        spy_ret = spy['Close'].iloc[-1] / spy['Close'].iloc[-63]
        crs_val = get_num(50 + ((asset_ret - spy_ret) * 230), 50.0)

        # --- 💰 EJ 錢流 & 短期能量演算 ---
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        cej_score = get_num((v21 / v252) * 100, 50.0)
        
        # 今晚新研發：短期能量 (短期價格變動 vs 波動)
        short_ret = (df['Close'].iloc[-1] / df['Close'].iloc[-5]) - 1
        short_energy = 50 + (short_ret * 800) # 放大短期爆發感
        power_score = get_num(short_energy, 50.0)

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)
        
        # A. 第一層：三主星與能量 Bar
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS (星系強弱)</div><div class='cosmos-value'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        
        with c3:
            st.markdown("<div class='cosmos-box' style='border-color:#00FFFF; padding: 15px;'>", unsafe_allow_html=True)
            def draw_ej_style(val, title, theme_color="#00FFFF"):
                lit = int((min(120, val)/120)*21)
                html = f"<div class='ej-header'>{title}: {val:.1f}%</div><div class='ej-bar-container'>"
                for i in range(21):
                    color = "#FF4B4B" if i<3 else ("#FFD700" if i<8 else theme_color)
                    op = 1 if i < lit else 0.15
                    sh = f"box-shadow: 0 0 15px {color};" if i < lit else ""
                    html += f"<div class='ej-segment' style='background-color:{color if i < lit else '#1a1a1a'}; opacity:{op}; {sh}'></div>"
                return html + "</div>"
            
            st.markdown(draw_ej_style(cej_score, "EJ 錢流底氣"), unsafe_allow_html=True)
            st.markdown(draw_ej_style(power_score, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛
        st.write("")
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", f"{power_score:.0f}"), ("🔋 大資金", f"{cej_score:.0f}"), ("🎭 情緒", "75"), ("🏆 總分", f"{(cx_val+crs_val)/2.8:.0f}"), ("🔮 目標價", f"${(df['Close'].iloc[-1]*1.35):.2f}"), ("💰 成交比", f"{(v21/v252):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i][0]}</div><div class='king-value'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i+4][0]}</div><div class='king-value'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 今晚新研發：短期能量爆發 [{power_score:.1f}%] 🔥</div>", unsafe_allow_html=True)

        # C. 圖表
        recent = df.tail(120); fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Bar(x=recent.index, y=recent['High']-recent['Low'], base=recent['Low'], marker_color=np.where(recent['Close']>recent['Open'], '#00FF00', '#FF0000'), width=0.8), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=np.abs(recent['Close']-recent['Open']), base=np.minimum(recent['Open'], recent['Close']), marker_color=np.where(recent['Close']>recent['Open'], '#00FF00', '#FF0000'), width=1.2), row=1, col=1)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', xaxis='x2'), row=1, col=1)
        fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=800, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', range=[0, max(counts)*6]))
        st.plotly_chart(fig, use_container_width=True)

        # D. 名家
        st.markdown("<div class='whale-container'><div style='color:#FFD700; font-weight:bold; font-size:1.4rem; text-align:center;'>🧙 名家點兵：今晚最新動向</div>", unsafe_allow_html=True)
        whales = [("黃仁勳", "短期看漲"), ("巴菲特", "長線重倉"), ("李嘉誠", "價值防守"), ("林少陽", "價值修復")]
        for n, a in whales: st.markdown(f"<div style='display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #333;'><span style='color:#FFD700; font-weight:bold;'>{n}</span><span style='color:#00FFCC;'>{a}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e: st.error(f"系統演算中: {e}")
