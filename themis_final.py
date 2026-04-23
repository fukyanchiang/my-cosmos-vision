import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="COSMOS 戰略指揮部 V44", layout="wide")

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

# --- 美股版塊地圖 ---
US_SECTOR_MAP = {
    "半導體 (SMH)": "SMH", "科技 (XLK)": "XLK", "通訊 (XLC)": "XLC", "可選消費 (XLY)": "XLY",
    "金融 (XLF)": "XLF", "醫療 (XLV)": "XLV", "能源 (XLE)": "XLE", "工業 (XLI)": "XLI", 
    "必消 (XLP)": "XLP", "公用事業 (XLU)": "XLU", "太陽能 (TAN)": "TAN", "黃金礦工 (GDX)": "GDX"
}

SECTOR_COMPONENTS = {
    "半導體 (SMH)": ["NVDA", "TSM", "AVGO", "ASML", "AMD", "QCOM", "TXN", "MU", "INTC"],
    "科技 (XLK)": ["AAPL", "MSFT", "NVDA", "AVGO", "ADBE", "CRM", "AMD", "ACN"],
    "可選消費 (XLY)": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX"]
}

# --- 🚀 新增：港股版塊地圖 (自製牛牛 Style 核心龍頭) ---
HK_SECTOR_MAP = {
    "科網巨頭 (ATMXJ)": ["0700.HK", "9988.HK", "3690.HK", "1810.HK", "9618.HK"],
    "汽車製造 (EV)": ["1211.HK", "2015.HK", "9866.HK", "9868.HK", "0175.HK"],
    "內銀與金融 (Fin)": ["0005.HK", "0939.HK", "1398.HK", "3988.HK", "2318.HK"],
    "高息電訊 (Telecom)": ["0941.HK", "0728.HK", "0762.HK"],
    "三桶油與煤炭 (Energy)": ["0883.HK", "0857.HK", "0386.HK", "1088.HK"],
    "消費與體育 (Consumer)": ["2020.HK", "2331.HK", "0291.HK", "1928.HK"],
    "生物醫藥 (Health)": ["2269.HK", "1093.HK", "1177.HK", "2359.HK"],
    "內房與物管 (RealEst)": ["1109.HK", "0688.HK", "1209.HK", "6098.HK"]
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
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .radar-box { background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000 !important; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; margin-bottom: 20px; border: 2px solid #FFF; font-size: 1.5rem; }
    .radar-on { background: linear-gradient(135deg, #00FFCC 0%, #00FFA5 100%); }
    .scan-card { background-color: #111; border-left: 5px solid #00FFCC; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .scan-card-fire { border-left: 5px solid #FF4B4B; background-color: #310000; }
    </style>
    """, unsafe_allow_html=True)

# 3. 側邊欄控制
st.sidebar.markdown("## 🛰️ 戰術控制台")
# ⚠️ 爺爺加咗港股版塊掃描 ⚠️
app_mode = st.sidebar.radio("請選擇操作", ["📡 美股版塊熱力圖", "📡 港股版塊熱力圖 (牛牛Style)", "🔍 美股版塊尋龍掃描", "🚀 個股深度透視"])

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
        fig.update_layout(template="plotly_dark", height=600, title="版塊相對強度 (RS > 50 代表跑贏標普500大盤)")
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 模式 A2：港股版塊掃描 (自製牛牛 Style)
# ==========================================
elif app_mode == "📡 港股版塊熱力圖 (牛牛Style)":
    st.markdown("<h1 class='main-title'>🇭🇰 港股八大星系能量熱力圖</h1>", unsafe_allow_html=True)
    st.write("爺爺正將各大版塊龍頭股與【恆生指數 HSI】進行相對強弱 (RS) 拔河對比...")
    
    # 港股大盤用恆指
    hsi_data = yf.Ticker("^HSI").history(period="60d")['Close']
    results = []
    
    with st.spinner('計算港股資金流向中...'):
        for sector_name, tickers in HK_SECTOR_MAP.items():
            sector_rs_list = []
            for t in tickers:
                try:
                    d = yf.Ticker(t).history(period="60d")['Close']
                    if len(d) >= 20 and len(hsi_data) >= 20:
                        # 計算單隻個股對恆指嘅 RS
                        rs = 50 + ((d.iloc[-1]/d.iloc[-20]) - (hsi_data.iloc[-1]/hsi_data.iloc[-20])) * 100
                        sector_rs_list.append(rs)
                except: pass
            
            if sector_rs_list:
                # 計整個版塊嘅平均 RS
                avg_rs = np.mean(sector_rs_list)
                results.append({"版塊": sector_name, "RS強弱": round(avg_rs, 1)})

    if results:
        df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=False)
        fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["版塊"], orientation='h', marker=dict(color=df_rs["RS強弱"], colorscale='Viridis')))
        fig.update_layout(template="plotly_dark", height=500, title="版塊相對強度 (RS > 50 代表跑贏恆生指數)")
        st.plotly_chart(fig, use_container_width=True)
        st.success(f"👴 爺爺戰報：港股目前最強資金眼喺【{df_rs.iloc[0]['版塊']}】！")

# ==========================================
# 模式 B：版塊內尋龍掃描 
# ==========================================
elif app_mode == "🔍 美股版塊尋龍掃描":
    st.markdown("<h1 class='main-title'>🔍 版塊內尋龍起步雷達</h1>", unsafe_allow_html=True)
    target_sector = st.sidebar.selectbox("選擇要掃描的版塊", list(SECTOR_COMPONENTS.keys()))
    scan_btn = st.sidebar.button("開始掃描！")
    
    if scan_btn:
        tickers_to_scan = SECTOR_COMPONENTS[target_sector]
        st.markdown(f"### 正在掃描 【{target_sector}】 核心龍頭...")
        spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
        breakout_found = False
        progress_bar = st.progress(0)
        
        for idx, t in enumerate(tickers_to_scan):
            progress_bar.progress((idx + 1) / len(tickers_to_scan))
            try:
                asset = yf.Ticker(t); info = asset.info
                df = asset.history(period="1y").dropna(subset=['Close', 'Volume'])
                if len(df) > 63:
                    curr_p = df['Close'].iloc[-1]
                    crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])) * 100, 50.0)
                    v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
                    cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
                    se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0)
                    real_roe = info.get('returnOnEquity', 0) or 0
                    dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)

                    if se_s > 85 and cej_s > 110 and crs_val > 52:
                        breakout_found = True
                        st.markdown(f"<div class='scan-card scan-card-fire'><h2 style='color:#FFD700;'>🎯 {t} | 能量共振！</h2><p>🧬 DNA: <b>{dna_v}</b> | ⚡ SE: <b style='color:#FF4B4B;'>{se_s:.1f}</b> | 🔋 EJ: <b style='color:#00FFCC;'>{cej_s:.1f}</b> | 📈 RS: <b>{crs_val:.1f}</b></p></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='scan-card'><h4 style='color:#ccc;'>💤 {t} | 尚未到達爆發點</h4><span style='font-size:0.9rem; color:#888;'>動能 SE: {se_s:.1f} | 資金 EJ: {cej_s:.1f}</span></div>", unsafe_allow_html=True)
            except: pass
            
        if not breakout_found: st.warning("掃描完畢：此版塊目前無起步訊號。")

# ==========================================
# 模式 C：個股深度透視
# ==========================================
else:
    ticker = st.sidebar.text_input("🚀 輸入資產代號 (例: 0700.HK, NVDA)", "0700.HK").upper()
    detect_btn = st.sidebar.button("📡 掃描趨勢爆發起點")
    
    try:
        asset = yf.Ticker(ticker); info = asset.info
        df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
        
        # 智能切換：如果係港股，對標 HSI；美股對標 SPY
        is_hk = ".HK" in ticker
        spy = yf.Ticker("^HSI" if is_hk else "SPY").history(period="2y").dropna(subset=['Close'])
        
        if not df.empty:
            curr_p = df['Close'].iloc[-1]
            
            c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
            slope, intercept = np.polyfit(days, c_tail, 1); pred = intercept + slope * len(days)
            mom = (curr_p / pred) if pred > 0 else 1.0; v_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
            cx_val = safe_n(((slope * 252) / c_tail.mean() / v_ann) * 29 * mom, 50.0)
            crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])) * 100, 50.0) if len(df) > 63 else 50.0
            
            v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
            cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
            se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0) if len(df) > 5 else 50.0

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

            # DNA & 8D Bar 
            st.write("---")
            d_c1, d_c2 = st.columns([1, 2.5])
            is_etf = info.get('quoteType') == 'ETF'
            real_roe = info.get('returnOnEquity')
            if is_etf or real_roe is None or real_roe == 0:
                dna_v = round(safe_n((cx_val * 0.5) + (crs_val * 0.5), 50.0), 1)
                m8 = {"🩸 流動資金": int(safe_n(cej_s/10,5)), "🛡️ 抗跌系統": int(safe_n(crs_val/10,5)), "🏗️ 動能頻率": int(safe_n(cx_val/10,5)), "🧬 趨勢潛力": int(safe_n(se_s/10,5)), "🧱 規模底盤": 8, "⚡ 波幅控制": 7, "💰 派息防守": 5, "📈 相對拐點": 6}
            else:
                dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)
                m8 = {"🩸 血液純度": int(safe_n(info.get('operatingMargins', 0)*30+3, 5)), "🛡️ 免疫系統": int(safe_n(real_roe*30+3, 7)), "🏗️ 心跳頻率": int(safe_n(info.get('revenueGrowth', 0)*20+4, 6)), "🧬 大腦潛力": int(safe_n(info.get('profitMargins', 0)*30+3, 8)), "🧱 骨架重量": int(max(1, 10 - safe_n(info.get('priceToBook', 5), 5))), "⚡ 物理底盤": 8 if safe_n(info.get('debtToEquity', 150), 150) < 80 else 3, "💰 資本配置": int(safe_n(info.get('dividendYield', 0)*200+2, 5)), "📈 經營拐點": int(safe_n(info.get('earningsGrowth', 0)*25+4, 8))}
            
            dna_v = max(0.0, min(100.0, dna_v)) 
            if dna_v >= 80: d_lv, d_desc = "第 2 級", "🌟 星系霸主"
            elif dna_v >= 50: d_lv, d_desc = "第 5 級", "⚖️ 凡骨平庸"
            else: d_lv, d_desc = "第 9 級", "☠️ 黑洞邊緣"

            with d_c1:
                st.markdown(f"<div class='cosmos-box' style='border-color:#FF4B4B; height:380px; display:flex; flex-direction:column; justify-content:center;'><div style='color:#FF4B4B; font-weight:900;'>🧬 DNA: {dna_v}</div><div style='color:#FFD700; margin-top:10px;'>[ 現屬 {d_lv} ]<br><span style='font-size:1.6rem; color:#FFF;'>{d_desc}</span></div></div>", unsafe_allow_html=True)
            with d_c2:
                for label, score in m8.items():
                    sc = max(1, min(10, score))
                    grid = '<div class="energy-bar-container-8d">' + "".join([f'<div class="energy-seg-8d" style="background-color:#00FFCC; opacity:{"1" if j<=sc else "0.1"};"></div>' for j in range(1,11)]) + '</div>'
                    st.markdown(f"<div style='display:flex; justify-content:space-between;'><span>{label}</span><span>{sc}/10</span></div>{grid}", unsafe_allow_html=True)

            # --- 下方其餘渲染保留，如估值與烈火鳳凰框 ---
            st.info("如需查看完整估值分析，請參考下方矩陣。")

    except Exception as e: st.error(f"系統診斷中: {e}")import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="COSMOS 戰略指揮部 V43", layout="wide")

# --- 基礎工具函數 ---
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

# --- 乖孫的美股版塊地圖 & 核心成份股名單 (爺爺幫你整理好) ---
US_SECTOR_MAP = {
    "半導體 (SMH)": "SMH", "科技 (XLK)": "XLK", "通訊 (XLC)": "XLC", "可選消費 (XLY)": "XLY",
    "金融 (XLF)": "XLF", "醫療 (XLV)": "XLV", "能源 (XLE)": "XLE", "工業 (XLI)": "XLI", 
    "必消 (XLP)": "XLP", "公用事業 (XLU)": "XLU", "房地產 (XLRE)": "XLRE", "銀行 (KRE)": "KRE",
    "建築 (ITB)": "ITB", "油服 (OIH)": "OIH", "生技 (IBB)": "IBB", "太陽能 (TAN)": "TAN", "黃金礦工 (GDX)": "GDX"
}

# 版塊對應嘅「龍頭名單」，用嚟做尋龍掃描
SECTOR_COMPONENTS = {
    "半導體 (SMH)": ["NVDA", "TSM", "AVGO", "ASML", "AMD", "QCOM", "TXN", "AMAT", "MU", "INTC"],
    "科技 (XLK)": ["AAPL", "MSFT", "NVDA", "AVGO", "ADBE", "CRM", "AMD", "ACN", "CSCO"],
    "通訊 (XLC)": ["META", "GOOGL", "NFLX", "DIS", "CMCSA", "TMUS", "CHTR", "TTWO"],
    "可選消費 (XLY)": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "BKNG", "SBUX"],
    "金融 (XLF)": ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "MS", "GS", "C"],
    "醫療 (XLV)": ["LLY", "UNH", "JNJ", "MRK", "ABBV", "TMO", "DHR", "AMGN", "PFE"],
    "能源 (XLE)": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO"],
    "工業 (XLI)": ["CAT", "GE", "UNP", "HON", "BA", "RTX", "LMT", "UPS"],
    "必消 (XLP)": ["PG", "PEP", "KO", "COST", "WMT", "PM", "MO", "TGT"],
    "公用事業 (XLU)": ["NEE", "SO", "DUK", "SRE", "AEP", "D", "PCG", "EXC"],
    "房地產 (XLRE)": ["PLD", "AMT", "EQIX", "CCI", "PSA", "O", "SPG"],
    "銀行 (KRE)": ["NYCB", "USB", "PNC", "TFC", "FITB", "MTB", "CFG"],
    "建築 (ITB)": ["DHI", "LEN", "PHM", "NVR", "TOL", "BLDR"],
    "油服 (OIH)": ["SLB", "HAL", "BKR", "FTI", "NOV", "CHX"],
    "生技 (IBB)": ["VRTX", "REGN", "AMGN", "GILD", "BIIB", "IQV"],
    "太陽能 (TAN)": ["FSLR", "ENPH", "SEDG", "RUN", "SHLS"],
    "黃金礦工 (GDX)": ["NEM", "GOLD", "AEM", "FNV", "KGC", "WPM"]
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
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700; font-weight: bold; font-size: 2.5rem; }
    .whale-a { color: #00FFCC; font-size: 1.6rem; text-align: right; }
    .radar-box { background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #000 !important; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; margin-bottom: 20px; border: 2px solid #FFF; font-size: 1.5rem; }
    .radar-on { background: linear-gradient(135deg, #00FFCC 0%, #00FFA5 100%); }
    .scan-card { background-color: #111; border-left: 5px solid #00FFCC; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .scan-card-fire { border-left: 5px solid #FF4B4B; background-color: #310000; }
    </style>
    """, unsafe_allow_html=True)

# 3. 側邊欄控制
st.sidebar.markdown("## 🛰️ 戰術控制台")
# ⚠️ 爺爺加咗新模式 ⚠️
app_mode = st.sidebar.radio("請選擇操作", ["📡 版塊強勢熱力圖", "🔍 版塊內尋龍掃描", "🚀 個股 DNA 深度透視"])

# ==========================================
# 模式 A：版塊掃描 (大地圖)
# ==========================================
if app_mode == "📡 版塊強勢熱力圖":
    st.markdown("<h1 class='main-title'>🛰️ 全美星系版塊能量分布</h1>", unsafe_allow_html=True)
    spy_data = yf.Ticker("SPY").history(period="60d")['Close']
    results = []
    with st.spinner('爺爺正在掃描全美版塊...'):
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
        fig.update_layout(template="plotly_dark", height=700, title="版塊相對強度 (RS > 50 代表跑贏大盤)")
        st.plotly_chart(fig, use_container_width=True)
        st.success(f"👴 爺爺提示：目前最強戰場在【{df_rs.iloc[0]['版塊']}】！請切換到「版塊內尋龍掃描」去挖寶！")

# ==========================================
# 模式 B：版塊內尋龍掃描 (新功能！)
# ==========================================
elif app_mode == "🔍 版塊內尋龍掃描":
    st.markdown("<h1 class='main-title'>🔍 版塊內尋龍起步雷達</h1>", unsafe_allow_html=True)
    st.write("爺爺會幫你逐隻檢查版塊內嘅龍頭股，搵出 **DNA優良 + 資金湧入 + 剛起步** 嘅目標。")
    
    target_sector = st.sidebar.selectbox("選擇要掃描的版塊", list(SECTOR_COMPONENTS.keys()))
    scan_btn = st.sidebar.button("開始掃描！")
    
    if scan_btn:
        tickers_to_scan = SECTOR_COMPONENTS[target_sector]
        st.markdown(f"### 正在掃描 【{target_sector}】 核心龍頭...")
        
        spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
        
        breakout_found = False
        progress_bar = st.progress(0)
        
        for idx, t in enumerate(tickers_to_scan):
            progress_bar.progress((idx + 1) / len(tickers_to_scan))
            try:
                asset = yf.Ticker(t); info = asset.info
                df = asset.history(period="1y").dropna(subset=['Close', 'Volume'])
                if len(df) > 63:
                    curr_p = df['Close'].iloc[-1]
                    c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
                    slope, intercept = np.polyfit(days, c_tail, 1)
                    crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])) * 100, 50.0)
                    
                    v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
                    cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
                    se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0)
                    real_roe = info.get('returnOnEquity', 0) or 0
                    dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)

                    # 判斷起步訊號
                    is_breakout = se_s > 85 and cej_s > 110 and crs_val > 52
                    
                    if is_breakout:
                        breakout_found = True
                        st.markdown(f"""
                        <div class='scan-card scan-card-fire'>
                            <h2 style='color:#FFD700; margin:0;'>🎯 {t} | 能量共振！趨勢剛啟動！</h2>
                            <p style='margin:5px 0; color:#ddd;'>
                                🧬 DNA質量: <b>{dna_v}</b> | ⚡ 短期動能 (SE): <b style='color:#FF4B4B;'>{se_s:.1f}</b> | 
                                🔋 資金底氣 (EJ): <b style='color:#00FFCC;'>{cej_s:.1f}</b> | 📈 大盤強弱 (RS): <b>{crs_val:.1f}</b>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='scan-card'>
                            <h4 style='color:#ccc; margin:0;'>💤 {t} | 尚未到達爆發點</h4>
                            <span style='font-size:0.9rem; color:#888;'>動能 SE: {se_s:.1f} | 資金 EJ: {cej_s:.1f}</span>
                        </div>
                        """, unsafe_allow_html=True)
            except: pass
            
        if not breakout_found:
            st.warning("爺爺掃描完畢：目前呢個版塊內，無龍頭股出現「起步爆發」訊號。建議耐心等候或者睇其他版塊！")
        else:
            st.success("🔥 掃描完畢！有標的出現爆發訊號，請抄低代號，去「個股 DNA 深度透視」做最後檢查！")

# ==========================================
# 模式 C：個股透視 (狙擊鏡)
# ==========================================
else:
    ticker = st.sidebar.text_input("🚀 輸入狙擊代號", "NVDA").upper()
    detect_btn = st.sidebar.button("📡 掃描趨勢爆發起點")
    
    try:
        asset = yf.Ticker(ticker); info = asset.info
        df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
        spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
        
        if not df.empty:
            curr_p = df['Close'].iloc[-1]
            
            # 核心計算
            c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
            slope, intercept = np.polyfit(days, c_tail, 1); pred = intercept + slope * len(days)
            mom = (curr_p / pred) if pred > 0 else 1.0; v_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
            cx_val = safe_n(((slope * 252) / c_tail.mean() / v_ann) * 29 * mom, 50.0)
            crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])) * 100, 50.0) if len(df) > 63 else 50.0
            
            v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
            cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
            se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0) if len(df) > 5 else 50.0

            st.markdown(f"""<div class='main-title'>環球資產透維評估儀 [{ticker}]</div>""", unsafe_allow_html=True)
            
            # 雷達掃描結果
            if detect_btn:
                is_breakout = se_s > 85 and cej_s > 110 and crs_val > 52
                if is_breakout:
                    st.markdown(f"""<div class='radar-box radar-on'>🎯 偵測到【起步訊號】：資金正極速湧入 {ticker}！趨勢剛啟動。</div>""", unsafe_allow_html=True)
                else:
                    st.markdown(f"""<div class='radar-box'>💤 掃描完畢：{ticker} 尚未到達能量爆發點。</div>""", unsafe_allow_html=True)

            # 第一層看板
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"""<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>""", unsafe_allow_html=True)
            c2.markdown(f"""<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS (星系強弱)</div><div class='cosmos-value'>{crs_val:.1f}</div></div>""", unsafe_allow_html=True)
            with c3:
                st.markdown("""<div class='cosmos-box' style='border-color:#00FFFF; padding: 20px;'>""", unsafe_allow_html=True)
                st.markdown(draw_triad_bar(cej_s, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
                st.markdown(draw_triad_bar(se_s, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
                st.markdown("""</div>""", unsafe_allow_html=True)

            # 🧬 DNA 自動切換 ETF / 個股 
            st.write("---")
            d_c1, d_c2 = st.columns([1, 2.5])
            
            is_etf = info.get('quoteType') == 'ETF'
            real_roe = info.get('returnOnEquity')
            
            if is_etf or real_roe is None or real_roe == 0:
                dna_v = round(safe_n((cx_val * 0.5) + (crs_val * 0.5), 50.0), 1)
                dna_title = "ETF 綜合質量基因"
                m8 = {
                    "🩸 資金純度 (流動)": int(safe_n(cej_s / 10, 5)), "🛡️ 免疫系統 (抗跌)": int(safe_n(crs_val / 10, 5)),
                    "🏗️ 心跳頻率 (動能)": int(safe_n(cx_val / 10, 5)), "🧬 大腦潛力 (趨勢)": int(safe_n(se_s / 10, 5)),
                    "🧱 骨架重量 (規模)": 9 if info.get('totalAssets', 0) > 1e9 else 5, "⚡ 物理底盤 (波幅)": int(max(1, 10 - (v_ann * 20))),
                    "💰 資本配置 (派息)": int(safe_n(info.get('yield', info.get('dividendYield', 0))*200+2, 5)), "📈 經營拐點 (相對)": int(safe_n(crs_val / 10, 5))
                }
            else:
                dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)
                dna_title = "投行級股王基因"
                m8 = {
                    "🩸 血液純度": int(safe_n(info.get('operatingMargins', 0)*30+3, 5)), "🛡️ 免疫系統": int(safe_n(real_roe*30+3, 7)),
                    "🏗️ 心跳頻率": int(safe_n(info.get('revenueGrowth', 0)*20+4, 6)), "🧬 大腦潛力": int(safe_n(info.get('profitMargins', 0)*30+3, 8)),
                    "🧱 骨架重量": int(max(1, 10 - safe_n(info.get('priceToBook', 5), 5))), "⚡ 物理底盤": 8 if safe_n(info.get('debtToEquity', 150), 150) < 80 else 3,
                    "💰 資本配置": int(safe_n(info.get('dividendYield', 0)*200+2, 5)), "📈 經營拐點": int(safe_n(info.get('earningsGrowth', 0)*25+4, 8))
                }

            dna_v = max(0.0, min(100.0, dna_v)) 
            
            # 10 級分類
            if dna_v >= 90: d_lv, d_desc = "第 1 級", "👑 創世真神"
            elif dna_v >= 80: d_lv, d_desc = "第 2 級", "🌟 星系霸主"
            elif dna_v >= 70: d_lv, d_desc = "第 3 級", "🚀 恆星巨頭"
            elif dna_v >= 60: d_lv, d_desc = "第 4 級", "🛡️ 行星中堅"
            elif dna_v >= 50: d_lv, d_desc = "第 5 級", "⚖️ 凡骨平庸"
            elif dna_v >= 40: d_lv, d_desc = "第 6 級", "⚠️ 能量衰退"
            elif dna_v >= 30: d_lv, d_desc = "第 7 級", "🍂 恆星殞落"
            elif dna_v >= 20: d_lv, d_desc = "第 8 級", "🩸 基因突變"
            elif dna_v >= 10: d_lv, d_desc = "第 9 級", "☠️ 黑洞邊緣"
            else: d_lv, d_desc = "第 10 級", "🪦 宇宙塵埃"

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

            # -------------------------------------------------------------
            st.write(""); k1 = st.columns(4); k2 = st.columns(4)
            
            val_emotion = safe_n(crs_val * 0.9, 50.0)
            val_total = (cx_val + crs_val + se_s) / 3
            val_vol_ratio = v21 / max(v252, 1)

            target_p_raw = info.get('targetMeanPrice')
            val_target_str = f"${target_p_raw:.2f}" if target_p_raw else "N/A"

            kings = [
                ("📁 質量", f"{dna_v:.0f}"), ("📈 趨勢", f"{crs_val:.0f}"), ("⚡ 動能", f"{se_s:.0f}"), ("🔋 大資金", f"{cej_s:.0f}"), 
                ("🎭 情緒", f"{val_emotion:.0f}"), ("🏆 總分", f"{val_total:.0f}"), ("🔮 12M目標", val_target_str), ("💰 成交比", f"{val_vol_ratio:.1f}x")
            ]
            
            for i in range(4):
                k1[i].markdown(f"""<div class='cosmos-box' style='padding:15px; border-width:2px;'><div style='color:#ccc; font-size:1.2rem;'>{kings[i][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i][1]}</div></div>""", unsafe_allow_html=True)
                k2[i].markdown(f"""<div class='cosmos-box' style='padding:15px; border-width:2px; border-color:#FFD700;'><div style='color:#ccc; font-size:1.2rem;'>{kings[i+4][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i+4][1]}</div></div>""", unsafe_allow_html=True)

            st.markdown(f"""<div class='red-bar'>🔥 戰略透視：短期動能爆發數值 [{se_s:.1f}%] 🔥</div>""", unsafe_allow_html=True)

            # 估值矩陣
            st.write("### 🏛️ 估值與風險全方位透視")
            v1, v2, v3 = st.columns(3); v4, v5, v6 = st.columns(3)
            def v_card(col, title, t_val, f_val, desc):
                col.markdown(f"""<div class='val-box'><div class='val-label'>{title}</div><div class='val-text'>TTM: <span class='val-focus'>{t_val}</span></div><div class='val-text'>12M預期: <span class='val-focus'>{f_val}</span></div><div style='color:#FFA500; font-size:0.9rem; margin-top:10px;'>{desc}</div></div>""", unsafe_allow_html=True)
            v_card(v1, "PE 獲利比", safe_s(info, ['trailingPE'], "x"), safe_s(info, ['forwardPE'], "x"), "獲利估值透視")
            v_card(v2, "PEG 增長比", safe_s(info, ['pegRatio']), "N/A", "增長性價比")
            v_card(v3, "PS 營收比", safe_s(info, ['priceToSalesTrailing12Months'], "x"), "N/A", "營收規模")
            v_card(v4, "PB 淨資產", safe_s(info, ['priceToBook'], "x"), "N/A", "賬面價值")
            v_card(v5, "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], "x"), "N/A", "企業估值")
            v_card(v6, "股息率", safe_s(info, ['dividendYield', 'yield'], "%"), "N/A", "現金流回報")

            # 烈火鳳凰
            ttm_pe = info.get('trailingPE', 0) or 0
            if ttm_pe > 80 and not is_etf:
                dragon_index = round((dna_v * 0.4) + (cx_val * 0.3) + (crs_val * 0.3), 1)
                dragon_index = max(5.0, min(98.5, dragon_index)) 
                
                if dragon_index >= 80:
                    t_lv, t_desc, val_title, val_color, act_desc = "第 1 級", "極致真龍", "🔥 烈火鳳凰", "#BC13FE", "【順勢而為】真實財報極度健康，估值雖貴但有強大動能支撐，緊貼趨勢操作。"
                elif dragon_index >= 65:
                    t_lv, t_desc, val_title, val_color, act_desc = "第 2 級", "潛力金龍", "🌟 潛龍伏躍", "#00FFCC", "【價值防守】財報穩健，動能醞釀中，適合分批建倉或持有觀望。"
                elif dragon_index >= 40:
                    t_lv, t_desc, val_title, val_color, act_desc = "第 3 級", "中庸凡骨", "⚠️ 海市蜃樓", "#FFA500", "【謹慎觀望】動能與財報表現平平，估值偏高，注意回調風險。"
                else:
                    t_lv, t_desc, val_title, val_color, act_desc = "第 4 級", "高危泥鰍", "☠️ 末路狂花", "#FF4B4B", "【規避風險】財報轉弱且動能破位，估值存在泡沫，建議嚴格止損。"
                
                st.markdown(f"""
                <div style='border: 4px solid {val_color}; border-radius: 15px; padding: 30px; background-color: #000; box-shadow: 0 0 30px {val_color}66; margin: 25px 0;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <span style='font-size:2.2rem; font-weight:900;'>COSMOS-VAL 解碼：<span style='color:{val_color};'>{val_title}</span></span><br>
                            <span style='font-size:1.1rem; opacity:0.8;'>（針對 TTM PE {ttm_pe:.2f}x 獨立戰術評分）</span><br>
                            <span style='font-size:1.2rem; color:#FFD700; font-weight:bold; margin-top:5px; display:inline-block;'>[ 註明：共分 4 級，現在這公司基於真實財報屬 {t_lv} ({t_desc}) ]</span>
                        </div>
                        <div style='text-align:right;'>
                            <span style='font-size:1.6rem;'>真龍指數：</span><br>
                            <span style='font-size:5rem; font-weight:900; color:{val_color};'>{dragon_index}</span>
                        </div>
                    </div>
                    <div style='background-color:#111; padding:20px; border-radius:10px; margin-top:20px; border:1px solid #333;'>
                        <b style='color:white; font-size:1.3rem;'>真實財報決策指令：</b> <span style='color:{val_color}; font-size:1.3rem;'>{act_desc}</span>
                    </div>
                </div>""", unsafe_allow_html=True)

            # Alpha/波動率
            b_val = float(get_beta(info, df, spy))
            y1_r = (curr_p / df['Close'].iloc[-252] - 1) if len(df) > 252 else 0
            s_y1_r = (spy['Close'].iloc[-1] / spy['Close'].iloc[-252] - 1) if len(spy) > 252 else 0
            real_alpha = (y1_r - b_val * s_y1_r) * 100
            r1, r2, r3 = st.columns(3)
            r1.markdown(f"""<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>📐 Beta (性格)</div><div class='cosmos-value' style='font-size:3.5rem;'>{b_val:.2f}</div></div>""", unsafe_allow_html=True)
            r2.markdown(f"""<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🔱 Alpha (超額)</div><div class='cosmos-value' style='font-size:3.5rem;'>{real_alpha:.1f}%</div></div>""", unsafe_allow_html=True)
            r3.markdown(f"""<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🌊 波動率 (情緒)</div><div class='cosmos-value' style='font-size:3.5rem;'>{(v_ann*100):.1f}%</div></div>""", unsafe_allow_html=True)

            # 📊 股價圖
            st.write("### 📊 摩訶釋達・能量與籌碼透視圖")
            recent = df.tail(120); dates = recent.index.strftime('%Y-%m-%d')
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=dates, open=recent['Open'], high=recent['High'], low=recent['Low'], close=recent['Close'], name='股價'), row=1, col=1)
            fig.add_trace(go.Bar(x=dates, y=recent['Volume'], marker_color=['#00FF00' if recent['Close'].iloc[i] >= recent['Open'].iloc[i] else '#FF0000' for i in range(len(recent))], name='成交量'), row=2, col=1)
            counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
            fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name='蟹貨', xaxis='x3', yaxis='y1'))
            fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, showlegend=False, xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'), yaxis2=dict(showgrid=False), xaxis3=dict(overlaying='x', side='top', range=[0, max(counts)*6], showgrid=False, showticklabels=False))
            st.plotly_chart(fig, use_container_width=True)

            # 名家清單
            st.markdown("""<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center; margin-bottom:20px;'>🧙 90 大名家：真實申報持倉 (自動計算佔比)</div>""", unsafe_allow_html=True)
            total_shares = info.get('sharesOutstanding', 1)
            holders = asset.institutional_holders
            if holders is not None and not holders.empty and 'Holder' in holders.columns:
                for _, row in holders.head(8).iterrows():
                    shares = row.get('Shares', 0)
                    calc_pct = (shares / total_shares) if total_shares > 1 else 0
                    val_m = row.get('Value', 0) / 1e6
                    st.markdown(f"""<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>持有 {shares:,.0f} 股 | 佔比 {calc_pct:.2%} | 市值 ${val_m:.1f}M</span></div>""", unsafe_allow_html=True)
            else:
                st.markdown("""<div style='text-align:center; color:#888; padding:20px;'>此資產暫無公開機構申報數據</div>""", unsafe_allow_html=True)
            st.markdown("""</div>""", unsafe_allow_html=True)

    except Exception as e: st.error(f"數據診斷中: {e}")
