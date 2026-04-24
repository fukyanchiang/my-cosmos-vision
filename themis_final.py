import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="COSMOS 全球旗艦指揮部 V54", layout="wide")

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

# --- 🛰️ 港股 22 星系 (用於自動掃描) ---
HK_FULL_MAP = {
    "1. 互聯網平台": ["0700.HK", "9988.HK", "3690.HK", "1810.HK", "9618.HK"],
    "2. 半導體硬件": ["0981.HK", "1347.HK", "2400.HK", "0285.HK", "1478.HK"],
    "3. 汽車製造": ["1211.HK", "2015.HK", "9866.HK", "9868.HK", "0175.HK"],
    "4. 重型工業": ["1133.HK", "1072.HK", "1888.HK", "1286.HK", "3399.HK"],
    "5. 金融銀行": ["0005.HK", "0939.HK", "1398.HK", "3988.HK", "2388.HK"],
    "6. 化工材料": ["0148.HK", "1651.HK", "1378.HK", "3360.HK", "1963.HK"],
    "7. 三桶油氣": ["0883.HK", "0857.HK", "0386.HK", "1193.HK", "1083.HK"],
    "8. 煤炭金屬": ["1088.HK", "1171.HK", "1898.HK", "2899.HK", "0358.HK"],
    "9. 電力能源": ["0902.HK", "0836.HK", "1816.HK", "0916.HK", "0006.HK"],
    "10. 房產開發": ["1109.HK", "0688.HK", "0960.HK", "1918.HK", "3383.HK"]
}

# --- 🛰️ 美股 24 星系 (用於自動掃描) ---
US_FULL_MAP = {
    "1. 半導體龍頭": ["NVDA", "TSM", "AVGO", "ASML", "AMD", "MU"],
    "2. AI與軟體": ["MSFT", "GOOGL", "ORCL", "ADBE", "CRM", "PLTR"],
    "3. 消費硬件": ["AAPL", "DELL", "STX", "WDC", "APH", "TEL"],
    "4. 雲端通訊": ["AMZN", "META", "NFLX", "DIS", "TMUS", "VZ"],
    "5. 電動車自駕": ["TSLA", "RIVN", "LCID", "LI", "NIO", "XPEV"],
    "10. 能源石油": ["XOM", "CVX", "COP", "SLB", "MPC", "PSX"],
    "24. 中型高增長": ["SMCI", "DECK", "CELH", "WING", "APP", "ELF"]
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
    .scan-card-fire { border-left: 10px solid #FF4B4B; background-color: #310000; padding: 20px; margin-bottom: 15px; border-radius: 10px; box-shadow: 0 0 20px #FF4B4B66; }
    </style>
    """, unsafe_allow_html=True)

# 3. 側邊欄控制
st.sidebar.markdown("## 🛰️ 戰術控制台")
app_mode = st.sidebar.radio("請選擇操作", ["🚀 個股深度透視", "📡 全球版塊排序熱力圖", "🔍 版塊內尋龍掃描掣"])

# ==========================================
# 🚀 模式 A：個股深度透視 (首頁)
# ==========================================
if app_mode == "🚀 個股深度透視":
    ticker = st.sidebar.text_input("🚀 輸入資產代號", "NVDA").upper()
    try:
        asset = yf.Ticker(ticker); info = asset.info
        df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
        is_hk = ".HK" in ticker
        spy = yf.Ticker("^HSI" if is_hk else "SPY").history(period="2y").dropna(subset=['Close'])
        
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
        real_roe = info.get('returnOnEquity', 0)
        dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)
        dna_v = min(100.0, dna_v)
        
        with d_c1:
            st.markdown(f"""
            <div class='cosmos-box' style='border-color:#FF4B4B; height:380px; display:flex; flex-direction:column; justify-content:center;'>
                <div style='color:#FF4B4B; font-weight:900; font-size:1.8rem;'>🧬 COSMOS-DNA</div>
                <div style='font-size:6rem; font-weight:900;'>{dna_v}</div>
                <div style='color:#FFD700;'>[ 現屬 第 2 級 ]<br><span style='font-size:1.6rem;'>🌟 星系霸主</span></div>
            </div>""", unsafe_allow_html=True)
        with d_c2:
            st.markdown(f"**{ticker} ・ 8D 投行精確透視 BAR**")
            m8 = {"🩸 血液純度": 10, "🛡️ 免疫系統": 10, "🏗️ 心跳頻率": 10, "🧬 大腦潛力": 10, "🧱 骨架重量": 1}
            for label, sc in m8.items():
                grid = '<div class="energy-bar-container-8d">' + "".join([f'<div class="energy-seg-8d" style="background-color:#00FFCC; opacity:{"1" if j<=sc else "0.1"};"></div>' for j in range(1,11)]) + '</div>'
                st.markdown(f"<div style='display:flex; justify-content:space-between;'><span>{label}</span><span>{sc}/10</span></div>{grid}", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略透視：短期動能爆發數值 [{se_s:.1f}%] 🔥</div>", unsafe_allow_html=True)
        
        # ✅ 補回 Beta, Alpha, 波動率
        st.write("### 🔱 核心戰略指標 (Beta / Alpha / Volatility)")
        r1, r2, r3 = st.columns(3)
        b_val = float(get_beta(info, df, spy))
        y1_r = (curr_p / df['Close'].iloc[-252] - 1) if len(df) > 252 else 0
        s_y1_r = (spy['Close'].iloc[-1] / spy['Close'].iloc[-252] - 1) if len(spy) > 252 else 0
        real_alpha = (y1_r - b_val * s_y1_r) * 100
        r1.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>📐 Beta 性格</div><div class='cosmos-value' style='font-size:3.5rem;'>{b_val:.2f}</div></div>", unsafe_allow_html=True)
        r2.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🔱 Alpha 超額</div><div class='cosmos-value' style='font-size:3.5rem;'>{real_alpha:.1f}%</div></div>", unsafe_allow_html=True)
        r3.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🌊 波動情緒</div><div class='cosmos-value' style='font-size:3.5rem;'>{(v_ann*100):.1f}%</div></div>", unsafe_allow_html=True)

        st.write("### 🏛️ 估值矩陣")
        v1, v2, v3 = st.columns(3); v4, v5, v6 = st.columns(3)
        def v_card(col, title, t_val, f_val):
            col.markdown(f"<div class='val-box'><div class='val-label'>{title}</div><div class='val-text'>TTM: <span class='val-focus'>{t_val}</span></div><div class='val-text'>12M預期: <span class='val-focus'>{f_val}</span></div></div>", unsafe_allow_html=True)
        v_card(v1, "PE 獲利比", safe_s(info, ['trailingPE'], "x"), safe_s(info, ['forwardPE'], "x"))
        v_card(v2, "PEG 增長比", safe_s(info, ['pegRatio']), "N/A")
        v_card(v3, "PS 銷售比", safe_s(info, ['priceToSalesTrailing12Months'], "x"), "N/A")
        v_card(v4, "PB 淨資產", safe_s(info, ['priceToBook'], "x"), "N/A")
        v_card(v5, "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], "x"), "N/A")
        v_card(v6, "股息率回報", safe_s(info, ['dividendYield', 'yield'], "%"), "N/A")

    except Exception as e: st.error(f"系統診斷中: {e}")

# ==========================================
# 📡 模式 B：全球版塊排序熱力圖 (自動掃描排名)
# ==========================================
elif app_mode == "📡 全球版塊排序熱力圖":
    st.markdown("<h1 class='main-title'>📡 全星系版塊相對強弱排名</h1>", unsafe_allow_html=True)
    m_view = st.sidebar.radio("切換市場視角", ["🇺🇸 美股星系 (對標 SPY)", "🇭🇰 港股星系 (對標 ^HSI)"])
    is_us = "美股" in m_view
    bench_sym = "SPY" if is_us else "^HSI"
    target_map = US_FULL_MAP if is_us else HK_FULL_MAP
    
    with st.spinner(f'正在進行全球版塊拔河對比 ({bench_sym})...'):
        bench_df = yf.Ticker(bench_sym).history(period="60d")['Close']
        results = []
        for name, tickers in target_map.items():
            try:
                # 每個版塊取龍頭計 20 日相對升幅
                d = yf.Ticker(tickers[0]).history(period="60d")['Close']
                if len(d) >= 20:
                    rs_score = 50 + ((d.iloc[-1]/d.iloc[-20]) - (bench_df.iloc[-1]/bench_df.iloc[-20])) * 100
                    results.append({"版塊": name, "RS強弱": round(rs_score, 1)})
            except: pass
        
        if results:
            # ✅ 重點：自動由強到弱排序 (Descending Order)
            df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=True) # Plotly Bar 由下往上畫，所以用 True 視覺上會變 Top-Down
            fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["版塊"], orientation='h', 
                                    marker=dict(color=df_rs["RS強弱"], colorscale='Portland' if is_us else 'Viridis')))
            fig.update_layout(template="plotly_dark", height=800, title=f"當前最強版塊：{df_rs.iloc[-1]['版塊']}")
            st.plotly_chart(fig, use_container_width=True)
            st.success(f"👴 爺爺提醒：目前資金集中度最高的是 【{df_rs.iloc[-1]['版塊']}】！")

# ==========================================
# 🔍 模式 C：尋龍掃描掣
# ==========================================
else:
    st.markdown("<h1 class='main-title'>🔍 全球千龍起步狙擊雷達</h1>", unsafe_allow_html=True)
    st.info("請喺側邊欄選擇版塊，啟動大數據過濾...")
