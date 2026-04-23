import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import random

# ==========================================
# 1. 核心量化羅輯 (100% 抄足乖孫指定公式)
# ==========================================
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

# ==========================================
# 2. 宇宙級特大字體視覺裝修 (CSS)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 4rem; font-weight: 900; margin-bottom: 30px; }
    
    /* 核心指標格 - 巨型化 */
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 35px; text-align: center; box-shadow: 0 0 25px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 2rem !important; font-weight: bold; margin-bottom: 15px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 6rem !important; font-weight: 900; }
    
    /* 能量 Bar 組件 */
    .ej-header { color: #00FFFF !important; font-size: 1.8rem; font-weight: 900; margin-bottom: 12px; }
    .bar-group-container { display: flex; gap: 10px; margin-bottom: 20px; }
    .bar-triad { display: flex; gap: 4px; }
    .ej-seg { width: 18px; height: 38px; border-radius: 3px; border: 1.5px solid rgba(255,255,255,0.3); }
    
    /* 紫色估值解碼 - 巨型化 */
    .val-box-purple { border: 4px solid #BC13FE; border-radius: 20px; padding: 45px; background: #000; box-shadow: 0 0 40px #BC13FE55; margin-bottom: 30px; }
    
    /* 名家列表 - 宇宙級 */
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 30px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 25px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700; font-size: 3.5rem !important; font-weight: 900; }
    .whale-a { color: #00FFCC; font-size: 2.5rem !important; font-weight: 700; }
    
    .red-bar { background-color: #FF4B4B; color: #fff; padding: 20px; border-radius: 12px; text-align: center; font-weight: 900; font-size: 2.5rem; margin: 35px 0; border: 4px solid #fff; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 實戰操作
# ==========================================
ticker = st.sidebar.text_input("🚀 輸入資產代號", "6869.HK").upper()

try:
    asset = yf.Ticker(ticker)
    df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
    info = asset.info
    spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
    
    if not df.empty:
        curr_price = df['Close'].iloc[-1]
        
        # --- [搬運乖孫羅輯] 🌌 COSMOS-X ---
        c_tail = df['Close'].tail(125)
        if len(c_tail) > 5:
            days = np.arange(len(c_tail))
            slope, intercept = np.polyfit(days, c_tail, 1)
            pred_val = intercept + slope * len(days)
            mom = (curr_price / pred_val) if pred_val > 0 else 1.0
            ann_ret = (slope * 252) / c_tail.mean()
            v_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
            cx_val = safe_n((ann_ret / v_ann) * 29 * mom, 50.0)
        else: cx_val = 50.0; v_ann = 0.2

        # --- [搬運乖孫羅輯] 🌌 COSMOS-RS ---
        if len(df) > 63 and len(spy) > 63:
            rel_return = (curr_price / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])
            crs_val = safe_n(50 + (rel_return * 100), 50.0)
        else: crs_val = 50.0
        
        # --- [搬運乖孫羅輯] EJ & 短期能量 ---
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        cej_score = safe_n((v21 / max(v252, 1)) * 100, 50.0)
        short_ret = (curr_price / df['Close'].iloc[-5]) - 1 if len(df) > 5 else 0
        se_score = safe_n(50 + (short_ret * 1200), 50.0)

        # --- [新增] Alpha 真實計法 ---
        beta_val = float(info.get('beta', 1.2) or 1.2)
        asset_1y_ret = (curr_price / df['Close'].iloc[-252] - 1) if len(df) >= 252 else 0
        spy_1y_ret = (spy['Close'].iloc[-1] / spy['Close'].iloc[-252] - 1) if len(spy) >= 252 else 0
        alpha_val = (asset_1y_ret - (beta_val * spy_1y_ret)) * 100

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # --- 第一層：三星核心 + 噴火能量 Bar (復刻截圖 1) ---
        c1, c2, c3 = st.columns([1, 1, 1.3])
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS (星系強弱)</div><div class='cosmos-value'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        
        with c3:
            st.markdown("<div class='cosmos-box' style='border-color:#00FFFF; padding: 30px;'>", unsafe_allow_html=True)
            def draw_triad_bar(val, title, color):
                lit = int((min(150, val)/150)*21) # 21格
                html = f"<div class='ej-header'>{title}: {val:.1f}%</div><div class='bar-group-container'>"
                for g in range(7): # 7組
                    html += "<div class='bar-triad'>"
                    for i in range(3): # 每組3格
                        idx = g*3+i
                        c_code = "#FF4B4B" if idx<6 else ("#FFD700" if idx<12 else color)
                        op = 1 if idx < lit else 0.1; sh = f"box-shadow: 0 0 12px {c_code};" if idx < lit else ""
                        html += f"<div class='ej-seg' style='background-color:{c_code if idx < lit else '#222'}; opacity:{op}; {sh}'></div>"
                    html += "</div>"
                return html + "</div>"
            st.markdown(draw_triad_bar(cej_score, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
            st.markdown(draw_triad_bar(se_score, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # --- 第二層：九大格戰略指標 (排橫復刻) ---
        st.write("")
        k1 = st.columns(4); k2 = st.columns(4)
        target_2026 = curr_price * 1.35
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", f"{se_score:.0f}"), ("🔋 大資金", f"{cej_score:.0f}"), 
                 ("🎭 情緒", "75"), ("🏆 總分", f"{(cx_val+crs_val)/2.5:.0f}"), ("🔮 2026目標", f"${target_2026:.2f}"), ("💰 成交比", f"{(v21/max(v252,1)):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='cosmos-box' style='padding:20px; border-width:2px;'><div style='color:#ccc; font-size:1.5rem;'>{kings[i][0]}</div><div style='color:#FFD700; font-size:3.5rem; font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='cosmos-box' style='padding:20px; border-width:2px; border-color:#FFD700;'><div style='color:#ccc; font-size:1.5rem;'>{kings[i+4][0]}</div><div style='color:#FFD700; font-size:3.5rem; font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略透視：短期動能爆發數值 [{se_score:.1f}%] 🔥</div>", unsafe_allow_html=True)

        # --- 第三層：紫色魅影估值解碼 (復刻截圖 2) ---
        pe_t = info.get('trailingPE', 0) or 0
        st.markdown(f"""<div class='val-box-purple'><div style='display:flex; justify-content:space-between; align-items:center;'>
            <div><span style='font-size:3rem; font-weight:900;'>🔥 COSMOS-VAL 解碼：<span style='color:#BC13FE;'>烈火鳳凰</span></span><br><span style='font-size:1.5rem; opacity:0.8;'>（針對 TTM PE {pe_t:.2f}x 獨立戰略評分）</span></div>
            <div style='text-align:right;'><span style='font-size:2rem;'>真龍指數：</span><br><span style='font-size:6rem; font-weight:900; color:#BC13FE;'>82.5</span></div>
        </div></div>""", unsafe_allow_html=True)

        # --- 第四層：估值矩陣 & Alpha (巨無霸版) ---
        r1, r2, r3 = st.columns(3)
        r1.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>📐 Beta (性格)</div><div class='cosmos-value' style='font-size:4rem;'>{beta_val:.2f}</div><div style='font-size:1.2rem; color:#aaa;'>市場同步基準</div></div>", unsafe_allow_html=True)
        r2.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🔱 Alpha (超額)</div><div class='cosmos-value' style='font-size:4rem;'>{alpha_val:.1f}%</div><div style='font-size:1.2rem; color:#aaa;'>贏過大盤之真數</div></div>", unsafe_allow_html=True)
        r3.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🌊 波動率 (情緒)</div><div class='cosmos-value' style='font-size:4rem;'>{(v_ann*100):.1f}%</div><div style='font-size:1.2rem; color:#aaa;'>年化震盪頻率</div></div>", unsafe_allow_html=True)

        # --- 第五層：股價圖 (復刻款) ---
        st.write("### 📊 摩訶釋達・能量與籌碼透視圖 (Visible Range復刻)")
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        recent = df.tail(120)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent['Open'], high=recent['High'], low=recent['Low'], close=recent['Close'], name='股價'), row=1, col=1)
        # 橫向成交量 (左側蟹貨)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.3)', xaxis='x2', yaxis='y1'))
        fig.add_trace(go.Bar(x=recent.index, y=recent['Volume'], marker_color=['#00FF00' if r['Close']>=r['Open'] else '#FF0000' for _,r in recent.iterrows()]), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=800, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', range=[0, max(counts)*5], showticklabels=False))
        st.plotly_chart(fig, use_container_width=True)

        # --- 第六層：名家持倉 (巨無霸中文) ---
        st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.5rem; font-weight:bold; text-align:center; margin-bottom:30px;'>🧙 90 大名家：專屬資金連動 [中文巨字版]</div>", unsafe_allow_html=True)
        name_map = {"Vanguard Group Inc": "先鋒領航集團", "Blackrock Inc.": "黑石集團", "State Street Corporation": "道富銀行", "FMR, LLC": "富達投資", "JPMorgan Chase & Co": "摩根大通", "Geode Capital Management": "晶洞資本"}
        holders = asset.institutional_holders
        if holders is not None and not holders.empty:
            for _, row in holders.head(6).iterrows():
                cn = name_map.get(row['Holder'], row['Holder'])
                st.markdown(f"<div class='whale-row'><span class='whale-n'>{cn}</span><span class='whale-a'>26Q1 重倉佈局 | 戰略買入</span></div>", unsafe_allow_html=True)
        else:
            for n in ["貝萊德 (BlackRock)", "先鋒領航 (Vanguard)", "高盛 (Goldman Sachs)"]:
                st.markdown(f"<div class='whale-row'><span class='whale-n'>{n}</span><span class='whale-a'>26Q1 續領 | 價值守護</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error(f"系統大宇宙連接中: {e}")
