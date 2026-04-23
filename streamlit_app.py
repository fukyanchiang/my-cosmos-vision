import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="COSMOS 戰略指揮部 V44.4", layout="wide")

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

# --- 核心版塊數據庫 (美港雙通) ---
US_SECTOR_MAP = {
    "半導體 (SMH)": "SMH", "科技 (XLK)": "XLK", "通訊 (XLC)": "XLC", "可選消費 (XLY)": "XLY",
    "金融 (XLF)": "XLF", "醫療 (XLV)": "XLV", "能源 (XLE)": "XLE", "工業 (XLI)": "XLI", 
    "必消 (XLP)": "XLP", "公用事業 (XLU)": "XLU", "太陽能 (TAN)": "TAN", "黃金礦工 (GDX)": "GDX"
}

US_COMPONENTS = {
    "半導體 (SMH)": ["NVDA", "TSM", "AVGO", "ASML", "AMD", "QCOM", "TXN", "MU", "INTC"],
    "科技 (XLK)": ["AAPL", "MSFT", "NVDA", "AVGO", "ADBE", "CRM", "AMD", "ACN", "CSCO"],
    "通訊 (XLC)": ["META", "GOOGL", "NFLX", "DIS", "CMCSA", "TMUS", "CHTR", "TTWO"],
    "可選消費 (XLY)": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "BKNG", "SBUX"]
}

HK_SECTOR_MAP = {
    "科網巨頭 (ATMXJ)": ["0700.HK", "9988.HK", "3690.HK", "1810.HK", "9618.HK"],
    "汽車製造 (EV)": ["1211.HK", "2015.HK", "9866.HK", "9868.HK", "0175.HK"],
    "內銀與金融 (Fin)": ["0005.HK", "0939.HK", "1398.HK", "3988.HK", "2318.HK"],
    "高息電訊 (Telecom)": ["0941.HK", "0728.HK", "0762.HK"],
    "三桶油與煤炭 (Energy)": ["0883.HK", "0857.HK", "0386.HK", "1088.HK"]
}

# 2. 視覺裝修 (CSS)
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
    .radar-box { background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000 !important; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; margin-bottom: 20px; border: 2px solid #FFF; font-size: 1.5rem; }
    .radar-on { background: linear-gradient(135deg, #00FFCC 0%, #00FFA5 100%); }
    .scan-card { background-color: #111; border-left: 5px solid #00FFCC; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .scan-card-fire { border-left: 5px solid #FF4B4B; background-color: #310000; }
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700; font-weight: bold; font-size: 2.5rem; }
    .whale-a { color: #00FFCC; font-size: 1.6rem; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# 3. 側邊欄控制
st.sidebar.markdown("## 🛰️ 戰術控制台")
app_mode = st.sidebar.radio("請選擇操作", ["📡 美股版塊熱力圖", "📡 港股版塊熱力圖", "🔍 版塊內尋龍掃描", "🚀 個股深度透視"])

# ==========================================
# 模式 A1：美股版塊掃描 
# ==========================================
if app_mode == "📡 美股版塊熱力圖":
    st.markdown("<h1 class='main-title'>🇺🇸 全美星系版塊能量分布</h1>", unsafe_allow_html=True)
    spy_data = yf.Ticker("SPY").history(period="60d")['Close']
    results = []
    with st.spinner('掃描美股版塊中...'):
        for name, sym in US_SECTOR_MAP.items():
            try:
                d = yf.Ticker(sym).history(period="60d")['Close']
                if len(d) >= 20:
                    rs = 50 + ((d.iloc[-1]/d.iloc[-20]) - (spy_data.iloc[-1]/spy_data.iloc[-20])) * 100
                    results.append({"版塊": name, "RS強弱": round(rs, 1)})
            except: pass
    if results:
        df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=False)
        fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["版塊"], orientation='h', marker=dict(color=df_rs["RS強弱"], colorscale='Portland')))
        fig.update_layout(template="plotly_dark", height=600, title="版塊相對強度 (RS > 50 代表跑贏標普500)")
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 模式 A2：港股版塊掃描
# ==========================================
elif app_mode == "📡 港股版塊熱力圖":
    st.markdown("<h1 class='main-title'>🇭🇰 港股八大星系能量熱力圖</h1>", unsafe_allow_html=True)
    hsi_data = yf.Ticker("^HSI").history(period="60d")['Close']
    results = []
    with st.spinner('計算港股資金流向中...'):
        for sector_name, tickers in HK_SECTOR_MAP.items():
            sector_rs_list = []
            for t in tickers:
                try:
                    d = yf.Ticker(t).history(period="60d")['Close']
                    if len(d) >= 20 and len(hsi_data) >= 20:
                        rs = 50 + ((d.iloc[-1]/d.iloc[-20]) - (hsi_data.iloc[-1]/hsi_data.iloc[-20])) * 100
                        sector_rs_list.append(rs)
                except: pass
            if sector_rs_list:
                results.append({"版塊": sector_name, "RS強弱": round(np.mean(sector_rs_list), 1)})
    if results:
        df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=False)
        fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["版塊"], orientation='h', marker=dict(color=df_rs["RS強弱"], colorscale='Viridis')))
        fig.update_layout(template="plotly_dark", height=500, title="版塊相對強度 (RS > 50 代表跑贏恆生指數)")
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 模式 B：版塊內尋龍掃描 (港美雙通版)
# ==========================================
elif app_mode == "🔍 版塊內尋龍掃描":
    st.markdown("<h1 class='main-title'>🔍 跨星系版塊尋龍雷達</h1>", unsafe_allow_html=True)
    market_choice = st.sidebar.selectbox("1. 選擇市場", ["美股市場", "港股市場"])
    
    if market_choice == "美股市場":
        target_sector = st.sidebar.selectbox("2. 選擇美股版塊", list(US_COMPONENTS.keys()))
        tickers_to_scan = US_COMPONENTS[target_sector]
        bench_sym = "SPY"
    else:
        target_sector = st.sidebar.selectbox("2. 選擇港股版塊", list(HK_SECTOR_MAP.keys()))
        tickers_to_scan = HK_SECTOR_MAP[target_sector]
        bench_sym = "^HSI"
        
    scan_btn = st.sidebar.button("📡 開始全方位掃描！")
    
    if scan_btn:
        st.markdown(f"### 正在掃描 【{target_sector}】 核心龍頭...")
        bench_data = yf.Ticker(bench_sym).history(period="2y").dropna(subset=['Close'])
        breakout_found = False
        progress_bar = st.progress(0)
        
        for idx, t in enumerate(tickers_to_scan):
            progress_bar.progress((idx + 1) / len(tickers_to_scan))
            try:
                asset = yf.Ticker(t); info = asset.info
                df = asset.history(period="1y").dropna(subset=['Close', 'Volume'])
                if len(df) > 63:
                    curr_p = df['Close'].iloc[-1]
                    crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (bench_data['Close'].iloc[-1] / bench_data['Close'].iloc[-63])) * 100, 50.0)
                    v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
                    cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
                    se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0)
                    real_roe = info.get('returnOnEquity', 0) or 0
                    dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)

                    if se_s > 85 and cej_s > 110 and crs_val > 52:
                        breakout_found = True
                        st.markdown(f"""
                        <div class='scan-card scan-card-fire'>
                            <h2 style='color:#FFD700; margin:0;'>🎯 {t} | 能量共振！起飛訊號！</h2>
                            <p style='margin:5px 0; color:#ddd;'>🧬 DNA: <b>{dna_v}</b> | ⚡ SE: <b style='color:#FF4B4B;'>{se_s:.1f}</b> | 🔋 EJ: <b style='color:#00FFCC;'>{cej_s:.1f}</b> | 📈 RS: <b>{crs_val:.1f}</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='scan-card'><h4 style='color:#ccc; margin:0;'>💤 {t} | 能量蓄勢中</h4></div>", unsafe_allow_html=True)
            except: pass
            
        if not breakout_found: st.warning("目前該版塊暫無龍頭股觸發起步訊號。")

# ==========================================
# 模式 C：個股深度透視
# ==========================================
else:
    ticker = st.sidebar.text_input("🚀 輸入資產代號", "NVDA").upper()
    detect_btn = st.sidebar.button("📡 掃描趨勢爆發起點")
    
    try:
        asset = yf.Ticker(ticker); info = asset.info
        df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
        is_hk = ".HK" in ticker
        spy = yf.Ticker("^HSI" if is_hk else "SPY").history(period="2y").dropna(subset=['Close'])
        
        if not df.empty:
            curr_p = df['Close'].iloc[-1]
            c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
            slope, intercept = np.polyfit(days, c_tail, 1)
            v_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
            cx_val = safe_n(((slope * 252) / c_tail.mean() / v_ann) * 29, 50.0)
            crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])) * 100, 50.0)
            v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
            cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
            se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0)

            st.markdown(f"<div class='main-title'>環球資產透維評估儀 [{ticker}]</div>", unsafe_allow_html=True)
            if detect_btn:
                if se_s > 85 and cej_s > 110 and crs_val > 52:
                    st.markdown(f"<div class='radar-box radar-on'>🎯 偵測到【起步訊號】：資金正極速湧入 {ticker}！</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='radar-box'>💤 掃描完畢：{ticker} 尚未到達能量爆發點。</div>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS</div><div class='cosmos-value'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div class='cosmos-box' style='border-color:#00FFFF; padding: 20px;'>", unsafe_allow_html=True)
                st.markdown(draw_triad_bar(cej_s, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
                st.markdown(draw_triad_bar(se_s, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.write("---")
            d_c1, d_c2 = st.columns([1, 2.5])
            is_etf = info.get('quoteType') == 'ETF'
            real_roe = info.get('returnOnEquity', 0)
            if is_etf or real_roe == 0:
                dna_v = round(safe_n((cx_val * 0.5) + (crs_val * 0.5), 50.0), 1)
                m8 = {"🩸 流動資金": int(safe_n(cej_s/10,5)), "🛡️ 抗跌系統": int(safe_n(crs_val/10,5)), "🏗️ 動能頻率": int(safe_n(cx_val/10,5)), "🧬 趨勢潛力": int(safe_n(se_s/10,5)), "🧱 規模底盤": 8, "⚡ 波幅控制": 7, "💰 派息防守": 5, "📈 相對轉勢": 6}
            else:
                dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)
                m8 = {"🩸 血液純度": int(safe_n(info.get('operatingMargins', 0)*30+3, 5)), "🛡️ 免疫系統": int(safe_n(real_roe*30+3, 7)), "🏗️ 心跳頻率": int(safe_n(info.get('revenueGrowth', 0)*20+4, 6)), "🧬 大腦潛力": int(safe_n(info.get('profitMargins', 0)*30+3, 8)), "🧱 骨架重量": int(max(1, 10 - safe_n(info.get('priceToBook', 5), 5))), "⚡ 物理底盤": 8 if safe_n(info.get('debtToEquity', 150), 150) < 80 else 3, "💰 資本配置": int(safe_n(info.get('dividendYield', 0)*200+2, 5)), "📈 業績拐點": int(safe_n(info.get('earningsGrowth', 0)*25+4, 8))}
            
            dna_v = max(0.0, min(100.0, dna_v)) 
            if dna_v >= 80: d_lv, d_desc = "第 2 級", "🌟 星系霸主"
            elif dna_v >= 50: d_lv, d_desc = "第 5 級", "⚖️ 凡骨平庸"
            else: d_lv, d_desc = "第 9 級", "☠️ 黑洞邊緣"

            with d_c1:
                st.markdown(f"<div class='cosmos-box' style='border-color:#FF4B4B; height:380px; display:flex; flex-direction:column; justify-content:center;'><div style='color:#FF4B4B; font-weight:900; font-size:1.8rem;'>🧬 COSMOS-DNA</div><div style='font-size:6rem; font-weight:900;'>{dna_v}</div><div style='color:#FFD700; margin-top:10px;'>[ 現屬 {d_lv} ]<br><span style='font-size:1.6rem; color:#FFF;'>{d_desc}</span></div></div>", unsafe_allow_html=True)
            with d_c2:
                st.markdown(f"**{ticker} ・ 8D 投行精確透視 BAR**")
                colors_8d = ["#00FFCC", "#00FFCC", "#00FFCC", "#00FFCC", "#FF4B4B", "#BC13FE", "#FFFFFF", "#FFD700"]
                for i, (label, score) in enumerate(m8.items()):
                    sc = max(1, min(10, score))
                    grid = '<div class="energy-bar-container-8d">' + "".join([f'<div class="energy-seg-8d" style="background-color:{colors_8d[i%8]}; opacity:{"1" if j<=sc else "0.1"};"></div>' for j in range(1,11)]) + '</div>'
                    st.markdown(f"<div style='display:flex; justify-content:space-between;'><span>{label}</span><span>{sc}/10</span></div>{grid}", unsafe_allow_html=True)

            st.write(""); k1 = st.columns(4); k2 = st.columns(4)
            target_p = info.get('targetMeanPrice')
            val_target_str = f"${target_p:.2f}" if target_p else "N/A"
            kings = [("📁 質量", f"{dna_v:.0f}"), ("📈 趨勢", f"{crs_val:.0f}"), ("⚡ 動能", f"{se_s:.0f}"), ("🔋 大資金", f"{cej_s:.0f}"), ("🎭 情緒", f"{(crs_val*0.9):.0f}"), ("🏆 總分", f"{(cx_val+crs_val+se_s)/3:.0f}"), ("🔮 12M目標", val_target_str), ("💰 成交比", f"{(v21/max(v252,1)):.1f}x")]
            for i in range(4):
                k1[i].markdown(f"<div class='cosmos-box' style='padding:15px; border-width:2px;'><div style='color:#ccc;'>{kings[i][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
                k2[i].markdown(f"<div class='cosmos-box' style='padding:15px; border-width:2px; border-color:#FFD700;'><div style='color:#ccc;'>{kings[i+4][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

            st.markdown(f"<div class='red-bar'>🔥 戰略透視：短期動能爆發數值 [{se_s:.1f}%] 🔥</div>", unsafe_allow_html=True)
            v1, v2, v3 = st.columns(3); v4, v5, v6 = st.columns(3)
            def v_card(col, title, t_val, f_val, desc):
                col.markdown(f"<div class='val-box'><div class='val-label'>{title}</div><div class='val-text'>TTM: <span class='val-focus'>{t_val}</span></div><div class='val-text'>12M預期: <span class='val-focus'>{f_val}</span></div><div style='color:#FFA500; font-size:0.9rem; margin-top:10px;'>{desc}</div></div>", unsafe_allow_html=True)
            v_card(v1, "PE 獲利比", safe_s(info, ['trailingPE'], "x"), safe_s(info, ['forwardPE'], "x"), "獲利估值透視")
            v_card(v2, "PEG 增長比", safe_s(info, ['pegRatio']), "N/A", "增長性價比")
            v_card(v3, "PS 銷售比", safe_s(info, ['priceToSalesTrailing12Months'], "x"), "N/A", "銷售規模")
            v_card(v4, "PB 淨資產", safe_s(info, ['priceToBook'], "x"), "N/A", "賬面價值")
            v_card(v5, "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], "x"), "N/A", "企業估值")
            v_card(v6, "股息率", safe_s(info, ['dividendYield', 'yield'], "%"), "N/A", "現金流回報")

            ttm_pe = info.get('trailingPE', 0) or 0
            if ttm_pe > 80 and not is_etf:
                dragon_index = round((dna_v * 0.4) + (cx_val * 0.3) + (crs_val * 0.3), 1)
                if dragon_index >= 80: t_lv, t_desc, val_title, val_color, act_desc = "第 1 級", "極致真龍", "🔥 烈火鳳凰", "#BC13FE", "【順勢而為】真實財報極度健康，估值雖貴但有強大動能支撐。"
                elif dragon_index >= 40: t_lv, t_desc, val_title, val_color, act_desc = "第 3 級", "中庸凡骨", "⚠️ 海市蜃樓", "#FFA500", "【謹慎觀望】動能平平，估值偏高。"
                else: t_lv, t_desc, val_title, val_color, act_desc = "第 4 級", "高危泥鰍", "☠️ 末路狂花", "#FF4B4B", "【規避風險】財報轉弱且動能破位。"
                st.markdown(f"<div style='border: 4px solid {val_color}; border-radius: 15px; padding: 30px; background-color: #000; box-shadow: 0 0 30px {val_color}66; margin: 25px 0;'><div style='display:flex; justify-content:space-between;'><div><span style='font-size:2.2rem; font-weight:900;'>COSMOS-VAL：<span style='color:{val_color};'>{val_title}</span></span><br><span>[ 屬 {t_lv} ({t_desc}) ]</span></div><div style='text-align:right;'><span style='font-size:5rem; font-weight:900; color:{val_color};'>{dragon_index}</span></div></div><div style='background-color:#111; padding:20px; border-radius:10px; margin-top:20px;'><b style='color:white;'>決策指令：</b> <span style='color:{val_choice if "val_choice" in locals() else val_color};'>{act_desc}</span></div></div>", unsafe_allow_html=True)

            st.write("### 📊 摩訶釋達・能量與籌碼透視圖")
            recent = df.tail(120); dates = recent.index.strftime('%Y-%m-%d')
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=dates, open=recent['Open'], high=recent['High'], low=recent['Low'], close=recent['Close'], name='股價'), row=1, col=1)
            fig.add_trace(go.Bar(x=dates, y=recent['Volume'], marker_color=['#00FF00' if recent['Close'].iloc[i] >= recent['Open'].iloc[i] else '#FF0000' for i in range(len(recent))], name='成交量'), row=2, col=1)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center;'>🧙 90 大名家：真實申報持倉</div>", unsafe_allow_html=True)
            holders = asset.institutional_holders
            if holders is not None and not holders.empty:
                for _, row in holders.head(8).iterrows():
                    st.markdown(f"<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>持有 {row.get('Shares',0):,.0f} 股</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e: st.error(f"系統診斷中: {e}")
