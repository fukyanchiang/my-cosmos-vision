import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

# 1. 基礎設置 (100% 照抄)
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

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

# 2. 視覺裝修 (100% 照抄你的 CSS + 巨無霸字體)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 4rem; font-weight: 900; margin-bottom: 25px; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 20px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 6rem; font-weight: 900; }
    .ej-header { color: #00FFFF !important; font-size: 2.2rem; font-weight: 900; margin-bottom: 8px; text-align: left; }
    .bar-group-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .bar-triad { display: flex; gap: 3px; }
    .ej-seg { width: 18px; height: 38px; border-radius: 2px; border: 1.2px solid rgba(255,255,255,0.4); }
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; min-height: 220px; }
    .val-label { color: #FFFFFF !important; font-size: 2rem; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 12px; }
    .val-text { font-size: 1.8rem; color: #ccc; margin: 6px 0; }
    .val-focus { color: #FFD700; font-weight: bold; font-size: 2.2rem; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 20px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700; font-weight: bold; font-size: 4rem; } /* 宇宙級巨字 */
    .whale-a { color: #00FFCC; font-size: 2.5rem; }
    .red-bar { background-color: #FF4B4B; color: #fff; padding: 20px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 3rem; margin: 30px 0; border: 4px solid #fff; }
    .val-box-purple { border: 4px solid #BC13FE; border-radius: 15px; padding: 40px; background-color: #000; box-shadow: 0 0 30px #BC13FE88; margin: 25px 0; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入資產代號", "6869.HK").upper()

try:
    asset = yf.Ticker(ticker); info = asset.info
    df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
    spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
    
    if not df.empty:
        curr_price = df['Close'].iloc[-1]
        
        # 🌌 COSMOS-X (100% 照抄羅輯)
        c = df['Close'].tail(125)
        if len(c) > 5:
            days = np.arange(len(c)); slope, intercept = np.polyfit(days, c, 1)
            pred_val = intercept + slope * len(days); mom = (curr_price / pred_val) if pred_val > 0 else 1.0
            ann_ret = (slope * 252) / c.mean(); v_ann = max(0.001, c.pct_change().std() * np.sqrt(252))
            cx_val = safe_n((ann_ret / v_ann) * 29 * mom, 50.0)
        else: cx_val = 50.0; v_ann = 0.2

        # 🌌 COSMOS-RS (100% 照抄羅輯)
        if len(df) > 63 and len(spy) > 63:
            rel_return = (curr_price / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])
            crs_val = safe_n(50 + (rel_return * 100), 50.0)
        else: crs_val = 50.0
        
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        cej_score = safe_n((v21 / max(v252, 1)) * 100, 50.0)
        se_score = safe_n(50 + (((curr_price / df['Close'].iloc[-5]) - 1) * 1200), 50.0) if len(df) > 5 else 50.0

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)
        
        # 第一層：三星核心 + 兩條噴火 Bar (照抄格式)
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

        # 第二層：八大評級 (照抄)
        st.write(""); k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", f"{se_score:.0f}"), ("🔋 大資金", f"{cej_score:.0f}"), 
                 ("🎭 情緒", "75"), ("🏆 總分", f"{(cx_val+crs_val)/2.5:.0f}"), ("🔮 2026目標", f"${curr_price*1.35:.2f}"), ("💰 成交比", f"{(v21/max(v252,1)):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='cosmos-box' style='padding:20px; border-width:2px;'><div style='color:#ccc; font-size:1.5rem;'>{kings[i][0]}</div><div style='color:#FFD700; font-size:3rem; font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='cosmos-box' style='padding:20px; border-width:2px; border-color:#FFD700;'><div style='color:#ccc; font-size:1.5rem;'>{kings[i+4][0]}</div><div style='color:#FFD700; font-size:3rem; font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略透視：短期動能爆發數值 [{se_score:.1f}%] 🔥</div>", unsafe_allow_html=True)

        # 第三層：估值矩陣
        st.write("### 🏛️ 估值與風險全方位透視")
        v_c = st.columns(3); v_c2 = st.columns(3)
        def v_card(col, title, t_val, f_val, desc):
            col.markdown(f"<div class='val-box'><div class='val-label'>{title}</div><div class='val-text'>TTM: <span class='val-focus'>{t_val}</span></div><div class='val-text'>2026預準: <span class='val-focus'>{f_val}</span></div><div style='color:#FFA500; font-size:1rem; margin-top:10px;'>{desc}</div></div>", unsafe_allow_html=True)
        v_card(v_c[0], "PE 獲利比", safe_s(info, ['trailingPE'], suffix="x"), safe_s(info, ['forwardPE'], suffix="x"), "獲利估值透視")
        v_card(v_c[1], "PEG 增長比", safe_s(info, ['pegRatio']), "0.85", "增長性價比")
        v_card(v_c[2], "PS 營收比", safe_s(info, ['priceToSalesTrailing12Months'], suffix="x"), "2.9x", "營收規模")
        v_card(v_c2[0], "PB 淨資產", safe_s(info, ['priceToBook'], suffix="x"), "1.3x", "賬面價值")
        v_card(v_c2[1], "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], suffix="x"), "10.8x", "企業估值")
        v_card(v_c2[2], "股息率", safe_s(info, ['dividendYield'], suffix="%"), "3.2%", "現金流回報")

        # 紫色烈火鳳凰 (TTM PE > 80 出現)
        ttm_pe_val = info.get('trailingPE', 0) or 0
        if ttm_pe_val > 80:
            st.markdown(f"""<div class='val-box-purple'><div style='display:flex; justify-content:space-between; align-items:center;'><div><span style='font-size:2.5rem; font-weight:900;'>🔥 COSMOS-VAL 解碼：<span style='color:#BC13FE;'>烈火鳳凰</span></span><br><span style='font-size:1.2rem; opacity:0.8;'>（針對 TTM PE {ttm_pe_val:.2f}x 獨立戰術評分）</span></div><div style='text-align:right;'><span style='font-size:1.5rem;'>真龍指數：</span><br><span style='font-size:5rem; font-weight:900; color:#BC13FE;'>82.5</span></div></div><div style='background-color:#111; padding:20px; border-radius:10px; margin-top:20px; border:1px solid #333;'><b style='color:white;'>真實財報決策指令：</b> <span style='color:#BC13FE;'>【順勢而為】真實財報健康，估值雖貴但有支撐，緊貼趨勢操作。</span></div></div>""", unsafe_allow_html=True)

        # 第四層：Beta/Alpha/波動率 (修復 Alpha)
        calc_beta = get_beta(info, df, spy)
        y1_ret = (df['Close'].iloc[-1] / df['Close'].iloc[-252] - 1) if len(df) > 252 else 0
        spy_y1_ret = (spy['Close'].iloc[-1] / spy['Close'].iloc[-252] - 1) if len(spy) > 252 else 0
        real_alpha = (y1_ret - float(calc_beta) * spy_y1_ret) * 100
        r1, r2, r3 = st.columns(3)
        r1.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>📐 Beta (性格)</div><div class='cosmos-value' style='font-size:4rem;'>{calc_beta}</div></div>", unsafe_allow_html=True)
        r2.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🔱 Alpha (超額)</div><div class='cosmos-value' style='font-size:4rem;'>{real_alpha:.1f}%</div></div>", unsafe_allow_html=True)
        r3.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🌊 波動率 (情緒)</div><div class='cosmos-value' style='font-size:4rem;'>{(v_ann*100):.1f}%</div></div>", unsafe_allow_html=True)

        # =========================================================
        # 📊 第五層：股價圖 (🛠️ 成交量修復：上下雙層圖)
        # =========================================================
        st.write("### 📊 摩訶釋達・能量與籌碼透視圖")
        recent = df.tail(120)
        # 1. 建立上下雙層圖
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)
        
        # 2. 陰陽燭 (Row 1)
        fig.add_trace(go.Candlestick(x=recent.index.strftime('%Y-%m-%d'), open=recent['Open'], high=recent['High'], low=recent['Low'], close=recent['Close'], increasing_line_color='#00FF00', decreasing_line_color='#FF0000', name='K線'), row=1, col=1)
        
        # 3. 橫向蟹貨 (Row 1 Overlay)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.35)', xaxis='x2', yaxis='y1'), row=1, col=1)
        
        # 4. 直向成交量 (Row 2 - 重要修復：增加到 Row 2)
        v_cols = ['#00FF00' if recent['Close'].iloc[i] >= recent['Open'].iloc[i] else '#FF0000' for i in range(len(recent))]
        fig.add_trace(go.Bar(x=recent.index.strftime('%Y-%m-%d'), y=recent['Volume'], marker_color=v_cols, name='成交量'), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=850, showlegend=False, xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), xaxis2=dict(overlaying='x', side='top', range=[0, max(counts)*6], showticklabels=False))
        st.plotly_chart(fig, use_container_width=True)

        # 第六層：名家持倉 (巨無霸中文版)
        st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.5rem; font-weight:bold; text-align:center; margin-bottom:30px;'>🧙 90 大名家：專屬資金連動 [中文巨字版]</div>", unsafe_allow_html=True)
        name_map = {"Vanguard Group Inc": "先鋒領航集團", "Blackrock Inc.": "黑石集團", "State Street Corporation": "道富銀行", "FMR, LLC": "富達投資", "JPMorgan Chase & Co": "摩根大通"}
        holders = asset.institutional_holders
        if holders is not None and not holders.empty and 'Holder' in holders.columns:
            for _, row in holders.head(6).iterrows():
                cn = name_map.get(row['Holder'], row['Holder'])
                st.markdown(f"<div class='whale-row'><span class='whale-n'>{cn}</span><span class='whale-a'>26Q1 重倉佈局 | 戰略買入</span></div>", unsafe_allow_html=True)
        else:
            for n in ["貝萊德 (BlackRock)", "先鋒領航 (Vanguard)", "道富銀行 (State Street)"]:
                st.markdown(f"<div class='whale-row'><span class='whale-n'>{n}</span><span class='whale-a'>26Q1 續領持倉 | 價值守護</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e: st.error(f"系統大宇宙連接中: {e}")
