import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core_logic import scan_dragon_logic, smart_fetch, check_stop_loss
import time

# ==========================================
# 📚 港股字典保留 (維持原本功能)
# ==========================================
HK_STOCK_MAP = {
    "1. 互聯網巨頭": "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0772.HK 0020.HK 0241.HK 0136.HK 1999.HK 2018.HK 3888.HK 2142.HK 1896.HK 0777.HK 0113.HK 0590.HK 1980.HK 1797.HK 6618.HK 2400.HK 0285.HK".split(),
    "10. 房地產開發": "1109.HK 0688.HK 0960.HK 1918.HK 3383.HK 0884.HK 1233.HK 2777.HK 0813.HK 2007.HK 3301.HK 1638.HK 0012.HK 0016.HK 0017.HK 0101.HK 3900.HK 0817.HK 1966.HK".split()
}

HK_ETF_MAP = {
    "H1. 港股 ETF 全集": "2800.HK 2822.HK 3188.HK 3109.HK 2823.HK 2846.HK 3147.HK 3033.HK 3088.HK 3067.HK 3032.HK 7200.HK 7500.HK 7552.HK 2840.HK 3140.HK".split()
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

# --- 股價圖副功能：三層能量圖 ---
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
    # 🔍 個股專屬：修復個股掃描
    # ==========================================
    elif st.session_state.target == 'SINGLE':
        st.write("### 🔍 個股自訂掃描：")
        single_t = st.text_input("輸入股票代號 (例: NVDA, 0700.HK, TSLA)", "").upper().strip()
        if st.button("📡 立即分析此股"): 
            if single_t:
                selected_tickers = [(single_t, "自選個股")]
                btn_radar = True
            else: st.warning("請先輸入代號！")

    elif st.session_state.target == 'HK':
        st.write("### 🇭🇰 港股板塊掃描：")
        s_choice = st.selectbox("選擇範圍", ["🌐 啟動全星系大規模搜索"] + list(HK_STOCK_MAP.keys()))
        with c_btn: btn_radar = st.button("📡 啟動 5.0 雙線雷達", use_container_width=True)

    elif st.session_state.target == 'ETF':
        st.write("### 📦 港股 ETF 掃描：")
        s_choice = st.selectbox("選擇範圍", ["🌐 啟動全星系大規模搜索"] + list(HK_ETF_MAP.keys()))
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
            target_dict = HK_ETF_MAP if st.session_state.target == 'ETF' else HK_STOCK_MAP
            if "全星系" in s_choice:
                unique_map = {}
                for k, v in target_dict.items():
                    for t in v: unique_map[t] = k.split('.')[-1]
                selected_tickers = list(unique_map.items())
            else: selected_tickers = [(t, s_choice) for t in target_dict.get(s_choice, [])]
            market_mode = "HK"

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
                    if res: results.append(res)
            
            if sl_list: sl_container.markdown(f"<div class='bear-warning'>🛡️ 戰損置頂: {' | '.join(sl_list)} 跌穿 10-EMA！</div>", unsafe_allow_html=True)
            if results:
                results = sorted(results, key=lambda x: x['Score'], reverse=True)
                st.session_state.dragon_results = results
                for r in results:
                    st.markdown(f"<div class='dragon-card'><div style='font-size:1.4rem;font-weight:bold;'>{r['Status']} {r['Ticker']} <span style='color:#00FFCC;'>({r['Sector']})</span> {r['Icons']}</div><div class='data-row'><b>戰術總分: {r['Score']}分</b> | <b style='color:#FF9900;'>原始戰力: {r.get('RawPower', 0)} 🔥</b> | <b style='color:#FF4B4B;'>扣分: {r.get('Penalty', 0)} 🛑</b> | <span style='color:#FF4B4B; font-weight:bold;'>🛑 止損(10-EMA): ${r['EMA10']}</span> | Bias: {r['Bias']}%<br>📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 🔥 買盤力: {r['Power']}x</div></div>", unsafe_allow_html=True)
            else: st.warning("💤 萬人坑內無生還者。")

    # =========================================================
    # 📈 究極股價圖 (修復重貨橫條長短問題)
    # =========================================================
    if hasattr(st.session_state, 'dragon_results'):
        st.write("---")
        chart_t = st.selectbox("🎯 選擇目標查看「摩訶釋達」三層能量圖", [r['Ticker'] for r in st.session_state.dragon_results])
        if chart_t:
            with st.spinner("繪製中..."):
                df_c = smart_fetch(chart_t, period="6mo")
                if not df_c.empty:
                    dates_chart = df_c.index.strftime('%Y-%m-%d').tolist()
                    fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.1, 0.15], vertical_spacing=0.02)
                    # 1. K線
                    fig.add_trace(go.Candlestick(x=dates_chart, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="K線"), row=1, col=1)
                    # 重貨區橫條 (修復關鍵：xaxis='x6' 定位)
                    counts, bins = np.histogram(df_c['Close'], bins=30, weights=df_c['Volume']); max_c = max(counts) if len(counts)>0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136,136,136,0.4)', name='重貨區', xaxis='x6', yaxis='y1'), row=1, col=1)
                    # 2. 成交量與星星
                    v_colors = ['#00FF00' if df_c['Close'].iloc[i] >= df_c['Open'].iloc[i] else '#FF0000' for i in range(len(df_c))]
                    fig.add_trace(go.Bar(x=dates_chart, y=df_c['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    df_c['Vol50'] = df_c['Volume'].rolling(50).mean()
                    for i in range(len(df_c)):
                        if df_c['Close'].iloc[i] > df_c['Open'].iloc[i] and df_c['Volume'].iloc[i] > df_c['Vol50'].iloc[i]*1.5:
                            fig.add_annotation(x=dates_chart[i], y=df_c['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", row=2, col=1)
                    # 3-5. 能量副圖
                    add_energy_subplots(fig, df_c, dates_chart, row_start=3)
                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111111', height=950, barmode='overlay', showlegend=False,
                        xaxis6=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False),
                        xaxis=dict(type='category', showticklabels=False), xaxis5=dict(type='category', title="日期"))
                    st.plotly_chart(fig, use_container_width=True, theme=None)
