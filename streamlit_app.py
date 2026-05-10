import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core_logic import scan_dragon_logic, smart_fetch, check_stop_loss
import time

# --- 終極大字典 ---
HK_STOCK_MAP = {
    "1. 互聯網巨頭": "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0772.HK 0020.HK 0241.HK 0136.HK 1999.HK 2018.HK 3888.HK 2142.HK 1896.HK 0777.HK 0113.HK 0590.HK 1980.HK 1797.HK 6618.HK 2400.HK 0285.HK".split(),
    "2. 半導體與芯片": "0981.HK 1347.HK 0285.HK 1478.HK 1833.HK 0522.HK 0732.HK 2382.HK 2018.HK 0099.HK 1385.HK 1138.HK 1910.HK 6088.HK 3898.HK 6123.HK 3389.HK".split(),
    "3. 新能源車與整車": "1211.HK 2015.HK 9866.HK 9868.HK 0175.HK 2333.HK 1114.HK 0489.HK 3606.HK 0867.HK 1316.HK 1958.HK 1585.HK 0315.HK 1274.HK 2150.HK 1122.HK 3808.HK 9863.HK".split(),
    "4. 重型工業與機械": "1133.HK 1072.HK 1888.HK 1286.HK 3399.HK 1157.HK 2727.HK 1727.HK 6030.HK 0598.HK 0165.HK 0350.HK 1071.HK 1839.HK 1866.HK 0316.HK 0148.HK 1651.HK 1829.HK 1044.HK".split(),
    "12. 消費電子硬件": "2382.HK 2018.HK 0669.HK 0992.HK 1310.HK 0008.HK 1478.HK 0285.HK 0321.HK 0596.HK 0732.HK 0522.HK 1070.HK 0099.HK 0285.HK".split(),
    "13. 核心消費與餐飲": "0291.HK 2319.HK 0322.HK 1876.HK 9633.HK 6186.HK 0220.HK 1117.HK 0151.HK 1458.HK 1368.HK 6862.HK 9922.HK 2005.HK 0831.HK 0341.HK 1089.HK 6868.HK 1929.HK".split(),
    "14. 生物科技探索": "2269.HK 2359.HK 1801.HK 2162.HK 9966.HK 9969.HK 3759.HK 1548.HK 9926.HK 6990.HK 2126.HK 9939.HK 1099.HK 2171.HK 0512.HK 1952.HK 2096.HK".split()
}

HK_ETF_MAP = {
    "H1. A股門戶": "2822.HK 3188.HK 3109.HK 2823.HK 2846.HK 3147.HK 2801.HK 3010.HK 3081.HK 3151.HK 3072.HK 3042.HK 2839.HK 3180.HK 2827.HK 3139.HK 3118.HK 2838.HK".split(),
    "H2. 港股科技": "3033.HK 3088.HK 9888.HK 3067.HK 3167.HK 3191.HK 7709.HK 9191.HK 3434.HK 3112.HK 3171.HK 3091.HK 3032.HK 3001.HK 3060.HK 2826.HK".split(),
    "H4. 紅利收息": "3110.HK 3070.HK 3101.HK 3037.HK 3145.HK 3010.HK 3081.HK 3115.HK 3006.HK 3150.HK 3422.HK 3116.HK 3113.HK 3031.HK 3153.HK".split()
}

st.set_page_config(page_title="龍魂神殿 2.0", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #FFFFFF !important; }
    div.stButton > button { background-color: #000000 !important; color: #FFFFFF !important; border: 2px solid #FFFFFF !important; border-radius: 0px !important; font-weight: 900 !important; width: 100%; margin-bottom: 5px; }
    div.stButton > button:hover { background-color: #FFFFFF !important; color: #000000 !important; }
    .dragon-card { border-left: 5px solid #00FFCC; background-color: #111111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .data-row { font-size: 0.95rem; color: #CCCCCC; margin-top: 8px; line-height: 1.6; }
    .bear-warning { color: #FF0000 !important; font-size: 1.5rem; font-weight: 900; text-align: center; border: 3px dashed red; background-color: #220000; padding: 15px; margin: 10px 0; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

def add_energy_subplots(fig, df, dates_chart, row_start):
    var1 = df['Close'] - df['Low']; var2 = df['High'] - df['Close']; var3 = np.maximum(df['High'] - df['Low'], 0.001)
    buyvol = np.where(var3 > 0, df['Volume'] * var1 / var3, 0)
    sellvol = np.where(var3 > 0, df['Volume'] * var2 / var3, 0)
    netvol = buyvol - sellvol
    netma = pd.Series(netvol).rolling(10, min_periods=1).mean()
    
    fig.add_trace(go.Bar(x=dates_chart, y=buyvol, marker_color='#808000', name='買盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    fig.add_trace(go.Bar(x=dates_chart, y=-sellvol, marker_color='#800000', name='賣盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
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

if 'page' not in st.session_state: st.session_state.page = 'HOME'
if 'target' not in st.session_state: st.session_state.target = 'NONE'

if st.session_state.page == 'HOME':
    st.markdown("<h1 style='text-align:center;font-size:4rem;margin-top:80px;'>🐲 龍魂戰略總部</h1><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🐉 龍魂神殿"): st.session_state.page = 'DRAGON'
    if c2.button("📈 VCP 獵龍"): st.session_state.page = 'VCP'
    if c3.button("🐢 海龜加注"): st.session_state.page = 'TURTLE'

elif st.session_state.page == 'DRAGON':
    st.markdown("<h1 style='text-align:center;'>🐲 龍魂神殿 2.0 旗艦雷達</h1>", unsafe_allow_html=True)
    nav = st.columns(6)
    if nav[0].button("⬅️ 返回"): st.session_state.page = 'HOME'
    if nav[1].button("🇭🇰 港股"): st.session_state.target = 'HK'
    if nav[2].button("🇺🇸 美股"): st.session_state.target = 'US'
    if nav[3].button("📦 ETF"): st.session_state.target = 'ETF'
    if nav[4].button("🔍 個股"): st.session_state.target = 'SINGLE'
    
    st.markdown("---")
    
    c_ath, c_btn = st.columns([3, 1])
    with c_ath:
        is_ath_mode = st.checkbox("🔥 啟動 ATH 歷史新高極致過濾")
    with c_btn:
        btn_radar = st.button("📡 啟動雷達", use_container_width=True)
    
    st.markdown("---")
    sl_container = st.empty()
    selected_tickers = []
    market_mode = "HK"

    if st.session_state.target == 'US':
        st.write("### 🇺🇸 選擇美股戰略名單：")
        m = st.columns(5)
        files = [("SP500_Equities.csv", "大藍籌"), ("Market_Focus.csv", "精選"), ("Industry_Focus.csv", "行業"), ("Core_Stocks.csv", "核心"), ("US_ETFs.csv", "美股ETF")]
        for i, (f, name) in enumerate(files):
            if m[i].button(f"選定 {name}"): st.session_state.active_file = f; st.success(f"✅ 已選定 {f}")

    elif st.session_state.target == 'ETF':
        st.write("### 📦 選擇 ETF 戰場：")
        e1, e2 = st.columns(2)
        if e1.button("🇭🇰 掃描港股 ETF"): st.session_state.active_file = 'HK_ETF'; st.success("✅ 已選港股 ETF")
        if e2.button("🇺🇸 掃描美股 ETF"): st.session_state.active_file = 'US_ETFs.csv'; st.success("✅ 已選美股 ETF")

    elif st.session_state.target == 'SINGLE':
        st.write("### 🔍 個股掃描：")
        single_t = st.text_input("輸入股票代號 (例: 0700.HK, NVDA)")
        if single_t:
            st.session_state.single_ticker = single_t.upper()
            st.success(f"✅ 已鎖定個股: {st.session_state.single_ticker} (請按啟動雷達)")

    if btn_radar:
        if st.session_state.target == 'SINGLE' and hasattr(st.session_state, 'single_ticker'):
            selected_tickers = [(st.session_state.single_ticker, "自選")]
            market_mode = "US" if not st.session_state.single_ticker.endswith(".HK") else "HK"
        
        elif st.session_state.target == 'HK':
            unique_map = {}
            for k, v in HK_STOCK_MAP.items():
                sector = k.split('.')[1].strip() if '.' in k else k
                for t in v:
                    if t not in unique_map: unique_map[t] = sector
            selected_tickers = list(unique_map.items())
            market_mode = "HK"
            
        elif st.session_state.target == 'ETF':
            if getattr(st.session_state, 'active_file', '') == 'HK_ETF':
                unique_etfs = set([t for sub in HK_ETF_MAP.values() for t in sub])
                selected_tickers = [(t, "港股ETF") for t in unique_etfs]
                market_mode = "HK"
            elif getattr(st.session_state, 'active_file', '') == 'US_ETFs.csv':
                try:
                    df_csv = pd.read_csv('US_ETFs.csv')
                    col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol']][0]
                    selected_tickers = [(t, "美股ETF") for t in df_csv[col].dropna().unique()]
                    market_mode = "US"
                except: st.error("⚠️ 讀取 US_ETFs.csv 失敗。")
                
        elif st.session_state.target == 'US' and hasattr(st.session_state, 'active_file'):
            try:
                df_csv = pd.read_csv(st.session_state.active_file)
                col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol', '代號']][0]
                selected_tickers = [(t, "美股") for t in df_csv[col].dropna().unique()]
                market_mode = "US"
            except: pass

        if selected_tickers:
            st.info(f"🚀 龍魂發動！全火力掃描 {len(selected_tickers)} 隻不重覆標的...")
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

            if results:
                results = sorted(results, key=lambda x: x['Score'], reverse=True)
                st.session_state.dragon_results = results
                for r in results:
                    st.markdown(f"""
                        <div class='dragon-card'>
                            <div style='font-size:1.4rem;font-weight:bold;'>{r['Status']} {r['Ticker']} <span style='color:#00FFCC;'>({r['Sector']})</span> {r['Icons']}</div>
                            <div class='data-row'>
                                <b>總分: {r['Score']}分</b> | <span style='color:#FF4B4B; font-weight:bold;'>🛑 止損(10-EMA): ${r['EMA10']}</span> | Bias: {r['Bias']}%<br>
                                📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 🌊 OBV: 狀態 1 | 💰 資金流: {r['Flow']} | 🎯 集中度: {r['Conc']} | 🔥 買盤力: {r['Power']}x
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else: st.warning("💤 萬人坑內無生還者。")

    # =========================================================
    # 📈 X光戰術圖 (100% 舊 Code 搬運：HVN 橫條 + 🌟 星星)
    # =========================================================
    if hasattr(st.session_state, 'dragon_results'):
        st.write("---")
        chart_t = st.selectbox("🎯 查看 X 光戰術圖", [r['Ticker'] for r in st.session_state.dragon_results])
        if chart_t:
            with st.spinner("正在繪製全黑戰術圖表..."):
                try:
                    df_c = smart_fetch(chart_t, period="6mo")
                    if not df_c.empty:
                        ema10 = df_c['Close'].ewm(span=10, adjust=False).mean()
                        dates_chart = df_c.index.strftime('%Y-%m-%d').tolist()
                        
                        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.15, 0.1], vertical_spacing=0.02)
                        
                        # K線
                        fig.add_trace(go.Candlestick(x=dates_chart, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="K線"), row=1, col=1)
                        fig.add_trace(go.Scatter(x=dates_chart, y=df_c['Close'].rolling(50).mean(), mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=dates_chart, y=ema10, name="10 EMA", line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                        
                        # 🎯 買入點
                        recent_high = df_c['High'].tail(20).max()
                        fig.add_hline(y=recent_high, line_dash="dash", line_color="#00FFCC", annotation_text="🎯 買入點", row=1, col=1)
                        
                        # ==================================
                        # 🧱 舊 Code 搬運：重貨區 HVN 橫條
                        # ==================================
                        counts, bins = np.histogram(df_c['Close'], bins=30, weights=df_c['Volume'])
                        max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                        hvn_p = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                        stop_loss = hvn_p * 0.985
                        fig.add_hline(y=stop_loss, line_dash="solid", line_color="#FF4B4B", annotation_text="🛑 重貨止損", row=1, col=1)
                        
                        # 用 xaxis6 將 HVN 正確顯示出長短不一的效果
                        fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136,136,136,0.4)', name='重貨區', hoverinfo='skip', xaxis='x6', yaxis='y1'), row=1, col=1)
                        # ==================================

                        # ==================================
                        # 🌟 舊 Code 搬運：成交量與星星
                        # ==================================
                        v_colors = ['#00FF00' if df_c['Close'].iloc[i] >= df_c['Open'].iloc[i] else '#FF0000' for i in range(len(df_c))]
                        fig.add_trace(go.Bar(x=dates_chart, y=df_c['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                        
                        df_c['Vol50'] = df_c['Volume'].rolling(50, min_periods=1).mean()
                        for i in range(len(df_c)):
                            if df_c['Close'].iloc[i] > df_c['Open'].iloc[i] and df_c['Volume'].iloc[i] > df_c['Vol50'].iloc[i]*1.5:
                                fig.add_annotation(x=dates_chart[i], y=df_c['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", xanchor="center", font=dict(size=14, color="#FFD700"), row=2, col=1)
                        # ==================================

                        add_energy_subplots(fig, df_c, dates_chart, row_start=3)
                        
                        # 鎖定全黑與正確座標 (xaxis6 range 解決一樣長問題)
                        fig.update_layout(
                            template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111111', height=950, barmode='overlay', 
                            xaxis6=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False), 
                            xaxis=dict(type='category', showticklabels=False), showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True, theme=None)
                except Exception as e: st.error(f"繪圖出錯: {e}")
