import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core_logic import scan_dragon_logic, smart_fetch, check_stop_loss
import time

# ==========================================
# 📚 大字典：一字不漏
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
    "3. 基礎軟件與 SaaS": "INTU VMW CDNS PTC MSTR SPT ALTR MANH GWRE PAYC APPN TYL BLK PEGA BL DT DBX PATH BSY NCNO WK ME LAW ALIT VRM HCP RNG".split()
}

HK_ETF_MAP = {
    "H1. 旗艦大盤": "2800.HK 2822.HK 3188.HK 3109.HK".split()
}

# --- 黑魂 UI ---
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

# =========================================================================
# 📈 爺爺完美移植：摩訶釋達・三層能量股價圖
# =========================================================================
def add_energy_subplots(fig, df, dates_chart, row_start):
    # 第一層：買賣力度 (2層4色立體化)
    var1 = df['Close'] - df['Low']; var2 = df['High'] - df['Close']; var3 = np.maximum(df['High'] - df['Low'], 0.001)
    buyvol = np.where(var3 > 0, df['Volume'] * var1 / var3, 0)
    sellvol = np.where(var3 > 0, df['Volume'] * var2 / var3, 0)
    netvol = buyvol - sellvol
    netma = pd.Series(netvol).rolling(10, min_periods=1).mean()
    
    # 總兵力底色 (暗色, 闊身)
    fig.add_trace(go.Bar(x=dates_chart, y=buyvol, marker_color='#808000', name='買盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    fig.add_trace(go.Bar(x=dates_chart, y=-sellvol, marker_color='#800000', name='賣盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    # 淨勝方高光 (鮮色, 幼身疊加)
    net_colors = ['#00FF00' if val > 0 else '#FF0000' for val in netvol]
    fig.add_trace(go.Bar(x=dates_chart, y=netvol, marker_color=net_colors, name='淨勝方', width=0.4), row=row_start, col=1)
    fig.add_trace(go.Scatter(x=dates_chart, y=netma, mode='lines', line=dict(color='white', width=2), name='氣脈10MA'), row=row_start, col=1)

    # 第二層：王者能量雷達
    v_ma = df['Volume'].rolling(20, min_periods=1).mean()
    v_std = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
    v_upper = v_ma + (2.0 * v_std); ma60 = df['Volume'].rolling(60, min_periods=1).mean(); roc = abs(df['Close'].pct_change()) * 100
    is_burst = (df['Volume'] > v_upper) & (df['Volume'] > ma60 * 1.9) & (roc > 2.0)
    burst_colors = ['#00FFFF' if (is_burst.iloc[i] and df['Close'].iloc[i] > df['Open'].iloc[i]) else ('#FF00FF' if is_burst.iloc[i] else 'rgba(136,136,136,0.3)') for i in range(len(df))]
    fig.add_trace(go.Bar(x=dates_chart, y=df['Volume'], marker_color=burst_colors, name='能量雷達'), row=row_start+1, col=1)

    # 第三層：日波幅%
    daily_change = df['Close'].pct_change() * 100
    change_colors = ['#00FF00' if val >= 0 else '#FF0000' for val in daily_change]
    fig.add_trace(go.Bar(x=dates_chart, y=daily_change, marker_color=change_colors, name='日波幅%'), row=row_start+2, col=1)

# =========================================================================
# 🏠 狀態管理：三大掣主頁
# =========================================================================
if 'page' not in st.session_state: st.session_state.page = 'HOME'
if 'target' not in st.session_state: st.session_state.target = 'NONE'

if st.session_state.page == 'HOME':
    st.markdown("<h1 style='text-align:center;font-size:4rem;margin-top:80px;color:#FFD700;'>🐲 龍魂戰略總部</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;font-size:1.2rem;color:#AAA;'>5.0 明暗雙線引擎已啟動</p>", unsafe_allow_html=True)
    
    st.write("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🐉 龍魂神殿 (5.0雷達)"): st.session_state.page = 'DRAGON'
    if c2.button("📈 VCP 獵龍 (開發中)"): st.warning("VCP 開發中")
    if c3.button("🐢 海龜加注 (開發中)"): st.warning("海龜 開發中")

# =========================================================================
# 🐉 龍魂神殿 5.0 (主功能)
# =========================================================================
elif st.session_state.page == 'DRAGON':
    st.markdown("<h1 style='text-align:center; color:#00FFCC;'>🐲 龍魂神殿 5.0 旗艦雷達</h1>", unsafe_allow_html=True)
    
    # 頂部導航
    nav = st.columns(6)
    if nav[0].button("⬅️ 返回總部"): st.session_state.page = 'HOME'
    if nav[1].button("🇭🇰 港股"): st.session_state.target = 'HK'
    if nav[2].button("🇺🇸 美股"): st.session_state.target = 'US'
    if nav[3].button("📦 ETF"): st.session_state.target = 'ETF'
    if nav[4].button("🔍 個股"): st.session_state.target = 'SINGLE'
    
    st.markdown("---")
    
    # 控制台
    c_ath, c_btn = st.columns([3, 1])
    with c_ath:
        is_ath_mode = st.checkbox("🔥 啟動 ATH 歷史新高極致過濾 (建議開啟)")
    
    sl_container = st.empty()
    selected_tickers = []
    market_mode = "HK"
    btn_radar = False

    # ==========================================
    # 處理四種不同嘅選擇介面
    # ==========================================
    if st.session_state.target == 'SINGLE':
        st.write("### 🔍 個股專屬掃描：")
        col1, col2 = st.columns([3, 1])
        with col1:
            single_t = st.text_input("輸入股票代號 (例: 0700.HK, NVDA, TSLA)", "")
        with col2:
            st.write("<br>", unsafe_allow_html=True) # 對齊
            # 爺爺特製：個股專屬掃描掣！
            btn_single_radar = st.button("🔍 立即掃描此股", use_container_width=True)
            if btn_single_radar and single_t:
                btn_radar = True # 觸發下方嘅雷達邏輯

    elif st.session_state.target == 'HK':
        st.write("### 🇭🇰 港股大名單：")
        s_choice = st.selectbox("選擇板塊", ["🌐 啟動全星系大規模搜索"] + list(HK_STOCK_MAP.keys()))
        with c_btn: btn_radar = st.button("📡 啟動 5.0 雙線雷達", use_container_width=True)
        
    elif st.session_state.target == 'US':
        st.write("### 🇺🇸 美股大名單：")
        s_choice = st.selectbox("選擇板塊", ["🌐 啟動全星系大規模搜索"] + list(US_STOCK_MAP.keys()))
        with c_btn: btn_radar = st.button("📡 啟動 5.0 雙線雷達", use_container_width=True)

    elif st.session_state.target == 'ETF':
        st.write("### 📦 港股 ETF 名單：")
        s_choice = st.selectbox("選擇板塊", ["🌐 啟動全星系大規模搜索"] + list(HK_ETF_MAP.keys()))
        with c_btn: btn_radar = st.button("📡 啟動 5.0 雙線雷達", use_container_width=True)

    # ==========================================
    # 🚀 執行 5.0 掃描邏輯
    # ==========================================
    if btn_radar:
        # 1. 決定掃描名單
        if st.session_state.target == 'SINGLE' and single_t:
            selected_tickers = [(single_t.upper().strip(), "自訂分析")]
            market_mode = "US" if not single_t.upper().endswith(".HK") else "HK"
        else:
            target_dict = US_STOCK_MAP if st.session_state.target == 'US' else (HK_ETF_MAP if st.session_state.target == 'ETF' else HK_STOCK_MAP)
            market_mode = "US" if st.session_state.target == 'US' else "HK"
            
            if "全星系" in s_choice:
                unique_map = {}
                for k, v in target_dict.items():
                    sector = k.split('.')[1].strip() if '.' in k else k
                    for t in v:
                        if t not in unique_map: unique_map[t] = sector
                selected_tickers = list(unique_map.items())
            else:
                sector = s_choice.split('.')[1].strip() if '.' in s_choice else s_choice
                selected_tickers = [(t, sector) for t in target_dict.get(s_choice, [])]

        # 2. 開始掃描
        if selected_tickers:
            st.info(f"🚀 龍魂發動！5.0 引擎全火力掃描 {len(selected_tickers)} 隻標的...")
            results = []; sl_list = []; pb = st.progress(0)
            
            for i, (t, sec) in enumerate(selected_tickers):
                pb.progress((i+1)/len(selected_tickers))
                df = smart_fetch(t)
                
                if is_ath_mode and not df.empty:
                    if (df['Close'].iloc[-1] / df['High'].tail(252).max()) < 0.93: continue
                
                if check_stop_loss(df): sl_list.append(t)
                res = scan_dragon_logic(df, t, sec, market_mode)
                if res: results.append(res)
            
            if sl_list: sl_container.markdown(f"<div class='bear-warning'>🛡️ 戰損置頂: {' | '.join(sl_list)} 跌穿 10-EMA！</div>", unsafe_allow_html=True)

            # 3. 顯示結果卡片
            if results:
                results = sorted(results, key=lambda x: x['Score'], reverse=True)
                st.session_state.dragon_results = results
                
                st.success(f"🎉 審判完成！成功尋獲 {len(results)} 隻過關真龍！")
                for r in results:
                    st.markdown(f"""
                        <div class='dragon-card'>
                            <div style='font-size:1.4rem;font-weight:bold;'>{r['Status']} {r['Ticker']} <span style='color:#00FFCC;'>({r['Sector']})</span> {r['Icons']}</div>
                            <div class='data-row'>
                                <b>戰術總分: {r['Score']}分</b> | 
                                <b style='color:#FF9900;'>原始戰力: {r.get('RawPower', 0)} 🔥</b> | 
                                <b style='color:#FF4B4B;'>扣分: {r.get('Penalty', 0)} 🛑</b> | 
                                <span style='color:#FF4B4B; font-weight:bold;'>🛑 止損(10-EMA): ${r['EMA10']}</span> | Bias: {r['Bias']}%<br>
                                📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 🌊 OBV: 狀態 1 | 💰 資金流: {r['Flow']} | 🎯 集中度: {r['Conc']} | 🔥 買盤力: {r['Power']}x
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else: 
                st.warning("💤 萬人坑內無生還者。(無股符合 5.0 嚴格標準)")
        else:
            st.error("請輸入有效嘅股票代號！")

    # =========================================================
    # 📈 X光戰術圖 (完美移植摩訶圖)
    # =========================================================
    if hasattr(st.session_state, 'dragon_results') and len(st.session_state.dragon_results) > 0:
        st.write("---")
        chart_t = st.selectbox("🎯 選擇目標查看「3 層視覺化戰術儀表板」", [r['Ticker'] for r in st.session_state.dragon_results], key="dragon_chart_select")
        if chart_t:
            with st.spinner("正在為您繪製極致戰術圖表..."):
                try:
                    df_c = smart_fetch(chart_t, period="6mo")
                    if not df_c.empty:
                        ema10 = df_c['Close'].ewm(span=10, adjust=False).mean()
                        dates_chart = df_c.index.strftime('%Y-%m-%d').tolist()
                        
                        # 設定 5 行，分配比例完美配合 3 層能量圖
                        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.15, 0.1], vertical_spacing=0.02)
                        
                        # 1. K線 + 均線
                        fig.add_trace(go.Candlestick(x=dates_chart, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="K線"), row=1, col=1)
                        fig.add_trace(go.Scatter(x=dates_chart, y=df_c['Close'].rolling(50).mean(), mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=dates_chart, y=ema10, name="10 EMA", line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                        
                        # 買入位與重貨區 HVN
                        recent_high = df_c['High'].tail(20).max()
                        fig.add_hline(y=recent_high, line_dash="dash", line_color="#00FFCC", annotation_text="🎯 買入點", row=1, col=1)
                        
                        counts, bins = np.histogram(df_c['Close'], bins=30, weights=df_c['Volume'])
                        max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                        hvn_p = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                        stop_loss = hvn_p * 0.985
                        fig.add_hline(y=stop_loss, line_dash="solid", line_color="#FF4B4B", annotation_text="🛑 重貨止損", row=1, col=1)
                        fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136,136,136,0.4)', name='重貨區', hoverinfo='skip', xaxis='x6', yaxis='y1'), row=1, col=1)

                        # 2. 成交量 + 大戶星星
                        v_colors = ['#00FF00' if df_c['Close'].iloc[i] >= df_c['Open'].iloc[i] else '#FF0000' for i in range(len(df_c))]
                        fig.add_trace(go.Bar(x=dates_chart, y=df_c['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                        
                        df_c['Vol50'] = df_c['Volume'].rolling(50).mean()
                        for i in range(len(df_c)):
                            if df_c['Close'].iloc[i] > df_c['Open'].iloc[i] and df_c['Volume'].iloc[i] > df_c['Vol50'].iloc[i]*1.5:
                                fig.add_annotation(x=dates_chart[i], y=df_c['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", xanchor="center", font=dict(size=14, color="#FFD700"), row=2, col=1)

                        # 3, 4, 5. 三層能量副圖
                        add_energy_subplots(fig, df_c, dates_chart, row_start=3)
                        
                        # 鎖死黑底，配置
                        fig.update_layout(
                            template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111111', height=950, barmode='overlay', 
                            hovermode='x unified',
                            xaxis6=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False), 
                            xaxis=dict(type='category', showticklabels=False, showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True, theme=None)
                except Exception as e: st.error(f"繪圖出錯: {e}")
