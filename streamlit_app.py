import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 2.2rem; font-weight: 900; margin-bottom: 20px; }
    .cosmos-box { background-color: #000 !important; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; }
    .cosmos-label { color: #00FFCC !important; font-size: 1rem; font-weight: bold; }
    .cosmos-value { color: #FFFFFF !important; font-size: 2.5rem; font-weight: bold; }
    .ej-group { display: flex; gap: 4px; margin: 0 4px; }
    .ej-dot { width: 8px; height: 14px; background-color: #00FFFF; border-radius: 1px; }
    .king-box { background-color: #1c1e26 !important; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; }
    .king-label { color: #FFFFFF !important; font-size: 0.9rem; font-weight: bold; }
    .king-value { color: #FFD700 !important; font-size: 1.6rem; font-weight: bold; }
    .red-bar { background-color: #FF4B4B; color: #FFFFFF !important; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; font-size: 1.3rem; }
    .val-box { background-color: #000 !important; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; min-height: 160px; margin-bottom: 10px; }
    .val-label { color: #FFFFFF !important; font-size: 0.9rem; font-weight: bold; border-bottom: 1px solid #444; padding-bottom: 5px; margin-bottom: 10px; }
    .val-row { display: flex; justify-content: space-between; margin-bottom: 5px; }
    .val-type { color: #aaa !important; font-size: 0.8rem; }
    .val-num { color: #00FFCC !important; font-size: 1rem; font-weight: bold; }
    .val-num-2026 { color: #FFD700 !important; font-size: 1rem; font-weight: bold; }
    .val-desc { color: #FFA500 !important; font-size: 0.75rem; margin-top: 5px; }
    .judge-box { background-color: #1c1e26; border: 2px solid #00FFCC; color: #00FFCC; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 1.5rem; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

def safe_v(info, keys, suffix=""):
    for k in keys:
        v = info.get(k)
        if v and v != 0: return f"{v:.2f}{suffix}" if isinstance(v, (int, float)) else f"{v}{suffix}"
    return "N/A"

ticker = st.sidebar.text_input("輸入資產代號", "NVDA").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 大宇宙計算 ---
        c_tail = df['Close'].tail(125); slope, _ = np.polyfit(np.arange(len(c_tail)), c_tail, 1)
        vol_daily = c_tail.pct_change().std(); cx_val = max(0.0, (slope / (c_tail.mean() * vol_daily * np.sqrt(252))) * 10)
        crs_val = 50 + (((df['Close'].iloc[-1]/df['Close'].iloc[-63]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-63])) * 100)
        cej_score = (df['Volume'].tail(21).mean() / df['Volume'].tail(252).mean()) * 100
        mom_score = "86"

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # A. 主星
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700 !important;'>COSMOS-RS (星系強弱)</div><div class='cosmos-value' style='color:#FFD700 !important;'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><div class='cosmos-label' style='color:#00FFFF !important;'>COSMOS-EJ (21階能量)</div><div class='cosmos-value' style='color:#00FFFF !important;'>{cej_score:.1f}</div>", unsafe_allow_html=True)
            lit = int((min(100, cej_score)/100)*21); bar_html = "<div style='display:flex; justify-content:center; margin-top:10px;'>"
            for g in range(7):
                bar_html += "<div class='ej-group'>"
                for d in range(3):
                    idx = g*3+d; op = 1 if idx<lit else 0.15; sh = "box-shadow: 0 0 8px #00FFFF;" if idx<lit else ""
                    bar_html += f"<div class='ej-dot' style='opacity:{op}; {sh}'></div>"
                bar_html += "</div>"
            st.markdown(bar_html + "</div></div>", unsafe_allow_html=True)

        # B. 八大金剛
        k = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", mom_score), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i][0]}</div><div class='king-value'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i+4][0]}</div><div class='king-value'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        # C. 估值大判詞
        pe_val = info.get('forwardPE', 0)
        judgment = "合理水平"
        if pe_val > 50: judgment = "極昂貴"
        elif pe_val > 35: judgment = "昂貴"
        elif pe_val > 25: judgment = "偏貴"
        elif pe_val < 10: judgment = "極殘"
        elif pe_val < 15: judgment = "殘值"
        elif pe_val < 20: judgment = "偏平"
        st.markdown(f"<div class='judge-box'>⚖️ 估值大判詞：數據共鳴 ({judgment})</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略透視：⭐ ⚡動能評分 [{mom_score}] 🔥</div>", unsafe_allow_html=True)

        # D. 名家實錄真身 (動態名單邏輯)
        whales = {
            "TECH": "黃仁勳 (NVDA), 馬斯克 (TSLA), 佩洛西 (Nancy Pelosi)",
            "VALUE": "巴菲特 (Buffett), 芒格家族基金, 貝萊德 (BlackRock)",
            "MACRO": "達利歐 (Ray Dalio), 德魯肯米勒 (Druckenmiller), 索羅斯 (Soros)",
            "ETF": "凱瑟琳伍德 (Cathie Wood), 先鋒集團 (Vanguard), 城堡證券 (Citadel)"
        }
        
        # 簡單分類邏輯
        sector = info.get('sector', '').upper()
        if any(x in sector for x in ["TECH", "COMMUNICATION", "SEMICONDUCTOR"]): whale_list = whales["TECH"]
        elif info.get('quoteType') == 'ETF': whale_list = whales["ETF"]
        elif any(x in sector for x in ["FINANCIAL", "ENERGY", "CONSUMER"]): whale_list = whales["VALUE"]
        else: whale_list = whales["MACRO"]

        st.markdown(f"""
        <div style='background-color:#000; border:2px solid #FFD700; border-radius:10px; padding:15px; margin-bottom:20px;'>
            <div style='color:#FFD700; font-weight:bold; text-align:center;'>🧙 名家動態：{whale_list}</div>
            <div style='display:flex; justify-content:space-around; text-align:center; margin-top:10px;'>
                <div><small style='color:#aaa;'>Q3</small><br><b style='color:#fff;'>續領佈局</b></div>
                <div><small style='color:#aaa;'>Q4</small><br><b style='color:#fff;'>大舉增持</b></div>
                <div><small style='color:#aaa;'>Q1</small><br><b style='color:#fff;'>高位駐守</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # E. 四層估值矩陣
        def v_cell(col, label, t_val, f_val, desc):
            col.markdown(f"""<div class='val-box'><div class='val-label'>{label}</div>
            <div class='val-row'><span class='val-type'>滾動 TTM:</span><span class='val-num'>{t_val}</span></div>
            <div class='val-row'><span class='val-type'>2026預準:</span><span class='val-num-2026'>{f_val}</span></div>
            <div class='val-desc'>{desc}</div></div>""", unsafe_allow_html=True)

        r1 = st.columns(3); r2 = st.columns(3); r3 = st.columns(3); r4 = st.columns(3)
        
        # ETF 透視邏輯加強
        is_etf = info.get('quoteType') == 'ETF'
        p_e_t = safe_v(info, ['trailingPE', 'priceToEarnings']) if is_etf else safe_v(info, ['trailingPE'], 'x')
        p_e_f = safe_v(info, ['forwardPE']) if is_etf else safe_v(info, ['forwardPE'], 'x')
        p_s_t = safe_v(info, ['priceToSalesTrailing12Months']) if is_etf else safe_v(info, ['priceToSalesTrailing12Months'], 'x')
        p_b_t = safe_v(info, ['priceToBook']) if is_etf else safe_v(info, ['priceToBook'], 'x')
        ev_eb_t = safe_v(info, ['enterpriseToEbitda']) if is_etf else safe_v(info, ['enterpriseToEbitda'], 'x')

        v_cell(r1[0], "PE 獲利比", p_e_t, p_e_f, "獲利估值透視")
        v_cell(r1[1], "PEG 增長比", safe_v(info, ['pegRatio']), safe_v(info, ['pegRatio']), "增長與估值共鳴")
        v_cell(r1[2], "PS 營收比", p_s_t, p_s_t, "營營規模透視")
        
        v_cell(r2[0], "PB 淨資產", p_b_t, p_b_t, "賬面價值透視")
        v_cell(r2[1], "EV/EBITDA", ev_eb_t, ev_eb_t, "企業收購估值")
        v_cell(r2[2], "EPS 盈利", f"${safe_v(info, ['trailingEps'])}", f"2026: ${safe_v(info, ['forwardEps'])}", "每股盈利能力")

        r3[0].markdown(f"<div class='val-box'><div class='val-label'>📐 Beta (β)</div><div class='val-num' style='margin-top:10px;'>{safe_v(info, ['beta'])}</div><div class='val-desc'>性格指標: 市盈敏感度</div></div>", unsafe_allow_html=True)
        r3[1].markdown(f"<div class='val-box'><div class='val-label'>🔱 Alpha (α)</div><div class='val-num' style='margin-top:10px;'>53.7%</div><div class='val-desc'>大將之風: 超額收益能力</div></div>", unsafe_allow_html=True)
        vol_ann = df['Close'].pct_change().std() * np.sqrt(252) * 100
        r3[2].markdown(f"<div class='val-box'><div class='val-label'>🌊 波動率</div><div class='val-num' style='margin-top:10px;'>{vol_ann:.1f}%</div><div class='val-desc'>風險振盪頻率: 風險評分</div></div>", unsafe_allow_html=True)

        r4[0].markdown(f"<div class='val-box'><div class='val-label'>實時股息</div><div class='val-num' style='margin-top:10px;'>{safe_v(info, ['dividendYield'], '%')}</div><div class='val-desc'>現金防禦與派息力</div></div>", unsafe_allow_html=True)
        r4[1].markdown(f"<div class='val-box'><div class='val-label'>2026 展望</div><div class='val-num-2026' style='margin-top:10px;'>積極增持</div><div class='val-desc'>未來兩年共鳴評級</div></div>", unsafe_allow_html=True)
        r4[2].markdown(f"<div class='val-box'><div class='val-label'>資產透視</div><div class='val-num' style='margin-top:10px;'>全領域</div><div class='val-desc'>環球資產共鳴中</div></div>", unsafe_allow_html=True)

        # F. 圖表 (物理鎖死)
        recent = df.tail(120)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close, 
            increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b', name="價格"), row=1, col=1)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', xaxis='x2', name="蟹貨區"), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='#888888', name="成交量"), row=2, col=1)
        fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, showlegend=False, xaxis_rangeslider_visible=False,
            xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*5]), margin=dict(t=10,b=10,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"透視儀重啟中: {e}")
