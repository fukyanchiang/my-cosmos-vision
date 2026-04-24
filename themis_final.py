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

# =========================================================================
# 🛸 爺爺嘅外掛資料庫：已將【個股】與【ETF】完美拆分獨立
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

HK_ETF_MAP = {
    "E1. 港股大盤與科指": "2800.HK 2828.HK 3032.HK 3067.HK 3147.HK 2812.HK 3033.HK 3058.HK 3068.HK".split(),
    "E2. 國央企與高息紅利": "3110.HK 3115.HK 3046.HK 3141.HK 3432.HK 2836.HK 3010.HK".split(),
    "E3. A股寬基 (滬深/A50)": "3188.HK 2822.HK 2823.HK 3100.HK 3010.HK 3153.HK 3173.HK 83188.HK 2833.HK".split(),
    "E4. 大中華科技與新經濟": "3134.HK 3124.HK 3136.HK 2843.HK 3191.HK".split(),
    "E5. 新能源與半導體 (A股)": "2806.HK 2809.HK 3122.HK 3069.HK 3088.HK 3132.HK".split(),
    "E6. 醫藥與消費 (A股)": "2826.HK 3133.HK 3145.HK 3061.HK".split(),
    "E7. 商品與貴金屬 (黃金/石油)": "2840.HK 3081.HK 3117.HK 3132.HK".split(),
    "E8. 環球市場 (美/日/印)": "3140.HK 2834.HK 3126.HK 3155.HK 2814.HK".split(),
    "E9. 債券與貨幣市場": "3075.HK 3079.HK 3199.HK 3086.HK".split()
}

US_ETF_MAP = {
    "E1. 大盤與寬基 (Broad)": "SPY QQQ DIA IWM VOO IVV VTI RSP QQQM ONEQ VUG VTV IWD IWF".split(),
    "E2. 科技與半導體 (Tech)": "SMH SOXX XLK VGT IGV IYW XSD FDN SKYY XSW".split(),
    "E3. 金融與工業 (Fin/Ind)": "XLF XLI KRE KBE VIS IYT".split(),
    "E4. 能源與公用 (Energy/Util)": "XLE XLU VDE OIH".split(),
    "E5. 醫療與生物 (Health/Bio)": "XLV XBI IBB".split(),
    "E6. 消費與地產 (Cons/REIT)": "XLY XLP XLRE VNQ IYR".split(),
    "E7. 股息與價值 (Dividend)": "SCHD VYM VIG DVY SDY".split(),
    "E8. 國家與新興市場 (Country)": "EWJ INDA EWZ EWW EWT EZU FXI MCHI KWEB EWU EWQ EWG EWC EWA EZA ARGT TUR VNM".split(),
    "E9. 發達國家與全球 (Global)": "VEA VWO EFA URTH ACWI".split(),
    "E10. 貴金屬與商品 (Commodity)": "GLD SLV IAU URA COPX USO UNG DBC GDX GDXJ PALL PPLT WEAT CORN SOYB DBA BCI".split(),
    "E11. 國債與信用債 (Bonds)": "TLT AGG BND LQD HYG IEF SHY MBB MUB JNK TIP IGOV EMB GOVT".split(),
    "E12. 主題與前沿 (Thematic)": "ARKK ARKG ICLN TAN LIT CIBR HACK PBW MOO BOTZ ROBO".split()
}

# 2. 視覺裝修 (一條毛都冇改)
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
    .val-box-purple { border: 3px solid #BC13FE; border-radius: 15px; padding: 30px; background-color: #000; box-shadow: 0 0 25px #BC13FE66; margin: 25px 0; }
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700; font-weight: bold; font-size: 2.5rem; }
    .whale-a { color: #00FFCC; font-size: 1.6rem; text-align: right; }
    .scan-card-fire { border-left: 10px solid #FF4B4B; background-color: #310000; padding: 20px; margin-bottom: 15px; border-radius: 10px; box-shadow: 0 0 15px #FF4B4B66; }
    </style>
    """, unsafe_allow_html=True)

# 3. 側邊欄控制
st.sidebar.markdown("## 🛰️ 戰術控制台 (六大引擎版)")
app_mode = st.sidebar.radio("請選擇操作", [
    "🚀 個股深度透視", 
    "📡 個股版塊拔河熱力圖", 
    "📡 ETF 資產拔河熱力圖", 
    "🔍 千龍起步尋龍雷達 (個股)",
    "🛡️ 美股 ETF 專屬雷達",
    "🛡️ 港/A股 ETF 專屬雷達"
])

# =========================================================================
# 🚀 模式 A：個股深度透視
# =========================================================================
if app_mode == "🚀 個股深度透視":
    ticker = st.sidebar.text_input("🚀 輸入資產代號", "6869.HK").upper()

    try:
        asset = yf.Ticker(ticker); info = asset.info
        df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
        spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
        
        if not df.empty:
            curr_p = df['Close'].iloc[-1]
            
            # 🌌 COSMOS-X & RS
            c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
            slope, intercept = np.polyfit(days, c_tail, 1); pred = intercept + slope * len(days)
            mom = (curr_p / pred) if pred > 0 else 1.0; v_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
            cx_val = safe_n(((slope * 252) / c_tail.mean() / v_ann) * 29 * mom, 50.0)

            crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])) * 100, 50.0) if len(df) > 63 else 50.0
            
            v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
            cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
            se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0) if len(df) > 5 else 50.0

            st.markdown(f"""<div class='main-title'>環球資產透維評估儀 [{ticker}]</div>""", unsafe_allow_html=True)
            
            # 第一層看板
            c1, c2, c3 = st.columns(3)

            c1.markdown(f"""<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>""", unsafe_allow_html=True)

            c2.markdown(f"""<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS (星系強弱)</div><div class='cosmos-value'>{crs_val:.1f}</div></div>""", unsafe_allow_html=True)
            with c3:

                st.markdown("""<div class='cosmos-box' style='border-color:#00FFFF; padding: 20px;'>""", unsafe_allow_html=True)
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
                st.markdown(draw_triad_bar(cej_s, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
                st.markdown(draw_triad_bar(se_s, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
                st.markdown("""</div>""", unsafe_allow_html=True)

            # 🧬 [DNA 自動切換 ETF / 個股]
            st.write("---")
            d_c1, d_c2 = st.columns([1, 2.5])
            
            is_etf = info.get('quoteType') == 'ETF'
            real_roe = info.get('returnOnEquity')
            
            if is_etf or real_roe is None or real_roe == 0:
                dna_v = round(safe_n((cx_val * 0.5) + (crs_val * 0.5), 50.0), 1)
                dna_title = "ETF 綜合質量基因"
                m8 = {
                    "🩸 資金純度 (流動)": int(safe_n(cej_s / 10, 5)),
                    "🛡️ 免疫系統 (抗跌)": int(safe_n(crs_val / 10, 5)),
                    "🏗️ 心跳頻率 (動能)": int(safe_n(cx_val / 10, 5)),
                    "🧬 大腦潛力 (趨勢)": int(safe_n(se_s / 10, 5)),
                    "🧱 骨架重量 (規模)": 9 if info.get('totalAssets', 0) > 1e9 else 5,
                    "⚡ 物理底盤 (波幅)": int(max(1, 10 - (v_ann * 20))),
                    "💰 資本配置 (派息)": int(safe_n(info.get('yield', info.get('dividendYield', 0))*200+2, 5)),
                    "📈 經營拐點 (相對)": int(safe_n(crs_val / 10, 5))
                }
            else:
                dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)
                dna_title = "投行級股王基因"
                m8 = {
                    "🩸 血液純度": int(safe_n(info.get('operatingMargins', 0)*30+3, 5)),
                    "🛡️ 免疫系統": int(safe_n(real_roe*30+3, 7)),
                    "🏗️ 心跳頻率": int(safe_n(info.get('revenueGrowth', 0)*20+4, 6)),
                    "🧬 大腦潛力": int(safe_n(info.get('profitMargins', 0)*30+3, 8)),
                    "🧱 骨架重量": int(max(1, 10 - safe_n(info.get('priceToBook', 5), 5))),
                    "⚡ 物理底盤": 8 if safe_n(info.get('debtToEquity', 150), 150) < 80 else 3,
                    "💰 資本配置": int(safe_n(info.get('dividendYield', 0)*200+2, 5)),
                    "📈 經營拐點": int(safe_n(info.get('earningsGrowth', 0)*25+4, 8))
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
                # 🚨 修正 HTML 排版錯誤：移除 Markdown 多餘空格縮排
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
            # ✅ 正名: 12M 目標價 & N/A 誠實處理
            # -------------------------------------------------------------
            st.write(""); k1 = st.columns(4); k2 = st.columns(4)
            
            val_emotion = safe_n(crs_val * 0.9, 50.0)
            val_total = (cx_val + crs_val + se_s) / 3
            val_vol_ratio = v21 / max(v252, 1)

            # 讀取分析師大行 12 個月目標價，搵唔到就 N/A，絕不老作
            target_p_raw = info.get('targetMeanPrice')
            val_target_str = f"${target_p_raw:.2f}" if target_p_raw else "N/A"

            kings = [
                ("📁 質量", f"{dna_v:.0f}"), 
                ("📈 趨勢", f"{crs_val:.0f}"), 
                ("⚡ 動能", f"{se_s:.0f}"), 
                ("🔋 大資金", f"{cej_s:.0f}"), 
                ("🎭 情緒", f"{val_emotion:.0f}"), 
                ("🏆 總分", f"{val_total:.0f}"), 
                ("🔮 12M目標", val_target_str),   # 已經改名為 12M 目標
                ("💰 成交比", f"{val_vol_ratio:.1f}x")
            ]
            
            for i in range(4):

                k1[i].markdown(f"""<div class='cosmos-box' style='padding:15px; border-width:2px;'><div style='color:#ccc; font-size:1.2rem;'>{kings[i][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i][1]}</div></div>""", unsafe_allow_html=True)

                k2[i].markdown(f"""<div class='cosmos-box' style='padding:15px; border-width:2px; border-color:#FFD700;'><div style='color:#ccc; font-size:1.2rem;'>{kings[i+4][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i+4][1]}</div></div>""", unsafe_allow_html=True)

            st.markdown(f"""<div class='red-bar'>🔥 戰略透視：短期動能爆發數值 [{se_s:.1f}%] 🔥</div>""", unsafe_allow_html=True)

            # 估值矩陣 (正名為 12M預期)
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

            # 烈火鳳凰 (常駐所有股票顯示，並增加 PE > 80 紅色警告)
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

                # 🚨 修正 HTML 排版錯誤：移除 Markdown 多餘空格縮排
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
            st.plotly_chart(fig, use_container_width=True, theme=None, config={'displayModeBar': False})

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

# =========================================================================
# 📡 模式 B1：個股版塊拔河熱力圖 (✅ 已加上鎖定防止誤觸)
# =========================================================================
elif app_mode == "📡 個股版塊拔河熱力圖":
    st.markdown("<h1 class='main-title'>📡 個股版塊相對強弱拔河排名</h1>", unsafe_allow_html=True)
    st.write("👴 爺爺提示：此處專注比較**個股板塊**，尋找資金炒作的熱點。圖表已鎖定，可用手指點擊查看數值。")
    m_view = st.sidebar.radio("選擇星系地圖", ["🇺🇸 美股 50 大版塊", "🇭🇰 港股 22 大版塊"])
    is_us = "美股" in m_view
    bench_sym = "SPY" if is_us else "^HSI"
    target_map = US_STOCK_MAP if is_us else HK_STOCK_MAP
    
    with st.spinner(f'正在進行個股版塊拔河對比 ({bench_sym})...'):
        bench_df = yf.Ticker(bench_sym).history(period="60d")['Close']
        results = []
        for name, tickers in target_map.items():
            try:
                d = yf.Ticker(tickers[0]).history(period="60d")['Close']
                if len(d) >= 20:
                    rs_score = 50 + ((d.iloc[-1]/d.iloc[-20]) - (bench_df.iloc[-1]/bench_df.iloc[-20])) * 100
                    results.append({"版塊": name, "RS強弱": round(rs_score, 1)})
            except: pass
        
        if results:
            df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=True) 
            fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["版塊"], orientation='h', 
                                    marker=dict(color=df_rs["RS強弱"], colorscale='Portland' if is_us else 'Viridis')))
            
            # ✅ 鎖定 X/Y 軸防止誤觸縮放
            fig.update_layout(
                template="plotly_dark", 
                height=1000 if is_us else 700, 
                title=f"最強個股吸金版塊：{df_rs.iloc[-1]['版塊']}",
                xaxis=dict(fixedrange=True),
                yaxis=dict(fixedrange=True)
            )
            # ✅ 隱藏 ModeBar + 強制載入自訂 Theme
            st.plotly_chart(fig, use_container_width=True, theme=None, config={'displayModeBar': False})

# =========================================================================
# 📡 模式 B2：ETF 資產拔河熱力圖 (✅ 已加上鎖定防止誤觸)
# =========================================================================
elif app_mode == "📡 ETF 資產拔河熱力圖":
    st.markdown("<h1 class='main-title'>📡 ETF 資產相對強弱拔河排名</h1>", unsafe_allow_html=True)
    st.write("👴 爺爺提示：此處展示**大類資產與國家 ETF** 排名，判斷避險與進攻大方向。圖表已鎖定，可用手指點擊查看數值。")
    m_view = st.sidebar.radio("選擇星系地圖", ["🇺🇸 美股 ETF 陣列", "🇭🇰 港股 (含A股) ETF 陣列"])
    is_us = "美股" in m_view
    bench_sym = "SPY" if is_us else "^HSI"
    target_map = US_ETF_MAP if is_us else HK_ETF_MAP
    
    with st.spinner(f'正在進行 ETF 大類資產拔河對比 ({bench_sym})...'):
        bench_df = yf.Ticker(bench_sym).history(period="60d")['Close']
        results = []
        for name, tickers in target_map.items():
            try:
                d = yf.Ticker(tickers[0]).history(period="60d")['Close']
                if len(d) >= 20:
                    rs_score = 50 + ((d.iloc[-1]/d.iloc[-20]) - (bench_df.iloc[-1]/bench_df.iloc[-20])) * 100
                    results.append({"版塊": name, "RS強弱": round(rs_score, 1)})
            except: pass
        
        if results:
            df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=True) 
            fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["版塊"], orientation='h', 
                                    marker=dict(color=df_rs["RS強弱"], colorscale='Aggrnyl')))
            
            # ✅ 鎖定 X/Y 軸防止誤觸縮放
            fig.update_layout(
                template="plotly_dark", 
                height=600, 
                title=f"最強 ETF 資產：{df_rs.iloc[-1]['版塊']}",
                xaxis=dict(fixedrange=True),
                yaxis=dict(fixedrange=True)
            )
            # ✅ 隱藏 ModeBar + 強制載入自訂 Theme
            st.plotly_chart(fig, use_container_width=True, theme=None, config={'displayModeBar': False})

# =========================================================================
# 🔍 模式 C：千龍起步尋龍雷達 (專注個股)
# =========================================================================
elif app_mode == "🔍 千龍起步尋龍雷達 (個股)":
    st.markdown("<h1 class='main-title'>🔍 個股專屬：起步狙擊雷達</h1>", unsafe_allow_html=True)
    st.write("👴 爺爺提示：此雷達**專門過濾個股**，尋找資金與動能共振的爆發點！")
    m_choice = st.sidebar.selectbox("1. 選擇個股市場", ["🇺🇸 美股市場 (~2800隻個股)", "🇭🇰 港股市場 (~1500隻個股)"])
    target_dict = US_STOCK_MAP if "美股" in m_choice else HK_STOCK_MAP
    
    s_choice = st.sidebar.selectbox("2. 選擇狙擊版塊", ["🌐 啟動全星系個股盲掃"] + list(target_dict.keys()))
    scan_btn = st.sidebar.button("📡 發射個股尋龍電波！")
    
    if scan_btn:
        bench_sym = "SPY" if "美股" in m_choice else "^HSI"
        bench_data = yf.Ticker(bench_sym).history(period="2y").dropna(subset=['Close'])
        
        if s_choice == "🌐 啟動全星系個股盲掃":
            st.warning("⚠️ 爺爺警告：全星系盲掃包含過千隻股票，為免網絡塞車，請耐心等候幾分鐘！")
            tickers_to_scan = list(set([t for sub in target_dict.values() for t in sub]))
        else:
            st.info(f"正在深度掃描 【{s_choice}】 內核心標的...")
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
                        st.markdown(f"""
                        <div class='scan-card-fire'>
                            <h2 style='color:#FFD700; margin:0;'>🎯 {t} | 個股起飛訊號！</h2>
                            <p style='margin:5px 0; color:#ddd; font-size:1.2rem;'>⚡ SE: <b style='color:#FF4B4B;'>{se:.1f}</b> | 🔋 EJ: <b style='color:#00FFCC;'>{ej:.1f}</b> | 📈 RS: <b>{crs:.1f}</b></p>
                        </div>
                        """, unsafe_allow_html=True)
            except: pass
        progress_bar.empty()
        if not breakout_found: st.warning("💤 掃描完畢：目前未有標的觸發起飛訊號。")

# =========================================================================
# 🛡️ 模式 D1：美股 ETF 專屬雷達
# =========================================================================
elif app_mode == "🛡️ 美股 ETF 專屬雷達":
    st.markdown("<h1 class='main-title'>🛡️ 美股 ETF 穩中求勝雷達</h1>", unsafe_allow_html=True)
    st.write("涵蓋大盤、科技、高息、國債、黃金石油及全球國家 ETF。")
    s_choice = st.sidebar.selectbox("選擇 ETF 版塊", ["🌐 啟動全 ETF 綜合掃描"] + list(US_ETF_MAP.keys()))
    scan_btn = st.sidebar.button("📡 發射美股 ETF 電波！")
    
    if scan_btn:
        bench_data = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
        tickers_to_scan = list(set([t for sub in US_ETF_MAP.values() for t in sub])) if s_choice == "🌐 啟動全 ETF 綜合掃描" else US_ETF_MAP[s_choice]
        
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
                        st.markdown(f"""
                        <div class='scan-card-fire' style='border-color:#00FFCC; box-shadow: 0 0 15px #00FFCC66;'>
                            <h2 style='color:#00FFCC; margin:0;'>🛡️ {t} | ETF 穩步發車！</h2>
                            <p style='margin:5px 0; color:#ddd;'>⚡ SE: <b style='color:#FF4B4B;'>{se:.1f}</b> | 🔋 EJ: <b style='color:#00FFCC;'>{ej:.1f}</b> | 📈 RS: <b>{crs:.1f}</b></p>
                        </div>
                        """, unsafe_allow_html=True)
            except: pass
        progress_bar.empty()
        if not breakout_found: st.warning("💤 掃描完畢：目前未有 ETF 觸發起飛訊號。")

# =========================================================================
# 🛡️ 模式 D2：港/A股 ETF 專屬雷達
# =========================================================================
elif app_mode == "🛡️ 港/A股 ETF 專屬雷達":
    st.markdown("<h1 class='main-title'>🛡️ 港/A股 ETF 穩中求勝雷達</h1>", unsafe_allow_html=True)
    st.write("涵蓋港股科指、國企紅利、A股滬深300及強勢主題 ETF。")
    s_choice = st.sidebar.selectbox("選擇 ETF 版塊", ["🌐 啟動全 ETF 綜合掃描"] + list(HK_ETF_MAP.keys()))
    scan_btn = st.sidebar.button("📡 發射港/A股 ETF 電波！")
    
    if scan_btn:
        bench_data = yf.Ticker("^HSI").history(period="2y").dropna(subset=['Close'])
        tickers_to_scan = list(set([t for sub in HK_ETF_MAP.values() for t in sub])) if s_choice == "🌐 啟動全 ETF 綜合掃描" else HK_ETF_MAP[s_choice]
        
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
                        st.markdown(f"""
                        <div class='scan-card-fire' style='border-color:#00FFCC; box-shadow: 0 0 15px #00FFCC66;'>
                            <h2 style='color:#00FFCC; margin:0;'>🛡️ {t} | ETF 穩步發車！</h2>
                            <p style='margin:5px 0; color:#ddd;'>⚡ SE: <b style='color:#FF4B4B;'>{se:.1f}</b> | 🔋 EJ: <b style='color:#00FFCC;'>{ej:.1f}</b> | 📈 RS: <b>{crs:.1f}</b></p>
                        </div>
                        """, unsafe_allow_html=True)
            except: pass
        progress_bar.empty()
        if not breakout_found: st.warning("💤 掃描完畢：目前未有 ETF 觸發起飛訊號。")

except Exception as e: st.error(f"數據診斷中: {e}")
