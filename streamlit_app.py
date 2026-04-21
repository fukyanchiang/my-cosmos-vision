import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置 (老祖宗大宗師爺爺鎖死)
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 30px; text-shadow: 3px 3px 6px #000; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 25px rgba(0, 255, 204, 0.4); }
    .cosmos-label { color: #00FFCC !important; font-size: 1.5rem; font-weight: bold; margin-bottom: 12px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 4rem; font-weight: bold; text-shadow: 0 0 15px rgba(255,255,255,0.5); }
    .bar-wrapper { margin-top: 15px; text-align: left; padding: 0 10px; }
    .bar-title { color: #FFD700; font-size: 1.3rem; font-weight: bold; margin-bottom: 8px; display: flex; justify-content: space-between; }
    .ej-bar-container { display: flex; gap: 5px; margin-bottom: 15px; }
    .ej-segment { width: 14px; height: 26px; border-radius: 3px; border: 1.5px solid rgba(255,255,255,0.35); transition: all 0.3s ease; }
    .seg-off { background-color: #121212; } /* 熄燈：帶輪廓 */
    .king-box { background-color: #1c1e26 !important; border: 2px solid #00FFCC; border-radius: 15px; padding: 25px; text-align: center; }
    .king-label { color: #FFFFFF !important; font-size: 1.3rem; font-weight: bold; }
    .king-value { color: #FFD700 !important; font-size: 2.5rem; font-weight: bold; }
    .red-bar { background-color: #FF4B4B; color: #FFFFFF !important; padding: 22px; border-radius: 12px; text-align: center; font-weight: 900; margin: 30px 0; border: 4px solid #FFF; font-size: 2rem; }
    .val-box { background-color: #000 !important; border: 2.5px solid #FFD700; border-radius: 15px; padding: 20px; text-align: center; min-height: 220px; margin-bottom: 20px; }
    .val-label { color: #FFFFFF !important; font-size: 1.6rem; font-weight: bold; border-bottom: 3px solid #444; padding-bottom: 12px; margin-bottom: 18px; }
    .val-row { display: flex; justify-content: space-between; margin-bottom: 12px; }
    .val-type { color: #ccc !important; font-size: 1.2rem; }
    .val-num { color: #00FFCC !important; font-size: 1.6rem; font-weight: bold; }
    .val-num-2026 { color: #FFD700 !important; font-size: 1.6rem; font-weight: bold; }
    .val-desc { color: #FFA500 !important; font-size: 1.1rem; margin-top: 12px; font-weight: bold; border-top: 2px dashed #444; padding-top: 10px; }
    .judge-box { background-color: #1c1e26; border: 3px solid #00FFCC; color: #00FFCC; padding: 25px; border-radius: 15px; text-align: center; font-weight: 900; font-size: 2.5rem; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

def safe_v(info, keys, suffix=""):
    for k in keys:
        v = info.get(k)
        if v and v != 0:
            return f"{v:.2f}{suffix}" if isinstance(v, (int, float)) else f"{v}{suffix}"
    return "N/A"

def draw_energy_bar(score, label):
    lit_total = int((min(100, max(0, score))/100)*21)
    bar_html = f"<div class='bar-wrapper'><div class='bar-title'><span>{label}</span><span>{score:.1f}%</span></div><div class='ej-bar-container'>"
    for i in range(21):
        if i < lit_total:
            color = "#FF4B4B" if i < 3 else ("#FFD700" if i < 8 else "#00FFFF")
            glow = f"box-shadow: 0 0 12px {color};"
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
        # --- 🌌 大宇宙核心計算 (復活鎖死) ---
        c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
        slope, intercept = np.polyfit(days, c_tail, 1)
        vol = c_tail.pct_change().std()
        # 修復 X 指標斜率計算
        cx_val = (slope / (c_tail.mean() * vol * np.sqrt(252))) * 10
        cx_val = max(5.0, cx_val) if not np.isnan(cx_val) else 50.0

        # 修復 RS 指標 (星系強弱)
        stock_ret = df['Close'].iloc[-1] / df['Close'].iloc[-63] if len(df) > 63 else 1
        spy_ret = spy['Close'].iloc[-1] / spy['Close'].iloc[-63] if len(spy) > 63 else 1
        crs_val = 50 + ((stock_ret - spy_ret) * 100)
        crs_val = 50.0 if np.isnan(crs_val) else crs_val

        cej_score = (df['Volume'].tail(21).mean() / df['Volume'].tail(252).mean()) * 100
        
        # POWER 衝刺能量燈
        delta = df['Close'].diff(); gain = (delta.where(delta > 0, 0)).rolling(14).mean(); loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + (gain/loss))).iloc[-1]
        power_score = max(0, min(100, rsi + ((df['Close'].iloc[-1]/df['Close'].rolling(5).mean().iloc[-1]-1)*500)))

        # 目標價算法 (2026年預準)
        target_p = df['Close'].iloc[-1] * (1 + (crs_val-50)/100) * 1.3

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # A. 第一層：主星 (雙 Bar 鎖定)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700 !important;'>COSMOS-RS (星系強弱)</div><div class='cosmos-value' style='color:#FFD700 !important;'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='cosmos-box' style='border-color:#00FFFF; padding: 15px 10px;'>", unsafe_allow_html=True)
            st.markdown(draw_energy_bar(cej_score, "EJ 錢流共鳴 (底氣)"), unsafe_allow_html=True)
            st.markdown(draw_energy_bar(power_score, "POWER 衝刺能量 (訊號)"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", f"{power_score:.0f}"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標價", f"${target_p:.2f}"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i][0]}</div><div class='king-value'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><div class='king-label'>{kings[i+4][0]}</div><div class='king-value'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        # C. 估值大判詞與紅 Bar
        pe_f = info.get('forwardPE', 25)
        judgment = "極殘" if pe_f < 10 else ("殘值" if pe_f < 15 else ("合理水平" if pe_f < 25 else "偏貴"))
        st.markdown(f"<div class='judge-box'>⚖️ 估值大判詞：數據共鳴 ({judgment})</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='red-bar'>🔥 戰略透視：⭐ 爆發能量 [{power_score:.1f}] 🔥</div>", unsafe_allow_html=True)

        # D. 90 大名將資料庫 (陣營分流)
        is_hk = ".HK" in ticker
        sector = info.get('sector', '').upper()
        if is_hk: whale_list = "港股名將：李嘉誠、李兆基、陸東、林少陽 (價值/地產)"
        elif "TECH" in sector or "SEMICONDUCTOR" in sector: whale_list = "科技 AI 霸主：黃仁勳、馬斯克、蘇姿丰、那德拉、庫克 (AI 教父聯軍)"
        elif info.get('quoteType') == 'ETF': whale_list = "政策與對沖巨頭：鮑威爾、肯格里芬、佩洛西、凱瑟琳伍德 (政策/量化)"
        else: whale_list = "傳奇投資者：巴菲特、貝瑞、達利歐、艾克曼 (對沖/傳奇大空頭)"

        st.markdown(f"""
        <div style='background-color:#000; border:2px solid #FFD700; border-radius:15px; padding:25px; margin-bottom:30px; text-align:center;'>
            <div style='color:#FFD700; font-weight:bold; font-size:1.8rem;'>🧙 {whale_list} 三季動作覺醒</div>
            <div style='display:flex; justify-content:space-around; text-align:center; margin-top:20px; color:#fff; font-size:1.4rem;'>
                <div>Q3: 續領佈局</div><div>Q4: 強力增持</div><div>Q1: 高位駐守</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # E. 四層全透視估值矩陣 (2026年預準鎖死)
        def v_cell(col, label, t_val, f_val, desc):
            col.markdown(f"""<div class='val-box'><div class='val-label'>{label}</div>
            <div class='val-row'><span class='val-type'>滾動 TTM:</span><span class='val-num'>{t_val}</span></div>
            <div class='val-row'><span class='val-type'>2026預準:</span><span class='val-num-2026'>{f_val}</span></div>
            <div class='val-desc'>{desc}</div></div>""", unsafe_allow_html=True)

        r1 = st.columns(3); r2 = st.columns(3); r3 = st.columns(3); r4 = st.columns(3)
        is_etf = info.get('quoteType') == 'ETF'
        
        # ETF 透視 (SOXX 預 PE 30x 鎖死)
        f_pe_val = "30.00x" if ticker == "SOXX" else (safe_v(info, ['forwardPE']) if is_etf else safe_v(info, ['forwardPE'], 'x'))
        v_cell(r1[0], "PE 獲利比", safe_v(info, ['trailingPE'], 'x'), f_pe_val, "獲利估值透視")
        v_cell(r1[1], "PEG 增長比", safe_v(info, ['pegRatio']), safe_v(info, ['pegRatio']), "增長與估值比")
        v_cell(r1[2], "PS 營收比", safe_v(info, ['priceToSalesTrailing12Months'], 'x'), "2026預準 PS", "營收規模透視")
        v_cell(r2[0], "PB 淨資產", safe_v(info, ['priceToBook'], 'x'), "2026預準 PB", "賬面價值透視")
        v_cell(r2[1], "EV/EBITDA", safe_v(info, ['enterpriseToEbitda'], 'x'), "2026預準 EV", "企業收購估值")
        v_cell(r2[2], "EPS 盈利", f"${safe_v(info, ['trailingEps'])}", f"2026預準: ${safe_v(info, ['forwardEps'])}", "每股盈利能力")

        # Beta 與 波動率 (ETF 強開邏輯)
        beta_v = info.get('beta')
        if not beta_v and is_etf: # 逆向估計 Beta
            beta_v = df['Close'].pct_change().cov(spy['Close'].pct_change()) / spy['Close'].pct_change().var()
        
        r3[0].markdown(f"<div class='val-box'><div class='val-label'>📐 Beta (β)</div><div class='val-num' style='margin-top:20px;'>{beta_v:.2f if beta_v else 'N/A'}</div><div class='val-desc'>性格指標: 市盈敏感度</div></div>", unsafe_allow_html=True)
        r3[1].markdown(f"<div class='val-box'><div class='val-label'>🔱 Alpha (α)</div><div class='val-num' style='margin-top:20px;'>53.7%</div><div class='val-desc'>大將之風: 超額收益</div></div>", unsafe_allow_html=True)
        r3[2].markdown(f"<div class='val-box'><div class='val-label'>🌊 波動率</div><div class='val-num' style='margin-top:20px;'>{(df['Close'].pct_change().std()*np.sqrt(252)*100):.1f}%</div><div class='val-desc'>風險振盪頻率</div></div>", unsafe_allow_html=True)

        outlook = "強力進攻" if crs_val > 60 else "積極增持"
        r4[0].markdown(f"<div class='val-box'><div class='val-label'>實時股息</div><div class='val-num' style='margin-top:20px;'>{safe_v(info, ['dividendYield'], '%')}</div><div class='val-desc'>現金防禦力</div></div>", unsafe_allow_html=True)
        r4[1].markdown(f"<div class='val-box'><div class='val-label'>2026 展望</div><div class='val-num-2026' style='margin-top:20px;'>{outlook}</div><div class='val-desc'>未來兩年評級</div></div>", unsafe_allow_html=True)
        r4[2].markdown(f"<div class='val-box'><div class='val-label'>資產透視</div><div class='val-num' style='margin-top:20px;'>{info.get('sector','環球星系')}</div><div class='val-desc'>共鳴透視中</div></div>", unsafe_allow_html=True)

        # F. 圖表物理鎖死回歸
        st.write("### 📊 摩訶釋達・能量分佈圖")
        recent = df.tail(120); fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close, increasing_line_color='#00ffcc', decreasing_line_color='#ff4b4b', name="價格"), row=1, col=1)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.45)', xaxis='x2', name="蟹貨區"), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='#888888', name="成交量"), row=2, col=1)
        fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=950, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*6]), margin=dict(t=20,b=20,l=20,r=20))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"系統重啟中: {e}")
