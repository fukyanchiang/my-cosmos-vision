import streamlit as st 
import yfinance as yf 
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go 
from plotly.subplots import make_subplots 

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

HK_STOCK_MAP = {
    "1. 互聯網巨頭": "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0772.HK 0020.HK 0241.HK 0136.HK 1999.HK 2018.HK 3888.HK 2142.HK 1896.HK 0777.HK 0113.HK 0590.HK 1980.HK 1797.HK 6618.HK 2400.HK 0285.HK".split(),
    "2. 半導體與芯片": "0981.HK 1347.HK 0285.HK 1478.HK 1833.HK 0522.HK 0732.HK 2382.HK 2018.HK 0099.HK 1385.HK 1138.HK 1910.HK 6088.HK 3898.HK 6123.HK 3389.HK".split(),
    "3. 新能源車與整車": "1211.HK 2015.HK 9866.HK 9868.HK 0175.HK 2333.HK 1114.HK 0489.HK 3606.HK 0867.HK 1316.HK 1958.HK 1585.HK 0315.HK 1274.HK 2150.HK 1122.HK 3808.HK 9863.HK".split(),
    "4. 重型工業與機械": "1133.HK 1072.HK 1888.HK 1286.HK 3399.HK 1157.HK 2727.HK 1727.HK 6030.HK 0598.HK 0165.HK 0350.HK 1071.HK 1839.HK 1866.HK 0316.HK 0148.HK 1651.HK 1829.HK 1044.HK".split(),
    "5. 國有大行與金融": "0005.HK 0939.HK 1398.HK 3988.HK 2318.HK 2388.HK 0011.HK 3968.HK 3328.HK 0998.HK 0023.HK 2016.HK 1658.HK 6198.HK 0410.HK 6066.HK 1551.HK 1963.HK 1988.HK 3866.HK".split(),
    "6. 基礎化工與材料": "0148.HK 1651.HK 1378.HK 3360.HK 1963.HK 0860.HK 1282.HK 1387.HK 0386.HK 1812.HK 2128.HK 1126.HK 0268.HK 0338.HK 2009.HK 3389.HK 1008.HK 1898.HK 3993.HK 0868.HK".split(),
    "7. 石油氣與能源設備": "0883.HK 0857.HK 0386.HK 1193.HK 1083.HK 0003.HK 2688.HK 0392.HK 1035.HK 0135.HK 1600.HK 1250.HK 0855.HK 3330.HK 1138.HK 0164.HK 2883.HK 0135.HK".split(),
    "8. 煤炭與有色金屬": "1088.HK 1171.HK 1898.HK 2899.HK 0358.HK 3993.HK 0471.HK 1378.HK 3939.HK 0895.HK 0868.HK 1258.HK 1818.HK 3983.HK 2099.HK 1208.HK 1963.HK 2302.HK 0347.HK".split(),
    "9. 電力與綠能": "0902.HK 0836.HK 1816.HK 0916.HK 1798.HK 0958.HK 0006.HK 1071.HK 1250.HK 3800.HK 0002.HK 1193.HK 0819.HK 2380.HK 0735.HK 0384.HK 0066.HK 1038.HK".split(),
    "10. 房地產開發": "1109.HK 0688.HK 0960.HK 1918.HK 3383.HK 0884.HK 1233.HK 2777.HK 0813.HK 2007.HK 3301.HK 1638.HK 0012.HK 0016.HK 0017.HK 0101.HK 3900.HK 0817.HK 1966.HK".split(),
    "11. 物業管理服務": "6098.HK 1209.HK 2669.HK 3319.HK 1516.HK 1755.HK 1995.HK 2869.HK 9909.HK 0873.HK 9928.HK 6626.HK 9983.HK 9979.HK 2168.HK 2602.HK 3316.HK".split(),
    "12. 消費電子硬件": "2382.HK 2018.HK 0669.HK 0992.HK 1310.HK 0008.HK 1478.HK 0285.HK 0321.HK 0596.HK 0732.HK 0522.HK 1070.HK 0099.HK 0285.HK".split(),
    "13. 核心消費與餐飲": "0291.HK 2319.HK 0322.HK 1876.HK 9633.HK 6186.HK 0220.HK 1117.HK 0151.HK 1458.HK 1368.HK 6862.HK 9922.HK 2005.HK 0831.HK 0341.HK 1089.HK 6868.HK 1929.HK".split(),
    "14. 生物科技探索": "2269.HK 2359.HK 1801.HK 2162.HK 9966.HK 9969.HK 3759.HK 1548.HK 9926.HK 6990.HK 2126.HK 9939.HK 1099.HK 2171.HK 0512.HK 1952.HK 2096.HK".split(),
    "15. 傳統中西藥業": "1093.HK 1177.HK 1515.HK 0511.HK 2666.HK 3320.HK 2196.HK 0867.HK 1099.HK 0460.HK 0853.HK 1513.HK 3933.HK 1528.HK 1513.HK 2005.HK".split()
}

US_STOCK_MAP = {
    "1. 半導體設備與設計": "NVDA TSM AVGO ASML AMD QCOM TXN MU INTC AMAT LRCX KLAC ADI NXPI MRVL MCHP SWKS MPWR ON LSCC TER QRVO SLAB WOLF SYNA RMBS ALGM SITM ACLS CRUS".split(),
    "2. AI與大數據雲端": "MSFT GOOGL ORCL ADBE CRM PLTR SNOW PANW FTNT NOW WDAY ZS DDOG CRWD MDB NET OKTA TEAM SPLK GEN CYBR CHKP VRSN ESTC TENB SQSP PCOR DOCN AI FSLY MSTR".split(),
    "3. 基礎軟件與 SaaS": "INTU VMW CDNS PTC MSTR SPT ALTR MANH GWRE PAYC APPN TYL BLK PEGA BL DT DBX PATH BSY NCNO WK ME LAW ALIT VRM HCP RNG".split(),
    "4. 網絡安全 (Cyber)": "PANW CRWD FTNT ZS CYBR CHKP GEN TENB NET OKTA S OKTA VRNS QLYS SAIL MIME RPD PFPT FEYE EVBG IMPV".split(),
    "5. 消費電子與硬件": "AAPL HPQ DELL STX WDC APH TEL LOGI HPE NTAP GLW ST ANET FFIV GRMN LITE SMCI VRT JBL FLEX NVT ROK CSL HUBB CNHI GWW PH SANM PLXS".split(),
    "6. 通訊與網絡設備": "CSCO MSI JNPR ANET COMM ZBRA JNPR CIEN LITE VIAV ADTN CALX HLIT INFN NTGR ACIA EXTR CRDO FN CLFD".split(),
    "7. 互聯網平台內容": "META GOOGL PINS SNAP MATCH MTCH IAC OGI YELP BMBL BUMBLE GRND COMP ZIP TRUE CARG MTTR LEA GRPN".split()
}

HK_ETF_MAP = {"E1. 港股大盤與科指": "2800.HK 2828.HK 3032.HK 3033.HK 3067.HK 3147.HK 2812.HK 3058.HK 3068.HK 3428.HK 3134.HK 3115.HK 3046.HK".split()}
US_ETF_MAP = {"E1. 大盤/寬基/信用債": "SPY QQQ DIA IWM VOO IVV VTI RSP QQQM ONEQ VUG VTV IWD IWF TLT AGG BND LQD HYG IEF SHY MBB MUB JNK TIP IGOV EMB GOVT".split()}

# 🚀 爺爺防彈市寬計算引擎 (V114.0 完全破解 Yahoo MultiIndex 新格式)
@st.cache_data(ttl=3600)
def get_breadth_data(tickers):
    if not tickers: return {'20MA':0, '50MA':0, '150MA':0, '200MA':0, 'valid':1, 'above_50_list': []}
    try:
        data = yf.download(tickers, period="1y", threads=True, show_errors=False)
        closes = pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            if 'Close' in data.columns.get_level_values(0): closes = data['Close']
            elif 'Close' in data.columns.get_level_values(1): closes = data.xs('Close', level=1, axis=1)
        else:
            if 'Close' in data.columns: closes = pd.DataFrame({tickers[0]: data['Close']})
            else: closes = data
            
        stats = {'20MA':0, '50MA':0, '150MA':0, '200MA':0, 'valid':0, 'above_50_list': []}
        if isinstance(closes, pd.DataFrame) and not closes.empty:
            for t in tickers:
                if t in closes.columns:
                    c = closes[t].dropna()
                    if len(c) < 50: continue
                    curr = c.iloc[-1]
                    if curr > c.tail(20).mean(): stats['20MA'] += 1
                    if curr > c.tail(50).mean(): 
                        stats['50MA'] += 1
                        stats['above_50_list'].append(t)
                    if len(c) >= 150 and curr > c.tail(150).mean(): stats['150MA'] += 1
                    if len(c) >= 200 and curr > c.tail(200).mean(): stats['200MA'] += 1
                    stats['valid'] += 1
        stats['valid'] = max(1, stats['valid'])
        return stats
    except Exception as e: return {'20MA':0, '50MA':0, '150MA':0, '200MA':0, 'valid':1, 'above_50_list': []}

# 2. 視覺裝修 (🚀 爺爺強制消除灰色字 CSS)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    /* 強制側邊欄所有字體變純白 */
    div[data-testid="stSidebar"] * { color: white !important; }
    div[data-testid="stMetricValue"] > div { color: #FFFFFF !important; font-size: 3rem !important; font-weight: 900 !important; }
    div[data-testid="stMetricLabel"] > div { color: #00FFCC !important; font-size: 1.2rem !important; font-weight: bold !important; }
    .bear-warning p, .bear-warning span { color: #FF0000 !important; }
    
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
    .val-box-purple { border: 3px solid #BC13FE; border-radius: 15px; padding: 30px; background-color: #000; box-shadow: 0 0 25px #BC13FE66; margin: 25px 0; }
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700; font-weight: bold; font-size: 2.5rem; }
    .whale-a { color: #00FFCC; font-size: 1.6rem; text-align: right; }
    .scan-card-fire { border-left: 10px solid #FF4B4B; background-color: #310000; padding: 20px; margin-bottom: 15px; border-radius: 10px; box-shadow: 0 0 15px #FF4B4B66; }
    .bear-warning { color: #FF0000; font-size: 2.5rem; font-weight: 900; text-align: center; text-shadow: 2px 2px 5px #000; padding: 20px; border: 4px dashed red; background-color: #220000; margin: 20px 0; border-radius: 15px;}
    </style>
    """, unsafe_allow_html=True)

# 3. 側邊欄控制
st.sidebar.markdown("## 🛰️ 戰術控制台 (V114.0 終極白字版)")
app_mode = st.sidebar.radio("請選擇操作", [
    "🚀 個股深度透視", 
    "🛡️ 環球市底大師指揮塔", 
    "📡 個股版塊拔河熱力圖", 
    "📡 ETF 資產拔河熱力圖", 
    "🔍 千龍起步尋龍雷達 (個股)",
    "🛡️ 美股 ETF 專屬雷達",
    "🛡️ 港/A股 ETF 專屬雷達"
])

# 🚀 爺爺 9大開關掣：長駐側邊欄！完全跟足要求
if app_mode in ["🚀 個股深度透視", "🛡️ 環球市底大師指揮塔"]:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🛠️ 圖表顯示開關")
    st.sidebar.markdown("**📈 個股均線區**")
    show_s_ma20 = st.sidebar.checkbox("20日線 (短線動能)", value=False)
    show_s_ma50 = st.sidebar.checkbox("50日線 / 10周 (中期趨勢)", value=False)
    show_s_ma150 = st.sidebar.checkbox("150日線 / 30周 (大師分界)", value=False)
    show_s_ma200 = st.sidebar.checkbox("200日線 (終極牛熊)", value=False)

    st.sidebar.markdown("**🌊 市寬系統區 (虛線對比)**")
    show_b_idx = st.sidebar.checkbox("基準指數實線", value=True)
    show_b_ma20 = st.sidebar.checkbox("20市寬線", value=True)
    show_b_ma50 = st.sidebar.checkbox("50市寬線", value=True)
    show_b_ma150 = st.sidebar.checkbox("150市寬線", value=True)
    show_b_ma200 = st.sidebar.checkbox("200市寬線", value=True)

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
    
    HSI_82 = "0001.HK 0002.HK 0003.HK 0005.HK 0006.HK 0011.HK 0012.HK 0016.HK 0017.HK 0027.HK 0066.HK 0101.HK 0175.HK 0241.HK 0267.HK 0268.HK 0288.HK 0291.HK 0316.HK 0322.HK 0369.HK 0386.HK 0388.HK 0688.HK 0700.HK 0762.HK 0823.HK 0857.HK 0868.HK 0883.HK 0939.HK 0941.HK 0968.HK 0981.HK 0992.HK 1038.HK 1044.HK 1088.HK 1093.HK 1109.HK 1113.HK 1177.HK 1209.HK 1211.HK 1299.HK 1378.HK 1398.HK 1810.HK 1876.HK 1928.HK 1997.HK 2015.HK 2020.HK 2269.HK 2313.HK 2318.HK 2319.HK 2331.HK 2382.HK 2628.HK 2688.HK 2899.HK 3690.HK 3968.HK 3988.HK 6098.HK 6690.HK 9618.HK 9633.HK 9888.HK 9988.HK 9999.HK".split()
    TECH_30 = "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0241.HK 0020.HK 0772.HK 0981.HK 1347.HK 0285.HK 1478.HK 1833.HK 0522.HK 0732.HK 2382.HK 2018.HK 0099.HK 1385.HK 1138.HK 1910.HK 6088.HK 3898.HK 6123.HK 3389.HK 0136.HK 1999.HK 2142.HK".split()
    DOW_30 = "AAPL MSFT UNH JNJ XOM JPM V PG HD CVX MRK KO ABBV BAC AVGO PEP TMO COST CSCO MCD CRM DIS LIN ABT ACN AMD WFC NFLX INTC CAT".split()
    SPX_100 = DOW_30 + "AMZN GOOGL GOOG META TSLA NVDA LLY BRK-B V MA TSLA ADBE NFLX ORCL QCOM AMD INTU IBM AMAT TXN NOW UBER BA HON GE ISGN RTX LMT NOC DE CAT CMI MMM ETN PH ROK DOV URI PNR GWW NDSN AOS SWK SNA FLS LECO IEX GGG TTC NVT HUBB".split()
    NDX_100 = "AAPL MSFT AMZN NVDA META GOOGL GOOG TSLA AVGO ASML COST PEP CSCO TMUS ADBE TXN NFLX QCOM AMD INTU INTU VMW CDNS PTC MSTR SPT ALTR MANH GWRE PAYC APPN TYL BLK PEGA BL DT DBX PATH BSY NCNO WK ME LAW ALIT VRM HCP RNG".split()
    IWM_100 = "MSTR SMCI CELH WING APP ELF ANF MOD TMDX AXON FOUR INDI VRT ALKT ACLS ONTO POWI SOUN RXRX AI BBAI HIVE VLD IONQ BBAI CRDO NRDS INDI LUNA QBTS KTRA RGTI ARQQ INVZ".split()

    if "恒指" in idx_choice: ticker_sym = "2800.HK"; b_tickers = HSI_82 
    elif "科指" in idx_choice: ticker_sym = "3032.HK"; b_tickers = TECH_30
    elif "道指" in idx_choice: ticker_sym = "DIA"; b_tickers = DOW_30
    elif "標指" in idx_choice: ticker_sym = "SPY"; b_tickers = SPX_100
    elif "納市" in idx_choice: ticker_sym = "QQQ"; b_tickers = NDX_100
    else: ticker_sym = "IWM"; b_tickers = IWM_100

    with st.spinner(f"⏳ 大宗師正在計算市寬數據... 請稍候 ☕🚀"):
        try:
            idx_df = yf.Ticker(ticker_sym).history(period="2y").dropna(subset=['Close', 'Volume'])
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
                
                st.markdown(f"<h3 style='color: white;'>🌊 {idx_choice} - 內部成份股市寬健康度</h3>", unsafe_allow_html=True)
                st.markdown(f"<div style='color: white; font-size:1.1rem; margin-bottom:15px;'>（系統真實成功掃描：<b style='color:#00FFCC;'>{v_count}</b> 隻核心成份股）</div>", unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='display: flex; justify-content: space-between; text-align: center; background-color: #111; padding: 20px; border-radius: 15px;'>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>20市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['20MA']/v_count)*100:.1f}%</span></div>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>50市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['50MA']/v_count)*100:.1f}%</span></div>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>150市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['150MA']/v_count)*100:.1f}%</span></div>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>200市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['200MA']/v_count)*100:.1f}%</span></div>
                </div>
                """, unsafe_allow_html=True)

                st.write("")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                
                o_col = clean_recent['Open'].values; c_col = clean_recent['Close'].values
                h_col = clean_recent['High'].values; l_col = clean_recent['Low'].values
                v_col = clean_recent['Volume'].values

                if show_b_idx: fig.add_trace(go.Candlestick(x=dates, open=o_col, high=h_col, low=l_col, close=c_col, name=f'{ticker_sym} 基準指數'), row=1, col=1)
                else: fig.add_trace(go.Scatter(x=dates, y=c_col, mode='lines', name='隱藏基準', line=dict(color='rgba(255,255,255,0)')), row=1, col=1)

                if show_b_ma20: fig.add_trace(go.Scatter(x=dates, y=clean_recent['20MA'], mode='lines', name='20市寬線', line=dict(color='white', width=1.5, dash='dot')), row=1, col=1)
                if show_b_ma50: fig.add_trace(go.Scatter(x=dates, y=clean_recent['50MA'], mode='lines', name='50市寬線', line=dict(color='yellow', width=1.5, dash='dot')), row=1, col=1)
                if show_b_ma150: 
                    fig.add_trace(go.Scatter(x=dates, y=clean_recent['150MA'], mode='lines', name='150市寬線', line=dict(color='cyan', width=2, dash='dot')), row=1, col=1)
                    if len(clean_recent) > 10 and clean_recent['150MA'].iloc[-1] < clean_recent['150MA'].iloc[-10]:
                        fig.add_annotation(x=dates[-1], y=clean_recent['150MA'].iloc[-1], ax=0, ay=-40, xref="x", yref="y", showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=3, arrowcolor="red", text="⬇")
                if show_b_ma200: 
                    fig.add_trace(go.Scatter(x=dates, y=clean_recent['200MA'], mode='lines', name='200市寬線', line=dict(color='magenta', width=2, dash='dot')), row=1, col=1)
                    if len(clean_recent) > 10 and clean_recent['200MA'].iloc[-1] < clean_recent['200MA'].iloc[-10]:
                        fig.add_annotation(x=dates[-1], y=clean_recent['200MA'].iloc[-1], ax=0, ay=-40, xref="x", yref="y", showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=3, arrowcolor="red", text="⬇")

                colors = ['#00FF00' if c_col[i] >= o_col[i] else '#FF0000' for i in range(len(clean_recent))]
                fig.add_trace(go.Bar(x=dates, y=v_col, marker_color=colors, name='成交量'), row=2, col=1)
                counts, bins = np.histogram(c_col, bins=20, weights=v_col)
                max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name='蟹貨區', xaxis='x3', yaxis='y1'))

                fig.update_layout(
                    template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, 
                    showlegend=True, legend=dict(font=dict(color="white"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), 
                    yaxis=dict(showgrid=True, gridcolor='#333'), xaxis3=dict(overlaying='x', side='top', range=[0, max_c*1.1], showgrid=False, showticklabels=False)
                )
                st.plotly_chart(fig, use_container_width=True, theme=None, config={'scrollZoom': True, 'displayModeBar': False})

                if ("科指" in idx_choice or "道指" in idx_choice) and b_stats['above_50_list']:
                    st.markdown(f"<h3 style='color: white;'>🏆 逆市名單 ({idx_choice}) - 企穩 50天線之上</h3>", unsafe_allow_html=True)
                    cols = st.columns(6)
                    for i, t in enumerate(b_stats['above_50_list'][:30]):
                        cols[i % 6].info(t)
        except Exception as e: st.error(f"⚠️ 數據載入失敗：{e}")


# =========================================================================
# 🚀 模式 A：個股深度透視 
# =========================================================================
elif app_mode == "🚀 個股深度透視":
    ticker = st.sidebar.text_input("🚀 輸入資產代號", "6869.HK").upper()
    with st.spinner(f"⏳ 系統正在切換引擎，重新為您下載海量數據及繪製摩訶圖... 請稍候 ☕🚀"):
        try:
            asset = yf.Ticker(ticker); info = asset.info
            df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
            spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
            
            b_sym_plot = "^HSI" if ".HK" in ticker else "SPY"
            b_df_plot = yf.Ticker(b_sym_plot).history(period="2y").dropna()
            if not b_df_plot.empty:
                b_df_plot['20MA'] = b_df_plot['Close'].rolling(20).mean().bfill()
                b_df_plot['50MA'] = b_df_plot['Close'].rolling(50).mean().bfill()
                b_df_plot['150MA'] = b_df_plot['Close'].rolling(150).mean().bfill()
                b_df_plot['200MA'] = b_df_plot['Close'].rolling(200).mean().bfill()

            if not df.empty:
                if df.index.tz is not None: df.index = df.index.tz_localize(None)
                df.index = df.index.normalize()
                if spy.index.tz is not None: spy.index = spy.index.tz_localize(None)
                spy.index = spy.index.normalize()
                curr_p = df['Close'].iloc[-1]
                
                c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
                slope, intercept = np.polyfit(days, c_tail, 1); pred = intercept + slope * len(days)
                mom = (curr_p / pred) if pred > 0 else 1.0; v_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
                cx_val = safe_n(((slope * 252) / c_tail.mean() / v_ann) * 29 * mom, 50.0)

                spy_aligned = spy['Close'].reindex(df.index).ffill().bfill() 
                crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy_aligned.iloc[-1] / spy_aligned.iloc[-63])) * 100, 50.0) if len(df) > 63 else 50.0
                v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean(); cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
                se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0) if len(df) > 5 else 50.0

                def get_trend_stats(metric):
                    try:
                        if len(df) < 25: return "N/A", "#888"
                        if metric == "RS":
                            past_p = df['Close'].iloc[-20]; past_spy = spy_aligned.iloc[-20]
                            past_bench = df['Close'].iloc[-83] if len(df) > 83 else df['Close'].iloc[0]
                            past_bench_spy = spy_aligned.iloc[-83] if len(spy_aligned) > 83 else spy_aligned.iloc[0]
                            past = 50 + ((past_p / past_bench) - (past_spy / past_bench_spy)) * 100
                            diff = crs_val - past
                        elif metric == "EJ":
                            v_past_21 = df['Volume'].iloc[-41:-20].mean()
                            v_past_252 = df['Volume'].iloc[-273:-20].mean() if len(df) > 280 else df['Volume'].iloc[:-20].mean()
                            past = (v_past_21 / max(v_past_252, 1)) * 100
                            diff = cej_s - past
                        else: past = 50 + (((df['Close'].iloc[-20] / df['Close'].iloc[-25]) - 1) * 1200); diff = se_s - past
                        color = "#00FF00" if diff >= 0 else "#FF4B4B"
                        return f"{'+' if diff>=0 else ''}{diff:.1f}%", color
                    except: return "N/A", "#888"

                def get_pulse_fig(pulse_vals):
                    try:
                        colors = ['#00FFCC' if v >= 0 else '#FF4B4B' for v in pulse_vals]
                        fig = go.Figure(go.Bar(x=list(range(len(pulse_vals))), y=pulse_vals, marker_color=colors, hoverinfo='skip'))
                        fig.update_layout(height=130, margin=dict(l=0,r=0,t=5,b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False, fixedrange=True), yaxis=dict(visible=False, fixedrange=True), showlegend=False)
                        return fig
                    except: return go.Figure().update_layout(height=130, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False))

                asset_name = info.get('shortName', info.get('longName', ''))
                name_html = f"<span style='font-size: 1.8rem; color: #AAAAAA; font-weight: 500; margin-left: 15px;'>{asset_name}</span>" if asset_name else ""
                
                st.markdown(f"""<div class='main-title' style='margin-bottom:10px;'>環球資產透維評估儀 [{ticker}]{name_html}</div>""", unsafe_allow_html=True)
                st.markdown(f"""<div style='text-align: center; color: #00FFCC; font-size: 1.2rem; font-weight: bold; margin-bottom: 25px; padding: 10px; background-color: rgba(0, 255, 204, 0.1); border-radius: 8px; border: 1px dashed #00FFCC;'>🛡️ 必勝潛伏方程式：COSMOS-RS (星系強弱) > 52, EJ 錢流底氣 > 85, 短期能量 > 75, 最近 20 日主力資金池淨額是正數買入，OBV 大戶籌碼流入或觀望，資金部署集中度是分散</div>""", unsafe_allow_html=True)
                
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

                try:
                    mf_df = df.tail(41).copy(); mf_df['Typical_Price'] = (mf_df['High'] + mf_df['Low'] + mf_df['Close']) / 3
                    mf_df['Net_Flow'] = mf_df['Typical_Price'] * mf_df['Volume'] * np.where(mf_df['Close'] > mf_df['Close'].shift(1).fillna(mf_df['Close']), 1, -1)
                    mf_df['OBV_Daily'] = (np.sign(mf_df['Close'].diff()) * mf_df['Volume']).fillna(0); mf_df['OBV'] = mf_df['OBV_Daily'].cumsum()
                    curr_20d_flow = mf_df['Net_Flow'].tail(20).sum(); prev_20d_flow = mf_df['Net_Flow'].iloc[-40:-20].sum()
                    if abs(curr_20d_flow) >= 1e8: flow_str = f"{'+' if curr_20d_flow>0 else ''}${curr_20d_flow/1e8:.1f} 億"
                    elif abs(curr_20d_flow) >= 1e6: flow_str = f"{'+' if curr_20d_flow>0 else ''}${curr_20d_flow/1e6:.1f} M (百萬)"
                    else: flow_str = f"{'+' if curr_20d_flow>0 else ''}${curr_20d_flow:,.0f}"
                    flow_color = "#00FF00" if curr_20d_flow > 0 else "#FF4B4B"
                    mf_pct = (curr_20d_flow - prev_20d_flow) / abs(prev_20d_flow) * 100 if prev_20d_flow != 0 else 0
                    obv_curr_val = mf_df['OBV'].iloc[-1] - mf_df['OBV'].iloc[-21]; obv_prev_val = mf_df['OBV'].iloc[-21] - mf_df['OBV'].iloc[-41] if len(mf_df) > 40 else 1
                    price_trend = mf_df['Close'].iloc[-1] - mf_df['Close'].iloc[-21]; obv_pct = (obv_curr_val - obv_prev_val) / abs(obv_prev_val) * 100 if obv_prev_val != 0 else 0
                    obv_total_vol = mf_df['Volume'].tail(20).sum() or 1
                    if abs(obv_curr_val) / obv_total_vol < 0.02: trend_str, trend_color, obv_state = "9. 🧊 資金膠著盤整 (觀望)", "#888888", 9
                    else:
                        if price_trend >= 0:
                            if obv_curr_val > 0: 
                                if obv_pct > 20: trend_str, trend_color, obv_state = "1. 👑 強烈流入", "#00FF00", 1
                                else: trend_str, trend_color, obv_state = "2. 📈 流入", "#00FF00", 2
                            else:
                                if obv_pct < -20: trend_str, trend_color, obv_state = "5. 💣 資金高位撤離 (量價強烈背離 - 大兇兆)", "#FF4B4B", 5
                                else: trend_str, trend_color, obv_state = "6. ⚠️ 資金高位撤離 (量價背離 - 兇兆)", "#FF4B4B", 6
                        else:
                            if obv_curr_val < 0:
                                if obv_pct < -20: trend_str, trend_color, obv_state = "3. 💀 大戶持續派發 (強烈流出)", "#FF4B4B", 3
                                else: trend_str, trend_color, obv_state = "4. 📉 大戶持續派發 (流出)", "#FF4B4B", 4
                            else:
                                if obv_pct > 20: trend_str, trend_color, obv_state = "7. 🐉 底部分歧掃貨 (量價強烈背離 - 大吉兆)", "#00FFCC", 7
                                else: trend_str, trend_color, obv_state = "8. 🐲 底部分歧掃貨 (量價背離 - 吉兆)", "#00FFCC", 8
                    daily_abs_flow = abs(mf_df['Net_Flow'].tail(20)); total_abs_flow = daily_abs_flow.sum() or 1; conc_pct = (daily_abs_flow.max() / total_abs_flow) * 100
                    if conc_pct > 35: conc_level, conc_color, conc_note = "⚡ 高度集中", "#FF4B4B", "（高度集中 / 突發一棍買入，可能是想令散戶跟風）" if curr_20d_flow > 0 else "（高度集中 / 突發一棍掟貨，可能引發恐慌）"
                    elif conc_pct > 15: conc_level, conc_color, conc_note = "🌿 正常分佈", "#FFD700", "（沒有特別想偷偷買，就是公開正常買入）" if curr_20d_flow > 0 else "（公開正常沽出）"
                    else: conc_level, conc_color, conc_note = "💎 穩定分散", "#00FFCC", "（不想被人知道偷偷買入）" if curr_20d_flow > 0 else "（不想被人知道偷偷派發）"
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
                                    if len(align_b)>10 and align_b['150MA'].iloc[-1] < align_b['150MA'].iloc[-10]:
                                        fig.add_annotation(x=dates[-1], y=align_b['150MA'].iloc[-1]*norm, ax=0, ay=-40, xref="x", yref="y", showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=3, arrowcolor="red", text="⬇")
                                if show_b_ma200:
                                    fig.add_trace(go.Scatter(x=dates, y=align_b['200MA']*norm, mode='lines', name='200市寬線', line=dict(color='rgba(255,0,255,0.6)', width=1.5, dash='dot')), row=1, col=1)
                                    if len(align_b)>10 and align_b['200MA'].iloc[-1] < align_b['200MA'].iloc[-10]:
                                        fig.add_annotation(x=dates[-1], y=align_b['200MA'].iloc[-1]*norm, ax=0, ay=-40, xref="x", yref="y", showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=3, arrowcolor="red", text="⬇")

                        colors = ['#00FF00' if c_col[i] >= o_col[i] else '#FF0000' for i in range(len(recent))]
                        fig.add_trace(go.Bar(x=dates, y=v_col, marker_color=colors, name='成交量'), row=2, col=1)
                        counts, bins = np.histogram(c_col, bins=20, weights=v_col)
                        max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name='蟹貨區', xaxis='x3', yaxis='y1'))
                        
                        fig.update_layout(
                            template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, 
                            showlegend=True, legend=dict(font=dict(color="white"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), 
                            xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), 
                            yaxis=dict(showgrid=True, gridcolor='#333'), xaxis3=dict(overlaying='x', side='top', range=[0, max_c*1.1], showgrid=False, showticklabels=False)
                        )
                        st.plotly_chart(fig, use_container_width=True, theme=None, config={'scrollZoom': True, 'displayModeBar': False})
                except Exception as e: pass

                st.write("---"); d_c1, d_c2 = st.columns([1, 2.5]); is_etf = info.get('quoteType') == 'ETF'; real_roe = info.get('returnOnEquity')
                if is_etf or real_roe is None or real_roe == 0:
                    dna_v = round(safe_n((cx_val * 0.5) + (crs_val * 0.5), 50.0), 1); dna_title = "ETF 綜合質量基因"
                    m8 = {"🩸 資金純度 (流動)": int(safe_n(cej_s / 10, 5)), "🛡️ 免疫系統 (抗跌)": int(safe_n(crs_val / 10, 5)), "🏗️ 心跳頻率 (動能)": int(safe_n(cx_val / 10, 5)), "🧬 大腦潛力 (趨勢)": int(safe_n(se_s / 10, 5)), "🧱 骨架重量 (規模)": 9 if info.get('totalAssets', 0) > 1e9 else 5, "⚡ 物理底盤 (波幅)": int(max(1, 10 - (v_ann * 20))), "💰 資本配置 (派息)": int(safe_n(info.get('yield', info.get('dividendYield', 0))*200+2, 5)), "📈 經營拐點 (相對)": int(safe_n(crs_val / 10, 5))}
                else:
                    dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1); dna_title = "投行級股王基因"
                    m8 = {"🩸 血液純度": int(safe_n(info.get('operatingMargins', 0)*30+3, 5)), "🛡️ 免疫系統": int(safe_n(real_roe*30+3, 7)), "🏗️ 心跳頻率": int(safe_n(info.get('revenueGrowth', 0)*20+4, 6)), "🧬 大腦潛力": int(safe_n(info.get('profitMargins', 0)*30+3, 8)), "🧱 骨架重量": int(max(1, 10 - safe_n(info.get('priceToBook', 5), 5))), "⚡ 物理底盤": 8 if safe_n(info.get('debtToEquity', 150), 150) < 80 else 3, "💰 資本配置": int(safe_n(info.get('dividendYield', 0)*200+2, 5)), "📈 經營拐點": int(safe_n(info.get('earningsGrowth', 0)*25+4, 8))}
                dna_v = max(0.0, min(100.0, dna_v)); d_lv = "第 1 級" if dna_v>=90 else ("第 2 級" if dna_v>=80 else ("第 3 級" if dna_v>=70 else "後續"))
                with d_c1: st.markdown(f"<div class='cosmos-box' style='border-color:#FF4B4B; height:380px; display:flex; flex-direction:column; justify-content:center;'><div style='color:#FF4B4B; font-weight:900; font-size:1.8rem;'>🧬 COSMOS-DNA</div><div style='font-size:0.9rem; opacity:0.7; margin:5px 0;'>{dna_title}</div><div style='font-size:6rem; font-weight:900;'>{dna_v}</div><div style='color:#FFD700;'>[ 現屬 {d_lv} ]</div></div>", unsafe_allow_html=True)
                with d_c2:
                    colors_8d = ["#00FFCC", "#00FFCC", "#00FFCC", "#00FFCC", "#FF4B4B", "#BC13FE", "#FFFFFF", "#FFD700"]
                    for i, (l, s) in enumerate(m8.items()):
                        sc = max(1, min(10, s)); grid = '<div class="energy-bar-container-8d">' + "".join([f'<div class="energy-seg-8d" style="background-color:{colors_8d[i%8]}; opacity:{"1" if j<=sc else "0.1"};"></div>' for j in range(1,11)]) + '</div>'
                        st.markdown(f"<div style='display:flex; justify-content:space-between; font-weight:bold;'><span>{l}</span><span>{sc}/10</span></div>{grid}", unsafe_allow_html=True)
                st.markdown(f"<div class='red-bar'>🔥 戰略透視：短期動能爆發數值 [{se_s:.1f}%] 🔥</div>", unsafe_allow_html=True)
                v1,v2,v3 = st.columns(3); v4,v5,v6 = st.columns(3)
                def v_card(col, t, t_v, f_v, d): col.markdown(f"<div class='val-box'><div class='val-label'>{t}</div><div class='val-text'>TTM: <span class='val-focus'>{t_v}</span></div><div class='val-text'>預期: <span class='val-focus'>{f_v}</span></div><div style='color:#FFA500; font-size:0.9rem;'>{d}</div></div>", unsafe_allow_html=True)
                v_card(v1, "PE 獲利比", safe_s(info, ['trailingPE'], "x"), safe_s(info, ['forwardPE'], "x"), "獲利估值")
                v_card(v2, "PEG 增長比", safe_s(info, ['pegRatio']), "N/A", "增長性價比")
                v_card(v3, "PS 營收比", safe_s(info, ['priceToSalesTrailing12Months'], "x"), "N/A", "營收規模")
                v_card(v4, "PB 淨資產", safe_s(info, ['priceToBook'], "x"), "N/A", "賬面價值")
                v_card(v5, "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], "x"), "N/A", "企業估值")
                v_card(v6, "股息率", safe_s(info, ['dividendYield', 'yield'], "%"), "N/A", "回報率")

                ttm_pe = info.get('trailingPE', 0) or 0
                fwd_pe = info.get('forwardPE', 0) or 0
                if not is_etf:
                    dragon_index = round((dna_v * 0.4) + (cx_val * 0.3) + (crs_val * 0.3), 1)
                    dragon_index = max(5.0, min(98.5, dragon_index)) 
                    
                    if dragon_index >= 80:
                        t_lv, t_desc, val_title, val_color = "第 1 級", "極致真龍", "🔥 烈火鳳凰", "#BC13FE"
                        act_desc = "【順勢而為】真實財報極度健康，估值雖貴但有強大動能支撐，緊貼趨勢操作。"
                    elif dragon_index >= 65:
                        t_lv, t_desc, val_title, val_color = "第 2 級", "潛力金龍", "🌟 潛龍伏躍", "#00FFCC"
                        act_desc = "【價值防守】財報穩健，動能醞釀中，適合分批建倉或持有觀望。"
                    elif dragon_index >= 40:
                        t_lv, t_desc, val_title, val_color = "第 3 級", "中庸凡骨", "⚠️ 海市蜃樓", "#FFA500"
                        act_desc = "【謹慎觀望】動能與財報表現平平，估值偏高，注意回調風險。"
                    else:
                        t_lv, t_desc, val_title, val_color = "第 4 級", "高危泥鰍", "☠️ 末路狂花", "#FF4B4B"
                        act_desc = "【規避風險】財報轉弱且動能破位，估值存在泡沫，建議嚴格止損。"
                    
                    warning_html = ""
                    if ttm_pe > 80 or fwd_pe > 80:
                        warning_html = "<span style='color:#FF0000; font-size:3.5rem; font-weight:900; margin-left:20px; text-shadow: 2px 2px 4px #000;'>警告</span>"

                    st.markdown(f"""
<div style='border: 4px solid {val_color}; border-radius: 15px; padding: 30px; background-color: #000; box-shadow: 0 0 30px {val_color}66; margin: 25px 0;'>
    <div style='display:flex; justify-content:space-between; align-items:center;'>
        <div>
            <span style='font-size:2.2rem; font-weight:900;'>COSMOS-VAL 解碼：<span style='color:{val_color};'>{val_title}</span>{warning_html}</span><br>
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

                st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center;'>🧙 90 大名家：真實申報持倉</div>", unsafe_allow_html=True)
                total_shares = info.get('sharesOutstanding', 1); holders = asset.institutional_holders
                if holders is not None and not holders.empty and 'Holder' in holders.columns:
                    for _, row in holders.head(8).iterrows():
                        shares = row.get('Shares', 0); calc_pct = (shares/total_shares); val_m = row.get('Value', 0)/1e6
                        st.markdown(f"<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>持有 {shares:,.0f} 股 | 佔比 {calc_pct:.2%} | 市值 ${val_m:.1f}M</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        except: pass

# =========================================================================
# 🔍 模式 C：起步尋龍雷達 (必勝潛龍羅輯 V87.0 撒網版)
# =========================================================================
elif "雷達" in app_mode and not "熱力圖" in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    
    if app_mode == "🔍 千龍起步尋龍雷達 (個股)":
        m_choice = st.sidebar.radio("1. 選擇個股市場", ["🇺🇸 美股市場", "🇭🇰 港股市場"])
        is_us = "美股" in m_choice
    else:
        is_us = "美股" in app_mode
        
    bench_sym = "SPY" if is_us else "^HSI"
    target_dict = (US_ETF_MAP if "ETF" in app_mode else US_STOCK_MAP) if is_us else (HK_ETF_MAP if "ETF" in app_mode else HK_STOCK_MAP)
    
    s_choice = st.sidebar.selectbox("2. 選擇掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()))
    
    if st.sidebar.button("📡 發射撒網尋龍電波！"):
        bench_data = yf.Ticker(bench_sym).history(period="2y").dropna()
        tickers_to_scan = list(set([t for sub in target_dict.values() for t in sub])) if "全星系" in s_choice else target_dict[s_choice]
        
        found = False; pb = st.progress(0)
        for idx, t in enumerate(tickers_to_scan):
            pb.progress((idx + 1) / len(tickers_to_scan))
            try:
                d = yf.Ticker(t).history(period="63d").dropna()
                if len(d) > 40:
                    tp = (d['High']+d['Low']+d['Close'])/3; nf = tp*d['Volume']*np.where(d['Close']>d['Close'].shift(1).fillna(d['Close']),1,-1)
                    net_flow_20 = nf.tail(20).sum(); conc_20 = (abs(nf.tail(20)).max()/abs(nf.tail(20)).sum())*100
                    obv = (np.sign(d['Close'].diff())*d['Volume']).fillna(0).cumsum()
                    obv_curr = obv.iloc[-1]-obv.iloc[-21]; obv_prev = obv.iloc[-21]-obv.iloc[-41]
                    obv_pct = (obv_curr-obv_prev)/abs(obv_prev)*100 if obv_prev!=0 else 0
                    p_trend = d['Close'].iloc[-1]-d['Close'].iloc[-21]; state = 9
                    if p_trend>=0: state = 1 if obv_pct>20 else 2
                    else: state = 7 if obv_pct>20 else 8
                    
                    curr_p = d['Close'].iloc[-1]; crs = 50+((curr_p/d['Close'].iloc[-63])-(bench_data['Close'].iloc[-1]/bench_data['Close'].iloc[-63]))*100 if len(d)>60 else 50
                    ej = (d['Volume'].tail(21).mean()/max(d['Volume'].tail(252).mean() if len(d)>200 else d['Volume'].mean(),1))*100
                    se = 50+(((curr_p/d['Close'].iloc[-5])-1)*1200)

                    if net_flow_20 > 0 and conc_20 < 50 and state in [1, 2, 7, 8, 9]:
                        if se > 75 and ej > 85 and crs > 52:
                            found = True
                            st.markdown(f"<div class='scan-card-fire'><h2>🎯 {t} | 符合大戶佈局！</h2><p>💰 資金流: {net_flow_20/1e8:.1f}億 | 🎯 集中度: {conc_20:.1f}% | 🌊 OBV: {state}<br>⚡ SE: {se:.1f} | 🔋 EJ: {ej:.1f} | 📈 RS: {crs:.1f}</p></div>", unsafe_allow_html=True)
            except: pass
        if not found: st.warning("💤 雷達掃描完畢，目前未有起飛目標。(此過濾條件為潛龍必勝模式，要求大戶真實佈局)")

# =========================================================================
# 📡 拔河熱力圖 
# =========================================================================
elif "熱力圖" in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    m_view = st.sidebar.radio("選擇星系", ["🇺🇸 美股陣列", "🇭🇰 港股陣列"])
    is_us = "美股" in m_view; bench_sym = "SPY" if is_us else "^HSI"
    target_map = (US_ETF_MAP if "ETF" in app_mode else US_STOCK_MAP) if is_us else (HK_ETF_MAP if "ETF" in app_mode else HK_STOCK_MAP)
    with st.spinner('拔河排名計算中...'):
        try:
            bench_df = yf.Ticker(bench_sym).history(period="60d")['Close'].dropna(); results = []
            for name, tickers in target_map.items():
                for t in tickers:
                    try:
                        d = yf.Ticker(t).history(period="60d")['Close'].dropna()
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
