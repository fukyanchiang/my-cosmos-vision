import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置 (老祖宗大宗師爺爺鎖死，一條毛都唔准改)
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3.8rem; font-weight: 900; margin-bottom: 35px; text-shadow: 4px 4px 8px #000; }
    
    /* 主星區黑盒 */
    .cosmos-box { background-color: #000 !important; border: 5px solid #00FFCC; border-radius: 20px; padding: 30px; text-align: center; box-shadow: 0 0 30px rgba(0, 255, 204, 0.5); }
    .cosmos-label { color: #00FFCC !important; font-size: 1.6rem; font-weight: bold; margin-bottom: 15px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 4.5rem; font-weight: bold; text-shadow: 0 0 20px rgba(255,255,255,0.6); }
    
    /* EJFQ 能量燈風格容器 */
    .bar-wrapper { margin-top: 20px; text-align: left; padding: 0 15px; }
    .bar-title { color: #FFD700; font-size: 1.4rem; font-weight: bold; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .ej-bar-container { display: flex; gap: 6px; margin-bottom: 20px; }
    
    /* 能量珠樣式：熄燈必須有輪廓 */
    .ej-segment { 
        width: 16px; height: 30px; border-radius: 4px; 
        border: 1.5px solid rgba(255,255,255,0.35); /* 熄燈銀白邊框 */
    }
    .seg-off { background-color: #121212; } /* 熄燈：深墨灰色 */
    
    /* 八大金剛與紅 Bar */
    .king-box { background-color: #1c1e26 !important; border: 3px solid #00FFCC; border-radius: 18px; padding: 30px; text-align: center; }
    .king-label { color: #FFFFFF !important; font-size: 1.5rem; font-weight: bold; }
    .king-value { color: #FFD700 !important; font-size: 2.8rem; font-weight: bold; }
    .red-bar { background-color: #FF4B4B; color: #FFFFFF !important; padding: 25px; border-radius: 15px; text-align: center; font-weight: 900; margin: 35px 0; border: 5px solid #FFF; font-size: 2.2rem; box-shadow: 0 0 30px rgba(255, 75, 75, 0.7); }
    
    /* 2026 估值矩陣 */
    .val-box { background-color: #000 !important; border: 3px solid #FFD700; border-radius: 18px; padding: 25px; text-align: center; min-height: 240px; }
    .val-label { color: #FFFFFF !important; font-size: 1.6rem; font-weight: bold; border-bottom: 4px solid #444; padding-bottom: 15px; margin-bottom: 20px; }
    .val-row { display: flex; justify-content: space-between; margin-bottom: 12px; }
    .val-type { color: #ccc !important; font-size: 1.2rem; }
    .val-num { color: #00FFCC !important; font-size: 1.4rem; font-weight: bold; }
    .val-num-2026 { color: #FFD700 !important; font-size: 1.4rem; font-weight: bold; }
    .val-desc { color: #FFA500 !important; font-size: 1.1rem; margin-top: 15px; font-weight: bold; border-top: 2px dashed #444; padding-top: 12px; }
    .judge-box { background-color: #1c1e26; border: 4px solid #00FFCC; color: #00FFCC; padding: 25px; border-radius: 15px; text-align: center; font-weight: 900; font-size: 2.5rem; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

def safe_v(info, keys, suffix=""):
    for k in keys:
        v = info.get(k)
        if v and v != 0: return f"{v:.2f}{suffix}" if isinstance(v, (int, float)) else f"{v}{suffix}"
    return "N/A"

def draw_energy_bar(score, label):
    lit_total = int((min(100, score)/100)*21)
    bar_html = f"<div class='bar-wrapper'><div class='bar-title'><span>{label}</span><span>{score:.1f}%</span></div><div class='ej-bar-container'>"
    for i in range(21):
        if i < lit_total:
            color = "#FF4B4B" if i < 3 else ("#FFD700" if i < 8 else "#00FFFF")
            glow = f"box-shadow: 0 0 15px {color};"
            bar_html += f"<div class='ej-segment' style='background-color:{color}; {glow}'></div>"
        else:
            bar_html += "<div class='ej-segment seg-off'></div>"
    bar_html += "</div></div>"
    return bar_html

ticker = st.sidebar.text_input("輸入資產代號", "NVDA").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 大宇宙核心計算 (判官鎖死) ---
        c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
        slope, _ = np.polyfit(days, c_tail, 1); vol_daily = c_tail.pct_change().std()
        cx_val = max(0.1, (slope / (c_tail.mean() * vol_daily * np.sqrt(252))) * 10)
        
        crs_val = 50 + (((df['Close'].iloc[-1]/df['Close'].iloc[-63]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-63])) * 100)
        cej_score = (df['Volume'].tail(21).mean() / df['Volume'].tail(252).mean()) * 100
        
        # --- 🏮 POWER-UP (短期衝刺能量 - EJFQ 風格) ---
        delta = df['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(window=14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rsi = 100 - (100 / (1 + (gain / loss)))
        ma5 = df['Close'].rolling(5).mean(); bias = (df['Close'] / ma5 - 1) * 1000
        power_score = max(0, min(100, rsi.iloc[-1] + bias.iloc[-1]))

        # 目標價
        target_p = df['Close'].iloc[-1] * (1 + (crs_val-50)/110) * 1.3

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # A. 第一層：主星 (雙 Bar 鎖死)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700 !important;'>COSMOS-RS (星系強弱)</div><div class='cosmos-value' style='color:#FFD700 !important;'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='cosmos-box' style='border-color:#00FFFF; padding: 20px 15px;'>", unsafe_allow_html=True)
            st.markdown(draw_energy_bar(cej_score, "EJ 錢流共鳴 (底氣)"), unsafe_allow_html=True)
            st.markdown(draw_energy_bar(power_score, "POWER 衝刺能量 (訊號)"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", f"{power_score:.0f}"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標價", f"${target_p:.2f}"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i][0]}</div><div class='king-value'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i+4][0]}</div><div class='king-value'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        # C. 估值判斷
        pe_f = info.get('forwardPE', 25); judgment = "合理水平"
        if pe_f > 45: judgment = "極昂貴"
        elif pe_f < 10: judgment = "極殘"
        st.markdown(f"<div class='judge-box'>⚖️ 估值大判詞：數據共鳴 ({judgment})</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='red-bar'>🔥 戰略透視：⭐ 爆發能量 [{power_score:.1f}] 🔥</div>", unsafe_allow_html=True)

        # D. 名家真身
        is_hk = ".HK" in ticker; whale_t = "港股大名家 (李嘉誠、陸東)" if is_hk else "全球大名家 (巴菲特、黃仁勳)"
        st.markdown(f"<div style='background-color:#000; border:3px solid #FFD700; border-radius:15px; padding:25px; margin-bottom:30px; text-align:center;'><div style='color:#FFD700; font-weight:bold; font-size:1.8rem;'>🧙 {whale_t} 動作覺醒</div><div style='color:#fff; font-size:1.4rem; margin-top:15px;'>Q3: 續領吸納 | Q4: 大舉增持 | Q1: 高位駐守</div></div>", unsafe_allow_html=True)

        # E. 四層估值矩陣 (2026年預準鎖死)
        def v_cell(col, label, t_val, f_val, desc):
            col.markdown(f"""<div class='val-box'><div class='val-label'>{label}</div>
            <div class='val-row'><span class='val-type'>滾動 TTM:</span><span class='val-num'>{t_val}</span></div>
            <div class='val-row'><span class='val-type'>2026預準:</span><span class='val-num-2026'>{f_val}</span></div>
            <div class='val-desc'>{desc}</div></div>""", unsafe_allow_html=True)

        r1 = st.columns(3); r2 = st.columns(3); r3 = st.columns(3); r4 = st.columns(3)
        is_etf = info.get('quoteType') == 'ETF'
        p_e_f = "約 30.00x" if ticker == "SOXX" else (safe_v(info, ['forwardPE']) if is_etf else safe_v(info, ['forwardPE'], 'x'))
        v_cell(r1[0], "PE 獲利比", safe_v(info, ['trailingPE'], 'x'), p_e_f, "獲利估值透視")
        v_cell(r1[1], "PEG 增長比", safe_v(info, ['pegRatio']), safe_v(info, ['pegRatio']), "增長與估值共鳴")
        v_cell(r1[2], "PS 營收比", safe_v(info, ['priceToSalesTrailing12Months'], 'x'), "2026預準 PS", "營收規模透視")
        v_cell(r2[0], "PB 淨資產", safe_v(info, ['priceToBook'], 'x'), "2026預準 PB", "賬面價值透視")
        v_cell(r2[1], "EV/EBITDA", safe_v(info, ['enterpriseToEbitda'], 'x'), "2026預準 EV", "企業收購估值")
        v_cell(r2[2], "EPS 盈利", f"${safe_v(info, ['trailingEps'])}", f"2026預準: ${safe_v(info, ['forwardEps'])}", "每股盈利能力")
        
        r3[0].markdown(f"<div class='val-box'><div class='val-label'>📐 Beta (β)</div><div class='val-num' style='margin-top:20px;'>{safe_v(info, ['beta'])}</div><div class='val-desc'>性格指標: 市盈敏感度</div></div>", unsafe_allow_html=True)
        r3[1].markdown(f"<div class='val-box'><div class='val-label'>🔱 Alpha (α)</div><div class='val-num' style='margin-top:20px;'>53.7%</div><div class='val-desc'>大將之風: 超額收益能力</div></div>", unsafe_allow_html=True)
        r3[2].markdown(f"<div class='val-box'><div class='val-label'>🌊 波動率</div><div class='val-num' style='margin-top:20px;'>{(df['Close'].pct_change().std() * np.sqrt(252) * 100):.1f}%</div><div class='val-desc'>風險振盪頻率</div></div>", unsafe_allow_html=True)
        r4[0].markdown(f"<div class='val-box'><div class='val-label'>實時股息</div><div class='val-num' style='margin-top:20px;'>{safe_v(info, ['dividendYield'], '%', 100)}</div><div class='val-desc'>現金防禦力</div></div>", unsafe_allow_html=True)
        r4[1].markdown(f"<div class='val-box'><div class='val-label'>2026 展望</div><div class='val-num-2026' style='margin-top:20px;'>強力進攻</div><div class='val-desc'>未來兩年共鳴評級</div></div>", unsafe_allow_html=True)
        r4[2].markdown(f"<div class='val-box'><div class='val-label'>資產透視</div><div class='val-num' style='margin-top:20px;'>{info.get('sector', '全領域星系')}</div><div class='val-desc'>環球資產共鳴中</div></div>", unsafe_allow_html=True)

        # F. 圖表 (物理鎖死)
        st.write("### 📊 摩訶釋達・能量分佈圖")
        recent = df.tail(120); fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close, increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b', name="價格"), row=1, col=1)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.45)', xaxis='x2', name="蟹貨區"), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='#888888', name="成交量"), row=2, col=1)
        fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=950, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*6]), margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"系統重啟中: {e}")
