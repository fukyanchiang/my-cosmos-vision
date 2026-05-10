import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core_logic import scan_dragon_logic, smart_fetch, check_stop_loss

# --- 1. 黑魂 UI 視覺 ---
st.set_page_config(page_title="龍魂神殿 2.0", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #FFFFFF; }
    div.stButton > button { background-color: #000000 !important; color: #FFFFFF !important; border: 2px solid #FFFFFF !important; border-radius: 0px !important; font-weight: 900 !important; width: 100%; margin-bottom: 5px; }
    div.stButton > button:hover { background-color: #FFFFFF !important; color: #000000 !important; }
    .dragon-card { border-left: 5px solid #00FFCC; background: #111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .data-row { font-size: 0.85rem; color: #CCCCCC; margin-top: 8px; }
    .bear-warning { color: #FF0000 !important; font-size: 1.5rem; font-weight: 900; text-align: center; text-shadow: 2px 2px 5px #000; padding: 15px; border: 3px dashed red; background-color: #220000; margin: 10px 0; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 舊 Code 圖表羅輯 (三層能量指標) ---
def add_energy_subplots(fig, df, row_start):
    var1 = df['Close'] - df['Low']; var2 = df['High'] - df['Close']
    var3 = np.maximum(df['High'] - df['Low'], 0.001)
    buyvol = np.where(var3 > 0, df['Volume'] * var1 / var3, 0)
    sellvol = np.where(var3 > 0, df['Volume'] * var2 / var3, 0)
    netvol = buyvol - sellvol
    netma = pd.Series(netvol).rolling(10, min_periods=1).mean()
    dates = df.index.strftime('%Y-%m-%d')
    
    # 第一層：總兵力底色與高光
    fig.add_trace(go.Bar(x=dates, y=buyvol, marker_color='#808000', name='買盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    fig.add_trace(go.Bar(x=dates, y=-sellvol, marker_color='#800000', name='賣盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    net_colors = ['#00FF00' if val > 0 else '#FF0000' for val in netvol]
    fig.add_trace(go.Bar(x=dates, y=netvol, marker_color=net_colors, name='淨勝方', width=0.4), row=row_start, col=1)
    fig.add_trace(go.Scatter(x=dates, y=netma, mode='lines', line=dict(color='white', width=2), name='氣脈10MA'), row=row_start, col=1)

    # 第二層：王者能量雷達
    v_ma = df['Volume'].rolling(20, min_periods=1).mean(); v_std = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
    v_upper = v_ma + (2.0 * v_std); ma60 = df['Volume'].rolling(60, min_periods=1).mean(); roc = abs(df['Close'].pct_change()) * 100
    is_burst = (df['Volume'] > v_upper) & (df['Volume'] > ma60 * 1.9) & (roc > 2.0)
    burst_colors = ['#00FFFF' if (is_burst.iloc[i] and df['Close'].iloc[i] > df['Open'].iloc[i]) else ('#FF00FF' if is_burst.iloc[i] else 'rgba(136,136,136,0.3)') for i in range(len(df))]
    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=burst_colors, name='能量雷達'), row=row_start+1, col=1)

    # 第三層：日波幅%
    daily_change = df['Close'].pct_change() * 100
    change_colors = ['#00FF00' if val >= 0 else '#FF0000' for val in daily_change]
    fig.add_trace(go.Bar(x=dates, y=daily_change, marker_color=change_colors, name='日波幅%'), row=row_start+2, col=1)

# --- 3. 狀態管理 ---
if 'page' not in st.session_state: st.session_state.page = 'HOME'
if 'target' not in st.session_state: st.session_state.target = 'NONE'

# --- 4. 首頁：3 個大掣 ---
if st.session_state.page == 'HOME':
    st.markdown("<h1 style='text-align:center;font-size:4rem;margin-top:80px;'>🐲 龍魂戰略總部</h1><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🐉 龍魂神殿 (11鐵律掃描)"): st.session_state.page = 'DRAGON'
    if c2.button("📈 VCP 形態獵龍"): st.session_state.page = 'VCP'
    if c3.button("🐢 海龜 N 字加注"): st.session_state.page = 'TURTLE'

# --- 5. 龍魂神殿專頁 ---
elif st.session_state.page == 'DRAGON':
    st.markdown("<h1 style='text-align:center;'>🐲 龍魂神殿 2.0 旗艦雷達</h1>", unsafe_allow_html=True)
    
    # 7 個橫向導航掣
    nav = st.columns(7)
    if nav[0].button("⬅️ 返回"): st.session_state.page = 'HOME'
    if nav[1].button("🇭🇰 港股"): st.session_state.target = 'HK_STOCK'
    if nav[2].button("🇺🇸 美股"): st.session_state.target = 'US_CSV'
    if nav[3].button("🔍 個股"): st.session_state.target = 'SINGLE'
    if nav[4].button("📦 ETF"): st.session_state.target = 'ETF'
    if nav[5].button("🔥 ATH"): st.session_state.target = 'ATH'
    btn_radar = nav[6].button("📡 啟動雷達")

    st.markdown("---")
    
    # 預留戰損置頂位置
    stop_loss_container = st.empty()

    # 選擇戰場
    selected_tickers = []
    market_mode = "HK"

    if st.session_state.target == 'US_CSV':
        st.write("### 🇺🇸 選擇美股戰略名單：")
        m = st.columns(5)
        files = [("SP500_Equities.csv", "大藍籌"), ("Market_Focus.csv", "精選"), ("Industry_Focus.csv", "行業"), ("Core_Stocks.csv", "核心"), ("US_ETFs.csv", "ETF")]
        for i, (f, name) in enumerate(files):
            if m[i].button(f"選定 {name}"): 
                st.session_state.active_file = f
                st.success(f"✅ 已選定 {name}，請按右上角『📡 啟動雷達』")

    # 發動雷達
    if btn_radar:
        if st.session_state.target == 'HK_STOCK':
            selected_tickers = [("0700.HK", "互聯網"), ("9988.HK", "互聯網"), ("3690.HK", "互聯網"), ("0981.HK", "半導體"), ("1211.HK", "汽車")]
            market_mode = "HK"
        elif st.session_state.target == 'US_CSV' and hasattr(st.session_state, 'active_file'):
            try:
                df_csv = pd.read_csv(st.session_state.active_file)
                col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol', '代號']][0]
                selected_tickers = [(t, "美股") for t in df_csv[col].dropna().tolist()]
                market_mode = "US"
            except: st.error(f"⚠️ 讀取 {st.session_state.active_file} 失敗。")
        
        if selected_tickers:
            st.info(f"🚀 龍魂發動！正在掃描 {len(selected_tickers)} 隻標的 (包含 10-EMA 戰損監控)...")
            results = []
            stop_loss_triggered = []
            pb = st.progress(0)
            
            # 限制測試數量，防止等太耐
            scan_list = selected_tickers[:50]
            for idx, (t, sec) in enumerate(scan_list):
                pb.progress((idx+1)/len(scan_list))
                df = smart_fetch(t)
                
                # 🛡️ 執行 10-EMA 止損偵測
                if check_stop_loss(df):
                    stop_loss_triggered.append(t)

                # 🐲 執行 11 鐵律篩選
                res = scan_dragon_logic(df, t, sec, market_mode)
                if res: results.append(res)
            
            # 更新頂部戰損 Banner
            if stop_loss_triggered:
                sl_str = " | ".join([f"[{t}]" for t in stop_loss_triggered])
                stop_loss_container.markdown(f"<div class='bear-warning'>🛡️ 戰損置頂警報：以下股票最近 2 日跌穿 10-day EMA，請嚴格執行止損！<br>{sl_str}</div>", unsafe_allow_html=True)
            else:
                stop_loss_container.success("🛡️ 戰場安全，掃描清單內暫無觸發 10-EMA 止損之標的。")

            # 顯示合格名單
            if results:
                results = sorted(results, key=lambda x: (x['Score'], x['IconCount']), reverse=True)
                st.session_state.dragon_results = results # Save for chart selection
                
                for r in results:
                    st.markdown(f"""
                        <div class='dragon-card'>
                            <div style='font-size:1.4rem;font-weight:bold;'>
                                {r['Status']} {r['Ticker']} <span style='color:#00FFCC;'>({r['Sector']})</span> {r['Icons']}
                            </div>
                            <div class='data-row'>
                                <b>總分: {r['Score']}分</b> (Bias: {r['Bias']}%) | 📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 
                                🌊 OBV: {r['OBV']} | 💰 資金流: {r['Flow']} | 🎯 集中度: {r['Conc']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("💤 經過 7 大死刑與 8 大硬指標過濾後，萬人坑內無生還者。")

    # --- 📈 戰術圖表選擇器 ---
    if hasattr(st.session_state, 'dragon_results') and st.session_state.dragon_results:
        st.write("---")
        st.write("### 📊 摩訶釋達・能量與籌碼透視圖 (自動讀取名單)")
        chart_target = st.selectbox("🎯 選擇已掃描出之真龍，開啟 X 光戰術圖", [r['Ticker'] for r in st.session_state.dragon_results])
        
        if chart_target:
            with st.spinner(f"正在為 {chart_target} 繪製三層能量戰術圖..."):
                try:
                    df_chart = smart_fetch(chart_target, period="6mo")
                    if not df_chart.empty:
                        df_chart['MA50'] = df_chart['Close'].rolling(50, min_periods=1).mean()
                        df_chart['EMA10'] = df_chart['Close'].ewm(span=10, adjust=False).mean()
                        dates_chart = df_chart.index.strftime('%Y-%m-%d')
                        
                        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.15, 0.1], vertical_spacing=0.02)
                        
                        # K 線與均線
                        fig.add_trace(go.Candlestick(x=dates_chart, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name="K線"), row=1, col=1)
                        fig.add_trace(go.Scatter(x=dates_chart, y=df_chart['MA50'], mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=dates_chart, y=df_chart['EMA10'], mode='lines', name='10 EMA', line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                        
                        # 成交量
                        v_colors = ['#00FF00' if df_chart['Close'].iloc[i] >= df_chart['Open'].iloc[i] else '#FF0000' for i in range(len(df_chart))]
                        fig.add_trace(go.Bar(x=dates_chart, y=df_chart['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                        
                        # 呼叫舊 Code 嘅三層能量函數
                        add_energy_subplots(fig, df_chart, row_start=3)
                        
                        fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=950, barmode='overlay',
                                          hovermode='x unified', xaxis_rangeslider_visible=False, 
                                          xaxis=dict(type='category', showticklabels=False), 
                                          legend=dict(font=dict(color="white", size=13), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"繪圖出錯: {e}")

elif st.session_state.page in ['VCP', 'TURTLE']:
    st.markdown(f"<h1 style='text-align:center;'>施工中: {st.session_state.page} 引擎</h1>", unsafe_allow_html=True)
    if st.button("⬅️ 返回總部"): st.session_state.page = 'HOME'
