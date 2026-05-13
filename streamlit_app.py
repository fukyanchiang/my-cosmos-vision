import streamlit as st 
import yfinance as yf 
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go 
from plotly.subplots import make_subplots 
from core_logic import scan_dragon_logic, smart_fetch, check_stop_loss
import time

# ==========================================
# 📚 大字典：100% 完整保留 (一字不少)
# ==========================================
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
    "H1. A股門戶/旗艦大盤": "2822.HK 3188.HK 3109.HK 2823.HK 2846.HK 3147.HK 2801.HK 3010.HK 3081.HK 3151.HK 3072.HK 3042.HK 2839.HK 3180.HK 2827.HK 3139.HK 3118.HK 2838.HK".split(),
    "H2. 港股科技/AI/芯片": "3033.HK 3088.HK 9888.HK 3067.HK 3167.HK 3191.HK 7709.HK 9191.HK 3434.HK 3112.HK 3171.HK 3091.HK 3032.HK 3001.HK 3060.HK 2826.HK".split(),
    "H3. A股及港股行業板塊": "3134.HK 2845.HK 9845.HK 3136.HK 3069.HK 3174.HK 2820.HK 3133.HK 3111.HK 3141.HK 3148.HK 3149.HK 2842.HK 3120.HK 2806.HK 3143.HK 3137.HK 3051.HK".split(),
    "H4. 紅利收息/Covered Call": "3110.HK 3070.HK 3101.HK 3037.HK 3145.HK 3010.HK 3081.HK 3115.HK 3006.HK 3150.HK 3422.HK 3116.HK 3113.HK 3031.HK 3153.HK".split(),
    "H5. 虛擬資產/加密貨幣": "3066.HK 3068.HK 3439.HK 3419.HK 3460.HK 3461.HK 3471.HK 3472.HK 3083.HK 3087.HK 3135.HK 3175.HK 7799.HK 7711.HK 7747.HK".split(),
    "H6. 商品/債券/貨幣基金": "2840.HK 3030.HK 3152.HK 3192.HK 3196.HK 3161.HK 3071.HK 2812.HK 3140.HK 3181.HK 3187.HK 3189.HK 3192.HK 3117.HK 3011.HK 3119.HK".split(),
    "H7. 槓桿/反向 (指數/商品)": "7200.HK 7226.HK 7205.HK 7299.HK 7266.HK 7500.HK 7522.HK 7552.HK 7300.HK 7333.HK 7348.HK 7233.HK 7248.HK 7288.HK 7231.HK".split()
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

# --- 股價圖副功能：三層能量圖 (已修正 row_start) ---
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
    
    v_ma = df['Volume'].rolling(20, min_periods=1).mean(); v_std = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
    v_upper = v_ma + (2.0 * v_std); ma60 = df['Volume'].rolling(60, min_periods=1).mean(); roc = abs(df['Close'].pct_change()) * 100
    is_burst = (df['Volume'] > v_upper) & (df['Volume'] > ma60 * 1.9) & (roc > 2.0)
    burst_colors = ['#00FFFF' if (is_burst.iloc[i] and df['Close'].iloc[i] > df['Open'].iloc[i]) else ('#FF00FF' if is_burst.iloc[i] else 'rgba(136,136,136,0.3)') for i in range(len(df))]
    fig.add_trace(go.Bar(x=dates_chart, y=df['Volume'], marker_color=burst_colors, name='能量雷達'), row=row_start+1, col=1)
    
    daily_change = df['Close'].pct_change() * 100
    change_colors = ['#00FF00' if val >= 0 else '#FF0000' for val in daily_change]
    fig.add_trace(go.Bar(x=dates_chart, y=daily_change, marker_color=change_colors, name='日波幅%'), row=row_start+2, col=1)

# --- 🏠 狀態管理：三大掣主頁 ---
if 'page' not in st.session_state: st.session_state.page = 'HOME'
if 'target' not in st.session_state: st.session_state.target = 'NONE'

if st.session_state.page == 'HOME':
    st.markdown("<h1 style='text-align:center;font-size:4rem;margin-top:80px;color:#FFD700;'>🐲 龍魂戰略總部</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🐉 龍魂神殿 (5.0雷達)"): st.session_state.page = 'DRAGON'
    if c2.button("📈 VCP 獵龍"): st.info("VCP 模式運作中"); st.session_state.page = 'DRAGON'
    if c3.button("🐢 海龜加注"): st.info("海龜 模式運作中"); st.session_state.page = 'DRAGON'

# --- 🐉 龍魂神殿 5.0 (主功能) ---
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

    # ==========================================
    # 🇺🇸 美股專屬：恢復 5 份 CSV 名單選擇
    # ==========================================
    if st.session_state.target == 'US':
        st.write("### 🇺🇸 選擇美股戰略名單：")
        m = st.columns(5)
        files = [("SP500_Equities.csv", "大藍籌"), ("Market_Focus.csv", "精選"), ("Industry_Focus.csv", "行業"), ("Core_Stocks.csv", "核心"), ("US_ETFs.csv", "美股ETF")]
        for i, (f, name) in enumerate(files):
            if m[i].button(f"選定 {name}"): 
                st.session_state.active_file = f
                st.success(f"✅ 已選定 {f}")
        with c_btn: btn_radar = st.button("📡 啟動 5.0 雙線雷達", use_container_width=True)

    # ==========================================
    # 🔍 個股專屬：修復個股掃描 (自動繞過 5.0 限制畫圖)
    # ==========================================
    elif st.session_state.target == 'SINGLE':
        st.write("### 🔍 個股自訂掃描：")
        col1, col2 = st.columns([3, 1])
        with col1:
            single_t = st.text_input("輸入股票代號 (例: NVDA, 0700.HK)", "").upper().strip()
        with col2:
            st.write("<br>", unsafe_allow_html=True)
            if st.button("📡 立即分析此股", use_container_width=True): 
                if single_t:
                    selected_tickers = [(single_t, "自選個股")]
                    btn_radar = True
                else: st.warning("請先輸入代號！")

    elif st.session_state.target == 'HK':
        st.write("### 🇭🇰 港股板塊掃描：")
        s_choice = st.selectbox("選擇板塊", list(HK_STOCK_MAP.keys()))
        with c_btn: btn_radar = st.button("📡 啟動 5.0 雙線雷達", use_container_width=True)

    elif st.session_state.target == 'ETF':
        st.write("### 📦 港股/美股 ETF 掃描：")
        s_choice = st.selectbox("選擇板塊", list(HK_ETF_MAP.keys()) + list(US_ETF_MAP.keys()))
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
        elif st.session_state.target == 'HK' or st.session_state.target == 'ETF':
            target_dict = HK_ETF_MAP if s_choice in HK_ETF_MAP else (US_ETF_MAP if s_choice in US_ETF_MAP else HK_STOCK_MAP)
            selected_tickers = [(t, s_choice) for t in target_dict.get(s_choice, [])]
            market_mode = "US" if s_choice in US_ETF_MAP else "HK"

        if selected_tickers:
            st.info(f"🚀 5.0 引擎掃描中 ({len(selected_tickers)} 隻)...")
            results = []; sl_list = []; pb = st.progress(0)
            
            for i, (t, sec) in enumerate(selected_tickers):
                pb.progress((i+1)/len(selected_tickers))
                df = smart_fetch(t)
                if not df.empty:
                    if is_ath_mode and (df['Close'].iloc[-1] / df['High'].tail(252).max()) < 0.93: continue
                    if check_stop_loss(df): sl_list.append(t)
                    res = scan_dragon_logic(df, t, sec, market_mode)
                    
                    if res: 
                        results.append(res)
                    elif st.session_state.target == 'SINGLE':
                        # 如果是個股掃描，但肥佬咗，強制畫圖！
                        st.session_state.force_chart_ticker = t
                        st.warning(f"⚠️ {t} 未能通過 5.0 嚴格審判（可能已觸發家法死刑或動力不足）。為您強制啟動 X光圖表：")
            
            if sl_list: sl_container.markdown(f"<div class='bear-warning'>🛡️ 戰損置頂: {' | '.join(sl_list)} 跌穿 10-EMA！</div>", unsafe_allow_html=True)
            
            if results:
                results = sorted(results, key=lambda x: x['Score'], reverse=True)
                st.session_state.dragon_results = results
                for r in results:
                    st.markdown(f"<div class='dragon-card'><div style='font-size:1.4rem;font-weight:bold;'>{r['Status']} {r['Ticker']} <span style='color:#00FFCC;'>({r['Sector']})</span> {r['Icons']}</div><div class='data-row'><b>戰術總分: {r['Score']}分</b> | <b style='color:#FF9900;'>原始戰力: {r.get('RawPower', 0)} 🔥</b> | <b style='color:#FF4B4B;'>扣分: {r.get('Penalty', 0)} 🛑</b> | <span style='color:#FF4B4B; font-weight:bold;'>🛑 止損(10-EMA): ${r['EMA10']}</span> | Bias: {r['Bias']}%<br>📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 🔥 買盤力: {r['Power']}x</div></div>", unsafe_allow_html=True)
            else: 
                if st.session_state.target != 'SINGLE':
                    st.warning("💤 萬人坑內無生還者。")

    # =========================================================
    # 📈 究極股價圖 (修復重貨橫條長短 + 修復重疊問題)
    # =========================================================
    chart_t = None
    if hasattr(st.session_state, 'dragon_results') and len(st.session_state.dragon_results) > 0:
        st.write("---")
        chart_t = st.selectbox("🎯 選擇目標查看「摩訶釋達」三層能量圖", [r['Ticker'] for r in st.session_state.dragon_results])
    elif st.session_state.target == 'SINGLE' and hasattr(st.session_state, 'force_chart_ticker'):
        chart_t = st.session_state.force_chart_ticker

    if chart_t:
        with st.spinner("繪製中..."):
            df_c = smart_fetch(chart_t, period="6mo")
            if not df_c.empty:
                dates_chart = df_c.index.strftime('%Y-%m-%d').tolist()
                ema10 = df_c['Close'].ewm(span=10, adjust=False).mean()
                fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.1, 0.15], vertical_spacing=0.02)
                
                # 1. K線 + 均線
                fig.add_trace(go.Candlestick(x=dates_chart, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="K線"), row=1, col=1)
                fig.add_trace(go.Scatter(x=dates_chart, y=df_c['Close'].rolling(50).mean(), mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                fig.add_trace(go.Scatter(x=dates_chart, y=ema10, name="10 EMA", line=dict(color='orange', width=2, dash='dot')), row=1, col=1)

                # 重貨區橫條 (修復關鍵：xaxis='x6' 定位，比例 max_c*1.1)
                counts, bins = np.histogram(df_c['Close'], bins=30, weights=df_c['Volume']); max_c = max(counts) if len(counts)>0 else 1
                fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136,136,136,0.4)', name='重貨區', hoverinfo='skip', xaxis='x6', yaxis='y1'), row=1, col=1)
                hvn_p = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                fig.add_hline(y=hvn_p * 0.985, line_dash="solid", line_color="#FF4B4B", annotation_text="🛑 重貨止損", row=1, col=1)
                
                # 2. 成交量與星星 (獨立喺 row 2)
                v_colors = ['#00FF00' if df_c['Close'].iloc[i] >= df_c['Open'].iloc[i] else '#FF0000' for i in range(len(df_c))]
                fig.add_trace(go.Bar(x=dates_chart, y=df_c['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                df_c['Vol50'] = df_c['Volume'].rolling(50).mean()
                for i in range(len(df_c)):
                    if df_c['Close'].iloc[i] > df_c['Open'].iloc[i] and df_c['Volume'].iloc[i] > df_c['Vol50'].iloc[i]*1.5:
                        fig.add_annotation(x=dates_chart[i], y=df_c['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", row=2, col=1)
                
                # 3-5. 能量副圖
                add_energy_subplots(fig, df_c, dates_chart, row_start=3)
                
                # 終極排版修復：鎖死 K 線同能量圖唔重疊
                fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111111', height=950, barmode='overlay', showlegend=False,
                    xaxis6=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*1.1], showgrid=False, showticklabels=False),
                    xaxis=dict(type='category', showticklabels=False), xaxis5=dict(type='category', title="日期"))
                st.plotly_chart(fig, use_container_width=True, theme=None)
