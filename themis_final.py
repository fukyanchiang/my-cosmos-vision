import streamlit as st 
import yfinance as yf 
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go 
from plotly.subplots import make_subplots 
import time

# 1. 基礎設置
st.set_page_config(page_title="環球資產透維評估儀 V188.0", layout="wide") 

# 🎨 爺爺精準 CSS
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
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; min-height: 220px; margin-bottom: 15px; }
    .val-label { color: #FFFFFF !important; font-size: 1.6rem; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 12px; }
    .val-focus { color: #FFD700 !important; font-weight: bold; font-size: 1.8rem; }
    .val-box-purple { border: 3px solid #BC13FE; border-radius: 15px; padding: 30px; background-color: #000; box-shadow: 0 0 25px #BC13FE66; margin: 25px 0; }
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700 !important; font-weight: bold; font-size: 2.5rem; }
    .whale-a { color: #00FFCC !important; font-size: 1.6rem; text-align: right; }
    .scan-card-fire { border-left: 5px solid #00FFCC; background-color: #111; padding: 15px; margin-bottom: 10px; border-radius: 8px; }
    .pullback-card { border-left: 8px solid #BC13FE; background-color: #1a0024; padding: 15px; margin-bottom: 10px; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# ----------------- 🛡️ 核心引擎 -----------------
@st.cache_data(ttl=3600)
def smart_fetch(ticker_sym, period="2y"):
    try:
        time.sleep(0.3) 
        # FIX 3: 加入 auto_adjust=True 防止除淨斷層，確保抓取最真實升跌
        data = yf.Ticker(ticker_sym).history(period=period, auto_adjust=True)
        return data.dropna(subset=['Close', 'Volume'])
    except: return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_all_data(ticker_sym):
    try:
        time.sleep(0.3)
        asset = yf.Ticker(ticker_sym)
        return asset.info, asset.institutional_holders
    except: return {}, None

def get_tri_sword_logic(df):
    """實裝三劍客：NETMA + 王者能量 + 升跌幅"""
    d = df.copy()
    # 1. TRADEFORCEDELTAME 
    # FIX 4: 零波幅保險，就算一字板都不會燒機
    denom = (d['High'] - d['Low']).replace(0, 0.001)
    d['BuyVol'] = d['Volume'] * (d['Close'] - d['Low']) / denom
    d['SellVol'] = d['Volume'] * (d['High'] - d['Close']) / denom
    d['NetVol'] = d['BuyVol'] - d['SellVol']
    # FIX 2: IPO 保險絲 (min_periods=1)
    d['NETMA'] = d['NetVol'].rolling(10, min_periods=1).mean()
    
    # 2. TRADEFORCE02TURNVIX
    v_ma20 = d['Volume'].rolling(20, min_periods=1).mean()
    v_std20 = d['Volume'].rolling(20, min_periods=1).std().fillna(0)
    v_upper = v_ma20 + (2.0 * v_std20)
    v_ma60 = d['Volume'].rolling(60, min_periods=1).mean()
    d['ROC'] = d['Close'].pct_change() * 100
    d['Cyan'] = (d['Volume'] > v_upper) & (d['Volume'] > v_ma60 * 1.9) & (d['ROC'].abs() > 2.0) & (d['Close'] > d['Open'])
    d['Magenta'] = (d['Volume'] > v_upper) & (d['Volume'] > v_ma60 * 1.9) & (d['ROC'].abs() > 2.0) & (d['Close'] <= d['Open'])
    return d

def safe_n(val, alt=50.0): 
    try: v = float(val); return v if not np.isnan(v) and not np.isinf(v) else alt 
    except: return alt 

# ----------------- 🛸 星系圖 -----------------
HK_STOCK_MAP = {"1. 互聯網巨頭": "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0772.HK 2400.HK".split(), "2. 半導體與芯片": "0981.HK 1347.HK 0285.HK 1478.HK 1833.HK".split(), "5. 國有大行與金融": "0005.HK 0939.HK 1398.HK 3988.HK 2318.HK 2388.HK".split()}
US_STOCK_MAP = {"1. 半導體設備與設計": "NVDA TSM AVGO ASML AMD QCOM TXN MU INTC AMAT LRCX KLAC ADI".split(), "2. AI與大數據雲端": "MSFT GOOGL ORCL ADBE CRM PLTR SNOW PANW FTNT NOW WDAY ZS DDOG CRWD MDB NET".split()}
HK_ETF_MAP = {"H1. A股門戶/大盤": "2822.HK 3188.HK 3109.HK 2823.HK 2800.HK".split(), "H2. 港股科技/AI": "3033.HK 3088.HK 3067.HK 3032.HK".split(), "H5. 虛擬資產": "3066.HK 3068.HK 3439.HK 3419.HK 3460.HK 3461.HK 3471.HK 3472.HK".split()}
US_ETF_MAP = {"U1. Thematic 主題 A": "BWET OIH LIT GSG XTL PDBC DBC SOXX FCG SLX IXC REMX ROKT FENY VDE AIS SMH XOP IYE XLE AIRR UFO XBI IDGT TAN DTCR ICLN XME KRE GRID IFRA PAVE".split(), "U4. SPDR 核心板塊": "XLE XBI XLI XLK XLB XLP XLU XLRE XLC XLY XLV XLF".split(), "U5. 全球國家/地區": "EWY EWZ ILF EIS EWT TUR ECH EFNL EWC EWP EWH EWI EPOL EPU EWW THD VNM EWM EWA EWJ EWN EWS EWQ EZA EWU EWL SPY KSA EWD EWG UAE QAT EPHE FXI EIDO INDA".split()}

# ----------------- 🔘 控制台 -----------------
st.sidebar.markdown("## 🛰️ 戰術控制台 (V188.0)")
app_mode = st.sidebar.radio("請選擇操作", ["🚀 個股深度透視", "🛡️ 環球市底大師指揮塔", "📡 個股版塊拔河熱力圖", "📡 ETF 資產拔河熱力圖", "🔍 千龍起步尋龍雷達 (個股)", "📈 VCP 形態戰術掃描 & 防守圖", "🌊 海龜回測加注雷達 (Mode E)"])

# =========================================================================
# 🚀 模式 A：個股深度透視 
# =========================================================================
if app_mode == "🚀 個股深度透視":
    ticker = st.sidebar.text_input("🚀 輸入資產代號", "6869.HK").upper()
    run_a = st.sidebar.button("🔍 確認透視")
    if ticker:
        with st.spinner(f"⏳ 正在透視 {ticker} 大戶氣脈..."):
            info, holders = get_all_data(ticker)
            df = smart_fetch(ticker, period="2y")
            # FIX 1: 首頁入港股用恆指做對手
            bench_sym = "^HSI" if ".HK" in ticker else "SPY"
            spy = smart_fetch(bench_sym, period="2y")
            
            if not df.empty and not spy.empty:
                df = get_tri_sword_logic(df); curr_p = df['Close'].iloc[-1]
                
                # FIX 5: 52周高位過時烏龍 (用K線現抽)
                ath_val = df['High'].tail(252).max()
                dist_ath = ((curr_p / ath_val) - 1) * 100 if ath_val and ath_val > 0 else 0
                
                # FIX 2: IPO保險絲
                df['50MA_strat'] = df['Close'].rolling(50, min_periods=1).mean()
                ma50_bias = ((curr_p / df['50MA_strat'].iloc[-1]) - 1) * 100 if df['50MA_strat'].iloc[-1] > 0 else 0
                
                hist_len = len(df); rs_win = min(63, hist_len-1)
                spy_aligned = spy['Close'].reindex(df.index).ffill().bfill()
                crs_val = safe_n(50 + ((curr_p/df['Close'].iloc[-rs_win]) - (spy_aligned.iloc[-1]/spy_aligned.iloc[-rs_win])) * 100)
                cej_s = safe_n((df['Volume'].tail(21).mean()/max(df['Volume'].tail(252).mean(), 1)) * 100)
                se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-min(5, hist_len-1)]) - 1) * 1200))
                
                st.markdown(f"<div class='main-title'>環球資產透維評估儀 [{ticker}]</div>", unsafe_allow_html=True)
                
                # --- 能量磚 ---
                c1, c2, c3 = st.columns([1, 1, 1.5])
                with c1: st.markdown(f"<div class='cosmos-box' style='height:400px;'><div class='cosmos-label'>COSMOS-RS</div><div class='cosmos-value'>{crs_val:.1f}</div><p style='color:#FFD700;'>基準: {bench_sym}</p></div>", unsafe_allow_html=True)
                with c2: st.markdown(f"<div class='val-box-purple' style='height:400px;'><div class='val-label'>🏆 綜合總分</div><div style='font-size:5rem; color:#BC13FE;'>{int((crs_val+cej_s/2)/1.5)}</div></div>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF; height:180px;'>EJ 錢流底氣: {cej_s:.1f}%</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='cosmos-box' style='border-color:#FF00FF; height:180px; margin-top:20px;'>短期能量 BAR: {se_s:.1f}%</div>", unsafe_allow_html=True)

                # --- 4層大戶照妖鏡圖 ---
                fig = make_subplots(rows=4, cols=1, shared_xaxes=True, row_heights=[0.4, 0.2, 0.2, 0.15], vertical_spacing=0.03)
                dates = df.index.strftime('%Y-%m-%d')
                fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
                
                # 成交量染色 (Cyan/Magenta)
                v_colors = ['#00FFFF' if c else ('#FF00FF' if m else '#888888') for c, m in zip(df['Cyan'], df['Magenta'])]
                fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name="量能情緒"), row=2, col=1)
                
                # NETMA 氣脈
                fig.add_trace(go.Bar(x=dates, y=df['NetVol'], marker_color=np.where(df['NetVol']>0, 'green', 'red'), opacity=0.3, name="主力淨額"), row=3, col=1)
                fig.add_trace(go.Scatter(x=dates, y=df['NETMA'], line=dict(color='white', width=2), name="氣脈線"), row=3, col=1)
                
                # 升跌幅
                fig.add_trace(go.Bar(x=dates, y=df['ROC'], marker_color=np.where(df['ROC']>0, 'red', 'green'), name="升跌%"), row=4, col=1)
                
                fig.update_layout(template="plotly_dark", height=1000, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

                # 🧙 名家持倉 (保證原封不動)
                st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center;'>🧙 90 大名家：真實申報持倉</div>", unsafe_allow_html=True)
                if holders is not None and not holders.empty:
                    for _, row in holders.head(8).iterrows():
                        st.markdown(f"<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>持有 {row['Shares']:,.0f} 股 | 市值 ${row['Value']/1e6:.1f}M</span></div>", unsafe_allow_html=True)
                else: st.markdown("<p style='text-align:center; padding:20px;'>暫無大名家數據</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

# =========================================================================
# 📡 拔河熱力圖 (5/20日切換 + 全拆解排行榜)
# =========================================================================
elif "熱力圖" in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    m_view = st.sidebar.radio("選擇星系", ["🇺🇸 美國陣列", "🇭🇰 港股陣列"])
    lookback = st.sidebar.radio("戰術時間窗", [5, 20], horizontal=True)
    is_us = "美國" in m_view; is_etf = "ETF" in app_mode
    bench_sym = "SPY" if is_us else "^HSI"
    target_map = (US_ETF_MAP if is_etf else US_STOCK_MAP) if is_us else (HK_ETF_MAP if is_etf else HK_STOCK_MAP)
    
    if st.button("📡 啟動全拆解拔河掃描！"):
        all_tickers = list(set([t for sub in target_map.values() for t in sub])) if is_etf else list(target_map.keys())
        chart_height = (3000 if is_us else 1500) if is_etf else 800
        with st.spinner('龍虎榜瘋狂計算中...'):
            bench_df = smart_fetch(bench_sym, period="60d")['Close'].dropna()
            results = []
            for t in all_tickers:
                d = smart_fetch(t if is_etf else target_map[t][0], period="60d")['Close'].dropna()
                if len(d) >= lookback and len(bench_df) >= lookback:
                    rs = 50 + ((d.iloc[-1]/d.iloc[-lookback]) - (bench_df.iloc[-1]/bench_df.iloc[-lookback])) * 100
                    results.append({"項目": t, "RS": round(rs, 1)})
            if results:
                df_rs = pd.DataFrame(results).sort_values("RS", ascending=True)
                fig = go.Figure(go.Bar(x=df_rs["RS"], y=df_rs["項目"], orientation='h', marker=dict(color=df_rs["RS"], colorscale='Portland')))
                fig.update_layout(template="plotly_dark", height=chart_height, title=f"{lookback}日 相對強弱龍虎榜")
                st.plotly_chart(fig, use_container_width=True)

# =========================================================================
# 🔍 尋龍雷達 (加 💰 Icon)
# =========================================================================
elif app_mode == "🔍 千龍起步尋龍雷達 (個股)":
    st.markdown("<h1 class='main-title'>🔍 千龍起步 💰 錢袋子雷達</h1>", unsafe_allow_html=True)
    m_choice = st.radio("1. 市場", ["🇺🇸 美股", "🇭🇰 港股"])
    target_dict = US_STOCK_MAP if "美股" in m_choice else HK_STOCK_MAP
    if st.button("📡 發射撒網尋龍電波！"):
        bench_data = smart_fetch("SPY" if "美股" in m_choice else "^HSI", period="2y")
        for name, tickers in target_dict.items():
            for t in tickers:
                df = smart_fetch(t, period="1y")
                if len(df) > 63:
                    df = get_tri_sword_logic(df); curr_p = df['Close'].iloc[-1]
                    # 原本 6 大羅輯計算法 (基準對齊)
                    crs = safe_n(50+((curr_p/df['Close'].iloc[-63])-(bench_data['Close'].iloc[-1]/bench_data['Close'].iloc[-63]))*100)
                    ej = safe_n((df['Volume'].tail(21).mean()/max(df['Volume'].tail(252).mean(), 1))*100)
                    se = safe_n(50+(((curr_p/df['Close'].iloc[-5])-1)*1200))
                    # 💰 爆發判定 (3日內有過 Cyan)
                    has_money = df['Cyan'].tail(3).any()
                    if crs > 52 and ej > 85 and se > 75:
                        bag = " 💰" if has_money else ""
                        st.markdown(f"<div class='scan-card-fire'>🎯 {t} | 符合大戶佈局！{bag} (RS:{crs:.1f})</div>", unsafe_allow_html=True)

# =========================================================================
# 📈 VCP 形態 (NETMA 門神 + IPO保險絲)
# =========================================================================
elif app_mode == "📈 VCP 形態戰術掃描 & 防守圖":
    st.markdown("<h1 class='main-title'>📈 VCP 形態戰術掃描 & 防守圖</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background-color:#111; padding:15px; border-radius:10px; border-left: 5px solid #BC13FE; margin-bottom: 20px;'>
        <h3 style='color:#BC13FE; margin-top:0;'>🐉 終極獵龍引擎 (Mark Minervini)</h3>
        <p style='color:#ddd; margin-bottom:0;'>海選：50>150>200多頭排列 | RS Rating > 80 | 大戶掃貨標籤<br>
        狙擊：VCP 形態偵測 | HVN 重貨區動態止損 | 獨立 RS 領先線 | 雙戰術過濾</p>
    </div>
    """, unsafe_allow_html=True)

    c_cat, c_mkt, c_sec, c_strat = st.columns([1, 1, 1.5, 1.5])
    with c_cat: asset_type = st.radio("1. 資產類別", ["🏢 領頭個股", "🧺 優質 ETF"])
    with c_mkt: market_choice = st.radio("2. 掃描市場", ["🇺🇸 美股", "🇭🇰 港股"])
    
    is_us = "美股" in market_choice
    is_etf = "ETF" in asset_type
    bench_sym = "SPY" if is_us else "2800.HK"
    
    if is_etf: target_dict = US_ETF_MAP if is_us else HK_ETF_MAP
    else: target_dict = US_STOCK_MAP if is_us else HK_STOCK_MAP
    
    with c_sec: s_choice = st.selectbox("3. 選擇掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()))
    with c_strat: vcp_strat = st.radio("4. 戰術過濾 (機變)", ["🔥 極致新高 (ATH)", "🐉 潛龍伏躍 (10-20% 空間)"])

    if 'vcp_scanned_stocks' not in st.session_state:
        st.session_state.vcp_scanned_stocks = []

    if st.button("📡 [神掣] 發射！執行核心 RS 海選與大戶偵測"):
        tickers_to_scan = list(set([t for sub in target_dict.values() for t in sub])) if "全星系" in s_choice else target_dict[s_choice]
        found_stocks = []
        pb = st.progress(0)
        
        with st.spinner("⏳ 慢速防封鎖引擎已啟動，正在對比大盤 RS 同尋找大戶足跡..."):
            try:
                bench_df = smart_fetch(bench_sym, period="1y")['Close'].dropna()
                yearly_returns = {}
                valid_dfs = {}
                for idx, t in enumerate(tickers_to_scan):
                    pb.progress((idx + 1) / len(tickers_to_scan))
                    if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                    try:
                        df_t = smart_fetch(t, period="1y")
                        if len(df_t) > 150:
                            ret = (df_t['Close'].iloc[-1] / df_t['Close'].iloc[0]) - 1
                            yearly_returns[t] = ret
                            valid_dfs[t] = df_t
                    except: continue

                if yearly_returns:
                    all_rets = pd.Series(list(yearly_returns.values()))
                    for t, ret in yearly_returns.items():
                        df_vcp = valid_dfs[t].copy()
                        
                        # 🌟 FIX 4: 零波幅保險 + 計算 NETMA 門神
                        denom = np.maximum(df_vcp['High'] - df_vcp['Low'], 0.001)
                        df_vcp['BuyVol'] = np.where(df_vcp['High'] > df_vcp['Low'], df_vcp['Volume'] * (df_vcp['Close'] - df_vcp['Low']) / denom, 0)
                        df_vcp['SellVol'] = np.where(df_vcp['High'] > df_vcp['Low'], df_vcp['Volume'] * (df_vcp['High'] - df_vcp['Close']) / denom, 0)
                        df_vcp['NetVol'] = df_vcp['BuyVol'] - df_vcp['SellVol']
                        df_vcp['NETMA'] = df_vcp['NetVol'].rolling(10, min_periods=1).mean()

                        # 🌟 FIX 2: IPO 保險絲 (min_periods=1)
                        df_vcp['MA50'] = df_vcp['Close'].rolling(50, min_periods=1).mean()
                        df_vcp['MA150'] = df_vcp['Close'].rolling(150, min_periods=1).mean()
                        df_vcp['MA200'] = df_vcp['Close'].rolling(200, min_periods=1).mean()
                        curr = df_vcp.iloc[-1]
                        ath = df_vcp['High'].tail(252).max()
                        
                        if not (curr['Close'] > df_vcp['MA50'].iloc[-1] and df_vcp['MA50'].iloc[-1] > df_vcp['MA150'].iloc[-1]): continue
                        
                        # 🌟 門神濾網：NETMA 必須大於 0
                        if df_vcp['NETMA'].iloc[-1] <= 0: continue
                        
                        if vcp_strat == "🔥 極致新高 (ATH)":
                            if not (df_vcp['MA150'].iloc[-1] > df_vcp['MA200'].iloc[-1]): continue
                            if (curr['Close'] / ath) < 0.93: continue
                        else:
                            if not (0.75 <= (curr['Close'] / ath) <= 0.90): continue

                        rs_rating = int((all_rets[all_rets <= ret].count() / len(all_rets)) * 99)
                        if rs_rating < 80: continue
                        
                        df_vcp['Vol50'] = df_vcp['Volume'].rolling(50, min_periods=1).mean()
                        whale_count = len(df_vcp.tail(10)[(df_vcp.tail(10)['Close'] > df_vcp.tail(10)['Open']) & (df_vcp.tail(10)['Volume'] > df_vcp.tail(10)['Vol50'] * 1.5)])
                        
                        found_stocks.append({
                            'Ticker': t, 'RS Rating': rs_rating, 'Tags': f"🔥 大戶掃貨 ({whale_count}/10)" if whale_count >= 3 else "",
                            'Pivot': df_vcp['High'].tail(20).max()
                        })
                st.session_state.vcp_scanned_stocks = sorted(found_stocks, key=lambda x: x['RS Rating'], reverse=True)
            except Exception as e: st.error(f"掃描受限: {e}")

    if st.session_state.vcp_scanned_stocks:
        st.success(f"🎉 成功尋獲 {len(st.session_state.vcp_scanned_stocks)} 隻終極潛力標的！")
        
        st.markdown("### 🏆 領頭羊精銳名單")
        for s in st.session_state.vcp_scanned_stocks:
            bg = "scan-card-super" if '🔥' in s['Tags'] else "scan-card-fire"
            st.markdown(f"<div class='{bg}'><div style='display:flex; justify-content:space-between;'><span style='font-size:1.5rem; font-weight:bold; color:white;'>[{s['Ticker']}] 趨勢: ✅ | RS Rating: <span style='color:#00FFCC;'>{s['RS Rating']}</span></span><span style='font-size:1.2rem; font-weight:bold; color:#FFD700;'>{s['Tags']}</span></div></div>", unsafe_allow_html=True)

        st.write("---")
        selected_stock = st.selectbox("🎯 選擇目標查看「3 層視覺化戰術儀表板」", [s['Ticker'] for s in st.session_state.vcp_scanned_stocks])
        if selected_stock:
            sel_data = next((item for item in st.session_state.vcp_scanned_stocks if item["Ticker"] == selected_stock), None)
            pivot_price = sel_data['Pivot']
            
            with st.spinner("正在繪製 K線、重貨區 HVN 及 RS 領先線..."):
                try:
                    df = smart_fetch(selected_stock, period="6mo")
                    b_df = smart_fetch(bench_sym, period="6mo")['Close']
                    df['MA50'] = df['Close'].rolling(50, min_periods=1).mean()
                    df['Vol50'] = df['Volume'].rolling(50, min_periods=1).mean()
                    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
                    
                    df_a, b_a = df['Close'].align(b_df, join='inner')
                    rs_line = (df_a / b_a).reindex(df.index).ffill().bfill() 
                    
                    counts, bins = np.histogram(df['Close'], bins=25, weights=df['Volume'])
                    hvn_price = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                    stop_loss = hvn_price * 0.985
                    
                    df['H-L'] = df['High'] - df['Low']
                    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
                    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
                    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
                    df['ATR'] = df['TR'].rolling(14).mean()
                    atr_stop = df['Close'].iloc[-1] - (1.5 * df['ATR'].iloc[-1]) if not pd.isna(df['ATR'].iloc[-1]) else stop_loss
                    
                    risk_pct = ((df['Close'].iloc[-1] - stop_loss) / df['Close'].iloc[-1]) * 100

                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.03)
                    dates = df.index.strftime('%Y-%m-%d')
                    
                    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['MA50'], mode='lines', name='50MA (黃實線)', line=dict(color='yellow', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['EMA10'], mode='lines', name='10 EMA (橙虛線)', line=dict(color='orange', width=1.5, dash='dot')), row=1, col=1)
                    
                    fig.add_hline(y=pivot_price, line_dash="dash", line_color="#00FFCC", annotation_text=f"🎯 買入 (Pivot): ${pivot_price:.2f}", annotation_position="top left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    fig.add_hline(y=stop_loss, line_dash="solid", line_color="#FF4B4B", annotation_text=f"🛑 重貨區止損: ${stop_loss:.2f}", annotation_position="bottom left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    fig.add_hline(y=atr_stop, line_dash="dash", line_color="#BC13FE", annotation_text=f"🛡️ 1.5 ATR 止損: ${atr_stop:.2f}", annotation_position="bottom right", annotation_font=dict(color="white", size=13), row=1, col=1)
                    
                    max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136, 136, 136, 0.4)', name='重貨區 HVN', hoverinfo='skip', xaxis='x4', yaxis='y1'))
                    
                    v_colors = ['#00FF00' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF0000' for i in range(len(df))]
                    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    for i in range(len(df)):
                        if df['Close'].iloc[i] > df['Open'].iloc[i] and df['Volume'].iloc[i] > df['Vol50'].iloc[i]*1.5:
                            fig.add_annotation(x=dates[i], y=df['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", xanchor="center", font=dict(size=14, color="#FFD700"), row=2, col=1)

                    fig.add_trace(go.Scatter(x=dates, y=rs_line, mode='lines', line=dict(color='#BC13FE', width=2), name="RS線"), row=3, col=1)
                    if df['Close'].iloc[-1] < df['Close'].tail(20).max() * 0.98 and rs_line.iloc[-1] >= rs_line.tail(20).max() * 0.99:
                        fig.add_annotation(x=dates[-1], y=rs_line.iloc[-1], text="🌟 起步點！", showarrow=True, ax=-40, ay=-30, font=dict(color="white", size=14), row=3, col=1)

                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=850,
                                      hovermode='x unified',
                                      xaxis_rangeslider_visible=False, 
                                      xaxis=dict(type='category', showticklabels=False, showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      xaxis2=dict(type='category', showticklabels=False, showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'),
                                      xaxis3=dict(type='category', title="日期", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      yaxis=dict(title="股價", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      yaxis2=dict(title="成交量", showticklabels=False),
                                      yaxis3=dict(title="RS Rating", showticklabels=False),
                                      xaxis4=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False),
                                      legend=dict(font=dict(color="white", size=13), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True)

                    risk_alert = f"<span style='color:#FF4B4B;'>⚠️ 長線防波堤極限風險 ({risk_pct:.1f}%)，請相應縮小買入倉位！</span>" if risk_pct > 7.0 else f"<span style='color:#00FFCC;'>✅ 長線防波堤風險可控 ({risk_pct:.1f}%)</span>"
                    st.markdown(f"<div style='background-color:#111; padding:20px; border-radius:10px; border:2px solid #FFD700;'><h4 style='color:#FFD700; margin-top:0;'>🛡️ 三重防線管理</h4><p style='font-size:1.2rem; color:white;'>🎯 設定買入觸發價 (Pivot)： <b style='color:#00FFCC;'>${pivot_price:.2f}</b></p><hr style='border-color:#333;'><p style='font-size:1.1rem; color:white;'>1️⃣ 極限短炒止盈 (10 EMA)： <b style='color:orange;'>${df['EMA10'].iloc[-1]:.2f}</b></p><p style='font-size:1.1rem; color:white;'>2️⃣ 波段抗震止損 (1.5 ATR)： <b style='color:#BC13FE;'>${atr_stop:.2f}</b></p><p style='font-size:1.1rem; color:white;'>3️⃣ 終極底線止損 (HVN 重貨區)： <b style='color:#FF4B4B;'>${stop_loss:.2f}</b></p><p>{risk_alert}</p></div>", unsafe_allow_html=True)
                except Exception as e: st.error(f"繪圖出錯: {e}")

# =========================================================================
# 🌊 模式 E：海龜回測加注雷達 (🌟 修改點 5: No Magenta + NETMA 門神 + IPO保險)
# =========================================================================
elif app_mode == "🌊 海龜回測加注雷達 (Mode E)":
    st.markdown("<h1 class='main-title'>🌊 海龜回測加注雷達 (Mode E)</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background-color:#111; padding:15px; border-radius:10px; border-left: 5px solid #00FFCC; margin-bottom: 20px;'>
        <h3 style='color:#00FFCC; margin-top:0;'>🐢 N字型突破加注法 (1-2-3 Continuation)</h3>
        <p style='color:#ddd; margin-bottom:0;'>此雷達已實裝「真龍基因過濾」：先過濾最強 RS，再搵 <b>N字回測 10 EMA</b>。<br>
        確保踢走所有弱勢股，只搵強者回調嘅黃金加注機會！</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1.5])
    with c1: asset_type = st.radio("1. 掃描對象", ["🏢 領頭個股", "🧺 優質 ETF"])
    with c2: market_choice = st.radio("2. 掃描市場", ["🇺🇸 美股", "🇭🇰 港股"])
    with c3: turtle_strat = st.radio("3. 海龜戰術 (機變)", ["🔥 極致真龍 (ATH 回測)", "🐉 潛龍初醒 (剛入強勢)"])

    is_us = "美股" in market_choice
    is_etf = "ETF" in asset_type
    target_dict = (US_ETF_MAP if is_etf else US_STOCK_MAP) if is_us else (HK_ETF_MAP if is_etf else HK_STOCK_MAP)
    s_choice = st.selectbox("4. 選擇掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()))

    if 'e_scanned_stocks' not in st.session_state:
        st.session_state.e_scanned_stocks = []

    if st.button("📡 發射真龍 N 字雷達！"):
        tickers = list(set([t for sub in target_dict.values() for t in sub])) if "星系" in s_choice else target_dict[s_choice]
        found = []
        pb = st.progress(0)
        
        with st.spinner("⏳ 雷達正在慢速穩定過濾「去弱留強」 N 字加注點..."):
            yearly_returns = {}
            valid_dfs = {}
            for idx, t in enumerate(tickers):
                pb.progress((idx + 1) / len(tickers))
                if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                try:
                    df_t = smart_fetch(t, period="1y")
                    if len(df_t) > 150:
                        ret = (df_t['Close'].iloc[-1] / df_t['Close'].iloc[0]) - 1
                        yearly_returns[t] = ret
                        valid_dfs[t] = df_t
                except: continue
            
            if yearly_returns:
                all_rets = pd.Series(list(yearly_returns.values()))
                for t, ret in yearly_returns.items():
                    df = valid_dfs[t].copy()
                    
                    # 🌟 FIX 4: 零波幅保險 + 海龜 NETMA/Magenta 門神
                    denom = np.maximum(df['High'] - df['Low'], 0.001)
                    df['BuyVol'] = np.where(df['High'] > df['Low'], df['Volume'] * (df['Close'] - df['Low']) / denom, 0)
                    df['SellVol'] = np.where(df['High'] > df['Low'], df['Volume'] * (df['High'] - df['Close']) / denom, 0)
                    df['NetVol'] = df['BuyVol'] - df['SellVol']
                    df['NETMA'] = df['NetVol'].rolling(10, min_periods=1).mean()
                    
                    # FIX 2: IPO 保險絲 (min_periods=1)
                    v_ma20 = df['Volume'].rolling(20, min_periods=1).mean()
                    v_std20 = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
                    v_upper = v_ma20 + (2.0 * v_std20)
                    v_ma60 = df['Volume'].rolling(60, min_periods=1).mean()
                    roc = df['Close'].pct_change() * 100
                    df['Magenta'] = (df['Volume'] > v_upper) & (df['Volume'] > v_ma60 * 1.9) & (roc.abs() > 2.0) & (df['Close'] <= df['Open'])

                    curr_p = df['Close'].iloc[-1]
                    ma50 = df['Close'].rolling(50, min_periods=1).mean().iloc[-1]
                    ma150 = df['Close'].rolling(150, min_periods=1).mean().iloc[-1]
                    ma200 = df['Close'].rolling(200, min_periods=1).mean().iloc[-1]
                    ema10 = df['Close'].ewm(span=10, adjust=False).mean().iloc[-1]
                    ath = df['High'].tail(252).max()
                    
                    rs_rating = int((all_rets[all_rets <= ret].count() / len(all_rets)) * 99)
                    
                    if not (curr_p > ma50 and ma50 > ma150): continue
                    if turtle_strat == "🔥 極致真龍 (ATH 回測)":
                        if not (ma150 > ma200): continue 
                        if (curr_p / ath) < 0.90: continue
                        if rs_rating < 80: continue
                    else: 
                        if not (0.75 <= (curr_p / ath) <= 0.92): continue 
                        if rs_rating < 70: continue

                    last_20_high = df['High'].tail(20).max()
                    high_idx = df['High'].tail(20).argmax()
                    days_since_high = 19 - high_idx
                    
                    if 2 <= days_since_high <= 15: # 回落中
                        pullback_pct = ((curr_p - last_20_high) / last_20_high) * 100
                        if -15 <= pullback_pct <= -1:
                            if ema10 * 0.98 <= curr_p <= ema10 * 1.04: # 企穩 10 EMA
                                
                                # 🌟 健康回測確認門神
                                pullback_magenta = df['Magenta'].iloc[-days_since_high:].any()
                                current_netma = df['NETMA'].iloc[-1]
                                
                                if current_netma > 0 and not pullback_magenta:
                                    swing_low = df['Low'].iloc[-days_since_high:].min()
                                    found.append({
                                        'Ticker': t, 'Price': curr_p, 'High': last_20_high,
                                        'Low': swing_low, 'Pullback': pullback_pct, 'EMA10': ema10,
                                        'Days Since High': days_since_high
                                    })
            
            st.session_state.e_scanned_stocks = sorted(found, key=lambda x: x['Pullback'], reverse=True)

    if st.session_state.e_scanned_stocks:
        st.success(f"🎉 捕捉到 {len(st.session_state.e_scanned_stocks)} 隻健康回測中嘅目標！")
        for p in st.session_state.e_scanned_stocks:
            st.markdown(f"""
            <div class='pullback-card'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span style='font-size:1.8rem; font-weight:bold; color:white;'>🎯 [{p['Ticker']}] 💰</span>
                    <span style='font-size:1.2rem; font-weight:bold; color:#00FFCC;'>現價: ${p['Price']:.2f}</span>
                </div>
                <hr style='border-color:#444; margin:10px 0;'>
                <div style='display:flex; justify-content:space-between;'>
                    <span>📈 前高阻力 (海龜買入點): <b style='color:#00FFCC;'>${p['High']:.2f}</b> <span style='font-size:0.9rem;'>({p['Days Since High']} 日前)</span></span>
                    <span>📉 回落幅度: <b style='color:#FF4B4B;'>{p['Pullback']:.1f}%</b></span>
                </div>
                <div style='display:flex; justify-content:space-between; margin-top:5px;'>
                    <span>🛡️ 極限防守 (10 EMA): <b style='color:orange;'>${p['EMA10']:.2f}</b></span>
                    <span>🛑 N字波谷底 (海龜止損): <b style='color:#FF00FF;'>${p['Low']:.2f}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("---")
        sel = st.selectbox("🎯 選擇目標查看 X 光戰術圖", [s['Ticker'] for s in st.session_state.e_scanned_stocks])
        if sel:
            p_data = next(x for x in st.session_state.e_scanned_stocks if x['Ticker'] == sel)
            with st.spinner("正在為您繪製專屬海龜回測戰術圖表..."):
                try:
                    df = smart_fetch(sel, period="6mo")
                    df['MA50'] = df['Close'].rolling(50, min_periods=1).mean()
                    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
                    
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
                    dates = df.index.strftime('%Y-%m-%d')
                    
                    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['MA50'], mode='lines', name='50MA (黃實線)', line=dict(color='yellow', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['EMA10'], mode='lines', name='10 EMA (橙虛線)', line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                    
                    fig.add_hline(y=p_data['High'], line_dash="dash", line_color="#00FFCC", annotation_text=f"🐢 破頂買入: ${p_data['High']:.2f}", annotation_position="top left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    fig.add_hline(y=p_data['Low'], line_dash="solid", line_color="#FF00FF", annotation_text=f"🛑 波谷止損: ${p_data['Low']:.2f}", annotation_position="bottom left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    
                    counts, bins = np.histogram(df['Close'], bins=30, weights=df['Volume'])
                    max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(150,150,150,0.3)', name='重貨區', hoverinfo='skip', xaxis='x4', yaxis='y1'))

                    v_colors = ['#00FF00' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF0000' for i in range(len(df))]
                    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    
                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=650,
                                      hovermode='x unified',
                                      xaxis_rangeslider_visible=False, 
                                      xaxis=dict(type='category', showticklabels=False, showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      xaxis2=dict(type='category', title="日期", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      xaxis4=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False),
                                      yaxis=dict(title="股價", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      yaxis2=dict(title="成交量", showticklabels=False),
                                      legend=dict(font=dict(color="white", size=13), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e: st.error(f"繪圖出錯: {e}")
    else:
        st.warning("💤 雷達掃描完畢，未有符合雙重過濾之標的。")
