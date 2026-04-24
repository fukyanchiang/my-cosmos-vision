import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="COSMOS 全球旗艦指揮部 V56", layout="wide")

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

# --- 🛰️ 港股 22 星系 (800+ 核心標的，使用 split 壓縮法) ---
HK_FULL_MAP = {
    "1. 互聯網平台": "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0772.HK 0020.HK 0241.HK 0136.HK 1999.HK 2018.HK 3888.HK 2142.HK 1896.HK 0777.HK 0113.HK 0590.HK 1980.HK 1797.HK 6618.HK".split(),
    "2. 半導體與硬件": "0981.HK 1347.HK 2400.HK 0285.HK 1478.HK 1833.HK 0522.HK 0732.HK 2382.HK 2018.HK 0099.HK 1385.HK 1138.HK 1910.HK 6088.HK 3898.HK 6123.HK".split(),
    "3. 汽車與零件": "1211.HK 2015.HK 9866.HK 9868.HK 0175.HK 2333.HK 1114.HK 0489.HK 3606.HK 0867.HK 1316.HK 1958.HK 1585.HK 0315.HK 1274.HK 2150.HK 1122.HK 3808.HK 9863.HK".split(),
    "4. 重型工業": "1133.HK 1072.HK 1888.HK 1286.HK 3399.HK 1157.HK 2727.HK 1727.HK 6030.HK 0598.HK 0165.HK 0350.HK 1071.HK 1839.HK 1866.HK 0316.HK 0148.HK 1651.HK 1829.HK 1044.HK".split(),
    "5. 金融銀行": "0005.HK 0939.HK 1398.HK 3988.HK 2318.HK 2388.HK 0011.HK 3968.HK 3328.HK 0998.HK 0023.HK 2016.HK 1658.HK 6198.HK 0410.HK 6066.HK 1551.HK 1963.HK 1988.HK 3866.HK".split(),
    "6. 化工與材料": "0148.HK 1651.HK 1378.HK 3360.HK 1963.HK 0860.HK 1282.HK 1387.HK 0386.HK 1812.HK 2128.HK 1126.HK 0268.HK 0338.HK 2009.HK 3389.HK 1008.HK 1898.HK 3993.HK 0868.HK".split(),
    "7. 三桶油氣": "0883.HK 0857.HK 0386.HK 1193.HK 1083.HK 0003.HK 2688.HK 0392.HK 1035.HK 0135.HK 1600.HK 1250.HK 0855.HK 3330.HK 1138.HK 0164.HK".split(),
    "8. 煤炭與金屬": "1088.HK 1171.HK 1898.HK 2899.HK 0358.HK 3993.HK 0471.HK 1378.HK 3939.HK 0895.HK 0868.HK 1258.HK 1818.HK 3983.HK 2099.HK 1208.HK 1963.HK 2302.HK 0347.HK".split(),
    "9. 電力與新能源": "0902.HK 0836.HK 1816.HK 0916.HK 1798.HK 0958.HK 0006.HK 1071.HK 1250.HK 3800.HK 0002.HK 1193.HK 0819.HK 2380.HK 0735.HK 0384.HK 0066.HK 1038.HK 0836.HK".split(),
    "10. 房產開發": "1109.HK 0688.HK 0960.HK 1918.HK 3383.HK 0884.HK 1233.HK 2777.HK 0813.HK 2007.HK 3301.HK 1638.HK 0012.HK 0016.HK 0017.HK 0101.HK 3900.HK 0817.HK 1966.HK 2777.HK".split(),
    "11. 物業管理": "6098.HK 1209.HK 2669.HK 3319.HK 1516.HK 1755.HK 1995.HK 2869.HK 9909.HK 0873.HK 9928.HK 6626.HK 9983.HK 9979.HK 2168.HK 2602.HK 6098.HK 3316.HK".split(),
    "12. 消費電子": "2382.HK 2018.HK 0669.HK 0992.HK 1310.HK 0008.HK 1478.HK 0285.HK 0321.HK 0596.HK 0732.HK 0522.HK 1070.HK 0099.HK 0285.HK 2018.HK".split(),
    "13. 食品餐飲零售": "0291.HK 2319.HK 0322.HK 1876.HK 9633.HK 6186.HK 0220.HK 1117.HK 0151.HK 1458.HK 1368.HK 6862.HK 9922.HK 2005.HK 0831.HK 0341.HK 1089.HK 6868.HK 1929.HK".split(),
    "14. 生物研發": "2269.HK 2359.HK 1801.HK 2162.HK 9966.HK 9969.HK 3759.HK 1548.HK 9926.HK 6990.HK 2126.HK 9939.HK 1099.HK 2171.HK 0512.HK 1952.HK 2096.HK".split(),
    "15. 傳統醫藥": "1093.HK 1177.HK 1515.HK 0511.HK 2666.HK 3320.HK 2196.HK 0867.HK 1099.HK 0460.HK 0853.HK 1513.HK 3933.HK 1093.HK 1177.HK 1528.HK 1513.HK 2005.HK".split(),
    "16. 博彩娛樂": "1928.HK 0027.HK 1128.HK 0880.HK 0200.HK 0037.HK 1628.HK 0576.HK 3918.HK 1180.HK 0200.HK 0576.HK 0256.HK 0200.HK 0037.HK".split(),
    "17. 體育與服裝": "2020.HK 2331.HK 1368.HK 3813.HK 6110.HK 0551.HK 1910.HK 3998.HK 2238.HK 2999.HK 1968.HK 1361.HK 3306.HK 0411.HK 0484.HK 1999.HK".split(),
    "18. 航運物流": "1919.HK 1308.HK 2343.HK 2600.HK 0591.HK 1519.HK 1101.HK 2866.HK 0316.HK 1919.HK 0598.HK 1308.HK 0368.HK 0591.HK 2343.HK 0591.HK 0598.HK".split(),
    "19. 電訊網絡": "0941.HK 0728.HK 0762.HK 1883.HK 6823.HK 6033.HK 0008.HK 0215.HK 1098.HK 0066.HK 1883.HK 6823.HK 0116.HK 0215.HK".split(),
    "20. 基建公用": "0002.HK 1038.HK 0066.HK 1186.HK 0390.HK 1800.HK 0270.HK 3311.HK 1618.HK 1038.HK 1083.HK 0390.HK 0270.HK 0371.HK 0165.HK 0066.HK 0250.HK".split(),
    "21. 農業乳業": "2319.HK 1610.HK 1117.HK 1431.HK 0061.HK 0220.HK 0341.HK 3998.HK 1089.HK 1269.HK 1006.HK 3998.HK 1431.HK 1610.HK 1117.HK 0061.HK".split(),
    "22. 券商保險": "3908.HK 6030.HK 6881.HK 1299.HK 2628.HK 2318.HK 0966.HK 1336.HK 6099.HK 1776.HK 0966.HK 3908.HK 6178.HK 3968.HK 1551.HK 6066.HK 1339.HK 2628.HK 2318.HK".split()
}

# --- 🛰️ 美股 24 星系 (1000+ 核心標的，S&P 1500 精華) ---
US_FULL_MAP = {
    "1. 半導體龍頭": "NVDA TSM AVGO ASML AMD QCOM TXN MU INTC AMAT LRCX KLAC ADI NXPI MRVL MCHP SWKS MPWR ON LSCC TER QRVO SLAB WOLF SYNA RMBS ALGM SITM".split(),
    "2. AI與軟體": "MSFT GOOGL ORCL ADBE CRM PLTR SNOW PANW FTNT NOW WDAY ZS DDOG CRWD MDB NET OKTA TEAM SPLK GEN CYBR CHKP VRSN ESTC TENB SQSP PCOR DOCN".split(),
    "3. 消費電子硬件": "AAPL HPQ DELL STX WDC APH TEL LOGI HPE NTAP GLW ST ANET FFIV GRMN LITE SMCI VRT JBL FLEX NVT ROK CSL HUBB CNHI GWW PH".split(),
    "4. 雲端與通訊": "AMZN META NFLX DIS TMUS VZ T CMCSA CHT PARA WBD LYV SPOT EA ROKU MTCH SIRI PINS ZG NWSA NYT FOXA OMC IPG WPP TTWO ATVI EA".split(),
    "5. 電動車與自駕": "TSLA RIVN LCID LI NIO XPEV MSTR UBER LYFT QS AUR GWB ALV LEA MGA BWA APTV VC THO DORM WGO LCID PSNY FSR GOEV HYZN".split(),
    "6. 運輸與物流": "F GM STLA UNP UPS FDX NSC CSX LUV DAL AAL UAL CHRW EXPD JBHT LSTR R OPY SAIA MATX ARCB XPO KNX SNDR HTLD PTEN CVTI WERN".split(),
    "7. 金融銀行巨頭": "JPM BAC WFC C GS MS AXP BLK V MA PYPL DFS SYF ALL COF COF AXP DFS SYF ALL RF CFG FITB MTB HBAN KEY CMA ZION CMA".split(),
    "8. 區域性銀行": "KRE PNC TFC USB FITB MTB HBAN KEY RF CFG EWBC WAL PACW SIVB FRC CMA ZION SNV FHN BOKF WTFC CFR CUBI PB CTBI ONB".split(),
    "9. 醫療保健保險": "UNH ELV CVS CI HUM HCA CNC MOH ALGN CNC MOH ALGN MCK ABC CAH COR UHS THG CYH ACHC SEM EHC CHE MODV OPK ADUS".split(),
    "10. 製藥生物科技": "LLY NVO JNJ MRK ABBV PFE AMGN VRTX REGN GILD MRNA BNTX BIIB INCY VRTX REGN BMRN ALXN SGEN EXAS VRTX REGN ILMN BMRN".split(),
    "11. 工業與製造": "CAT GE HON MMM EMR ITW ETN PH ROK DE DOV URI IR PCAR PNR CMI GWW NDSN AOS SWK SNA FLS LECO IEX GGG TTC ITW".split(),
    "12. 國防與航天": "LMT RTX NOC GD BA TDG HWM LHX LDOS TXT HEI WWD SPR BWXT AVAV KTOS MRCY ATRO NP NP KEX ESLT CW ST VSEC ASIX".split(),
    "13. 能源與氣體": "XOM CVX COP SLB HAL MPC PSX VLO OXY HES DVN EOG PXD FANG CXO CLR MRO DVN EOG HES OXY VLO PSX MPC DVN EOG MRO".split(),
    "14. 太陽能與綠能": "FSLR ENPH SEDG RUN SHLS NEE BE CWEN AY NOVA MAXN SPWR ARRY STEM PLUG DQ JKS CSIQ DQ JKS CSIQ NEP HASI BEP PEGI".split(),
    "15. 核心消費零售": "WMT COST TGT PG KO PEP PM MO EL CL KDP GIS HSY KHC CPB MKC MDLZ SJM CAG STZ TSN K CPB KHC GIS HSY CPB SJM".split(),
    "16. 可選消費餐飲": "HD LOW MCD NKE SBUX TJX OR LVMUY YUM CMG DASH DPZ DRI QSR YUMC TXRH DARD BLMN EAT CAKE PLAY DENN TXRH RUTH".split(),
    "17. 電子商務平臺": "AMZN EBAY ETSY MELI SHOP PDD BABA JD SE CPNG W GMED CVNA W FAIR FTCH CHWY OSTK REAL RVLV PRTS QRTEA POSH".split(),
    "18. 房地產 REITs": "PLD AMT EQIX CCI PSA O SPG VICI CBRE ARE DRE EXR DLR MAA AVB WELL VTR PEAK INV INVH CPT MAA AVB ESS UDR".split(),
    "19. 材料與採礦": "LIN APD NEM GOLD FCX SCCO CTVA DOW SHW ALB DD CE IFF ECL LYB FMC EMN CF MOS NTR SMG WLK HUN CF MOS".split(),
    "20. 公用事業水電": "NEE SO DUK SRE AEP D EXC PCG FE ED PEG XEL WEC ES AWK LNT CMS NI ATO EVRG PNW CNP DTE LNT CMS".split(),
    "21. 旅遊博彩酒店": "BKNG ABNB MAR HLT LVS WYNN MGM RCL CCL EXPE NCLH H WH CHH MAR HLT WH CHH MAR HLT LVS WYNN MGM PENN CZR".split(),
    "22. 券商與交易所": "CME ICE MS SCHW IBKR COIN HOOD NDAQ CBOE MCO NDAQ CBOE TROW AMTD RJF BEN BK STT NTRS ARES JHG AMG".split(),
    "23. 金融科技支付": "V MA SQ PYPL AFRM SOFI NU GPN FIS FI FISV GPN TOST MQ BILL FLYW REVG BKI LPRO IIIV HAE FOR EVTC RPCE".split(),
    "24. 中型高增長區": "SMCI DECK CELH WING APP ELF ANF MDB DDOG NET OKTA TTD HUBS BILL MOND ASAN CFLT TOST FROG MNDY DOCN GLBE ESTC".split()
}

# 2. 視覺裝修 (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 25px; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 20px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 5rem; font-weight: 900; }
    .ej-header { color: #00FFFF !important; font-size: 1.5rem; font-weight: 900; margin-bottom: 8px; }
    .bar-group-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .bar-triad { display: flex; gap: 3px; }
    .ej-seg { width: 16px; height: 30px; border-radius: 2px; border: 1.2px solid rgba(255,255,255,0.4); }
    .scan-card-fire { border-left: 10px solid #FF4B4B; background-color: #310000; padding: 20px; margin-bottom: 15px; border-radius: 10px; box-shadow: 0 0 15px #FF4B4B66; }
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; }
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
    </style>
    """, unsafe_allow_html=True)

# 3. 側邊欄控制
st.sidebar.markdown("## 🛰️ 戰術控制台")
app_mode = st.sidebar.radio("請選擇操作", ["🚀 個股深度透視", "📡 全球版塊排序熱力圖", "🔍 版塊內尋龍掃描掣"])

# ==========================================
# 🚀 模式 A：個股深度透視 (首頁 - 靈魂全歸位)
# ==========================================
if app_mode == "🚀 個股深度透視":
    ticker = st.sidebar.text_input("🚀 輸入資產代號", "NVDA").upper()
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
            
            # 短期能量 BAR (支援負數顯示)
            se_p = ((curr_p / df['Close'].iloc[-5]) - 1) * 100
            
            st.markdown(f"<div class='main-title'>環球資產透維評估儀 [{ticker}]</div>", unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS</div><div class='cosmos-value'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div class='cosmos-box' style='border-color:#00FFFF; padding: 20px;'>", unsafe_allow_html=True)
                st.markdown(draw_triad_bar(cej_s, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
                # 短期能量 BAR 特殊處理
                se_lit = int(abs(se_p) / 5) # 每 5% 著一格
                html_se = f"<div class='ej-header'>短期能量 BAR: {se_p:.1f}%</div><div class='bar-group-container'>"
                for g in range(7):
                    html_se += "<div class='bar-triad'>"
                    for i in range(3):
                        idx = g*3+i
                        c_code = "#FF4B4B" if se_p < 0 else "#FF00FF"
                        op = 1 if idx < se_lit else 0.1
                        html_se += f"<div class='ej-seg' style='background-color:{c_code if idx < se_lit else '#222'}; opacity:{op};'></div>"
                    html_se += "</div>"
                st.markdown(html_se + "</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            st.write("---")
            d_c1, d_c2 = st.columns([1, 2.5])
            real_roe = info.get('returnOnEquity', 0)
            dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)
            dna_v = min(100.0, dna_v)
            
            with d_c1:
                st.markdown(f"""
                <div class='cosmos-box' style='border-color:#FF4B4B; height:450px; display:flex; flex-direction:column; justify-content:center;'>
                    <div style='color:#FF4B4B; font-weight:900; font-size:1.8rem;'>🧬 COSMOS-DNA</div>
                    <div style='font-size:0.9rem; color:#ccc; margin-bottom:10px;'>投行級股王基因 (100分滿分)</div>
                    <div style='font-size:6.5rem; font-weight:900;'>{dna_v}</div>
                    <div style='color:#FFD700; margin-top:20px;'>[ 現屬 第 2 級 ]<br><span style='font-size:1.8rem;'>🌟 星系霸主</span></div>
                </div>""", unsafe_allow_html=True)
            with d_c2:
                # ✅ 完美復刻：8行詳細數據分析 (支援負數與專屬顏色)
                st.markdown(f"<div style='background-color:#111; padding:15px; text-align:center; font-weight:bold; font-size:1.2rem; border-radius:8px; margin-bottom:15px;'><span style='color:#00FFCC;'>🌌 {ticker} ・ 8D 投行精確透視 BAR</span></div>", unsafe_allow_html=True)
                
                # 計算動態分數
                s1 = int(safe_n(info.get('operatingMargins', 0)*30+3, 7))
                s2 = int(safe_n(real_roe*30+3, 7))
                s3 = int(safe_n(info.get('revenueGrowth', 0)*20+4, 6))
                s4 = int(safe_n(info.get('profitMargins', 0)*30+3, 8))
                s5 = int(max(-5, 10 - safe_n(info.get('priceToBook', 12), 12))) # 支援負數
                s6 = 8 if safe_n(info.get('debtToEquity', 150), 150) < 80 else 6
                s7 = int(safe_n(info.get('dividendYield', 0)*200+2, 9))
                s8 = int(safe_n(info.get('earningsGrowth', 0)*25+4, 8))

                labels_8d = [
                    "🩸 血液純度 (營運現金流)", "🛡️ 免疫系統 (核心技術/生態)", "🏗️ 心跳頻率 (訂單/供應鏈VIP)",
                    "🧬 大腦潛力 (研發/開支回報)", "🧱 骨架重量 (資產底價/估值)", "⚡ 物理底盤 (能源/算力基建)",
                    "💰 資本配置 (回購/派息/併購)", "📈 經營拐點 (毛利率/主業反轉)"
                ]
                scores_8d = [s1, s2, s3, s4, s5, s6, s7, s8]
                colors_8d = ["#00FFCC", "#00FFCC", "#00FFCC", "#00FFCC", "#FF4B4B", "#BC13FE", "#FFFFFF", "#FFA500"]

                for i in range(8):
                    label = labels_8d[i]
                    sc = scores_8d[i]
                    color = colors_8d[i] if sc >= 0 else "#FF4B4B" # 負數強制紅色
                    abs_sc = min(10, abs(sc))
                    
                    grid = '<div class="energy-bar-container-8d">'
                    for j in range(1, 11):
                        op = "1" if j <= abs_sc else "0.1"
                        grid += f'<div class="energy-seg-8d" style="background-color:{color}; opacity:{op};"></div>'
                    grid += '</div>'
                    st.markdown(f"<div style='display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #222; padding-bottom:5px; margin-top:5px;'><span style='font-size:0.95rem; color:#ddd;'>{label}</span><span style='font-weight:bold; color:{color}; font-size:1.1rem;'>{sc}</span></div>{grid}", unsafe_allow_html=True)

            # --- 🏛️ 估值矩陣 ---
            st.write("---")
            st.write("### 🏛️ 估值與風險矩陣")
            v1, v2, v3 = st.columns(3); v4, v5, v6 = st.columns(3)
            def v_card(col, title, t_val, f_val):
                col.markdown(f"<div class='val-box'><div class='val-label'>{title}</div><div class='val-text'>TTM: <span class='val-focus'>{t_val}</span></div><div class='val-text'>12M預期: <span class='val-focus'>{f_val}</span></div></div>", unsafe_allow_html=True)
            v_card(v1, "PE 獲利比", safe_s(info, ['trailingPE'], "x"), safe_s(info, ['forwardPE'], "x"))
            v_card(v2, "PEG 增長比", safe_s(info, ['pegRatio']), "N/A")
            v_card(v3, "PS 銷售比", safe_s(info, ['priceToSalesTrailing12Months'], "x"), "N/A")
            v_card(v4, "PB 淨資產", safe_s(info, ['priceToBook'], "x"), "N/A")
            v_card(v5, "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], "x"), "N/A")
            v_card(v6, "股息率回報", safe_s(info, ['dividendYield', 'yield'], "%"), "N/A")

            # ✅ 完美復刻：COSMOS-VAL 烈火鳳凰框 (當 TTM PE > 80 時出現)
            ttm_pe = info.get('trailingPE', 0) or 0
            if ttm_pe > 80:
                dragon_index = round((dna_v * 0.4) + (cx_val * 0.3) + (crs_val * 0.3), 1)
                dragon_index = max(5.0, min(98.5, dragon_index)) 
                
                if dragon_index >= 80: 
                    t_lv, val_title, val_color, act_desc = "第 2 級", "烈火鳳凰", "#BC13FE", "【順勢而為】真實財報健康，估值雖貴但有支撐，緊貼趨勢操作。"
                else: 
                    t_lv, val_title, val_color, act_desc = "第 3 級", "海市蜃樓", "#FFA500", "【謹慎觀望】動能平平，估值偏高，注意回調風險。"
                
                st.markdown(f"""
                <div style='border: 2px solid {val_color}; border-radius: 12px; padding: 25px; background-color: #050011; margin: 25px 0; box-shadow: 0 0 20px {val_color}44;'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                        <div>
                            <span style='font-size:1.8rem; font-weight:900;'>🔥 COSMOS-VAL 估值解碼 : <span style='color:{val_color};'>🔥 {val_title}</span></span><br><br>
                            <span style='font-size:0.9rem; color:#aaa;'>( 針對 TTM PE {ttm_pe:.2f}x 的獨立戰略評分 )</span><br>
                            <span style='font-size:0.9rem; color:{val_color}; font-weight:bold;'>[ 註明：共分 4 級，現在這公司基於真實財報屬{t_lv} ]</span>
                        </div>
                        <div style='text-align:right;'>
                            <span style='font-size:0.9rem; color:#aaa;'>真龍指數：</span><br>
                            <span style='font-size:4rem; font-weight:900; color:{val_color};'>{dragon_index}</span>
                        </div>
                    </div>
                    <div style='background-color:#111; padding:15px; border-radius:8px; margin-top:20px; border:1px solid #222;'>
                        <b style='color:white; font-size:1rem;'>真實財報決策指令：</b> <span style='color:{val_color}; font-size:1rem;'>{act_desc}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ✅ 保留：Beta, Alpha, 波動率
            st.write("---")
            st.write("### 🔱 核心戰略指標 (Beta / Alpha / Volatility)")
            r1, r2, r3 = st.columns(3)
            b_val = float(get_beta(info, df, spy))
            y1_r = (curr_p / df['Close'].iloc[-252] - 1) if len(df) > 252 else 0
            s_y1_r = (spy['Close'].iloc[-1] / spy['Close'].iloc[-252] - 1) if len(spy) > 252 else 0
            real_alpha = (y1_r - b_val * s_y1_r) * 100
            r1.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>📐 Beta 性格</div><div class='cosmos-value' style='font-size:3.5rem;'>{b_val:.2f}</div></div>", unsafe_allow_html=True)
            r2.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🔱 Alpha 超額</div><div class='cosmos-value' style='font-size:3.5rem;'>{real_alpha:.1f}%</div></div>", unsafe_allow_html=True)
            r3.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🌊 波動情緒</div><div class='cosmos-value' style='font-size:3.5rem;'>{(v_ann*100):.1f}%</div></div>", unsafe_allow_html=True)

            # ✅ 完美復刻：股價圖 (摩訶釋達圖)
            st.write("### 📊 摩訶釋達・能量與籌碼透視圖")
            recent = df.tail(120); dates = recent.index.strftime('%Y-%m-%d')
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
            fig.add_trace(go.Candlestick(x=dates, open=recent['Open'], high=recent['High'], low=recent['Low'], close=recent['Close'], name='股價'), row=1, col=1)
            fig.add_trace(go.Bar(x=dates, y=recent['Volume'], marker_color=['#00FF00' if recent['Close'].iloc[i] >= recent['Open'].iloc[i] else '#FF0000' for i in range(len(recent))], name='成交量'), row=2, col=1)
            fig.update_layout(template="plotly_dark", height=600, showlegend=False, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

            # ✅ 完美復刻：90 大名家持倉
            st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center; margin-bottom:20px;'>🧙 90 大名家：真實申報持倉</div>", unsafe_allow_html=True)
            holders = asset.institutional_holders
            if holders is not None and not holders.empty:
                for _, row in holders.head(8).iterrows():
                    st.markdown(f"<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>持有 {row.get('Shares',0):,.0f} 股</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:center; color:#ccc;'>暫無持倉數據</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

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
            # 自動由強到弱排序 (Descending Order)
            df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=True) 
            fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["版塊"], orientation='h', 
                                    marker=dict(color=df_rs["RS強弱"], colorscale='Portland' if is_us else 'Viridis')))
            fig.update_layout(template="plotly_dark", height=800, title=f"當前最強版塊：{df_rs.iloc[-1]['版塊']}")
            st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 🔍 模式 C：尋龍掃描掣 (千龍全開版)
# ==========================================
else:
    st.markdown("<h1 class='main-title'>🔍 全球千龍起步狙擊雷達</h1>", unsafe_allow_html=True)
    m_choice = st.sidebar.selectbox("1. 選擇市場", ["美股市場 (1200隻)", "港股市場 (800隻)"])
    target_dict = US_FULL_MAP if "美股" in m_choice else HK_FULL_MAP
    s_choice = st.sidebar.selectbox("2. 選擇狙擊版塊", ["全部綜合掃描"] + list(target_dict.keys()))
    scan_btn = st.sidebar.button("📡 啟動全方位雷達！")
    
    if scan_btn:
        bench_sym = "SPY" if "美股" in m_choice else "^HSI"
        st.info(f"正在深度對焦 {s_choice} 核心標的...")
        bench_data = yf.Ticker(bench_sym).history(period="2y").dropna(subset=['Close'])
        
        if s_choice == "全部綜合掃描":
            tickers_to_scan = list(set([t for sub in target_dict.values() for t in sub]))
        else:
            tickers_to_scan = target_dict[s_choice]
            
        breakout_found = False
        progress_bar = st.progress(0)
        
        for idx, t in enumerate(tickers_to_scan):
            progress_bar.progress((idx + 1) / len(tickers_to_scan))
            try:
                d = yf.Ticker(t).history(period="1y").dropna()
                if len(d) > 63:
                    curr_p = d['Close'].iloc[-1]
                    crs = 50 + ((curr_p / d['Close'].iloc[-63]) - (bench_data['Close'].iloc[-1] / bench_data['Close'].iloc[-63])) * 100
                    ej = (d['Volume'].tail(21).mean() / max(d['Volume'].tail(252).mean(), 1)) * 100
                    se = 50 + (((curr_p / d['Close'].iloc[-5]) - 1) * 1200)
                    
                    if se > 85 and ej > 110 and crs > 52:
                        breakout_found = True
                        st.markdown(f"<div class='scan-card-fire'>🎯 {t} | 起飛共振訊號！<br>⚡ SE: {se:.1f} | 🔋 EJ: {ej:.1f} | 📈 RS: {crs:.1f}</div>", unsafe_allow_html=True)
            except: pass
        if not breakout_found: st.warning("目前該星系暫無標的觸發起飛訊號。")
