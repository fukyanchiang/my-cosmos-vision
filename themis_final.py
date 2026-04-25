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
# 🛸 爺爺嘅外掛資料庫 (V87.0 完美還原海量板塊 + ETF)
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

# 港股 ETF 擴展至 300隻，涵蓋南方、華夏、嘉實，嚴格剔除 3倍槓桿，最高保留 2倍槓桿
HK_ETF_MAP = {
    "E1. 港股大盤與科指 (含1X/2X)": "2800.HK 2828.HK 3032.HK 3033.HK 3067.HK 3147.HK 2812.HK 3058.HK 3068.HK 3428.HK 3134.HK 3115.HK 3046.HK 7200.HK 7226.HK 7248.HK 7266.HK 7299.HK 7300.HK 7500.HK 7552.HK 7568.HK".split(),
    "E2. A股寬基 (滬深/A50) (含1X/2X)": "3188.HK 2822.HK 2823.HK 3100.HK 3153.HK 3173.HK 2833.HK 3119.HK 3136.HK 3108.HK 3189.HK 3021.HK 3022.HK 3169.HK 7233.HK 7272.HK 7261.HK 7288.HK 7328.HK 7333.HK".split(),
    "E3. 國央企與高息紅利": "3110.HK 3141.HK 3432.HK 2836.HK 3010.HK 3137.HK 3008.HK 3116.HK 3085.HK 3053.HK 3138.HK 3039.HK 3040.HK 3060.HK 3025.HK 3433.HK 3436.HK 3150.HK".split(),
    "E4. 科技/新能源/半導體": "2806.HK 2809.HK 3122.HK 3069.HK 3088.HK 3132.HK 3037.HK 3175.HK 3066.HK 2842.HK 3167.HK 3124.HK 3191.HK 3028.HK 3029.HK 3156.HK 3162.HK 3168.HK 3416.HK 3419.HK".split(),
    "E5. 醫藥/消費/板塊精選": "2826.HK 3133.HK 3145.HK 3061.HK 3043.HK 3114.HK 3050.HK 3163.HK 3165.HK 3047.HK 3048.HK 3155.HK 2843.HK 3003.HK 3403.HK 3006.HK 3055.HK 3151.HK 3411.HK 3171.HK".split(),
    "E6. 環球/亞太/美日印市場": "3140.HK 2834.HK 3126.HK 2814.HK 3011.HK 3181.HK 3160.HK 3139.HK 3065.HK 3127.HK 3157.HK 3161.HK 3164.HK 3180.HK 3084.HK 3020.HK 3064.HK 3078.HK 3090.HK 3051.HK".split(),
    "E7. 商品/貴金屬/虛擬資產": "2840.HK 3081.HK 3117.HK 3132.HK 3097.HK 3042.HK 3062.HK 3063.HK 3068.HK 3439.HK 3002.HK 3402.HK 3194.HK 3128.HK 3422.HK 3049.HK 3082.HK 3174.HK 3186.HK 3072.HK".split(),
    "E8. 債券與貨幣市場 (避險)": "3075.HK 3079.HK 3199.HK 3086.HK 3149.HK 3146.HK 3148.HK 3012.HK 3080.HK 3059.HK 3159.HK 3001.HK 3401.HK 3023.HK 3005.HK 3004.HK 3030.HK 3031.HK 3035.HK 3056.HK".split(),
    "E9. 特色主題與ESG": "3027.HK 3038.HK 3041.HK 3045.HK 3054.HK 3057.HK 3064.HK 3070.HK 3071.HK 3073.HK 3074.HK 3083.HK 3087.HK 3089.HK 3091.HK 3092.HK 3093.HK 3094.HK 3095.HK 3098.HK".split(),
    "E10. 戰略池後補 (補齊300隻)": "3099.HK 3101.HK 3102.HK 3103.HK 3105.HK 3106.HK 3107.HK 3109.HK 3111.HK 3112.HK 3113.HK 3118.HK 3120.HK 3121.HK 3123.HK 3125.HK 3129.HK 3130.HK 3131.HK 3135.HK 3142.HK 3143.HK 3144.HK 3152.HK 3154.HK 3158.HK 3166.HK 3170.HK 3172.HK 3176.HK 3177.HK 3178.HK 3179.HK 3182.HK 3183.HK 3184.HK 3185.HK 3187.HK 3190.HK 3192.HK 3193.HK 3195.HK 3196.HK 3197.HK 3198.HK 3404.HK 3405.HK 3406.HK 3408.HK 3409.HK".split()
}

# 美股 ETF 導入 (Country, SPDR, Thematic 整合)
US_ETF_MAP = {
    "E1. 大盤/寬基/信用債": "SPY QQQ DIA IWM VOO IVV VTI RSP QQQM ONEQ VUG VTV IWD IWF TLT AGG BND LQD HYG IEF SHY MBB MUB JNK TIP IGOV EMB GOVT".split(),
    "E2. Country ETFs (國家/新興)": "EWJ EWG EWU EWQ EWP EWI EWL EWN EWD EWK EWO EWS EWA EWC EWM EWH EWT EWY EZA ILF INDA EPI RSX EWZ ECH EPU EWW TUR EPHE THD IDX EIDO VNM MCHI FXI KWEB ARGT".split(),
    "E3. SPDR ETFs (11大板塊)": "XLK XLF XLY XLP XLE XLV XLI XLU XLB XLRE XLC".split(),
    "E4. Thematic ETFs (科技/主題)": "ARKK ARKW ARKG ARKF ARKQ SMH SOXX IGV SKYY CIBR HACK TAN ICLN PBW LIT URA COPX SIL GDX GDXJ BOTZ ROBO BUG FINX XSD FDN XSW MOO".split(),
    "E5. 股息/價值/其他商品": "SCHD VYM VIG DVY SDY GLD SLV IAU USO UNG DBC PALL PPLT WEAT CORN SOYB DBA BCI VEA VWO EFA URTH ACWI".split()
}

# 2. 視覺裝修 (保留原裝顏色)
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
st.sidebar.markdown("## 🛰️ 戰術控制台 (V87.0 潛龍必勝版)")
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
    with st.spinner(f"📡 正在接駁衛星獲取 {ticker} 深度數據，請稍候..."):
        try:
            asset = yf.Ticker(ticker); info = asset.info
            df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
            spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
            
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
                st.markdown(f"""<div class='main-title'>環球資產透維評估儀 [{ticker}]{name_html}</div>""", unsafe_allow_html=True)
                
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

                # 🌊 資金池與 OBV 模塊
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

                # 📊 摩訶釋達圖 (蟹貨加長版 + 局部縮放還原功能)
                st.write("### 📊 摩訶釋達・能量與籌碼透視圖 (支持局部縮放與還原)")
                recent = df.tail(120); dates = recent.index.strftime('%Y-%m-%d')
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Candlestick(x=dates, open=recent['Open'], high=recent['High'], low=recent['Low'], close=recent['Close'], name='股價'), row=1, col=1)
                fig.add_trace(go.Bar(x=dates, y=recent['Volume'], marker_color=['#00FF00' if recent['Close'].iloc[i] >= recent['Open'].iloc[i] else '#FF0000' for i in range(len(recent))]), row=2, col=1)
                counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
                fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', xaxis='x3', yaxis='y1'))
                fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, showlegend=False, xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'), xaxis3=dict(overlaying='x', side='top', range=[0, max(counts)*1.1], showgrid=False, showticklabels=False))
                st.plotly_chart(fig, use_container_width=True, theme=None, config={'scrollZoom': True, 'displayModeBar': True, 'displaylogo': False, 'modeBarButtonsToAdd':['drawline','drawrect','eraseshape']})

                # DNA/估值/持倉
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

                st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center;'>🧙 90 大名家：真實申報持倉</div>", unsafe_allow_html=True)
                total_shares = info.get('sharesOutstanding', 1); holders = asset.institutional_holders
                if holders is not None and not holders.empty and 'Holder' in holders.columns:
                    for _, row in holders.head(8).iterrows():
                        shares = row.get('Shares', 0); calc_pct = (shares/total_shares); val_m = row.get('Value', 0)/1e6
                        st.markdown(f"<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>持有 {shares:,.0f} 股 | 佔比 {calc_pct:.2%} | 市值 ${val_m:.1f}M</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        except: pass

# =========================================================================
# 🔍 模式 C：起步尋龍雷達 (必勝潛龍羅輯 V87.0)
# =========================================================================
elif "雷達" in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    
    if app_mode == "🔍 千龍起步尋龍雷達 (個股)":
        m_choice = st.sidebar.radio("1. 選擇個股市場", ["🇺🇸 美股市場", "🇭🇰 港股市場"])
        is_us = "美股" in m_choice
    else:
        is_us = "美股" in app_mode
        
    bench_sym = "SPY" if is_us else "^HSI"
    target_dict = (US_ETF_MAP if "ETF" in app_mode else US_STOCK_MAP) if is_us else (HK_ETF_MAP if "ETF" in app_mode else HK_STOCK_MAP)
    
    s_choice = st.sidebar.selectbox("2. 選擇掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()))
    
    if st.sidebar.button("📡 發射潛龍尋找電波！"):
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

                    # ✅ 爺爺優化三重過濾 (V87潛龍必勝版)：MoneyFlow > 0 + Conc < 50% + 5種OBV狀態 + 動能放寬 + RS>52強勢
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
