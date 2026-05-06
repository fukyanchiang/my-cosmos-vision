import streamlit as st 
import yfinance as yf 
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go 
from plotly.subplots import make_subplots 
import time

# 1. 基礎設置 
st.set_page_config(page_title="環球資產透維評估儀", layout="wide") 

# 👴 爺爺精準 CSS V174：白框黑字修復 + 側邊欄保護
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    section[data-testid="stMain"] div[data-testid="stWidgetLabel"] p, 
    section[data-testid="stMain"] div[data-testid="stWidgetLabel"] span { color: #FFFFFF !important; font-size: 1.1rem !important; font-weight: bold !important; }
    section[data-testid="stMain"] div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p { color: #FFFFFF !important; }
    section[data-testid="stMain"] div[data-baseweb="select"] span { color: #000000 !important; font-weight: bold !important; }
    section[data-testid="stMain"] div[data-baseweb="select"] ul li { color: #000000 !important; }
    section[data-testid="stMain"] button p { color: #000000 !important; font-weight: 900 !important; font-size: 1.1rem !important; }
    section[data-testid="stMain"] div[data-baseweb="input"] input { color: #000000 !important; font-weight: bold !important; }
    section[data-testid="stSidebar"] div[data-testid="stWidgetLabel"] p { color: #31333F !important; }
    section[data-testid="stSidebar"] div[data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p { color: #31333F !important; }

    .main-title { text-align: center; color: #FFD700 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 25px; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 20px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 5rem; font-weight: 900; }
    .ej-header { color: #00FFFF !important; font-size: 1.8rem; font-weight: 900; margin-bottom: 8px; }
    .bar-group-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .bar-triad { display: flex; gap: 3px; }
    .ej-seg { width: 16px; height: 35px; border-radius: 2px; border: 1.2px solid rgba(255,255,255,0.4); }
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; min-height: 220px; margin-bottom: 15px; }
    .val-label { color: #FFFFFF !important; font-size: 1.6rem; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 12px; }
    .val-text { font-size: 1.2rem; color: #ccc; margin: 8px 0; }
    .val-focus { color: #FFD700 !important; font-weight: bold; font-size: 1.8rem; }
    .red-bar { color: #fff !important; border-radius: 10px; text-align: center; font-weight: 900; }
    .val-box-purple { border: 3px solid #BC13FE; border-radius: 15px; padding: 30px; background-color: #000; box-shadow: 0 0 25px #BC13FE66; margin: 25px 0; }
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700 !important; font-weight: bold; font-size: 2.5rem; }
    .whale-a { color: #00FFCC !important; font-size: 1.6rem; text-align: right; }
    .scan-card-fire { border-left: 5px solid #00FFCC; background-color: #111; padding: 15px; margin-bottom: 10px; border-radius: 8px; }
    .scan-card-super { border-left: 8px solid #FF4B4B; background-color: #310000; padding: 15px; margin-bottom: 10px; border-radius: 8px; box-shadow: 0 0 15px #FF4B4B66; }
    .bear-warning { color: #FF0000 !important; font-size: 2.5rem; font-weight: 900; text-align: center; text-shadow: 2px 2px 5px #000; padding: 20px; border: 4px dashed red; background-color: #220000; margin: 20px 0; border-radius: 15px;}
    .exit-radar { background-color: #220000; border: 2px solid #FF0000; padding: 15px; border-radius: 10px; margin-top: 20px;}
    .pullback-card { border-left: 8px solid #BC13FE; background-color: #1a0024; padding: 15px; margin-bottom: 10px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# ----------------- 🛡️ 智慧緩存與百分比保險絲 -----------------
@st.cache_data(ttl=3600)
def smart_fetch(ticker_sym, period="1y"):
    try:
        time.sleep(0.4) 
        asset = yf.Ticker(ticker_sym)
        df = asset.history(period=period)
        if df.empty: return pd.DataFrame(), {}
        return df.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open']), asset.info
    except: return pd.DataFrame(), {}

def cap_pct(val):
    try:
        v = float(val)
        if np.isnan(v) or np.isinf(v): return 0.0
        return max(-999.0, min(999.0, v))
    except: return 0.0

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

def get_alpha(beta, df, spy_df):
    try:
        b = float(beta)
        df_aligned, spy_aligned = df['Close'].align(spy_df['Close'], join='inner')
        asset_ret = (df_aligned.iloc[-1] - df_aligned.iloc[0]) / df_aligned.iloc[0]
        spy_ret = (spy_aligned.iloc[-1] - spy_aligned.iloc[0]) / spy_aligned.iloc[0]
        risk_free = 0.04 
        alpha = asset_ret - (risk_free + b * (spy_ret - risk_free))
        return f"{alpha * 100:.1f}%"
    except: return "N/A"

def get_volatility(df):
    try:
        ret = df['Close'].pct_change().dropna().tail(252)
        vol = ret.std() * np.sqrt(252)
        return f"{vol * 100:.1f}%"
    except: return "N/A"

def get_iv(asset):
    try:
        options = asset.options
        if not options: return "N/A"
        chain = asset.option_chain(options[0])
        calls = chain.calls
        if calls.empty: return "N/A"
        mid_idx = len(calls) // 2
        iv = calls.iloc[mid_idx]['impliedVolatility']
        return f"{iv * 100:.1f}%"
    except: return "N/A"

# ----------------- 🛸 終極資料庫 -----------------
HK_STOCK_MAP = {
    "1. 互聯網巨頭": "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0772.HK 0020.HK 0241.HK 0136.HK 1999.HK 2018.HK 3888.HK 2142.HK 1896.HK 0777.HK 0113.HK 0590.HK 1980.HK 1797.HK 6618.HK 2400.HK 0285.HK".split(),
    "2. 半導體與芯片": "0981.HK 1347.HK 0285.HK 1478.HK 1833.HK 0522.HK 0732.HK 2382.HK 2018.HK 0099.HK 1385.HK 1138.HK 1910.HK 6088.HK 3898.HK 6123.HK 3389.HK".split(),
    "3. 新能源車與整車": "1211.HK 2015.HK 9866.HK 9868.HK 0175.HK 2333.HK 1114.HK 0489.HK 3606.HK 0867.HK 1316.HK 1958.HK 1585.HK 0315.HK 1274.HK 2150.HK 1122.HK 3808.HK 9863.HK".split(),
    "5. 國有大行與金融": "0005.HK 0939.HK 1398.HK 3988.HK 2318.HK 2388.HK 0011.HK 3968.HK 3328.HK 0998.HK 0023.HK 2016.HK 1658.HK 6198.HK 0410.HK 6066.HK 1551.HK 1963.HK 1988.HK 3866.HK".split()
}
US_STOCK_MAP = {
    "1. 半導體": "NVDA TSM AVGO ASML AMD QCOM TXN MU INTC AMAT LRCX KLAC ADI NXPI MRVL MCHP SWKS MPWR ON LSCC TER QRVO SLAB WOLF SYNA RMBS ALGM SITM ACLS CRUS DRAM".split(),
    "2. AI/軟件": "MSFT GOOGL ORCL ADBE CRM PLTR SNOW PANW FTNT NOW WDAY ZS DDOG CRWD MDB NET OKTA TEAM SPLK GEN CYBR CHKP VRSN ESTC TENB SQSP PCOR DOCN AI FSLY MSTR".split(),
    "13. EV/自駕": "TSLA RIVN LCID LI NIO XPEV MSTR UBER LYFT QS AUR GWB ALV LEA MGA BWA APTV VC THO DORM WGO PSNY FSR GOEV HYZN PTRA LEV VLTA".split()
}
HK_ETF_MAP = {
    "H1. A股門戶/旗艦大盤": "2822.HK 3188.HK 3109.HK 2823.HK 2846.HK 3147.HK 2801.HK 3010.HK 3081.HK 3151.HK 3072.HK 3042.HK 2839.HK 3180.HK 2827.HK 3139.HK 3118.HK 2838.HK".split(),
    "H5. 虛擬資產/加密貨幣": "3066.HK 3068.HK 3439.HK 3419.HK 3460.HK 3461.HK 3471.HK 3472.HK 3083.HK 3087.HK 3135.HK 3175.HK 7799.HK 7711.HK 7747.HK".split()
}
US_ETF_MAP = {
    "U1. 核心": "SPY QQQ DIA IWM SMH SOXX XLK XBI KRE ARKK IBIT FBTC BITB IYW DRAM".split()
}

@st.cache_data(ttl=3600)
def get_breadth_data(tickers):
    stats = {'20MA':0, '50MA':0, '150MA':0, '200MA':0, 'valid':0, 'above_50_list': [],
             'hist_20MA': [0]*20, 'hist_50MA': [0]*20, 'hist_150MA': [0]*20, 'hist_200MA': [0]*20}
    if not tickers: 
        stats['valid'] = 1
        return stats
    for t in tickers:
        try:
            c = yf.Ticker(t).history(period="1y")['Close'].dropna()
            n = len(c)
            if n < 50: continue
            
            curr = c.iloc[-1]
            if curr > c.tail(20).mean(): stats['20MA'] += 1
            if curr > c.tail(50).mean(): 
                stats['50MA'] += 1
                stats['above_50_list'].append(t)
            if n >= 150 and curr > c.tail(150).mean(): stats['150MA'] += 1
            if n >= 200 and curr > c.tail(200).mean(): stats['200MA'] += 1
            
            for i in range(20):
                days_ago = 19 - i
                end_idx = n - days_ago
                if end_idx >= 20:
                    past_curr = c.iloc[end_idx - 1]
                    if past_curr > c.iloc[end_idx-20:end_idx].mean(): stats['hist_20MA'][i] += 1
                    if end_idx >= 50 and past_curr > c.iloc[end_idx-50:end_idx].mean(): stats['hist_50MA'][i] += 1
                    if end_idx >= 150 and past_curr > c.iloc[end_idx-150:end_idx].mean(): stats['hist_150MA'][i] += 1
                    if end_idx >= 200 and past_curr > c.iloc[end_idx-200:end_idx].mean(): stats['hist_200MA'][i] += 1
                    
            stats['valid'] += 1
        except: pass
    stats['valid'] = max(1, stats['valid'])
    return stats

# ----------------- 🔘 側邊欄控制 -----------------
st.sidebar.markdown("## 🛰️ 戰術控制台 (V174.0)")
app_mode = st.sidebar.radio("請選擇操作", [
    "🚀 個股深度透視", 
    "🛡️ 環球市底大師指揮塔", 
    "📡 個股版塊拔河熱力圖", 
    "📡 ETF 資產拔河熱力圖", 
    "🔍 千龍起步尋龍雷達 (個股)",
    "🛡️ 美股 ETF 專屬雷達",
    "🛡️ 港/A股 ETF 專屬雷達",
    "📈 VCP 形態戰術掃描 & 防守圖",
    "🌊 海龜回測加注雷達 (Mode E)"
])

show_b_idx = show_b_ma20 = show_b_ma50 = show_b_ma150 = show_b_ma200 = True

if app_mode in ["🚀 個股深度透視", "🛡️ 環球市底大師指揮塔"]:
    st.sidebar.markdown("---")
    st.sidebar.header("🎭 投行定性打分 (X-Factor)")
    s10_mgmt = st.sidebar.slider("10. 靈魂人物溢價 (CEO/執行力)", 0, 100, 70)
    s11_story = st.sidebar.slider("11. 時代敘事溢價", 0, 100, 80)
    x_factor = st.sidebar.selectbox("🕵️‍♂️ 投行隱藏 X 因子", ["無特殊狀況", "跨界第二曲線 (+10分)", "自動印鈔機護城河 (+5分)", "隱形吸血鬼SBC (-15分)"])
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛠️ 圖表顯示開關")
    st.sidebar.markdown("**📈 個股均線區**")
    show_s_ma20 = st.sidebar.checkbox("20日線 (短線動能)", value=False)
    show_s_ma50 = st.sidebar.checkbox("50日線 / 10周 (中期趨勢)", value=False)
    show_s_ma150 = st.sidebar.checkbox("150日線 / 30周 (大師分界)", value=False)
    show_s_ma200 = st.sidebar.checkbox("200日線 (終極牛熊)", value=False)

# =========================================================================
# 🛡️ 模式 B：環球市底大師指揮塔 
# =========================================================================
if app_mode == "🛡️ 環球市底大師指揮塔":
    st.markdown("<h1 class='main-title'>🛡️ 環球市底大師指揮塔</h1>", unsafe_allow_html=True)
    
    st.markdown("<span style='color:white; font-size:16px; font-weight:bold;'>請選擇大盤陣營：</span>", unsafe_allow_html=True)
    market_choice = st.radio("", ["🇭🇰 港股市寬系統", "🇺🇸 美股市寬系統"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("<span style='color:white; font-size:16px; font-weight:bold;'>請選擇指數：</span>", unsafe_allow_html=True)
    if "港股" in market_choice: idx_choice = st.radio("", ["恒指", "科指"], horizontal=True, label_visibility="collapsed")
    else: idx_choice = st.radio("", ["道指", "標指", "納市", "IWM"], horizontal=True, label_visibility="collapsed")
    st.write("---")
    
    HSI_71 = (HK_STOCK_MAP["1. 互聯網巨頭"] + HK_STOCK_MAP["5. 國有大行與金融"])[:71]
    TECH_30 = (HK_STOCK_MAP["1. 互聯網巨頭"] + HK_STOCK_MAP["2. 半導體與芯片"])[:30]
    DOW_30 = "AAPL MSFT UNH JNJ XOM JPM V PG HD CVX MRK KO ABBV BAC AVGO PEP TMO COST CSCO MCD CRM DIS LIN ABT ACN AMD WFC NFLX INTC CAT".split()
    SPX_80 = (DOW_30 + US_STOCK_MAP["2. AI/軟件"])[:80]
    NDX_43 = (US_STOCK_MAP["2. AI/軟件"] + US_STOCK_MAP["1. 半導體"])[:43]
    IWM_32 = "CELH WING APP ELF ANF MOD MSTR SMCI TMDX AXON FOUR INDI VRT ALKT ACLS MOD ONTO POWI".split()

    if "恒指" in idx_choice: ticker_sym = "2800.HK"; b_tickers = HSI_71 
    elif "科指" in idx_choice: ticker_sym = "3032.HK"; b_tickers = TECH_30
    elif "道指" in idx_choice: ticker_sym = "DIA"; b_tickers = DOW_30
    elif "標指" in idx_choice: ticker_sym = "SPY"; b_tickers = SPX_80
    elif "納市" in idx_choice: ticker_sym = "QQQ"; b_tickers = NDX_43
    else: ticker_sym = "IWM"; b_tickers = IWM_32

    with st.spinner(f"⏳ 大宗師正在計算市寬數據... 請稍候 ☕🚀"):
        try:
            idx_df, _ = smart_fetch(ticker_sym, period="2y")
            if not idx_df.empty:
                idx_df['20MA'] = idx_df['Close'].rolling(20).mean()
                idx_df['50MA'] = idx_df['Close'].rolling(50).mean()
                idx_df['150MA'] = idx_df['Close'].rolling(150).mean()
                idx_df['200MA'] = idx_df['Close'].rolling(200).mean()
                
                clean_recent = idx_df.tail(250).copy()
                dates = clean_recent.index.strftime('%Y-%m-%d')
                
                if len(clean_recent) > 150:
                    curr_50 = clean_recent['50MA'].iloc[-1]
                    curr_150 = clean_recent['150MA'].iloc[-1]
                    past_150 = clean_recent['150MA'].iloc[-10] 
                    if curr_50 < curr_150 and curr_150 < past_150:
                        st.markdown("<div class='bear-warning'>🚨 警告：已進入熊市 (10周線跌穿30周線，且30周線向下) 🚨</div>", unsafe_allow_html=True)
                
                b_stats = get_breadth_data(b_tickers)
                v_count = b_stats['valid']
                
                st.markdown(f"### 🌊 {idx_choice} - 內部成份股市寬健康度")
                st.markdown(f"<div style='color: white; font-size:1.1rem; margin-bottom:15px;'>（系統真實成功掃描：<b style='color:#00FFCC;'>{v_count}</b> 隻核心成份股）</div>", unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='display: flex; justify-content: space-between; text-align: center; background-color: #111; padding: 20px; border-radius: 15px;'>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>20市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['20MA']/v_count)*100:.1f}%</span></div>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>50市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['50MA']/v_count)*100:.1f}%</span></div>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>150市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['150MA']/v_count)*100:.1f}%</span></div>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>200市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['200MA']/v_count)*100:.1f}%</span></div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<h4 style='color:#FFF; margin-top:20px; margin-bottom:5px;'>📊 最近 20 日市寬變化趨勢</h4>", unsafe_allow_html=True)
                fig_trend = go.Figure()
                
                x_dates = clean_recent.index[-20:].strftime('%m-%d').tolist()
                if len(x_dates) < 20: 
                    x_dates = [f"D{i}" for i in range(-19, 1)]
                
                y_20 = [(v/v_count)*100 for v in b_stats['hist_20MA']]
                y_50 = [(v/v_count)*100 for v in b_stats['hist_50MA']]
                y_150 = [(v/v_count)*100 for v in b_stats['hist_150MA']]
                y_200 = [(v/v_count)*100 for v in b_stats['hist_200MA']]

                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_20, mode='lines+markers', name='20市寬線', line=dict(color='white', width=2)))
                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_50, mode='lines+markers', name='50市寬線', line=dict(color='yellow', width=2)))
                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_150, mode='lines+markers', name='150市寬線', line=dict(color='cyan', width=2)))
                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_200, mode='lines+markers', name='200市寬線', line=dict(color='magenta', width=2)))
                
                fig_trend.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=300, margin=dict(l=20, r=60, t=10, b=20))
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

                st.write("")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                o_col = clean_recent['Open'].values; c_col = clean_recent['Close'].values
                h_col = clean_recent['High'].values; l_col = clean_recent['Low'].values
                v_col = clean_recent['Volume'].values

                if show_b_idx: fig.add_trace(go.Candlestick(x=dates, open=o_col, high=h_col, low=l_col, close=c_col, name=f'{ticker_sym} 基準指數'), row=1, col=1)
                
                if show_b_ma20: fig.add_trace(go.Scatter(x=dates, y=clean_recent['20MA'], mode='lines', name='20市寬線', line=dict(color='white', width=1.5, dash='dot')), row=1, col=1)
                if show_b_ma50: fig.add_trace(go.Scatter(x=dates, y=clean_recent['50MA'], mode='lines', name='50市寬線', line=dict(color='yellow', width=1.5, dash='dot')), row=1, col=1)
                if show_b_ma150: fig.add_trace(go.Scatter(x=dates, y=clean_recent['150MA'], mode='lines', name='150市寬線', line=dict(color='cyan', width=2, dash='dot')), row=1, col=1)
                if show_b_ma200: fig.add_trace(go.Scatter(x=dates, y=clean_recent['200MA'], mode='lines', name='200市寬線', line=dict(color='magenta', width=2, dash='dot')), row=1, col=1)

                colors = ['#00FF00' if c_col[i] >= o_col[i] else '#FF0000' for i in range(len(clean_recent))]
                fig.add_trace(go.Bar(x=dates, y=v_col, marker_color=colors, name='成交量'), row=2, col=1)
                counts, bins = np.histogram(c_col, bins=20, weights=v_col)
                max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name='蟹貨區', xaxis='x3', yaxis='y1'))

                fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, xaxis_rangeslider_visible=False, xaxis3=dict(overlaying='x', side='top', range=[0, max_c*1.1], showgrid=False, showticklabels=False))
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        except Exception as e: st.error(f"⚠️ 數據載入失敗：{e}")

# =========================================================================
# 🚀 模式 A：個股深度透視 (完美修復版)
# =========================================================================
elif app_mode == "🚀 個股深度透視":
    st.markdown("<h1 class='main-title'>🚀 個股深度透視</h1>", unsafe_allow_html=True)
    c1, c2 = st.columns([2, 1])
    with c1: ticker = st.text_input("🚀 輸入資產代號 (例: NVDA, 700.HK, DRAM)", "6869.HK").upper()
    with c2: st.write("##"); run_a = st.button("🔍 執行全方位深度分析")

    if run_a:
        with st.spinner(f"⏳ 系統正在啟動防封鎖引擎拉取 {ticker} 數據，請稍候..."):
            try:
                df, info = smart_fetch(ticker, period="2y")
                spy, _ = smart_fetch("SPY", period="2y")
                
                b_sym_plot = "2800.HK" if ".HK" in ticker else "SPY"
                b_df_plot, _ = smart_fetch(b_sym_plot, period="2y")
                if not b_df_plot.empty:
                    b_df_plot['20MA'] = b_df_plot['Close'].rolling(20).mean().bfill()
                    b_df_plot['50MA'] = b_df_plot['Close'].rolling(50).mean().bfill()
                    b_df_plot['150MA'] = b_df_plot['Close'].rolling(150).mean().bfill()
                    b_df_plot['200MA'] = b_df_plot['Close'].rolling(200).mean().bfill()

                if not df.empty and not spy.empty:
                    if df.index.tz is not None: df.index = df.index.tz_localize(None)
                    df.index = df.index.normalize()
                    if spy.index.tz is not None: spy.index = spy.index.tz_localize(None)
                    spy.index = spy.index.normalize()
                    curr_p = df['Close'].iloc[-1]
                    
                    asset_name = info.get('shortName', info.get('longName', ''))
                    industry_str = f" | {info.get('sector', 'N/A')} - {info.get('industry', 'N/A')}" if info.get('sector') else ""
                    name_html = f"<span style='font-size: 1.8rem; color: #AAAAAA; font-weight: 500; margin-left: 15px;'>{asset_name}{industry_str}</span>" if asset_name else ""
                    
                    st.markdown(f"""<div class='main-title' style='margin-bottom:10px;'>環球資產透維評估儀 [{ticker}]{name_html}</div>""", unsafe_allow_html=True)
                    
                    ath_val = info.get('fiftyTwoWeekHigh', curr_p)
                    dist_ath = ((curr_p / ath_val) - 1) * 100 if ath_val and ath_val > 0 else 0
                    
                    df['50MA_strat'] = df['Close'].rolling(50).mean().bfill()
                    ma50_bias = ((curr_p / df['50MA_strat'].iloc[-1]) - 1) * 100 if df['50MA_strat'].iloc[-1] > 0 else 0
                    
                    st.markdown(f"""
                    <div style='display: flex; gap: 15px; margin-bottom: 25px;'>
                        <div class='red-bar' style='flex: 1; background-color: #310000; border: 2px solid #FF4B4B; padding: 15px; font-size: 1.8rem;'>🎯 巔峰收復進度：距離 52周高位 [ {dist_ath:.1f}% ]</div>
                        <div class='red-bar' style='flex: 1; background-color: #002222; border: 2px solid #00FFCC; padding: 15px; font-size: 1.8rem;'>⚖️ 地心引力監控：偏離 50日線 [ {ma50_bias:+.1f}% ]</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown(f"""<div style='text-align: center; color: #00FFCC; font-size: 1.2rem; font-weight: bold; margin-bottom: 25px; padding: 10px; background-color: rgba(0, 255, 204, 0.1); border-radius: 8px; border: 1px dashed #00FFCC;'>🛡️ 必勝潛伏方程式：COSMOS-RS (星系強弱) > 52, EJ 錢流底氣 > 85, 短期能量 > 75, 最近 20 日主力資金池淨額是正數買入，OBV 大戶籌碼流入或觀望，資金部署集中度是分散</div>""", unsafe_allow_html=True)

                    # --- 🌟 爺爺補回的 cx_val (COSMOS-X) 計算法 ---
                    c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
                    slope, intercept = np.polyfit(days, c_tail, 1); pred = intercept + slope * len(days)
                    mom = (curr_p / pred) if pred > 0 else 1.0; v_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
                    cx_val = safe_n(((slope * 252) / c_tail.mean() / v_ann) * 29 * mom, 50.0)

                    # --- 計算 RS, EJ, SE ---
                    spy_aligned = spy['Close'].reindex(df.index).ffill().bfill() 
                    crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-min(63, len(df))]) - (spy_aligned.iloc[-1] / spy_aligned.iloc[-min(63, len(spy_aligned))])) * 100, 50.0)
                    v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean(); cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
                    se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-min(5, len(df))]) - 1) * 1200), 50.0)

                    # 👴 爺爺修復 N/A 問題：使用 compare_idx 確保新股都有數計
                    def get_trend_stats(metric):
                        try:
                            if len(df) < 5: return "新上市", "#888"
                            compare_idx = min(20, len(df)-1)
                            if metric == "RS":
                                past_p = df['Close'].iloc[-compare_idx]; past_spy = spy_aligned.iloc[-compare_idx]
                                past_bench = df['Close'].iloc[-min(83, len(df))] 
                                past_bench_spy = spy_aligned.iloc[-min(83, len(spy_aligned))]
                                past = 50 + ((past_p / past_bench) - (past_spy / past_bench_spy)) * 100
                                diff = cap_pct(crs_val - past)
                            elif metric == "EJ":
                                v_past_21 = df['Volume'].iloc[-(compare_idx+21):-compare_idx].mean() if len(df) > compare_idx+21 else df['Volume'].iloc[0]
                                past = (v_past_21 / max(v252, 1)) * 100
                                diff = cap_pct(cej_s - past)
                            else: 
                                past = 50 + (((df['Close'].iloc[-compare_idx] / df['Close'].iloc[-min(compare_idx+5, len(df))]) - 1) * 1200)
                                diff = cap_pct(se_s - past)
                            color = "#00FF00" if diff >= 0 else "#FF4B4B"
                            return f"{'+' if diff>=0 else ''}{diff:.1f}%", color
                        except: return "N/A", "#888"

                    def get_pulse_fig(pulse_vals):
                        try:
                            colors = ['#00FFCC' if v >= 0 else '#FF4B4B' for v in pulse_vals]
                            fig = go.Figure(go.Bar(x=list(range(len(pulse_vals))), y=pulse_vals, marker_color=colors, hoverinfo='skip'))
                            fig.update_layout(height=130, margin=dict(l=0,r=0,t=5,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False, fixedrange=True), yaxis=dict(visible=False, fixedrange=True), showlegend=False)
                            return fig
                        except: return go.Figure().update_layout(height=130, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')

                    # =======================================================
                    # 🚀 QUANTUM_X 八大護國神磚！(需要 cx_val)
                    # =======================================================
                    q_asset = int(min(100, max(0, safe_n(info.get('returnOnEquity', 0.1)*300 + 50, 75))))
                    q_trend = int(min(100, max(0, crs_val)))
                    q_power = int(min(100, max(0, cx_val * 1.5)))
                    q_money = int(min(100, max(0, cej_s)))
                    q_sent  = int(min(100, max(0, se_s)))
                    q_total = int((q_asset + q_trend + q_power + q_money + q_sent) / 5)
                    q_pivot = df['Close'].tail(120).mean() if not df.empty else 0
                    q_vol_ratio = df['Volume'].iloc[-1] / max(1, df['Volume'].tail(20).mean()) if not df.empty else 0

                    st.markdown("<div style='margin-bottom: 20px;'>", unsafe_allow_html=True)
                    qc1, qc2, qc3, qc4 = st.columns(4)
                    def q_card(col, icon, title, val, suffix=""):
                        col.markdown(f"""
                        <div style='background-color:#111; border-radius:10px; padding:15px; border:1px solid #00FFCC; margin-bottom:15px; box-shadow: 0 0 10px rgba(0,255,204,0.2);'>
                            <div style='color:#00FFCC; font-size:1.1rem; font-weight:bold; margin-bottom:8px;'>{icon} {title}</div>
                            <div style='color:white; font-size:2.2rem; font-weight:900;'>{val}{suffix}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    q_card(qc1, "🏢", "資產質量", f"{q_asset}/100")
                    q_card(qc2, "📈", "趨勢強度", f"{q_trend}/100")
                    q_card(qc3, "⚡", "動能 (Power)", f"{q_power}/100")
                    q_card(qc4, "🐋", "大資金", f"{q_money}/100")

                    qc5, qc6, qc7, qc8 = st.columns(4)
                    q_card(qc5, "🎭", "市場情緒", f"{q_sent}/100")
                    q_card(qc6, "🏆", "綜合總分", f"{q_total}/100")
                    q_card(qc7, "🏛️", "歷史中軸價", f"${q_pivot:.2f}")
                    q_card(qc8, "💰", "成交比率", f"{q_vol_ratio:.1f}x")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns([1, 1.2, 1.6])
                    with c1: st.markdown(f"""<div class='cosmos-box' style='height: 460px; display:flex; flex-direction:column; justify-content:center;'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>""", unsafe_allow_html=True)
                    with c2:
                        stat_rs, col_rs = get_trend_stats("RS")
                        st.markdown(f"""<div class='cosmos-box' style='border-color:#FFD700; height: 330px; display:flex; flex-direction:column; justify-content:center;'><div class='cosmos-label' style='font-size:1.6rem;'>COSMOS-RS (星系強弱)</div><div class='cosmos-value' style='font-size:4rem;'>{crs_val:.1f}</div><div style='color:{col_rs}; font-size:1.5rem; font-weight:bold; margin-top:15px;'>20日推力: {stat_rs}</div></div>""", unsafe_allow_html=True)
                        pulse_df = df.tail(21).copy(); rs_line = pulse_df['Close'] / spy_aligned.tail(21); rs_pulse_vals = rs_line.pct_change().tail(20).fillna(0).values * 600
                        st.plotly_chart(get_pulse_fig(rs_pulse_vals), use_container_width=True, theme=None, config={'displayModeBar': False})
                    with c3:
                        def draw_triad_bar(val, color):
                            lit = int((min(120, val)/120)*21); html = f"<div class='bar-group-container' style='margin:0;'>"
                            for g in range(7):
                                html += "<div class='bar-triad'>"
                                for i in range(3):
                                    idx = g*3+i; c_code = "#FF4B4B" if idx<6 else ("#FFD700" if idx<12 else color)
                                    html += f"<div class='ej-seg' style='height:14px; width:12px; background-color:{c_code if idx < lit else '#222'}; opacity:{1 if idx < lit else 0.1};'></div>"
                                html += "</div>"
                            return html + "</div>"
                        avg_vol = df['Volume'].tail(252).mean() or 1
                        stat_ej, col_ej = get_trend_stats("EJ")
                        st.markdown(f"""<div class='cosmos-box' style='border-color:#00FFFF; padding: 15px; height: 100px; display:flex; flex-direction:column; justify-content:center;'><div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:5px;'><span style='color:#00FFFF; font-size:1.4rem; font-weight:bold;'>EJ 錢流底氣: {cej_s:.1f}%</span><span style='color:{col_ej}; font-size:1.2rem; font-weight:bold;'>20日吸金: {stat_ej}</span></div>{draw_triad_bar(cej_s, "#00FFFF")}</div>""", unsafe_allow_html=True)
                        vol_ratio = (pulse_df['Volume'].tail(20) / avg_vol).values; direction = np.where(pulse_df['Close'].tail(20) >= pulse_df['Open'].tail(20), 1, -1); ej_pulse_vals = vol_ratio * direction * 50 
                        st.plotly_chart(get_pulse_fig(ej_pulse_vals), use_container_width=True, theme=None, config={'displayModeBar': False})
                        stat_se, col_se = get_trend_stats("SE")
                        st.markdown(f"""<div class='cosmos-box' style='border-color:#FF00FF; padding: 15px; height: 100px; display:flex; flex-direction:column; justify-content:center; margin-top:0px;'><div style='display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:5px;'><span style='color:#FF00FF; font-size:1.4rem; font-weight:bold;'>短期能量 BAR: {se_s:.1f}%</span><span style='color:{col_se}; font-size:1.2rem; font-weight:bold;'>20日動能: {stat_se}</span></div>{draw_triad_bar(se_s, "#FF00FF")}</div>""", unsafe_allow_html=True)
                        se_pulse_vals = pulse_df['Close'].pct_change().tail(20).fillna(0).values * 200
                        st.plotly_chart(get_pulse_fig(se_pulse_vals), use_container_width=True, theme=None, config={'displayModeBar': False})

                    # --- OBV 與資金池 ---
                    try:
                        mf_df = df.tail(41).copy(); mf_df['Typical_Price'] = (mf_df['High'] + mf_df['Low'] + mf_df['Close']) / 3
                        mf_df['Net_Flow'] = mf_df['Typical_Price'] * mf_df['Volume'] * np.where(mf_df['Close'] > mf_df['Close'].shift(1).fillna(mf_df['Close']), 1, -1)
                        mf_df['OBV_Daily'] = (np.sign(mf_df['Close'].diff()) * mf_df['Volume']).fillna(0); mf_df['OBV'] = mf_df['OBV_Daily'].cumsum()
                        curr_20d_flow = mf_df['Net_Flow'].tail(20).sum(); prev_20d_flow = mf_df['Net_Flow'].iloc[-40:-20].sum()
                        if abs(curr_20d_flow) >= 1e8: flow_str = f"{'+' if curr_20d_flow>0 else ''}${curr_20d_flow/1e8:.1f} 億"
                        elif abs(curr_20d_flow) >= 1e6: flow_str = f"{'+' if curr_20d_flow>0 else ''}${curr_20d_flow/1e6:.1f} M (百萬)"
                        else: flow_str = f"{'+' if curr_20d_flow>0 else ''}${curr_20d_flow:,.0f}"
                        flow_color = "#00FF00" if curr_20d_flow > 0 else "#FF4B4B"
                        
                        mf_pct = cap_pct((curr_20d_flow - prev_20d_flow) / abs(prev_20d_flow + 1) * 100)
                        
                        compare_idx = min(20, len(mf_df)-1)
                        obv_curr_val = mf_df['OBV'].iloc[-1] - mf_df['OBV'].iloc[-compare_idx]; 
                        obv_prev_val = mf_df['OBV'].iloc[-compare_idx] - mf_df['OBV'].iloc[0] if len(mf_df) > compare_idx else 1
                        price_trend = mf_df['Close'].iloc[-1] - mf_df['Close'].iloc[-compare_idx]
                        
                        obv_pct = cap_pct((obv_curr_val - obv_prev_val) / abs(obv_prev_val + 1) * 100) # 👴 保險絲！
                        
                        obv_total_vol = mf_df['Volume'].tail(20).sum() or 1
                        if abs(obv_curr_val) / obv_total_vol < 0.02: trend_str, trend_color, obv_state = "9. 🧊 資金膠著盤整 (觀望)", "#888888", 9
                        else:
                            if price_trend >= 0:
                                if obv_curr_val > 0: 
                                    if obv_pct > 20: trend_str, trend_color, obv_state = "1. 👑 強烈流入", "#00FF00", 1
                                    else: trend_str, trend_color, obv_state = "2. 📈 流入", "#00FF00", 2
                                else:
                                    if obv_pct < -20: trend_str, trend_color, obv_state = "5. 💣 資金高位撤離 (量價強烈背離)", "#FF4B4B", 5
                                    else: trend_str, trend_color, obv_state = "6. ⚠️ 資金高位撤離 (量價背離)", "#FF4B4B", 6
                            else:
                                if obv_curr_val < 0:
                                    if obv_pct < -20: trend_str, trend_color, obv_state = "3. 💀 大戶持續派發 (強烈流出)", "#FF4B4B", 3
                                    else: trend_str, trend_color, obv_state = "4. 📉 大戶持續派發 (流出)", "#FF4B4B", 4
                                else:
                                    if obv_pct > 20: trend_str, trend_color, obv_state = "7. 🐉 底部分歧掃貨 (量價強烈背離)", "#00FFCC", 7
                                    else: trend_str, trend_color, obv_state = "8. 🐲 底部分歧掃貨 (量價背離)", "#00FFCC", 8
                        
                        daily_abs_flow = abs(mf_df['Net_Flow'].tail(20)); total_abs_flow = daily_abs_flow.sum() or 1; conc_pct = (daily_abs_flow.max() / total_abs_flow) * 100
                        if conc_pct > 35: conc_level, conc_color, conc_note = "⚡ 高度集中", "#FF4B4B", "（集中買入/掟貨）"
                        elif conc_pct > 15: conc_level, conc_color, conc_note = "🌿 正常分佈", "#FFD700", "（公開正常買賣）"
                        else: conc_level, conc_color, conc_note = "💎 穩定分散", "#00FFCC", "（不想被人知道偷偷佈局）"
                        
                        st.write(""); st.markdown("<h3 style='color:#FFF; margin-bottom:10px;'>🌊 獨家解密：20日主力資金池淨額 (Money Flow & OBV)</h3>", unsafe_allow_html=True)
                        st.markdown("<div style='background-color:#000; border-radius:15px; padding:20px; border: 2px solid #333;'>", unsafe_allow_html=True)
                        mc1, mc2 = st.columns(2)
                        with mc1:
                            st.markdown(f"<div class='cosmos-box' style='border-color:{flow_color}; padding:15px; height:120px; display:flex; flex-direction:column; justify-content:center;'><div style='display:flex; justify-content:space-between;'><span style='color:{flow_color}; font-size:1.4rem; font-weight:bold;'>資金總數: {flow_str}</span><span style='color:{'#00FF00' if mf_pct>=0 else '#FF4B4B'}; font-size:1.2rem; font-weight:bold;'>20日變化: {mf_pct:.1f}%</span></div></div>", unsafe_allow_html=True)
                            st.plotly_chart(get_pulse_fig(mf_df['Net_Flow'].tail(20).values), use_container_width=True, theme=None, config={'displayModeBar': False})
                        with mc2:
                            st.markdown(f"<div class='cosmos-box' style='border-color:{trend_color}; padding:15px; height:120px; display:flex; flex-direction:column; justify-content:center;'><div style='display:flex; justify-content:space-between;'><span style='color:{trend_color}; font-size:1.4rem; font-weight:bold;'>OBV軌跡: {trend_str}</span><span style='color:{'#00FF00' if obv_pct>=0 else '#FF4B4B'}; font-size:1.2rem; font-weight:bold;'>20日變化: {obv_pct:.1f}%</span></div></div>", unsafe_allow_html=True)
                            st.plotly_chart(get_pulse_fig(mf_df['OBV_Daily'].tail(20).values), use_container_width=True, theme=None, config={'displayModeBar': False})
                        st.markdown(f"<div style='margin-top:20px; border-top:1px dashed #444; padding-top:15px;'><div style='display:flex; justify-content:space-between;'><span style='font-weight:bold;'>🎯 資金部署集中度：<span style='color:{conc_color};'>{conc_level}</span></span><span>極值佔比: {conc_pct:.1f}% <span style='color:{conc_color}; font-weight:bold;'>{conc_note}</span></span></div><div style='width:100%; background-color:#222; border-radius:10px; height:12px; margin-top:8px; border:1px solid #444;'><div style='width:{conc_pct}%; background-color:{conc_color}; height:100%; box-shadow:0 0 10px {conc_color};'></div></div></div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    except: pass

                    # --- 🌟 摩訶釋達巨型圖表 (完全恢復) ---
                    st.write("### 📊 摩訶釋達・能量與籌碼透視圖 (個股均線 vs 大盤市寬疊加)")
                    try:
                        df['20MA'] = df['Close'].rolling(20).mean().bfill()
                        df['50MA'] = df['Close'].rolling(50).mean().bfill()
                        df['150MA'] = df['Close'].rolling(150).mean().bfill()
                        df['200MA'] = df['Close'].rolling(200).mean().bfill()
                        
                        recent = df.tail(120).dropna(subset=['Close', 'Volume']).copy()
                        if not recent.empty:
                            dates = recent.index.strftime('%Y-%m-%d')
                            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                            
                            o_col = recent['Open'].values; c_col = recent['Close'].values
                            h_col = recent['High'].values; l_col = recent['Low'].values
                            v_col = recent['Volume'].values

                            fig.add_trace(go.Candlestick(x=dates, open=o_col, high=h_col, low=l_col, close=c_col, name='個股股價'), row=1, col=1)
                            
                            if show_s_ma20: fig.add_trace(go.Scatter(x=dates, y=recent['20MA'], mode='lines', name='個股20日線', line=dict(color='white', width=1.5)), row=1, col=1)
                            if show_s_ma50: fig.add_trace(go.Scatter(x=dates, y=recent['50MA'], mode='lines', name='個股50日線', line=dict(color='yellow', width=1.5)), row=1, col=1)
                            if show_s_ma150: fig.add_trace(go.Scatter(x=dates, y=recent['150MA'], mode='lines', name='個股150日線', line=dict(color='cyan', width=1.5)), row=1, col=1)
                            if show_s_ma200: fig.add_trace(go.Scatter(x=dates, y=recent['200MA'], mode='lines', name='個股200日線', line=dict(color='magenta', width=1.5)), row=1, col=1)

                            if not b_df_plot.empty:
                                align_b = b_df_plot.reindex(recent.index).ffill().bfill()
                                if len(align_b)>0 and align_b['Close'].iloc[0]!=0 and c_col[0]!=0:
                                    norm = c_col[0] / align_b['Close'].iloc[0]
                                    if show_b_idx: fig.add_trace(go.Scatter(x=dates, y=align_b['Close']*norm, mode='lines', name=f'{b_sym_plot} 基準', line=dict(color='#FF4B4B', width=2)), row=1, col=1)
                                    if show_b_ma20: fig.add_trace(go.Scatter(x=dates, y=align_b['20MA']*norm, mode='lines', name='20市寬線', line=dict(color='rgba(255,255,255,0.6)', width=1.5, dash='dot')), row=1, col=1)
                                    if show_b_ma50: fig.add_trace(go.Scatter(x=dates, y=align_b['50MA']*norm, mode='lines', name='50市寬線', line=dict(color='rgba(255,215,0,0.6)', width=1.5, dash='dot')), row=1, col=1)
                                    if show_b_ma150: 
                                        fig.add_trace(go.Scatter(x=dates, y=align_b['150MA']*norm, mode='lines', name='150市寬線', line=dict(color='rgba(0,255,255,0.6)', width=1.5, dash='dot')), row=1, col=1)
                                    if show_b_ma200:
                                        fig.add_trace(go.Scatter(x=dates, y=align_b['200MA']*norm, mode='lines', name='200市寬線', line=dict(color='rgba(255,0,255,0.6)', width=1.5, dash='dot')), row=1, col=1)

                            colors = ['#00FF00' if c_col[i] >= o_col[i] else '#FF0000' for i in range(len(recent))]
                            fig.add_trace(go.Bar(x=dates, y=v_col, marker_color=colors, name='成交量'), row=2, col=1)
                            counts, bins = np.histogram(c_col, bins=20, weights=v_col)
                            max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                            fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name='蟹貨區', xaxis='x3', yaxis='y1'))
                            
                            fig.update_layout(
                                template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, 
                                showlegend=True, legend=dict(font=dict(color="white"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), 
                                xaxis_rangeslider_visible=False, 
                                xaxis=dict(type='category', showgrid=False, showticklabels=True, tickfont=dict(color='white'), title="日期"), 
                                yaxis=dict(showgrid=True, gridcolor='#333', showticklabels=True, tickfont=dict(color='white'), title="股價"), 
                                xaxis3=dict(overlaying='x', side='top', range=[0, max_c*1.1], showgrid=False, showticklabels=False)
                            )
                            st.plotly_chart(fig, use_container_width=True, theme=None, config={'scrollZoom': True, 'displayModeBar': True}) 
                    except Exception as e: pass

                    # --- 估值與 DNA (完全恢復) ---
                    st.write("---"); d_c1, d_c2 = st.columns([1, 2.5]); is_etf = info.get('quoteType') == 'ETF'; real_roe = info.get('returnOnEquity')
                    
                    if is_etf or real_roe is None or real_roe == 0:
                        dna_v = round(safe_n((cx_val * 0.5) + (crs_val * 0.5), 50.0), 1); dna_title = "ETF 綜合質量基因"
                        m9 = {"🚀 增長加速度 (15%)": int(safe_n(cx_val / 10, 5)), "🔭 營收天花板 (15%)": int(safe_n(crs_val / 10, 5)), "🛡️ 定價權護城河 (15%)": int(safe_n(cej_s / 10, 5)), "🦖 市場佔有率 (15%)": 9 if info.get('totalAssets', 0) > 1e9 else 5, "💰 資本效率 (10%)": int(safe_n(se_s / 10, 5)), "💎 獲利含金量 (10%)": int(max(1, 10 - (v_ann * 20))), "🧱 財務安全墊 (10%)": int(safe_n(crs_val / 10, 5)), "🎁 股東回饋 (5%)": int(safe_n(info.get('yield', info.get('dividendYield', 0))*200+2, 5)), "📈 經營穩定性 (5%)": int(safe_n(cx_val / 12, 5))}
                    else:
                        f1_growth = min(100, max(0, safe_n(info.get('earningsGrowth', 0)) * 200 + 40))
                        f2_rev = min(100, max(0, safe_n(info.get('revenueGrowth', 0)) * 150 + 40))
                        f3_moat = min(100, max(0, safe_n(info.get('profitMargins', 0)) * 300 + 30))
                        rev_val = safe_n(info.get('totalRevenue', 0)); f4_dom = min(100, max(40, (rev_val / 1e10) * 5 + 50))
                        f5_roe = min(100, max(0, safe_n(info.get('returnOnEquity', 0)) * 300 + 30))
                        f6_cash = min(100, max(0, safe_n(info.get('operatingMargins', 0)) * 250 + 40))
                        de_ratio = safe_n(info.get('debtToEquity', 100)); f7_safe = min(100, max(0, 100 - (de_ratio / 2)))
                        f8_yield = min(100, safe_n(info.get('dividendYield', 0)) * 2000 + 20 if info.get('dividendYield') else 30)
                        f9_stable = min(100, max(0, safe_n(info.get('forwardPE', 15)) * -1 + 100 if safe_n(info.get('forwardPE', 0)) > 0 else 50))
                        dna_v = round(max(0.0, min(100.0, (f1_growth * 0.15) + (f2_rev * 0.15) + (f3_moat * 0.15) + (f4_dom * 0.15) + (f5_roe * 0.10) + (f6_cash * 0.10) + (f7_safe * 0.10) + (f8_yield * 0.05) + (f9_stable * 0.05))), 1)
                        dna_title = "投行級股王基因"
                        m9 = {"🚀 增長加速度 (15%)": int(max(1, min(10, f1_growth / 10))), "🔭 營收天花板 (15%)": int(max(1, min(10, f2_rev / 10))), "🛡️ 定價權護城河 (15%)": int(max(1, min(10, f3_moat / 10))), "🦖 市場佔有率 (15%)": int(max(1, min(10, f4_dom / 10))), "💰 資本效率 (10%)": int(max(1, min(10, f5_roe / 10))), "💎 獲利含金量 (10%)": int(max(1, min(10, f6_cash / 10))), "🧱 財務安全墊 (10%)": int(max(1, min(10, f7_safe / 10))), "🎁 股東回饋 (5%)": int(max(1, min(10, f8_yield / 10))), "📈 經營穩定性 (5%)": int(max(1, min(10, f9_stable / 10)))}
                        
                    dna_v = max(0.0, min(100.0, dna_v)); d_lv = "第 1 級" if dna_v>=90 else ("第 2 級" if dna_v>=80 else ("第 3 級" if dna_v>=70 else "後續"))
                    
                    with d_c1: st.markdown(f"<div class='cosmos-box' style='border-color:#FF4B4B; height:420px; display:flex; flex-direction:column; justify-content:center;'><div style='color:#FF4B4B; font-weight:900; font-size:1.8rem;'>🧬 COSMOS-DNA</div><div style='font-size:0.9rem; opacity:0.7; margin:5px 0;'>{dna_title}</div><div style='font-size:6rem; font-weight:900;'>{dna_v}</div><div style='color:#FFD700;'>[ 現屬 {d_lv} ]</div></div>", unsafe_allow_html=True)
                    with d_c2:
                        colors_9d = ["#00FFCC", "#00FFCC", "#00FFCC", "#00FFCC", "#FF4B4B", "#BC13FE", "#FFFFFF", "#FFD700", "#FF00FF"]
                        for i, (l, s) in enumerate(m9.items()):
                            sc = max(1, min(10, s)); grid = '<div class="energy-bar-container-8d">' + "".join([f'<div class="energy-seg-8d" style="background-color:{colors_9d[i%9]}; opacity:{"1" if j<=sc else "0.1"};"></div>' for j in range(1,11)]) + '</div>'
                            st.markdown(f"<div style='display:flex; justify-content:space-between; font-weight:bold;'><span>{l}</span><span>{sc}/10</span></div>{grid}", unsafe_allow_html=True)

                    st.write("---")
                    f_eps = info.get('forwardEps'); t_eps = info.get('trailingEps', 0)
                    if not f_eps or f_eps <= 0:
                        f_pe = info.get('forwardPE')
                        if f_pe and f_pe > 0: f_eps = curr_p / f_pe
                        else: f_eps = max(t_eps, 0.1) * (1 + (dna_v/100))
                    if t_eps > 0 and f_eps > (t_eps * 2.5): f_eps = t_eps * 2.5 
                    g_score = m9.get("🚀 增長加速度 (15%)", 5) if not is_etf else 5
                    is_semi_or_hardware = "Semiconductor" in info.get('industry', '') or "Hardware" in info.get('industry', '') or "Technology" in info.get('sector', '')
                    if is_semi_or_hardware: fair_pe = 18.0 if g_score >= 8 else (15.0 if g_score >= 5 else 10.0)
                    else: fair_pe = 35.0 if g_score >= 9 else (25.0 if g_score >= 7 else (18.0 if g_score >= 5 else 12.0))
                    
                    forward_price = f_eps * fair_pe
                    price_diff = ((forward_price - curr_p) / curr_p) * 100 if curr_p > 0 else 0

                    base_score = (dna_v * 0.70) + (s10_mgmt * 0.15) + (s11_story * 0.15)
                    if "第二曲線" in x_factor: base_score += 10
                    elif "印鈔機" in x_factor: base_score += 5
                    elif "吸血鬼" in x_factor: base_score -= 15
                    dragon_index = round(max(5.0, min(98.5, base_score)), 1)
                    
                    if dragon_index >= 80: t_lv, t_desc, val_title, val_color, act_desc = "第 1 級", "極致真龍", "🔥 烈火鳳凰", "#BC13FE", "【順勢重倉】強大動能與財報支撐，緊貼趨勢操作。"
                    elif dragon_index >= 65: t_lv, t_desc, val_title, val_color, act_desc = "第 2 級", "潛力金龍", "🌟 潛龍伏躍", "#00FFCC", "【分批建倉】財報穩健，動能醞釀中，適合持有觀望。"
                    elif dragon_index >= 40: t_lv, t_desc, val_title, val_color, act_desc = "第 3 級", "中庸凡骨", "⚠️ 海市蜃樓", "#FFA500", "【謹慎觀望】動能與財報平平，注意回調風險。"
                    else: t_lv, t_desc, val_title, val_color, act_desc = "第 4 級", "高危泥鰍", "☠️ 末路狂花", "#FF4B4B", "【規避風險】財報轉弱且動能破位，嚴格止損。"

                    vc1, vc2, vc3 = st.columns(3)
                    with vc1: st.markdown(f"""<div class='val-box-purple' style='height:280px;'><div class='val-label'>🎯 遠期目標價 (預測)</div><div style='font-size:3.5rem; font-weight:900; color:#00FFCC;'>${forward_price:,.2f}</div><div style='font-size:1.2rem; margin-top:10px;'>潛在空間: <span style='color:{"#00FFCC" if price_diff>0 else "#FF4B4B"}; font-weight:900;'>{"+" if price_diff>0 else ""}{price_diff:.1f}%</span></div><div style='font-size:1.2rem; font-weight:bold; margin-top:10px; opacity:0.9;'>TTM EPS: ${t_eps:.2f} | Fwd EPS: ${f_eps:.2f}</div></div>""", unsafe_allow_html=True)
                    with vc2: st.markdown(f"""<div class='val-box-purple' style='border-color:{val_color}; box-shadow: 0 0 25px {val_color}44; height:280px;'><div class='val-label'>🏆 真龍指數 ({val_title})</div><div style='font-size:5rem; font-weight:900; color:{val_color};'>{dragon_index}</div><div style='font-size:1.1rem; color:{val_color};'>[ 現屬 {t_lv} ({t_desc}) ]</div></div>""", unsafe_allow_html=True)
                    with vc3: st.markdown(f"""<div class='val-box-purple' style='border-color:#00FFFF; box-shadow: 0 0 25px #00FFFF44; height:280px;'><div class='val-label'>🎭 時代敘事與決策</div><div style='font-size:1.5rem; font-weight:bold; margin-top:10px;'>{x_factor}</div><p style='color:#00FFFF; margin-top:5px; font-size:1.2rem;'>敘事溢價信心: {s11_story}%</p><div style='background:#111; padding:10px; border-radius:5px; margin-top:15px; font-weight:bold;'>{act_desc}</div></div>""", unsafe_allow_html=True)

                    st.write("---")
                    v1,v2,v3 = st.columns(3); v4,v5,v6 = st.columns(3); v7,v8,v9 = st.columns(3)
                    def v_card(col, t, t_v, f_v, d): col.markdown(f"<div class='val-box'><div class='val-label'>{t}</div><div class='val-text'>TTM: <span class='val-focus'>{t_v}</span></div><div class='val-text'>預期: <span class='val-focus'>{f_v}</span></div><div style='color:#FFA500; font-size:0.9rem;'>{d}</div></div>", unsafe_allow_html=True)
                    v_card(v1, "PE 獲利比", safe_s(info, ['trailingPE'], "x"), safe_s(info, ['forwardPE'], "x"), "獲利估值")
                    v_card(v2, "PEG 增長比", safe_s(info, ['pegRatio']), "N/A", "增長性價比")
                    v_card(v3, "PS 營收比", safe_s(info, ['priceToSalesTrailing12Months'], "x"), "N/A", "營收規模")
                    v_card(v4, "PB 淨資產", safe_s(info, ['priceToBook'], "x"), "N/A", "賬面價值")
                    v_card(v5, "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], "x"), "N/A", "企業估值")
                    v_card(v6, "股息率", safe_s(info, ['dividendYield', 'yield'], "%"), "N/A", "回報率")
                    
                    v7.markdown(f"<div class='val-box'><div class='val-label'>Beta 敏感度</div><div class='val-focus' style='margin-top:20px;'>{get_beta(info, df, spy)}</div><div style='color:#FFA500; font-size:0.9rem; margin-top:15px;'>對大盤聯動性</div></div>", unsafe_allow_html=True)
                    v8.markdown(f"<div class='val-box'><div class='val-label'>@ (Alpha) 超額回報</div><div class='val-focus' style='margin-top:20px;'>{get_alpha(get_beta(info, df, spy), df, spy)}</div><div style='color:#FFA500; font-size:0.9rem; margin-top:15px;'>大盤外表現</div></div>", unsafe_allow_html=True)
                    
                    hv_v = get_volatility(df); iv_v = get_iv(asset); iv_warning = ""
                    if iv_v != 'N/A' and hv_v != 'N/A':
                        try:
                            if float(iv_v[:-1]) > float(hv_v[:-1]): iv_warning = '[ IV > HV 期權溢價中 ]'
                        except: pass
                    v9.markdown(f"<div class='val-box'><div class='val-label'>🌪️ 波動率雙併 (Risk)</div><div class='val-text' style='margin-top:15px;'>年化 (HV): <span class='val-focus'>{hv_v}</span></div><div class='val-text'>隱含 (IV): <span class='val-focus'>{iv_v}</span></div><div style='color:#FFA500; font-size:0.8rem; margin-top:10px;'>{iv_warning}</div></div>", unsafe_allow_html=True)

                    st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center;'>🧙 90 大名家：真實申報持倉</div>", unsafe_allow_html=True)
                    total_shares = info.get('sharesOutstanding', 1); holders = asset.institutional_holders
                    if holders is not None and not holders.empty and 'Holder' in holders.columns:
                        for _, row in holders.head(8).iterrows():
                            shares = row.get('Shares', 0); calc_pct = (shares/total_shares); val_m = row.get('Value', 0)/1e6
                            st.markdown(f"<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>持有 {shares:,.0f} 股 | 佔比 {calc_pct:.2%} | 市值 ${val_m:.1f}M</span></div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else: st.error("⚠️ 無法獲取有效數據。")
            except Exception as e: st.error(f"系統分析受阻，原因: {e}")

# =========================================================================
# 📡 拔河熱力圖 / 🔍 尋龍雷達 / 📉 VCP / 🌊 海龜 (使用慢速引擎)
# =========================================================================
elif "熱力圖" in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    m_view = st.sidebar.radio("選擇星系", ["🇺🇸 美股陣列", "🇭🇰 港股陣列"])
    is_us = "美股" in m_view; bench_sym = "SPY" if is_us else "^HSI"
    target_map = (US_ETF_MAP if "ETF" in app_mode else US_STOCK_MAP) if is_us else (HK_ETF_MAP if "ETF" in app_mode else HK_STOCK_MAP)
    with st.spinner('拔河排名計算中，慢速防封鎖引擎已啟動...'):
        try:
            bench_df, _ = smart_fetch(bench_sym, period="60d")
            bench_df = bench_df['Close'].dropna(); results = []
            for name, tickers in target_map.items():
                for idx, t in enumerate(tickers):
                    try:
                        d, _ = smart_fetch(t, period="60d")
                        d = d['Close'].dropna()
                        if len(d) >= 20:
                            rs = 50 + ((d.iloc[-1]/d.iloc[-20]) - (bench_df.iloc[-1]/bench_df.iloc[-20])) * 100
                            results.append({"版塊": name, "RS強弱": round(rs, 1)}); break
                    except: continue
            if results:
                df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=True)
                fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["版塊"], orientation='h', marker=dict(color=df_rs["RS強弱"], colorscale='Portland')))
                fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font=dict(color='white'), height=700)
                st.plotly_chart(fig, use_container_width=True, theme=None, config={'displayModeBar': False})
        except: pass

elif "尋龍雷達" in app_mode or "ETF 專屬雷達" in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    c_mkt, c_sec, c_strat = st.columns([1, 1, 1.5])
    if "尋龍雷達" in app_mode:
        with c_mkt: m_choice = st.radio("1. 市場", ["🇺🇸 美股", "🇭🇰 港股"])
        is_us = "美股" in m_choice; is_etf = False
    else:
        is_us = "美股" in app_mode; is_etf = True
        with c_mkt: st.info(f"鎖定 {app_mode.split(' ')[1]}")
    bench_sym = "SPY" if is_us else "^HSI"
    target_dict = (US_ETF_MAP if is_etf else US_STOCK_MAP) if is_us else (HK_ETF_MAP if is_etf else HK_STOCK_MAP)
    with c_sec: s_choice = st.selectbox("2. 掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()))
    with c_strat: t_strat = st.radio("3. 戰術過濾", ["🔥 極致新高 (ATH)", "🐉 潛龍伏躍 (10-20% 空間)"])
    
    if st.button("📡 發射撒網尋龍電波！"):
        bench_data, _ = smart_fetch(bench_sym, period="2y")
        tickers_to_scan = list(set([t for sub in target_dict.values() for t in sub])) if "全星系" in s_choice else target_dict[s_choice]
        found = False; pb = st.progress(0)
        with st.spinner("⏳ 慢速引擎過濾中，請稍候..."):
            for idx, t in enumerate(tickers_to_scan):
                pb.progress((idx + 1) / len(tickers_to_scan))
                if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                try:
                    d_full, _ = smart_fetch(t, period="1y")
                    if len(d_full) > 100:
                        d = d_full.tail(63)
                        curr_p = d['Close'].iloc[-1]; ath = d_full['High'].tail(252).max()
                        if t_strat == "🔥 極致新高 (ATH)" and (curr_p / ath) < 0.93: continue
                        elif t_strat != "🔥 極致新高 (ATH)" and not (0.75 <= (curr_p / ath) <= 0.90): continue

                        tp = (d['High']+d['Low']+d['Close'])/3; nf = tp*d['Volume']*np.where(d['Close']>d['Close'].shift(1).fillna(d['Close']),1,-1)
                        net_flow_20 = nf.tail(20).sum(); conc_20 = (abs(nf.tail(20)).max()/max(abs(nf.tail(20)).sum(), 1))*100
                        obv = (np.sign(d['Close'].diff())*d['Volume']).fillna(0).cumsum()
                        obv_curr = obv.iloc[-1]-obv.iloc[-21]; obv_prev = obv.iloc[-21]-obv.iloc[-41]
                        obv_pct = cap_pct((obv_curr-obv_prev)/max(abs(obv_prev), 1)*100)
                        p_trend = d['Close'].iloc[-1]-d['Close'].iloc[-21]; state = 9
                        if p_trend>=0: state = 1 if obv_pct>20 else 2
                        else: state = 7 if obv_pct>20 else 8
                        
                        crs = safe_n(50+((curr_p/d['Close'].iloc[-min(63, len(d))])-(bench_data['Close'].iloc[-1]/bench_data['Close'].iloc[-min(63, len(bench_data))]))*100)
                        ej = safe_n((d['Volume'].tail(21).mean()/max(d['Volume'].tail(252).mean() if len(d)>200 else d['Volume'].mean(),1))*100)
                        se = safe_n(50+(((curr_p/d['Close'].iloc[-min(5, len(d))])-1)*1200))

                        if net_flow_20 > 0 and conc_20 < 50 and state in [1, 2, 7, 8, 9] and se > 75 and ej > 85 and crs > 52:
                            found = True
                            st.markdown(f"<div class='scan-card-fire'><h2>🎯 {t} | 符合大戶佈局！</h2><p>💰 資金流: {net_flow_20/1e8:.1f}億 | 🎯 集中度: {conc_20:.1f}% | 🌊 OBV: {state}<br>⚡ SE: {se:.1f} | 🔋 EJ: {ej:.1f} | 📈 RS: {crs:.1f}</p></div>", unsafe_allow_html=True)
                except: pass
        if not found: st.warning("💤 雷達掃描完畢，未有標的。")

elif app_mode == "📈 VCP 形態戰術掃描 & 防守圖":
    st.markdown("<h1 class='main-title'>📈 VCP 形態戰術掃描 & 防守圖</h1>", unsafe_allow_html=True)
    c_cat, c_mkt, c_sec, c_strat = st.columns([1, 1, 1.5, 1.5])
    with c_cat: asset_type = st.radio("1. 類別", ["🏢 個股", "🧺 ETF"])
    with c_mkt: market_choice = st.radio("2. 市場", ["🇺🇸 美股", "🇭🇰 港股"])
    is_us = "美股" in market_choice; bench_sym = "SPY" if is_us else "2800.HK"
    target_dict = (US_ETF_MAP if "ETF" in asset_type else US_STOCK_MAP) if is_us else (HK_ETF_MAP if "ETF" in asset_type else HK_STOCK_MAP)
    with c_sec: s_choice = st.selectbox("3. 範圍", ["🌐 全星系大規模搜索"] + list(target_dict.keys()))
    with c_strat: vcp_strat = st.radio("4. 戰術", ["🔥 極致新高 (ATH)", "🐉 潛龍伏躍 (10-20% 空間)"])

    if 'vcp_scanned_stocks' not in st.session_state: st.session_state.vcp_scanned_stocks = []

    if st.button("📡 發射！執行 VCP 海選"):
        tickers_to_scan = list(set([t for sub in target_dict.values() for t in sub])) if "全星系" in s_choice else target_dict[s_choice]
        found_stocks = []; pb = st.progress(0)
        with st.spinner("⏳ 慢速引擎過濾中..."):
            try:
                bench_df, _ = smart_fetch(bench_sym, period="1y"); bench_df = bench_df['Close'].dropna()
                yearly_returns = {}; valid_dfs = {}
                for idx, t in enumerate(tickers_to_scan):
                    pb.progress((idx + 1) / len(tickers_to_scan))
                    if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                    try:
                        df_t, _ = smart_fetch(t, period="1y")
                        if len(df_t) > 150:
                            yearly_returns[t] = (df_t['Close'].iloc[-1] / df_t['Close'].iloc[0]) - 1
                            valid_dfs[t] = df_t
                    except: continue

                if yearly_returns:
                    all_rets = pd.Series(list(yearly_returns.values()))
                    for t, ret in yearly_returns.items():
                        df_vcp = valid_dfs[t]; curr = df_vcp.iloc[-1]; ath = df_vcp['High'].tail(252).max()
                        df_vcp['MA50'] = df_vcp['Close'].rolling(50).mean(); df_vcp['MA150'] = df_vcp['Close'].rolling(150).mean(); df_vcp['MA200'] = df_vcp['Close'].rolling(200).mean()
                        if not (curr['Close'] > df_vcp['MA50'].iloc[-1] > df_vcp['MA150'].iloc[-1]): continue
                        if vcp_strat == "🔥 極致新高 (ATH)":
                            if not (df_vcp['MA150'].iloc[-1] > df_vcp['MA200'].iloc[-1]) or (curr['Close'] / ath) < 0.93: continue
                        else:
                            if not (0.75 <= (curr['Close'] / ath) <= 0.90): continue
                        rs_rating = int((all_rets[all_rets <= ret].count() / len(all_rets)) * 99)
                        if rs_rating < 80: continue
                        df_vcp['Vol50'] = df_vcp['Volume'].rolling(50).mean()
                        whale_count = len(df_vcp.tail(10)[(df_vcp.tail(10)['Close'] > df_vcp.tail(10)['Open']) & (df_vcp.tail(10)['Volume'] > df_vcp.tail(10)['Vol50'] * 1.5)])
                        found_stocks.append({'Ticker': t, 'RS Rating': rs_rating, 'Tags': f"🔥 大戶掃貨 ({whale_count}/10)" if whale_count >= 3 else "", 'Pivot': df_vcp['High'].tail(20).max()})
                st.session_state.vcp_scanned_stocks = sorted(found_stocks, key=lambda x: x['RS Rating'], reverse=True)
            except Exception as e: st.error(f"掃描受阻: {e}")

    if st.session_state.vcp_scanned_stocks:
        st.success(f"🎉 成功尋獲 {len(st.session_state.vcp_scanned_stocks)} 隻標的！")
        for s in st.session_state.vcp_scanned_stocks:
            bg = "scan-card-super" if '🔥' in s['Tags'] else "scan-card-fire"
            st.markdown(f"<div class='{bg}'><div style='display:flex; justify-content:space-between;'><span style='font-size:1.5rem; font-weight:bold; color:white;'>[{s['Ticker']}] 趨勢: ✅ | RS Rating: <span style='color:#00FFCC;'>{s['RS Rating']}</span></span><span style='font-size:1.2rem; font-weight:bold; color:#FFD700;'>{s['Tags']}</span></div></div>", unsafe_allow_html=True)
        st.write("---")
        selected_stock = st.selectbox("🎯 選擇目標查看戰術圖表", [s['Ticker'] for s in st.session_state.vcp_scanned_stocks])
        if selected_stock:
            sel_data = next((item for item in st.session_state.vcp_scanned_stocks if item["Ticker"] == selected_stock), None)
            with st.spinner("繪製中..."):
                try:
                    df, _ = smart_fetch(selected_stock, period="6mo"); b_df, _ = smart_fetch(bench_sym, period="6mo"); b_df = b_df['Close']
                    df['MA50'] = df['Close'].rolling(50).mean(); df['Vol50'] = df['Volume'].rolling(50).mean(); df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
                    df_a, b_a = df['Close'].align(b_df, join='inner'); rs_line = (df_a / b_a).reindex(df.index).ffill().bfill() 
                    counts, bins = np.histogram(df['Close'], bins=25, weights=df['Volume']); stop_loss = ((bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2) * 0.985
                    df['TR'] = df[['High', 'Low', 'Close']].apply(lambda x: max(x['High']-x['Low'], abs(x['High']-df['Close'].shift(1).get(x.name, x['High'])), abs(x['Low']-df['Close'].shift(1).get(x.name, x['Low']))), axis=1)
                    df['ATR'] = df['TR'].rolling(14).mean(); atr_stop = df['Close'].iloc[-1] - (1.5 * df['ATR'].iloc[-1]) if not pd.isna(df['ATR'].iloc[-1]) else stop_loss
                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.03); dates = df.index.strftime('%Y-%m-%d')
                    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['MA50'], mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                    fig.add_hline(y=sel_data['Pivot'], line_dash="dash", line_color="#00FFCC", annotation_text=f"🎯 買入: ${sel_data['Pivot']:.2f}", annotation_font=dict(color="white"), row=1, col=1)
                    fig.add_hline(y=stop_loss, line_dash="solid", line_color="#FF4B4B", annotation_text=f"🛑 HVN止損: ${stop_loss:.2f}", annotation_font=dict(color="white"), row=1, col=1)
                    max_c = max(counts) if len(counts) > 0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136, 136, 136, 0.4)', name='重貨區', hoverinfo='skip', xaxis='x4', yaxis='y1'))
                    v_colors = ['#00FF00' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF0000' for i in range(len(df))]
                    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=rs_line, mode='lines', line=dict(color='#BC13FE', width=2), name="RS線"), row=3, col=1)
                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=850, xaxis_rangeslider_visible=False, xaxis4=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False))
                    st.plotly_chart(fig, use_container_width=True)
                except: st.error("繪圖出錯")

elif app_mode == "🌊 海龜回測加注雷達 (Mode E)":
    st.markdown("<h1 class='main-title'>🌊 海龜回測雷達</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1.5])
    with c1: asset_type = st.radio("1. 對象", ["🏢 個股", "🧺 ETF"])
    with c2: market_choice = st.radio("2. 市場", ["🇺🇸 美股", "🇭🇰 港股"])
    with c3: turtle_strat = st.radio("3. 戰術", ["🔥 極致真龍 (ATH 回測)", "🐉 潛龍初醒 (剛入強勢)"])
    target_dict = (US_ETF_MAP if "ETF" in asset_type else US_STOCK_MAP) if "美股" in market_choice else (HK_ETF_MAP if "ETF" in asset_type else HK_STOCK_MAP)
    s_choice = st.selectbox("4. 範圍", ["🌐 全星系大規模搜索"] + list(target_dict.keys()))

    if 'e_scanned_stocks' not in st.session_state: st.session_state.e_scanned_stocks = []

    if st.button("📡 發射真龍 N 字雷達！"):
        tickers = list(set([t for sub in target_dict.values() for t in sub])) if "全星系" in s_choice else target_dict[s_choice]
        found = []; pb = st.progress(0)
        with st.spinner("⏳ 慢速穩定掃描中..."):
            yearly_returns = {}; valid_dfs = {}
            for idx, t in enumerate(tickers):
                pb.progress((idx + 1) / len(tickers))
                if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                try:
                    df_t, _ = smart_fetch(t, period="1y")
                    if len(df_t) > 150:
                        yearly_returns[t] = (df_t['Close'].iloc[-1] / df_t['Close'].iloc[0]) - 1
                        valid_dfs[t] = df_t
                except: continue
            if yearly_returns:
                all_rets = pd.Series(list(yearly_returns.values()))
                for t, ret in yearly_returns.items():
                    df = valid_dfs[t]; curr_p = df['Close'].iloc[-1]; ath = df['High'].tail(252).max()
                    ma50 = df['Close'].rolling(50).mean().iloc[-1]; ma150 = df['Close'].rolling(150).mean().iloc[-1]; ma200 = df['Close'].rolling(200).mean().iloc[-1]; ema10 = df['Close'].ewm(span=10, adjust=False).mean().iloc[-1]
                    if not (curr_p > ma50 > ma150): continue
                    rs_rating = int((all_rets[all_rets <= ret].count() / len(all_rets)) * 99)
                    if turtle_strat == "🔥 極致真龍 (ATH 回測)":
                        if not (ma150 > ma200) or (curr_p / ath) < 0.90 or rs_rating < 80: continue
                    elif not (0.75 <= (curr_p / ath) <= 0.92) or rs_rating < 70: continue

                    last_20_high = df['High'].tail(20).max(); high_idx = df['High'].tail(20).argmax(); days_since_high = 19 - high_idx
                    if 2 <= days_since_high <= 15:
                        pullback_pct = ((curr_p - last_20_high) / last_20_high) * 100
                        if -15 <= pullback_pct <= -1 and ema10 * 0.98 <= curr_p <= ema10 * 1.04:
                            found.append({'Ticker': t, 'Price': curr_p, 'High': last_20_high, 'Low': df['Low'].iloc[-days_since_high:].min(), 'Pullback': pullback_pct, 'EMA10': ema10, 'Days': days_since_high})
            st.session_state.e_scanned_stocks = sorted(found, key=lambda x: x['Pullback'], reverse=True)

    if st.session_state.e_scanned_stocks:
        st.success(f"🎉 捕捉到 {len(st.session_state.e_scanned_stocks)} 隻回測目標！")
        for p in st.session_state.e_scanned_stocks:
            st.markdown(f"<div class='pullback-card'><span style='font-size:1.5rem; font-weight:bold; color:white;'>🎯 [{p['Ticker']}]</span> 現價: ${p['Price']:.2f} | 📉 回落: {p['Pullback']:.1f}% | 🎯 前高: ${p['High']:.2f} | 🛑 止損: ${p['Low']:.2f}</div>", unsafe_allow_html=True)
        sel = st.selectbox("🎯 查看戰術圖", [s['Ticker'] for s in st.session_state.e_scanned_stocks])
        if sel:
            p_data = next(x for x in st.session_state.e_scanned_stocks if x['Ticker'] == sel)
            with st.spinner("繪製中..."):
                try:
                    df, _ = smart_fetch(sel, period="6mo")
                    df['MA50'] = df['Close'].rolling(50).mean(); df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03); dates = df.index.strftime('%Y-%m-%d')
                    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['EMA10'], mode='lines', name='10 EMA', line=dict(color='orange', dash='dot')), row=1, col=1)
                    fig.add_hline(y=p_data['High'], line_dash="dash", line_color="#00FFCC", annotation_text=f"🐢 破頂: ${p_data['High']:.2f}", annotation_font=dict(color="white"), row=1, col=1)
                    fig.add_hline(y=p_data['Low'], line_dash="solid", line_color="#FF00FF", annotation_text=f"🛑 止損: ${p_data['Low']:.2f}", annotation_font=dict(color="white"), row=1, col=1)
                    counts, bins = np.histogram(df['Close'], bins=30, weights=df['Volume']); max_c = max(counts) if len(counts) > 0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(150,150,150,0.3)', name='重貨區', hoverinfo='skip', xaxis='x4', yaxis='y1'))
                    v_colors = ['#00FF00' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF0000' for i in range(len(df))]
                    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=650, xaxis_rangeslider_visible=False, xaxis4=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False))
                    st.plotly_chart(fig, use_container_width=True)
                except: st.error("繪圖出錯")
