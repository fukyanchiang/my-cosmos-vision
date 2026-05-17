import streamlit as st 
import yfinance as yf 
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go 
from plotly.subplots import make_subplots 
from core_logic import scan_dragon_logic, smart_fetch, check_stop_loss
import time

# ==========================================
# 🌐 GitHub 雲端名單 (爺爺已幫你填好！)
# ==========================================
HK_STOCK_CSV_URL = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/refs/heads/main/hk_stock.csv"
HK_ETF_CSV_URL = "https://raw.githubusercontent.com/fukyanchiang/my-cosmos-vision/refs/heads/main/hk_etf.csv"

@st.cache_data(ttl=3600) # 緩存1小時，提高掃描反應速度
def fetch_github_list(url):
    try:
        df = pd.read_csv(url)
        if 'Ticker' in df.columns:
            df['Ticker'] = df['Ticker'].astype(str)
        return df
    except Exception as e:
        return pd.DataFrame()

# ==========================================
# 📚 美股字典 (保持原樣)
# ==========================================
US_STOCK_MAP = {
    "1. 半導體設備與設計": "NVDA TSM AVGO ASML AMD QCOM TXN MU INTC AMAT LRCX KLAC ADI NXPI MRVL MCHP SWKS MPWR ON LSCC TER QRVO SLAB WOLF SYNA RMBS ALGM SITM ACLS CRUS".split(),
    "2. AI與大數據雲端": "MSFT GOOGL ORCL ADBE CRM PLTR SNOW PANW FTNT NOW WDAY ZS DDOG CRWD MDB NET OKTA TEAM SPLK GEN CYBR CHKP VRSN ESTC TENB SQSP PCOR DOCN AI FSLY MSTR".split(),
    "3. 基礎軟件與 SaaS": "INTU VMW CDNS PTC MSTR SPT ALTR MANH GWRE PAYC APPN TYL BLK PEGA BL DT DBX PATH BSY NCNO WK ME LAW ALIT VRM HCP RNG".split(),
    "4. 網絡安全 (Cyber)": "PANW CRWD FTNT ZS CYBR CHKP GEN TENB NET OKTA S OKTA VRNS QLYS SAIL MIME RPD PFPT FEYE EVBG IMPV".split(),
    "5. 消費電子與硬件": "AAPL HPQ DELL STX WDC APH TEL LOGI HPE NTAP GLW ST ANET FFIV GRMN LITE SMCI VRT JBL FLEX NVT ROK CSL HUBB CNHI GWW PH SANM PLXS".split(),
    "6. 通訊與網絡設備": "CSCO MSI JNPR ANET COMM ZBRA JNPR CIEN LITE VIAV ADTN CALX HLIT INFN NTGR ACIA EXTR CRDO FN CLFD".split(),
    "7. 互聯網平台內容": "META GOOGL PINS SNAP MATCH MTCH IAC OGI YELP BMBL BUMBLE GRND COMP ZIP TRUE CARG MTTR LEA GRPN".split(),
    "8. 媒體與影視娛樂": "NFLX DIS WBD PARA LYV SPOT SIRI ROKU NWSA NYT FOXA OMC IPG WPP NWS EVC NXST MEG TGNA SSP GTN SGA".split(),
    "9. 電子商務與零售": "AMZN EBAY ETSY MELI SHOP PDD BABA JD SE CPNG W GMED CVNA FAIR FTCH CHWY OSTK REAL RVLV PRTS QRTEA POSH VIPS BZUN".split(),
    "10. 傳統零售百貨": "WMT COST TGT DG DLTR KR SYY K DLTR BIG BBY BJ CFG SFM UNFI IMKTA SPTN ANDE VLGEA INTA GROC".split(),
    "11. 核心消費品": "PG KO PEP PM MO EL CL KDP GIS HSY KHC CPB MKC MDLZ SJM CAG STZ TSN K CPB KHC GIS HSY CPB SJM TAP BF.B CHD POST".split(),
    "12. 汽車製造商": "F GM STLA TM HMC RACE CARZ HOG WGO REV GOLF LCII WGO REVG SRG".split(),
    "13. 電動車與自駕 (EV)": "TSLA RIVN LCID LI NIO XPEV MSTR UBER LYFT QS AUR GWB ALV LEA MGA BWA APTV VC THO DORM WGO PSNY FSR GOEV HYZN PTRA LEV VLTA".split(),
    "14. 汽車零部件": "MGA APTV BWA LEA VC DAN ALV GNTX AXA FOXF SMP THO TEN CTB HY MLR SUP MOD PRG".split(),
    "15. 航空航天與國防": "LMT RTX NOC GD BA TDG HWM LHX LDOS TXT HEI WWD SPR BWXT AVAV KTOS MRCY ATRO NP KEX ESLT CW ST VSEC ASIX AJRD KAMN".split(),
    "16. 重型機械裝備": "CAT DE CMI PCAR OSK TEX TRN ALG GGW HY ALG REVG B RC BRC RAIL ARNC WNC GBX".split(),
    "17. 工業綜合集團": "GE HON MMM EMR ITW ETN PH ROK DOV URI IR PNR GWW NDSN AOS SWK SNA FLS LECO IEX GGG TTC NVT HUBB".split(),
    "18. 運輸與物流": "UNP UPS FDX NSC CSX LSTR OPY SAIA MATX ARCB XPO KNX SNDR HTLD PTEN CVTI WERN HUBG MRIN YELL EEX USX".split(),
    "19. 航空與機場": "LUV DAL AAL UAL ALK JBLU SAVE HA SKYW SNC LTM ULCC MESA JOBY ACHR".split(),
    "20. 旅遊酒店博彩": "BKNG ABNB MAR HLT LVS WYNN MGM RCL CCL EXPE NCLH WH CHH PENN CZR BALY CHDN RRR GDEN PLCE SG".split(),
    "21. 餐飲連鎖": "MCD SBUX YUM CMG DPZ DRI QSR YUMC TXRH DARD BLMN EAT CAKE PLAY DENN RUTH PZZA WEN SHAK JACK TACO CHUY".split(),
    "22. 商業銀行巨頭": "JPM BAC WFC C GS MS AXP BLK V MA PYPL DFS SYF ALL COF COF AXP DFS SYF ALL RF CFG FITB MTB HBAN KEY CMA ZION".split(),
    "23. 區域性銀行": "KRE PNC TFC USB EWBC WAL PACW FRC SNV FHN BOKF WTFC CFR CUBI PB CTBI ONB BOH UMBF CBSH FNB CATY".split(),
    "24. 投資與資產管理": "BLK BX TROW APO KKC KKR CG ARES OWL OAK STEP BEN STT BK NTRS IVZ JHG AMG LAZ APAM".split(),
    "25. 金融科技與支付": "V MA SQ PYPL AFRM SOFI NU GPN FIS FI FISV TOST MQ BILL FLYW REVG BKI LPRO IIIV HAE FOR EVTC RPCE FLT WEX REVG".split(),
    "26. 保險經紀與服務": "CB PGR TRV MET AIG PRU TRV HIG AFL L AL MKL CINF RGA RE WRB GL CNA AFG SIGI THG KMPR".split(),
    "27. 傳統製藥巨頭": "LLY NVO JNJ MRK ABBV PFE AMGN VRTX REGN GILD BMY BMY GSK SNY AZN NVS TEVA TAK RHHBY".split(),
    "28. 大中型生物科技": "MRNA BNTX BIIB INCY BMRN ALXN SGEN EXAS ILMN ALNY SRPT VRTX BMRN UTHR ARGX DNA CRSP NTLA EDIT BEAM".split(),
    "29. 醫療設備與器械": "MDT ABT SYK BSX EW BDX ISRG ZBH STE ALGN RMD HOLX XRAY COO TFX PEN RES IART GMED OMCL".split(),
    "30. 醫療服務與管理": "UNH ELV CVS CI HUM HCA CNC MOH ACHC SEM EHC CHE MODV OPK ADUS DVA USPH AMN EHC NHC CHE".split(),
    "31. 基因與生命科學": "ILMN TMO A TMO DHR CTLT WAT IQV MTD BRKR PKI CRL BIO TECH MED PINC QGEN NEO NEO EXAS".split(),
    "32. 傳統能源 (油氣)": "XOM CVX COP SLB HAL MPC PSX VLO OXY HES DVN EOG PXD FANG CXO CLR MRO PXD FANG MUR MRO APA MTDR".split(),
    "33. 油氣設備與服務": "SLB HAL BKR FTI NBR NOV CHX WTTR PTEN LBRT OIS RES HLX NCS NEX NINE SOI WTTR".split(),
    "34. 太陽能與清潔能源": "FSLR ENPH SEDG RUN SHLS NEE BE CWEN AY NOVA MAXN SPWR ARRY STEM PLUG DQ JKS CSIQ NEP HASI BEP PEGI TPIC".split(),
    "35. 公用事業 (水電)": "NEE SO DUK SRE AEP D EXC PCG FE ED PEG XEL WEC ES AWK LNT CMS NI ATO EVRG PNW CNP DTE PPL".split(),
    "36. 基礎與特殊化工": "LIN APD DOW LYB CE IFF ECL FMC EMN CF MOS NTR SMG WLK HUN ALB OLN ASH KRA GRA GGG FUL".split(),
    "37. 鋼鐵與基礎金屬": "NUE STLD X CLF RS RS CMP WOR RYI TMST CRS HAYN KALU ATI SCHN USAP ZEUS".split(),
    "38. 黃金與貴金屬": "NEM GOLD FCX SCCO AEM KGC WPM RGLD FNV HL CDE EXK IAG GORO GSS SA MUX TRX EGO AUY".split(),
    "39. 住宅房地產開發": "LEN DHI PHM TOL NVR KBH TMHC MDC MHO LGIH GRBK CCS BLD BZH HOV TPH".split(),
    "40. 商業地產 REITs": "PLD AMT EQIX CCI PSA O SPG VICI CBRE ARE DRE EXR DLR MAA AVB WELL VTR PEAK INV INVH CPT ESS UDR EQR".split(),
    "41. 特殊與基建 REITs": "AMT CCI SBAC DLR EQIX CONE COR QTS IRM LAMR OUT UNIT GLPI VICI EPR LXP".split(),
    "42. 加密貨幣與區塊鏈": "COIN MSTR MARA RIOT HUT CLSK CIFR BITF HIVE SDIG BTBT GLXY WULF CORZ ARBK IREN".split(),
    "43. 農業與肥料": "DE CTVA CF MOS NTR FMC SMG SQM IPI UAN SEB BIOC LMNR AVD CVA LNN".split(),
    "44. 體育戶外與服飾": "NKE LULU UA UAA CROX DECK ONON SKX PLCE FL LEVI VFC KTB BOOT WWW SHOO TBLA RCKY".split(),
    "45. 教育科技": "CHGG COUR LRN TWOU PRDO STRA APEI ATGE LOPE UTI LAUR BFAM".split(),
    "46. 太空與前沿探索": "SPCE RKLB PL BKSY ASTS RDW MNTS LLAP SIDU SPIR SATS SPIR LUNR ACHR JOBY".split(),
    "47. 機器人與自動化": "PATH SYM CGNX ISGN KEX LECO ROK PTC FARO FLIR ALTR NVMI ACLS CAMT ICHR COHU".split(),
    "48. 中型價值精選": "WSM GPC WSM WILLIAMS TSCO ODFL MIDD SAIA R EXPD CHRW GGG DOV NDSN LECO WTS ITW".split(),
    "49. 小型爆發精選": "CELH WING APP ELF ANF MOD MSTR SMCI TMDX AXON FOUR INDI VRT ALKT ACLS MOD ONTO POWI".split(),
    "50. 超微型探索 (Micro)": "SOUN RXRX AI BBAI HIVE VLD IONQ BBAI CRDO NRDS INDI LUNA QBTS KTRA RGTI ARQQ INVZ".split()
}

US_ETF_MAP = {
    "U1. Thematic 主題 A (1-70)": "BWET OIH LIT GSG XTL PDBC DBC SOXX FCG SLX IXC REMX ROKT FENY VDE AIS SMH XOP IYE XLE AIRR UFO XBI IDGT TAN DTCR ICLN XME KRE GRID IFRA PAVE XSMO XMMO KBWB VIS SPHB XLI SLYG IJK XSD IJT IVOG EXI ARTY URNM ROBO FXR IWM RSPT QTUM VBK IXN IWO VTWG ARKQ ARKX NUKZ URA NLR GNR GUNR SIL COPX GDX GDXJ IAU GLD IBB GDE QQQ VOX".split(),
    "U2. Thematic 主題 B (71-140)": "FCOM ONEQ MLPX FBCG SPMO IVW SPYG XLK IGM QGRW FTEC VGT QTEC TDIV IYW AIQ XT FELG MGK VUG IWF IWY SCHG MAGS EMLP XLB KOMP BOTZ VAW SOYB AMLP BCI ARKG FTGC KBE CORN EUFN USRT RWR SPXT ICF SCHH NFRA RWO DFAR DIA IYJ REET FUTY VPU IYR VNQ FREL DFGR UTES IMCG FTC SLV XAR SILJ ITA WEAT PPLT VEGI MOO IGF TAGS VDC".split(),
    "U3. Thematic 主題 C (141-214)": "FSTA XLP DBA FXU SPY IDU XLU XLRE CGW QQQE IYF XLC IAI JGRO FDIS VCR SHLD ARKK BLOK SPLV XLY FTXG IYK IXJ IYG PALL XHB BKCH ARKW LQD HYG VHT FHLC IYH XLV VNQI IYC QQEW ITB TLT FIW XLF VFH FNCL IWP CIBR HACK VOT FDN SKYY IHI PHO BIZD CANE BUG IGV GBTC BTC HODL FBTC ARKB BITB IBIT BITO ARKF ETHA".split(),
    "U4. SPDR 核心板塊": "XLE XBI XLI XLK XLB XLP XLU XLRE XLC XLY XLV XLF".split(),
    "U5. 全球國家/地區": "EWY EWZ ILF EIS EWT TUR ECH EFNL EWC EWP EWH EWI EPOL EPU EWW THD VNM EWM EWA EWJ EWN EWS EWQ EZA EWU EWL SPY KSA EWD EWG UAE QAT EPHE FXI EIDO INDA".split()
}

# --- 黑魂 UI 設定 ---
st.set_page_config(page_title="龍魂神殿 5.0", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #FFFFFF !important; }
    div.stButton > button { background-color: #000000 !important; color: #FFFFFF !important; border: 2px solid #FFFFFF !important; border-radius: 0px !important; font-weight: 900 !important; width: 100%; margin-bottom: 5px; }
    div.stButton > button:hover { background-color: #FFFFFF !important; color: #000000 !important; }
    .dragon-card { border-left: 5px solid #00FFCC; background-color: #111111; padding: 15px; margin-bottom: 10px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,255,204,0.1); }
    .data-row { font-size: 0.95rem; color: #CCCCCC; margin-top: 8px; line-height: 1.6; }
    .bear-warning { color: #FF0000 !important; font-size: 1.5rem; font-weight: 900; text-align: center; border: 3px dashed red; background-color: #220000; padding: 15px; margin: 10px 0; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- 能量副圖 ---
def add_energy_subplots(fig, df, dates_chart, row_start):
    var1 = df['Close'] - df['Low']; var2 = df['High'] - df['Close']; var3 = np.maximum(df['High'] - df['Low'], 0.001)
    buyvol = np.where(var3 > 0, df['Volume'] * var1 / var3, 0)
    sellvol = np.where(var3 > 0, df['Volume'] * var2 / var3, 0)
    netvol = buyvol - sellvol
    netma = pd.Series(netvol).rolling(10, min_periods=1).mean()
    
    fig.add_trace(go.Bar(x=dates_chart, y=buyvol, marker_color='#808000', name='買盤', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    fig.add_trace(go.Bar(x=dates_chart, y=-sellvol, marker_color='#800000', name='賣盤', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    net_colors = ['#00FF00' if val > 0 else '#FF0000' for val in netvol]
    fig.add_trace(go.Bar(x=dates_chart, y=netvol, marker_color=net_colors, name='淨勝方', width=0.4), row=row_start, col=1)
    fig.add_trace(go.Scatter(x=dates_chart, y=netma, mode='lines', line=dict(color='white', width=2), name='氣脈10MA'), row=row_start, col=1)

    v_ma = df['Volume'].rolling(20, min_periods=1).mean()
    v_std = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
    v_upper = v_ma + (2.0 * v_std); ma60 = df['Volume'].rolling(60, min_periods=1).mean(); roc = abs(df['Close'].pct_change()) * 100
    is_burst = (df['Volume'] > v_upper) & (df['Volume'] > ma60 * 1.9) & (roc > 2.0)
    burst_colors = ['#00FFFF' if (is_burst.iloc[i] and df['Close'].iloc[i] > df['Open'].iloc[i]) else ('#FF00FF' if is_burst.iloc[i] else 'rgba(136,136,136,0.3)') for i in range(len(df))]
    fig.add_trace(go.Bar(x=dates_chart, y=df['Volume'], marker_color=burst_colors, name='能量雷達'), row=row_start+1, col=1)

    daily_change = df['Close'].pct_change() * 100
    change_colors = ['#00FF00' if val >= 0 else '#FF0000' for val in daily_change]
    fig.add_trace(go.Bar(x=dates_chart, y=daily_change, marker_color=change_colors, name='日波幅%'), row=row_start+2, col=1)

# --- 🏠 狀態管理 ---
if 'page' not in st.session_state: st.session_state.page = 'HOME'
if 'target' not in st.session_state: st.session_state.target = 'NONE'

if st.session_state.page == 'HOME':
    st.markdown("<h1 style='text-align:center;font-size:4rem;margin-top:80px;color:#FFD700;'>🐲 龍魂戰略總部</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🐉 龍魂神殿 (5.0雷達)"): st.session_state.page = 'DRAGON'
    if c2.button("📈 VCP 獵龍"): st.info("VCP 模式運作中"); st.session_state.page = 'DRAGON'
    if c3.button("🐢 海龜加注"): st.info("海龜 模式運作中"); st.session_state.page = 'DRAGON'

# --- 🐉 龍魂神殿 5.0 ---
elif st.session_state.page == 'DRAGON':
    st.markdown("<h1 style='text-align:center; color:#00FFCC;'>🐲 龍魂神殿 5.0 旗艦雷達</h1>", unsafe_allow_html=True)
    nav = st.columns(6)
    if nav[0].button("⬅️ 返回總部"): st.session_state.page = 'HOME'
    if nav[1].button("🇭🇰 港股"): st.session_state.target = 'HK'
    if nav[2].button("🇺🇸 美股"): st.session_state.target = 'US'
    if nav[3].button("📦 ETF"): st.session_state.target = 'ETF'
    if nav[4].button("🔍 個股"): st.session_state.target = 'SINGLE'
    
    st.markdown("---")
    c_ath, c_btn = st.columns([3, 1])
    with c_ath: is_ath_mode = st.checkbox("🔥 啟動 ATH 歷史新高極致過濾")
    
    sl_container = st.empty(); selected_tickers = []; market_mode = "HK"; btn_radar = False

    # 🇺🇸 美股專屬 (CSV 檔案讀取)
    if st.session_state.target == 'US':
        st.write("### 🇺🇸 選擇美股戰略名單：")
        m = st.columns(5)
        files = [("SP500_Equities.csv", "大藍籌"), ("Market_Focus.csv", "精選"), ("Industry_Focus.csv", "行業"), ("Core_Stocks.csv", "核心"), ("US_ETFs.csv", "美股ETF")]
        for i, (f, name) in enumerate(files):
            if m[i].button(f"選定 {name}"): 
                st.session_state.active_file = f
                st.success(f"✅ 已選定 {f}")
        with c_btn: btn_radar = st.button("📡 啟動 5.0 雙線雷達", use_container_width=True)

    # 🔍 個股專屬
    elif st.session_state.target == 'SINGLE':
        st.write("### 🔍 個股自訂掃描：")
        col1, col2 = st.columns([3, 1])
        with col1:
            single_t = st.text_input("輸入股票代號 (例: NVDA, 0700.HK, TSLA)", "").upper().strip()
        with col2:
            st.write("<br>", unsafe_allow_html=True)
            if st.button("📡 立即分析此股", use_container_width=True): 
                if single_t:
                    selected_tickers = [(single_t, "自選個股")]
                    btn_radar = True
                else: st.warning("請先輸入代號！")

    # 🇭🇰 港股 (實時讀取 GitHub CSV)
    elif st.session_state.target == 'HK':
        st.write("### 🇭🇰 港股板塊掃描 (雲端 600 隻實時同步)：")
        df_hk = fetch_github_list(HK_STOCK_CSV_URL)
        hk_sectors = sorted(df_hk['Sector'].dropna().unique().tolist()) if not df_hk.empty else []
        s_choice = st.selectbox("選擇範圍", ["🌐 啟動全星系大規模搜索"] + hk_sectors)
        with c_btn: btn_radar = st.button("📡 啟動 5.0 雙線雷達", use_container_width=True)

    # 📦 ETF (實時讀取 GitHub CSV)
    elif st.session_state.target == 'ETF':
        st.write("### 📦 港股/美股 ETF 掃描 (雲端 140 隻實時同步)：")
        df_etf = fetch_github_list(HK_ETF_CSV_URL)
        etf_sectors = sorted(df_etf['Sector'].dropna().unique().tolist()) if not df_etf.empty else []
        s_choice = st.selectbox("選擇範圍", ["🌐 啟動全星系大規模搜索"] + etf_sectors + list(US_ETF_MAP.keys()))
        with c_btn: btn_radar = st.button("📡 啟動 5.0 雙線雷達", use_container_width=True)

    # ==========================================
    # 🚀 執行 5.0 雷達邏輯
    # ==========================================
    if btn_radar:
        if st.session_state.target == 'SINGLE':
            market_mode = "US" if not selected_tickers[0][0].endswith(".HK") else "HK"
        
        elif st.session_state.target == 'US' and hasattr(st.session_state, 'active_file'):
            try:
                df_csv = pd.read_csv(st.session_state.active_file)
                col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol', '代號']][0]
                selected_tickers = [(t, "美股戰略") for t in df_csv[col].dropna().unique()]
                market_mode = "US"
            except: st.error("讀取 CSV 失敗，請檢查檔案是否存在。")
        
        elif st.session_state.target == 'HK':
            df_hk = fetch_github_list(HK_STOCK_CSV_URL)
            if not df_hk.empty:
                if "全星系" in s_choice:
                    selected_tickers = list(df_hk.itertuples(index=False, name=None))
                else:
                    selected_tickers = list(df_hk[df_hk['Sector'] == s_choice].itertuples(index=False, name=None))
            market_mode = "HK"
            
        elif st.session_state.target == 'ETF':
            df_etf = fetch_github_list(HK_ETF_CSV_URL)
            raw_list = []
            if "全星系" in s_choice:
                if not df_etf.empty:
                    raw_list.extend(list(df_etf.itertuples(index=False, name=None)))
                for k, v in US_ETF_MAP.items():
                    sec = k.split('.')[1].strip() if '.' in k else k
                    for t in v: raw_list.append((t, sec))
                selected_tickers = raw_list
                market_mode = "HK"
            else:
                if s_choice in US_ETF_MAP:
                    selected_tickers = [(t, s_choice) for t in US_ETF_MAP[s_choice]]
                    market_mode = "US"
                else:
                    selected_tickers = list(df_etf[df_etf['Sector'] == s_choice].itertuples(index=False, name=None))
                    market_mode = "HK"

        # --- 啟動掃描引擎 ---
        if selected_tickers:
            st.info(f"🚀 5.0 引擎掃描中 ({len(selected_tickers)} 隻)...")
            results = []; sl_list = []; pb = st.progress(0)
            is_single_mode = (st.session_state.target == 'SINGLE')
            
            for i, (t, sec) in enumerate(selected_tickers):
                pb.progress((i+1)/len(selected_tickers))
                df = smart_fetch(t)
                if not df.empty:
                    if is_ath_mode and (df['Close'].iloc[-1] / df['High'].tail(252).max()) < 0.93: 
                        if not is_single_mode: continue
                    if check_stop_loss(df): sl_list.append(t)
                    
                    res = scan_dragon_logic(df, t, sec, market_mode, force_return=is_single_mode)
                    if res: results.append(res)
            
            if sl_list: sl_container.markdown(f"<div class='bear-warning'>🛡️ 戰損置頂: {' | '.join(sl_list)} 跌穿 10-EMA！</div>", unsafe_allow_html=True)
            
            if results:
                # ==========================================
                # 📊 啟動板塊聯動 
                # ==========================================
                sector_counts = {}
                for r in results:
                    if not r.get('IsDead'):
                        sec = r['Sector']
                        sector_counts[sec] = sector_counts.get(sec, 0) + 1
                
                results = sorted(results, key=lambda x: x['Score'], reverse=True)
                st.session_state.dragon_results = results
                
                for r in results:
                    # 分發 📊 勳章 (同板塊 >= 3 隻過關即中！)
                    if not r.get('IsDead') and sector_counts.get(r['Sector'], 0) >= 3:
                        if "📊" not in r['Icons']:
                            r['Icons'] += " 📊"
                            
                    border_color = "#FF4B4B" if r.get('IsDead') else "#00FFCC"
                    st.markdown(f"""
                    <div class='dragon-card' style='border-left: 5px solid {border_color};'>
                        <div style='font-size:1.4rem;font-weight:bold;'>{r['Status']} {r['Ticker']} <span style='color:#00FFCC;'>({r['Sector']})</span> {r['Icons']}</div>
                        <div class='data-row'>
                            <b>戰術總分: {r['Score']}分</b> | 
                            <b style='color:#FF9900;'>原始戰力: {r.get('RawPower', 0)} 🔥</b> | 
                            <b style='color:#FF4B4B;'>扣分: {r.get('Penalty', 0)} 🛑</b> | 
                            <span style='color:#FF4B4B; font-weight:bold;'>🛑 止損(10-EMA): ${r['EMA10']}</span> | Bias: {r['Bias']}%<br>
                            📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 🔥 買盤力: {r['Power']}x
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if is_single_mode:
                    st.session_state.force_chart_ticker = selected_tickers[0][0]
            else: 
                if not is_single_mode: st.warning("💤 萬人坑內無生還者。")

    # =========================================================
    # 📈 X 光戰術圖
    # =========================================================
    chart_t = None
    if hasattr(st.session_state, 'dragon_results') and len(st.session_state.dragon_results) > 0:
        st.write("---")
        chart_t = st.selectbox("🎯 查看 X 光戰術圖", [r['Ticker'] for r in st.session_state.dragon_results])
    elif st.session_state.target == 'SINGLE' and hasattr(st.session_state, 'force_chart_ticker'):
        chart_t = st.session_state.force_chart_ticker

    if chart_t:
        with st.spinner("正在繪製全黑戰術圖表..."):
            try:
                df_c = smart_fetch(chart_t, period="6mo")
                if not df_c.empty:
                    ema10 = df_c['Close'].ewm(span=10, adjust=False).mean()
                    dates_chart = df_c.index.strftime('%Y-%m-%d').tolist()
                    
                    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.15, 0.1], vertical_spacing=0.02)
                    
                    fig.add_trace(go.Candlestick(x=dates_chart, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates_chart, y=df_c['Close'].rolling(50).mean(), mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates_chart, y=ema10, name="10 EMA", line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                    
                    recent_high = df_c['High'].tail(20).max()
                    fig.add_hline(y=recent_high, line_dash="dash", line_color="#00FFCC", annotation_text=f"🎯 買入點: ${recent_high:.2f}", annotation_position="top right", annotation_font=dict(color="white", size=13), row=1, col=1)
                    
                    counts, bins = np.histogram(df_c['Close'], bins=30, weights=df_c['Volume'])
                    max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                    hvn_p = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                    stop_loss = hvn_p * 0.985
                    fig.add_hline(y=stop_loss, line_dash="solid", line_color="#FF4B4B", annotation_text=f"🛑 重貨止損: ${stop_loss:.2f}", annotation_position="bottom right", annotation_font=dict(color="white", size=13), row=1, col=1)
                    
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136,136,136,0.4)', name='重貨區', hoverinfo='skip', xaxis='x6', yaxis='y1'))

                    v_colors = ['#00FF00' if df_c['Close'].iloc[i] >= df_c['Open'].iloc[i] else '#FF0000' for i in range(len(df_c))]
                    fig.add_trace(go.Bar(x=dates_chart, y=df_c['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    
                    df_c['Vol50'] = df_c['Volume'].rolling(50).mean()
                    stars = df_c[(df_c['Close'] > df_c['Open']) & (df_c['Volume'] > df_c['Vol50'] * 1.5)]
                    if not stars.empty:
                        star_dates = stars.index.strftime('%Y-%m-%d').tolist()
                        fig.add_trace(go.Scatter(x=star_dates, y=stars['Volume'], mode='markers', marker=dict(symbol='star', size=14, color='#FFD700'), name='大戶星星'), row=2, col=1)

                    add_energy_subplots(fig, df_c, dates_chart, row_start=3)
                    
                    fig.update_layout(
                        template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111111', height=950, barmode='overlay', 
                        showlegend=False, hovermode='x unified',
                        xaxis_rangeslider_visible=False,
                        xaxis6=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*1.1], showgrid=False, showticklabels=False), 
                        xaxis=dict(type='category', showticklabels=False), xaxis5=dict(type='category', title="日期")
                    )
                    st.plotly_chart(fig, use_container_width=True, theme=None)
            except Exception as e: st.error(f"繪圖出錯: {e}")
