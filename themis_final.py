import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="環球資產透維評估儀", layout="wide")

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

# 2. 視覺裝修 
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

ticker = st.sidebar.text_input("🚀 輸入資產代號", "XLV").upper()

try:
    asset = yf.Ticker(ticker); info = asset.info
    df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
    spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
    
    if not df.empty:
        curr_p = df['Close'].iloc[-1]
        
        # 🌌 COSMOS-X & RS
        c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
        slope, intercept = np.polyfit(days, c_tail, 1); pred = intercept + slope * len(days)
        mom = (curr_p / pred) if pred > 0 else 1.0; v_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
        cx_val = safe_n(((slope * 252) / c_tail.mean() / v_ann) * 29 * mom, 50.0)
        crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])) * 100, 50.0) if len(df) > 63 else 50.0
        
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
        se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0) if len(df) > 5 else 50.0

        st.markdown(f"""<div class='main-title'>環球資產透維評估儀 [{ticker}]</div>""", unsafe_allow_html=True)
        
        # 第一層看板
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"""<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS (星系強弱)</div><div class='cosmos-value'>{crs_val:.1f}</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown("""<div class='cosmos-box' style='border-color:#00FFFF; padding: 20px;'>""", unsafe_allow_html=True)
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
            st.markdown(draw_triad_bar(cej_s, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
            st.markdown(draw_triad_bar(se_s, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
            st.markdown("""</div>""", unsafe_allow_html=True)

        # 🧬 [核心修復: 自動識別 ETF 與個股] 🧬
        st.write("---")
        d_c1, d_c2 = st.columns([1, 2.5])
        
        is_etf = info.get('quoteType') == 'ETF'
        real_roe = info.get('returnOnEquity')
        
        # 如果是 ETF 或者無 ROE，切換至「動能量化引擎」計分
        if is_etf or real_roe is None or real_roe == 0:
            dna_v = round(safe_n((cx_val * 0.5) + (crs_val * 0.5), 50.0), 1)
            dna_title = "ETF 綜合質量基因"
            
            # ETF 專屬 8D 指標
            m8 = {
                "🩸 資金純度 (流動)": int(safe_n(cej_s / 10, 5)),
                "🛡️ 免疫系統 (抗跌)": int(safe_n(crs_val / 10, 5)),
                "🏗️ 心跳頻率 (動能)": int(safe_n(cx_val / 10, 5)),
                "🧬 大腦潛力 (趨勢)": int(safe_n(se_s / 10, 5)),
                "🧱 骨架重量 (規模)": 9 if info.get('totalAssets', 0) > 1e9 else 5,
                "⚡ 物理底盤 (波幅)": int(max(1, 10 - (v_ann * 20))),
                "💰 資本配置 (派息)": int(safe_n(info.get('yield', info.get('dividendYield', 0))*200+2, 5)),
                "📈 經營拐點 (相對)": int(safe_n(crs_val / 10, 5))
            }
        else:
            # 個股保持真實財報計分
            dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)
            dna_title = "投行級股王基因"
            
            # 個股專屬 8D 指標
            m8 = {
                "🩸 血液純度": int(safe_n(info.get('operatingMargins', 0)*30+3, 5)),
                "🛡️ 免疫系統": int(safe_n(real_roe*30+3, 7)),
                "🏗️ 心跳頻率": int(safe_n(info.get('revenueGrowth', 0)*20+4, 6)),
                "🧬 大腦潛力": int(safe_n(info.get('profitMargins', 0)*30+3, 8)),
                "🧱 骨架重量": int(max(1, 10 - safe_n(info.get('priceToBook', 5), 5))),
                "⚡ 物理底盤": 8 if safe_n(info.get('debtToEquity', 150), 150) < 80 else 3,
                "💰 資本配置": int(safe_n(info.get('dividendYield', 0)*200+2, 5)),
                "📈 經營拐點": int(safe_n(info.get('earningsGrowth', 0)*25+4, 8))
            }

        dna_v = max(0.0, min(100.0, dna_v)) 
        
        # 10 級分類邏輯
        if dna_v >= 90:
            d_lv = "第 1 級"
            d_desc = "👑 創世真神"
        elif dna_v >= 80:
            d_lv = "第 2 級"
            d_desc = "🌟 星系霸主"
        elif dna_v >= 70:
            d_lv = "第 3 級"
            d_desc = "🚀 恆星巨頭"
        elif dna_v >= 60:
            d_lv = "第 4 級"
            d_desc = "🛡️ 行星中堅"
        elif dna_v >= 50:
            d_lv = "第 5 級"
            d_desc = "⚖️ 凡骨平庸"
        elif dna_v >= 40:
            d_lv = "第 6 級"
            d_desc = "⚠️ 能量衰退"
        elif dna_v >= 30:
            d_lv = "第 7 級"
            d_desc = "🍂 恆星殞落"
        elif dna_v >= 20:
            d_lv = "第 8 級"
            d_desc = "🩸 基因突變"
        elif dna_v >= 10:
            d_lv = "第 9 級"
            d_desc = "☠️ 黑洞邊緣"
        else:
            d_lv = "第 10 級"
            d_desc = "🪦 宇宙塵埃"

        with d_c1:
            st.markdown(f"""
            <div class='cosmos-box' style='border-color:#FF4B4B; height:380px; display:flex; flex-direction:column; justify-content:center;'>
                <div style='color:#FF4B4B; font-weight:900; font-size:1.8rem;'>🧬 COSMOS-DNA</div>
                <div style='font-size:0.9rem; opacity:0.7; margin:5px 0;'>{dna_title} (100分滿分)</div>
                <div style='font-size:6rem; font-weight:900;'>{dna_v}</div>
                <div style='color:#FFD700; font-size:1rem; font-weight:bold; margin-top:10px;'>
                    [ 註明：共分 10 級，現屬 {d_lv} ]<br>
                    <span style='font-size:1.6rem; color:#FFF;'>{d_desc}</span>
                </div>
            </div>""", unsafe_allow_html=True)
        
        with d_c2:
            st.markdown(f"""**{ticker} ・ 8D 投行精確透視 BAR**""")
            colors_8d = ["#00FFCC", "#00FFCC", "#00FFCC", "#00FFCC", "#FF4B4B", "#BC13FE", "#FFFFFF", "#FFD700"]
            for i, (label, score) in enumerate(m8.items()):
                sc = max(1, min(10, score))
                grid = '<div class="energy-bar-container-8d">' + "".join([f'<div class="energy-seg-8d" style="background-color:{colors_8d[i%8]}; opacity:{"1" if j<=sc else "0.1"};"></div>' for j in range(1,11)]) + '</div>'
                st.markdown(f"""<div style='display:flex; justify-content:space-between; font-weight:bold;'><span>{label}</span><span>{sc}/10</span></div>{grid}""", unsafe_allow_html=True)

        # 第二層評級
        st.write(""); k1 = st.columns(4); k2 = st.columns(4)
        kings = [
            ("📁 質量", f"{dna_v:.0f}"), 
            ("📈 趨勢", f"{crs_val:.0f}"), 
            ("⚡ 動能", f"{se_s:.0f}"), 
            ("🔋 大資金", f"{cej_s:.0f}"), 
            ("🎭 情緒", f"{safe_n(crs_val*0.9, 50):.0f}"), 
            ("🏆 總分", f"{(cx_val+crs_val+se_s)/3:.0f}"), 
            ("🔮 2026目標", f"${info.get('targetMeanPrice', curr_p*1.35):.2f}"), 
            ("💰 成交比", f"{(v2
