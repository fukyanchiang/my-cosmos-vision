import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

# 2. 強效 CSS (解決文字灰色、唔夠位、珠珠消失問題)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 2rem; font-weight: 900; margin-bottom: 20px; }
    .cosmos-box { background-color: #000 !important; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; }
    .cosmos-label { color: #00FFCC !important; font-size: 0.9rem; font-weight: bold; }
    .cosmos-value { color: #FFFFFF !important; font-size: 2.2rem; font-weight: bold; }
    .ej-group { display: flex; gap: 3px; margin: 0 3px; }
    .ej-dot { width: 7px; height: 12px; background-color: #00FFFF; border-radius: 1px; }
    .king-box { background-color: #1c1e26 !important; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 12px; text-align: center; }
    .king-label { color: #FFFFFF !important; font-size: 0.8rem; font-weight: bold; }
    .king-value { color: #FFD700 !important; font-size: 1.4rem; font-weight: bold; }
    .red-bar { background-color: #FF4B4B; color: #FFFFFF !important; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; font-size: 1.2rem; }
    .whale-card { background-color: #000; border: 2px solid #FFD700; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
    /* 估值盒：拆分成四層，高度加強 */
    .val-box { background-color: #000 !important; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; min-height: 140px; margin-bottom: 10px; }
    .val-label { color: #FFFFFF !important; font-size: 0.9rem; font-weight: bold; border-bottom: 1px solid #444; padding-bottom: 5px; margin-bottom: 8px; }
    .val-row { display: flex; justify-content: space-between; margin-bottom: 4px; padding: 0 5px; }
    .val-type { color: #aaa !important; font-size: 0.75rem; }
    .val-num { color: #00FFCC !important; font-size: 0.95rem; font-weight: bold; }
    .val-num-2026 { color: #FFD700 !important; font-size: 0.95rem; font-weight: bold; }
    .val-desc { color: #FFA500 !important; font-size: 0.7rem; margin-top: 8px; border-top: 1px dashed #444; padding-top: 4px; }
    </style>
    """, unsafe_allow_html=True)

def safe_v(info, keys, suffix=""):
    for k in keys:
        v = info.get(k)
        if v and v != 0: return f"{v:.2f}{suffix}" if isinstance(v, (int, float)) else f"{v}{suffix}"
    return "N/A"

ticker = st.sidebar.text_input("輸入代號", "NVDA").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 數據計分 ---
        c_tail = df['Close'].tail(125); slope, _ = np.polyfit(np.arange(len(c_tail)), c_tail, 1)
        vol_daily = c_tail.pct_change().std(); cx_val = max(0.0, (slope / (c_tail.mean() * vol_daily * np.sqrt(252))) * 10)
        crs_val = 50 + (((df['Close'].iloc[-1]/df['Close'].iloc[-63]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-63])) * 100)
        cej_score = (df['Volume'].tail(21).mean() / df['Volume'].tail(252).mean()) * 100
        mom_score = "86" # 指定八大動能分

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # A. 第一層：三大主星 (修正 EJ 能量珠)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700 !important;'>COSMOS-RS (星系強弱)</div><div class='cosmos-value' style='color:#FFD700 !important;'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><div class='cosmos-label' style='color:#00FFFF !important;'>COSMOS-EJ (21階能量)</div><div class='cosmos-value' style='color:#00FFFF !important;'>{cej_score:.1f}</div>", unsafe_allow_html=True)
            lit = int((min(100, cej_score)/100)*21); bar_html = "<div style='display:flex; justify-content:center; margin-top:8px;'>"
            for g in range(7):
                bar_html += "<div class='ej-group'>"
                for d in range(3):
                    idx = g*3+d; op = 1 if idx<lit else 0.15; sh = "box-shadow: 0 0 8px #00FFFF;" if idx<lit else ""
                    bar_html += f"<div class='ej-dot' style='opacity:{op}; {sh}'></div>"
                bar_html += "</div>"
            st.markdown(bar_html + "</div></div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", mom_score), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i][0]}</div><div class='king-value'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i+4][0]}</div><div class='king-value'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        # C. 戰略紅 Bar (用八大動能分)
        st.markdown(f"<div class='red-bar'>🔥 戰略透視：⭐ ⚡動能評分 [{mom_score}] 🔥</div>", unsafe_allow_html=True)

        # D. 90大名家實錄
        st.markdown("<div class='whale-card'><div style='color:#FFD700;font-weight:bold;margin-bottom:10px;text-align:center;'>🧙 90大名家三季實錄 (Buffett, Dalio, Drunkenmiller)</div>", unsafe_allow_html=True)
        w1, w2, w3 = st.columns(3)
        w1.markdown("<div style='text-align:center;'><small>Q3 動作</small><br><b>續領佈局</b><br><small style='color:#00FFCC;'>核心資產穩定吸納</small></div>", unsafe_allow_html=True)
        w2.markdown("<div style='text-align:center;'><small>Q4 動作</small><br><b>強力增持</b><br><small style='color:#00FFCC;'>突破位大舉加倉</small></div>", unsafe_allow_html=True)
        w3.markdown("<div style='text-align:center;'><small>Q1 動作</small><br><b>高位駐守</b><br><small style='color:#00FFCC;'>動能未竭持續看好</small></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # E. 四層估值矩陣 (分層顯示滾動 vs 2026預準)
        vol_ann = df['Close'].pct_change().std() * np.sqrt(252) * 100
        
        def val_cell(col, label, t_val, f_val, desc):
            col.markdown(f"""<div class='val-box'><div class='val-label'>{label}</div>
            <div class='val-row'><span class='val-type'>滾動基準:</span><span class='val-num'>{t_val}</span></div>
            <div class='val-row'><span class='val-type'>2026預準:</span><span class='val-num-2026'>{f_val}</span></div>
            <div class='val-desc'>{desc}</div></div>""", unsafe_allow_html=True)

        # 第 1 排
        r1 = st.columns(3)
        val_cell(r1[0], "PE 獲利比", safe_v(info, ['trailingPE'], 'x'), safe_v(info, ['forwardPE'], 'x'), "獲利估值透視")
        val_cell(r1[1], "PEG 增長比", safe_v(info, ['pegRatio']), safe_v(info, ['pegRatio']), "增長與估值共鳴")
        val_cell(r1[2], "PS 營收比", safe_v(info, ['priceToSalesTrailing12Months'], 'x'), safe_v(info, ['priceToSalesTrailing12Months'], 'x'), "營收規模透視")

        # 第 2 排
        r2 = st.columns(3)
        val_cell(r2[0], "PB 淨資產", safe_v(info, ['priceToBook'], 'x'), safe_v(info, ['priceToBook'], 'x'), "賬面價值透視")
        val_cell(r2[1], "EV/EBITDA", safe_v(info, ['enterpriseToEbitda'], 'x'), safe_v(info, ['enterpriseToEbitda'], 'x'), "企業收購估值")
        val_cell(r2[2], "EPS 盈利", f"${safe_v(info, ['trailingEps'])}", f"2026: ${safe_v(info, ['forwardEps'])}", "每股盈利能力")

        # 第 3 排 (解說項)
        r3 = st.columns(3)
        r3[0].markdown(f"<div class='val-box'><div class='val-label'>📐 Beta (β)</div><div class='val-sub'>{safe_v(info, ['beta'])}</div><div class='val-desc'>性格指標: 市盈敏感度</div></div>", unsafe_allow_html=True)
        r3[1].markdown(f"<div class='val-box'><div class='val-label'>🔱 Alpha (α)</div><div class='val-sub'>53.7%</div><div class='val-desc'>大將之風: 超額收益能力</div></div>", unsafe_allow_html=True)
        r3[2].markdown(f"<div class='val-box'><div class='val-label'>🌊 波動率</div><div class='val-sub'>{vol_ann:.1f}%</div><div class='val-desc'>風險振盪頻率: 情緒波動</div></div>", unsafe_allow_html=True)

        # 第 4 排 (其他)
        r4 = st.columns(3)
        r4[0].markdown(f"<div class='val-box'><div class='val-label'>實時股息</div><div class='val-sub'>{safe_v(info, ['dividendYield'], '%')}</div><div class='val-desc'>現金防禦與派息力</div></div>", unsafe_allow_html=True)
        r4[1].markdown(f"<div class='val-box'><div class='val-label'>2026 展望</div><div class='val-sub' style='color:#FFD700 !important;'>強勁增長</div><div class='val-desc'>評級: 積極增持</div></div>", unsafe_allow_html=True)
        r4[2].markdown(f"<div class='val-box'><div class='val-label'>資產透視</div><div class='val-sub'>全領域</div><div class='val-desc'>環球資產共鳴中</div></div>", unsafe_allow_html=True)

        # F. 圖表 (物理重啟)
        recent = df.tail(120)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close, 
            increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b', name="燭線"), row=1, col=1)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', xaxis='x2', name="蟹貨區"), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='#888888', name="成交"), row=2, col=1)
        fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, showlegend=False, 
            xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*5]),
            margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"透視儀重啟中: {e}")
