import streamlit as st 
import yfinance as yf 
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go 
from plotly.subplots import make_subplots 

# 1. 基礎設置 
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

# 🚀 爺爺還原：Beta、Alpha、波動率計算引擎
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
        # 🚀 爺爺優化：Alpha 限制顯示位數
        return f"{alpha * 100:.1f}%"
    except: return "N/A"

def get_volatility(df):
    try:
        ret = df['Close'].pct_change().dropna().tail(252)
        vol = ret.std() * np.sqrt(252)
        return f"{vol * 100:.1f}%"
    except: return "N/A"

# 🚀 爺爺新增：隱含波動率 (IV) 提取器
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

# =========================================================================
# 🛸 爺爺嘅外掛資料庫 (完全保留一條毛都冇改)
# =========================================================================
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
    "15. 傳統中西藥業": "1093.HK 1177.HK 1515.HK 0511.HK 2666.HK 3320.HK 2196.HK 0867.HK 1099.HK 0460.HK 0853.HK 1513.HK 3933.HK 1528.HK 1513.HK 2005.HK".split(),
    "16. 澳門博彩": "1928.HK 0027.HK 1128.HK 0880.HK 0200.HK 0037.HK 1628.HK 0576.HK 3918.HK 1180.HK 0256.HK".split(),
    "17. 體育與服裝": "2020.HK 2331.HK 1368.HK 3813.HK 6110.HK 0551.HK 1910.HK 3998.HK 2238.HK 2999.HK 1968.HK 1361.HK 3306.HK 0411.HK 0484.HK 1999.HK".split(),
    "18. 海運航運物流": "1919.HK 1308.HK 2343.HK 2600.HK 0591.HK 1519.HK 1101.HK 2866.HK 0316.HK 0598.HK 0368.HK".split(),
    "19. 電訊與網絡": "0941.HK 0728.HK 0762.HK 1883.HK 6823.HK 6033.HK 0008.HK 0215.HK 1098.HK 0066.HK 0116.HK".split(),
    "20. 公用與基礎建設": "0002.HK 1038.HK 0066.HK 1186.HK 0390.HK 1800.HK 0270.HK 3311.HK 1618.HK 1083.HK 0371.HK 0165.HK 0250.HK".split(),
    "21. 農業與食品供應": "2319.HK 1610.HK 1117.HK 1431.HK 0061.HK 0220.HK 0341.HK 3998.HK 1089.HK 1269.HK 1006.HK".split(),
    "22. 券商與保險": "3908.HK 6030.HK 6881.HK 1299.HK 2628.HK 2318.HK 0966.HK 1336.HK 6099.HK 1776.HK 6178.HK 3968.HK 1551.HK 6066.HK 1339.HK".split()
}

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

HK_ETF_MAP = {"E1. 港股大盤與科指": "2800.HK 2828.HK 3032.HK 3033.HK 3067.HK 3147.HK 2812.HK 3058.HK 3068.HK 3428.HK 3134.HK 3115.HK 3046.HK".split()}
US_ETF_MAP = {"E1. 大盤/寬基/信用債": "SPY QQQ DIA IWM VOO IVV VTI RSP QQQM ONEQ VUG VTV IWD IWF TLT AGG BND LQD HYG IEF SHY MBB MUB JNK TIP IGOV EMB GOVT".split()}

@st.cache_data(ttl=3600)
def get_breadth_data(tickers):
    stats = {'20MA':0, '50MA':0, '150MA':0, '200MA':0, 'valid':0, 'above_50_list': []}
    if not tickers: 
        stats['valid'] = 1
        return stats
        
    for t in tickers:
        try:
            c = yf.Ticker(t).history(period="1y")['Close'].dropna()
            if len(c) < 50: continue
            
            curr = c.iloc[-1]
            if curr > c.tail(20).mean(): stats['20MA'] += 1
            if curr > c.tail(50).mean(): 
                stats['50MA'] += 1
                stats['above_50_list'].append(t)
            if len(c) >= 150 and curr > c.tail(150).mean(): stats['150MA'] += 1
            if len(c) >= 200 and curr > c.tail(200).mean(): stats['200MA'] += 1
            stats['valid'] += 1
        except: 
            pass
            
    stats['valid'] = max(1, stats['valid'])
    return stats

# 2. 視覺裝修 
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
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
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; min-height: 220px; margin-bottom: 15px; }
    .val-label { color: #FFFFFF !important; font-size: 1.4rem; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 12px; }
    .val-text { font-size: 1.2rem; color: #ccc; margin: 6px 0; }
    .val-focus { color: #FFD700; font-weight: bold; font-size: 1.6rem; }
    .red-bar { background-color: #FF4B4B; color: #fff; padding: 20px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 2.2rem; margin: 30px 0; border: 3px solid #fff; }
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
st.sidebar.markdown("## 🛰️ 戰術控制台 (V119.0 神之八磚版)")
app_mode = st.sidebar.radio("請選擇操作", [
    "🚀 個股深度透視", 
    "🛡️ 環球市底大師指揮塔", 
    "📡 個股版塊拔河熱力圖", 
    "📡 ETF 資產拔河熱力圖", 
    "🔍 千龍起步尋龍雷達 (個股)",
    "🛡️ 美股 ETF 專屬雷達",
    "🛡️ 港/A股 ETF 專屬雷達"
])

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
    
    HSI_71 = (HK_STOCK_MAP["1. 互聯網巨頭"] + HK_STOCK_MAP["5. 國有大行與金融"] + HK_STOCK_MAP["10. 房地產開發"] + HK_STOCK_MAP["13. 核心消費與餐飲"])[:71]
    TECH_30 = (HK_STOCK_MAP["1. 互聯網巨頭"] + HK_STOCK_MAP["2. 半導體與芯片"] + HK_STOCK_MAP["12. 消費電子硬件"])[:30]
    DOW_30 = "AAPL MSFT UNH JNJ XOM JPM V PG HD CVX MRK KO ABBV BAC AVGO PEP TMO COST CSCO MCD CRM DIS LIN ABT ACN AMD WFC NFLX INTC CAT".split()
    SPX_80 = (DOW_30 + US_STOCK_MAP["2. AI與大數據雲端"] + US_STOCK_MAP["11. 核心消費品"] + US_STOCK_MAP["22. 商業銀行巨頭"])[:80]
    NDX_43 = (US_STOCK_MAP["2. AI與大數據雲端"] + US_STOCK_MAP["1. 半導體設備與設計"] + US_STOCK_MAP["6. 通訊與網絡設備"])[:43]
    IWM_32 = (US_STOCK_MAP["49. 小型爆發精選"] + US_STOCK_MAP["50. 超微型探索 (Micro)"])[:32]

    if "恒指" in idx_choice: ticker_sym = "2800.HK"; b_tickers = HSI_71 
    elif "科指" in idx_choice: ticker_sym = "3032.HK"; b_tickers = TECH_30
    elif "道指" in idx_choice: ticker_sym = "DIA"; b_tickers = DOW_30
    elif "標指" in idx_choice: ticker_sym = "SPY"; b_tickers = SPX_80
    elif "納市" in idx_choice: ticker_sym = "QQQ"; b_tickers = NDX_43
    else: ticker_sym = "IWM"; b_tickers = IWM_32

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
                    st.markdown(f"<h3 style='color: white;'>🏆 逆市名單 ({idx_choice.split(' ')[0]}) - 企穩 50天線之上</h3>", unsafe_allow_html=True)
                    cols = st.columns(6)
                    for i, t in enumerate(b_stats['above_50_list'][:30]):
                        cols[i % 6].info(t)
        except Exception as e: st.error(f"⚠️ 數據載入失敗：{e}")

# =========================================================================
# 🚀 模式 A：個股深度透視 
# =========================================================================
elif app_mode == "🚀 個股深度透視":
    ticker = st.sidebar.text_input("🚀 輸入資產代號", "6869.HK").upper()
    
    # 🚀 爺爺修改：側邊欄 X-Factor Slider (輸入端)
    st.sidebar.markdown("---")
    st.sidebar.header("🎭 投行定性打分")
    s10_mgmt = st.sidebar.slider("10. 靈魂人物溢價 (CEO/執行力)", 0, 100, 70)
    s11_story = st.sidebar.slider("11. 時代敘事溢價 (AI/政策風口)", 0, 100, 80)
    x_factor = st.sidebar.selectbox("🕵️‍♂️ 投行隱藏 X 因子", ["無特殊狀況", "跨界第二曲線 (+10分)", "自動印鈔機護城河 (+5分)", "隱形吸血鬼SBC (-15分)"])

    with st.spinner(f"⏳ 系統正在切換引擎，重新下載海量數據..."):
        try:
            asset = yf.Ticker(ticker); info = asset.info
            df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
            spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
            
            if not df.empty:
                df['50MA'] = df['Close'].rolling(50).mean().bfill()
                if df.index.tz is not None: df.index = df.index.tz_localize(None)
                df.index = df.index.normalize()
                curr_p = df['Close'].iloc[-1]
                
                # 🚀 爺爺修改：行業標籤與頂部顯示
                industry = info.get('industry', '未知行業')
                sector = info.get('sector', '未知板塊')
                asset_name = info.get('shortName', info.get('longName', ''))
                st.markdown(f"<h1 class='main-title' style='margin-bottom:5px;'>環球資產透維評估儀 [{ticker}]</h1>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center; color:#AAA; font-size:1.5rem; margin-bottom:20px;'>{asset_name} | {sector} - {industry}</div>", unsafe_allow_html=True)
                
                # 🚀 爺爺修改：取代 redundant 紅色 Bar，顯示攻防數據
                ath_val = info.get('fiftyTwoWeekHigh', curr_p)
                dist_ath = ((curr_p / ath_val) - 1) * 100 if ath_val > 0 else 0
                ma50_bias = ((curr_p / df['50MA'].iloc[-1]) - 1) * 100
                
                st.markdown(f"""
                <div style='display: flex; gap: 15px; margin-bottom: 25px;'>
                    <div class='red-bar' style='flex: 1; background-color: #310000; border: 2px solid #FF4B4B;'>🎯 巔峰收復進度：距離 52周高位 [ {dist_ath:.1f}% ]</div>
                    <div class='red-bar' style='flex: 1; background-color: #002222; border: 2px solid #00FFCC;'>⚖️ 地心引力監控：偏離 50日成本線 [ {ma50_bias:+.1f}% ]</div>
                </div>
                """, unsafe_allow_html=True)

                # 🚀 爺爺修改：圖表恢復放大與軸線標籤
                recent = df.tail(120).copy()
                dates = recent.index.strftime('%Y-%m-%d')
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Candlestick(x=dates, open=recent['Open'], high=recent['High'], low=recent['Low'], close=recent['Close'], name='股價'), row=1, col=1)
                fig.update_layout(
                    template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=600,
                    xaxis=dict(showticklabels=True, tickfont=dict(color='white'), type='category', title="日期"),
                    yaxis=dict(showticklabels=True, tickfont=dict(color='white'), title="股價 (USD)"),
                    xaxis_rangeslider_visible=False
                )
                st.plotly_chart(fig, use_container_width=True, theme=None, config={'displayModeBar': True}) # 開啟右上角 Toolbar

                # --- DNA 區塊 ---
                st.write("---"); d_c1, d_c2 = st.columns([1, 2.5]); is_etf = info.get('quoteType') == 'ETF'; real_roe = info.get('returnOnEquity')
                
                # 計算 DNA 與 Bar (補上 % 標籤)
                cej_s = safe_n((df['Volume'].tail(21).mean() / max(df['Volume'].tail(252).mean(), 1)) * 100, 50.0)
                spy_aligned = spy['Close'].reindex(df.index).ffill().bfill() 
                crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy_aligned.iloc[-1] / spy_aligned.iloc[-63])) * 100, 50.0) if len(df) > 63 else 50.0
                se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0) if len(df) > 5 else 50.0
                c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
                slope, _ = np.polyfit(days, c_tail, 1); v_ann_num = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
                cx_val = safe_n(((slope * 252) / c_tail.mean() / v_ann_num) * 29, 50.0)

                if is_etf or real_roe is None or real_roe == 0:
                    dna_v = round(safe_n((cx_val * 0.5) + (crs_val * 0.5), 50.0), 1); dna_title = "ETF 綜合質量基因"
                    m9 = {"🚀 增長加速度 (15%)": int(cx_val/10), "🔭 營收天花板 (15%)": int(crs_val/10), "🛡️ 定價權護城河 (15%)": int(cej_s/10), "🦖 市場佔有率 (15%)": 8, "💰 資本效率 (10%)": 7, "💎 獲利含金量 (10%)": 6, "🧱 財務安全墊 (10%)": 8, "🎁 股東回饋 (5%)": 5, "📈 經營穩定性 (5%)": 7}
                else:
                    f1_growth = min(100, max(0, safe_n(info.get('earningsGrowth', 0)) * 200 + 40))
                    f2_rev = min(100, max(0, safe_n(info.get('revenueGrowth', 0)) * 150 + 40))
                    f3_moat = min(100, max(0, safe_n(info.get('profitMargins', 0)) * 300 + 30))
                    f5_roe = min(100, max(0, safe_n(info.get('returnOnEquity', 0)) * 300 + 30))
                    dna_v = round((f1_growth*0.2 + f2_rev*0.2 + f3_moat*0.2 + f5_roe*0.4), 1)
                    dna_title = "投行級股王基因"
                    m9 = {"🚀 增長加速度 (15%)": int(f1_growth/10), "🔭 營收天花板 (15%)": int(f2_rev/10), "🛡️ 定價權護城河 (15%)": int(f3_moat/10), "🦖 市場佔有率 (15%)": 8, "💰 資本效率 (10%)": int(f5_roe/10), "💎 獲利含金量 (10%)": 7, "🧱 財務安全墊 (10%)": 8, "🎁 股東回饋 (5%)": 6, "📈 經營穩定性 (5%)": 7}

                with d_c1: st.markdown(f"<div class='cosmos-box' style='height:440px;'><div style='color:#FF4B4B; font-weight:900; font-size:1.8rem;'>🧬 COSMOS-DNA</div><div style='font-size:0.9rem; opacity:0.7;'>{dna_title}</div><div style='font-size:6rem; font-weight:900;'>{dna_v}</div></div>", unsafe_allow_html=True)
                with d_c2:
                    for l, s in m9.items():
                        sc = max(1, min(10, s)); grid = '<div class="energy-bar-container-8d">' + "".join([f'<div class="energy-seg-8d" style="background-color:#00FFCC; opacity:{"1" if j<=sc else "0.1"};"></div>' for j in range(1,11)]) + '</div>'
                        st.markdown(f"<div style='display:flex; justify-content:space-between; font-weight:bold;'><span>{l}</span><span>{sc}/10</span></div>{grid}", unsafe_allow_html=True)

                # 🚀 爺爺修改：Forward Price 估值指揮部 (DNA 下方)
                st.write("---")
                f_eps = info.get('forwardEps')
                t_eps = info.get('trailingEps', 0.01)
                if not f_eps:
                    f_pe = info.get('forwardPE')
                    if f_pe: f_eps = curr_p / f_pe
                    else: f_eps = t_eps * (1 + (dna_v/100))
                
                # 自動 PE 邏輯
                g_score = m9.get("🚀 增長加速度 (15%)", 5)
                fair_pe = 35 if g_score >= 9 else (25 if g_score >= 7 else 18)
                forward_price = f_eps * fair_pe
                price_diff = ((forward_price - curr_p) / curr_p) * 100
                
                # 真龍指數 (DNA 70% + X-Factor 30%)
                dragon_index = round((dna_v * 0.7) + (s10_mgmt * 0.15) + (s11_story * 0.15), 1)
                if "第二曲線" in x_factor: dragon_index += 10
                elif "印鈔機" in x_factor: dragon_index += 5
                elif "吸血鬼" in x_factor: dragon_index -= 15

                vc1, vc2, vc3 = st.columns(3)
                with vc1:
                    st.markdown(f"""<div class='val-box-purple' style='height:300px;'><div class='val-label'>🎯 遠期目標價 (預測)</div><div style='font-size:3.5rem; font-weight:900; color:#00FFCC;'>${forward_price:,.2f}</div><div style='font-size:1.2rem;'>空間: <span style='color:#00FFCC;'>{price_diff:+.1f}%</span></div><div style='font-size:0.9rem; margin-top:15px; opacity:0.8;'>TTM EPS: ${t_eps:.2f} | Forward: ${f_eps:.2f}</div></div>""", unsafe_allow_html=True)
                with vc2:
                    st.markdown(f"""<div class='val-box-purple' style='border-color:#FFD700; height:300px;'><div class='val-label'>🏆 真龍指數 (全維評分)</div><div style='font-size:5rem; font-weight:900; color:#FFD700;'>{dragon_index}</div><div style='font-size:1.1rem;'>狀態: {'極致真龍' if dragon_index>=80 else '潛力金龍' if dragon_index>=65 else '中庸凡骨'}</div></div>""", unsafe_allow_html=True)
                with vc3:
                    st.markdown(f"""<div class='val-box-purple' style='border-color:#00FFFF; height:300px;'><div class='val-label'>🎭 時代敘事與決策</div><div style='font-size:1.5rem; font-weight:bold;'>{x_factor}</div><p style='color:#00FFFF; margin-top:10px;'>溢價信心: {s11_story}%</p><div style='background:#111; padding:10px; border-radius:5px; margin-top:10px;'>{'【順勢重倉】' if dragon_index>=80 else '【分批佈局】' if dragon_index>=65 else '【觀望為上】'}</div></div>""", unsafe_allow_html=True)

                # --- 戰略透視 Grid ---
                v1,v2,v3,v4,v5,v6 = st.columns(6); v7,v8,v9 = st.columns(3)
                v_card = lambda col, t, t_v, f_v: col.markdown(f"<div class='val-box'><div class='val-label'>{t}</div><div class='val-text'>{t_v}</div><div class='val-focus'>{f_v}</div></div>", unsafe_allow_html=True)
                
                v_card(v1, "PE 獲利比", f"TTM: {safe_s(info, ['trailingPE'])}x", f"Fwd: {safe_s(info, ['forwardPE'])}x")
                v_card(v2, "PEG 比率", "增長性價比", safe_s(info, ['pegRatio']))
                v_card(v3, "PS 營收比", "營收估值", safe_s(info, ['priceToSalesTrailing12Months'], "x"))
                v_card(v4, "PB 淨資產", "賬面價值", safe_s(info, ['priceToBook'], "x"))
                v_card(v5, "EV/EBITDA", "企業倍數", safe_s(info, ['enterpriseToEbitda'], "x"))
                v_card(v6, "股息率", "現金回報", safe_s(info, ['dividendYield', 'yield'], "%"))
                
                v_card(v7, "Beta 敏感度", "對大盤聯動性", get_beta(info, df, spy))
                v_card(v8, "@ (Alpha) 表現", "大盤外超額回報", get_alpha(get_beta(info, df, spy), df, spy))
                
                # 🚀 爺爺修改：波動率雙併 HV + IV
                hv = get_volatility(df)
                iv = get_iv(asset)
                v9.markdown(f"""<div class='val-box'><div class='val-label'>🌪️ 波動率雙併 (Risk)</div><div class='val-text'>年化波動 (HV): <span class='val-focus'>{hv}</span></div><div class='val-text'>隱含波動 (IV): <span class='val-focus'>{iv}</span></div></div>""", unsafe_allow_html=True)

                st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center;'>🧙 90 大名家：真實申報持倉</div>", unsafe_allow_html=True)
                holders = asset.institutional_holders
                if holders is not None and not holders.empty:
                    for _, row in holders.head(6).iterrows():
                        st.markdown(f"<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>{row.get('Value', 0)/1e6:.1f}M USD</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e: st.error(f"數據載入失敗：{e}")

# =========================================================================
# 其餘模式 (熱力圖 / 雷達) - 爺爺保證：一條毛都冇改！
# =========================================================================
elif "雷達" in app_mode and not "熱力圖" in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    if app_mode == "🔍 千龍起步尋龍雷達 (個股)":
        m_choice = st.sidebar.radio("1. 選擇個股市場", ["🇺🇸 美股市場", "🇭🇰 港股市場"])
        is_us = "美股" in m_choice
    else: is_us = "美股" in app_mode
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
        if not found: st.warning("💤 雷達掃描完畢，目前未有起飛目標。")

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
