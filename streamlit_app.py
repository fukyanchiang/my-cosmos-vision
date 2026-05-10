import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core_logic import scan_dragon_logic, smart_fetch, check_stop_loss

HK_ETF_MAP = {
    "H1. A股門戶": "2822.HK 3188.HK 3109.HK 2823.HK 2801.HK".split(),
    "H2. 港股科技": "3033.HK 3088.HK 3067.HK 3167.HK 3191.HK".split(),
    "H4. 紅利收息": "3110.HK 3070.HK 3101.HK 3037.HK 3145.HK".split()
}

st.set_page_config(page_title="龍魂神殿 2.0", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #FFFFFF; }
    div.stButton > button { background-color: #000000 !important; color: #FFFFFF !important; border: 2px solid #FFFFFF !important; border-radius: 0px !important; font-weight: 900 !important; width: 100%; margin-bottom: 5px; }
    div.stButton > button:hover { background-color: #FFFFFF !important; color: #000000 !important; }
    .dragon-card { border-left: 5px solid #00FFCC; background: #111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .data-row { font-size: 0.95rem; color: #CCCCCC; margin-top: 8px; line-height: 1.6; }
    .bear-warning { color: #FF0000 !important; font-size: 1.5rem; font-weight: 900; text-align: center; text-shadow: 2px 2px 5px #000; padding: 15px; border: 3px dashed red; background-color: #220000; margin: 10px 0; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

def add_energy_subplots(fig, df, row_start):
    var1 = df['Close'] - df['Low']; var2 = df['High'] - df['Close']
    var3 = np.maximum(df['High'] - df['Low'], 0.001)
    buyvol = np.where(var3 > 0, df['Volume'] * var1 / var3, 0)
    sellvol = np.where(var3 > 0, df['Volume'] * var2 / var3, 0)
    netvol = buyvol - sellvol
    netma = pd.Series(netvol).rolling(10, min_periods=1).mean()
    dates = df.index.strftime('%Y-%m-%d')
    
    fig.add_trace(go.Bar(x=dates, y=buyvol, marker_color='#808000', name='買盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    fig.add_trace(go.Bar(x=dates, y=-sellvol, marker_color='#800000', name='賣盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    net_colors = ['#00FF00' if val > 0 else '#FF0000' for val in netvol]
    fig.add_trace(go.Bar(x=dates, y=netvol, marker_color=net_colors, name='淨勝方', width=0.4), row=row_start, col=1)
    fig.add_trace(go.Scatter(x=dates, y=netma, mode='lines', line=dict(color='white', width=2), name='氣脈10MA'), row=row_start, col=1)

    v_ma = df['Volume'].rolling(20, min_periods=1).mean(); v_std = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
    v_upper = v_ma + (2.0 * v_std); ma60 = df['Volume'].rolling(60, min_periods=1).mean(); roc = abs(df['Close'].pct_change()) * 100
    is_burst = (df['Volume'] > v_upper) & (df['Volume'] > ma60 * 1.9) & (roc > 2.0)
    burst_colors = ['#00FFFF' if (is_burst.iloc[i] and df['Close'].iloc[i] > df['Open'].iloc[i]) else ('#FF00FF' if is_burst.iloc[i] else 'rgba(136,136,136,0.3)') for i in range(len(df))]
    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=burst_colors, name='能量雷達'), row=row_start+1, col=1)

    daily_change = df['Close'].pct_change() * 100
    change_colors = ['#00FF00' if val >= 0 else '#FF0000' for val in daily_change]
    fig.add_trace(go.Bar(x=dates, y=daily_change, marker_color=change_colors, name='日波幅%'), row=row_start+2, col=1)

if 'page' not in st.session_state: st.session_state.page = 'HOME'
if 'target' not in st.session_state: st.session_state.target = 'NONE'

if st.session_state.page == 'HOME':
    st.markdown("<h1 style='text-align:center;font-size:4rem;margin-top:80px;'>🐲 龍魂戰略總部</h1><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🐉 龍魂神殿 (11鐵律掃描)"): st.session_state.page = 'DRAGON'
    if c2.button("📈 VCP 形態獵龍"): st.session_state.page = 'VCP'
    if c3.button("🐢 海龜 N 字加注"): st.session_state.page = 'TURTLE'

elif st.session_state.page == 'DRAGON':
    st.markdown("<h1 style='text-align:center;'>🐲 龍魂神殿 2.0 旗艦雷達</h1>", unsafe_allow_html=True)
    
    nav = st.columns(7)
    if nav[0].button("⬅️ 返回"): st.session_state.page = 'HOME'
    if nav[1].button("🇭🇰 港股"): st.session_state.target = 'HK_STOCK'
    if nav[2].button("🇺🇸 美股"): st.session_state.target = 'US_CSV'
    if nav[3].button("🔍 個股"): st.session_state.target = 'SINGLE'
    if nav[4].button("📦 ETF"): st.session_state.target = 'ETF'
    if nav[5].button("🔥 ATH"): st.session_state.target = 'ATH'
    btn_radar = nav[6].button("📡 啟動雷達")
    st.markdown("---")
    
    stop_loss_container = st.empty()
    selected_tickers = []
    market_mode = "HK"

    if st.session_state.target == 'US_CSV':
        m = st.columns(5)
        files = [("SP500_Equities.csv", "大藍籌"), ("Market_Focus.csv", "精選"), ("Industry_Focus.csv", "行業"), ("Core_Stocks.csv", "核心"), ("US_ETFs.csv", "戰略ETF")]
        for i, (f, name) in enumerate(files):
            if m[i].button(f"選定 {name}"): st.session_state.active_file = f; st.success(f"✅ 已選定 {name}")

    elif st.session_state.target == 'ETF':
        e1, e2 = st.columns(2)
        if e1.button("🇭🇰 設定為：掃描港股 ETF"): st.session_state.active_file = 'HK_ETF'; st.success("✅ 已選定 港股 ETF")
        if e2.button("🇺🇸 設定為：掃描美股 ETF"): st.session_state.active_file = 'US_ETFs.csv'; st.success("✅ 已選定 美股 ETF")

    if btn_radar:
        if st.session_state.target == 'HK_STOCK':
            selected_tickers = [("0700.HK", "互聯網"), ("9988.HK", "互聯網"), ("3690.HK", "互聯網"), ("0981.HK", "半導體"), ("1211.HK", "汽車")]
            market_mode = "HK"
        elif st.session_state.target == 'ETF':
            if getattr(st.session_state, 'active_file', '') == 'HK_ETF':
                selected_tickers = [(t, "港股ETF") for sublist in HK_ETF_MAP.values() for t in sublist]
                market_mode = "HK"
            elif getattr(st.session_state, 'active_file', '') == 'US_ETFs.csv':
                try:
                    df_csv = pd.read_csv('US_ETFs.csv')
                    col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol']][0]
                    selected_tickers = [(t, "美股ETF") for t in df_csv[col].dropna().tolist()]
                    market_mode = "US"
                except: pass
        elif st.session_state.target == 'US_CSV' and hasattr(st.session_state, 'active_file'):
            try:
                df_csv = pd.read_csv(st.session_state.active_file)
                col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol', '代號']][0]
                selected_tickers = [(t, "美股") for t in df_csv[col].dropna().tolist()]
                market_mode = "US"
            except: pass
        
        if selected_tickers:
            st.info(f"🚀 龍魂發動！正在執行絕對死刑過濾 (掃描 {len(selected_tickers)} 隻標的)...")
            results = []; stop_loss_triggered = []; pb = st.progress(0)
            
            scan_list = selected_tickers[:40]
            for idx, (t, sec) in enumerate(scan_list):
                pb.progress((idx+1)/len(scan_list))
                df = smart_fetch(t)
                if check_stop_loss(df): stop_loss_triggered.append(t)
                res = scan_dragon_logic(df, t, sec, market_mode)
                if res: results.append(res)
            
            if stop_loss_triggered:
                sl_str = " | ".join([f"[{t}]" for t in stop_loss_triggered])
                stop_loss_container.markdown(f"<div class='bear-warning'>🛡️ 戰損置頂警報：以下跌穿 10-EMA，請執行止損！<br>{sl_str}</div>", unsafe_allow_html=True)

            if results:
                results = sorted(results, key=lambda x: (x['Score'], x['IconCount']), reverse=True)
                st.session_state.dragon_results = results 
                for r in results:
                    # 依家會顯示 🛑 止損(10-EMA) 位
                    st.markdown(f"""
                        <div class='dragon-card'>
                            <div style='font-size:1.4rem;font-weight:bold;'>{r['Status']} {r['Ticker']} <span style='color:#00FFCC;'>({r['Sector']})</span> {r['Icons']}</div>
                            <div class='data-row'>
                                <b>總分: {r['Score']}分</b> | <span style='color:#FF4B4B; font-weight:bold;'>🛑 止損(10-EMA): ${r['EMA10']}</span> | Bias: {r['Bias']}%<br>
                                📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 🌊 OBV: {r['OBV']} | 💰 資金流: {r['Flow']} | 🎯 集中度: {r['Conc']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else: st.warning("💤 萬人坑內無生還者 (中一項 Foul 即出局)。")

    if hasattr(st.session_state, 'dragon_results') and st.session_state.dragon_results:
        st.write("---")
        st.write("### 📊 摩訶釋達・能量與籌碼透視圖")
        chart_target = st.selectbox("🎯 選擇標的，開啟 X 光戰術圖", [r['Ticker'] for r in st.session_state.dragon_results])
        
        if chart_target:
            with st.spinner("繪製戰術圖表..."):
                try:
                    df_chart = smart_fetch(chart_target, period="6mo")
                    if not df_chart.empty:
                        df_chart['MA50'] = df_chart['Close'].rolling(50, min_periods=1).mean()
                        df_chart['EMA10'] = df_chart['Close'].ewm(span=10, adjust=False).mean()
                        dates_chart = df_chart.index.strftime('%Y-%m-%d')
                        
                        fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.45, 0.1, 0.2, 0.15, 0.1], vertical_spacing=0.02)
                        
                        fig.add_trace(go.Candlestick(x=dates_chart, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], name="K線"), row=1, col=1)
                        fig.add_trace(go.Scatter(x=dates_chart, y=df_chart['MA50'], mode='lines', name='50MA', line=dict(color='yellow', width=1.5)), row=1, col=1)
                        fig.add_trace(go.Scatter(x=dates_chart, y=df_chart['EMA10'], mode='lines', name='10 EMA', line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                        
                        recent_high = df_chart['High'].tail(20).max()
                        fig.add_hline(y=recent_high, line_dash="dash", line_color="#00FFCC", annotation_text=f"🎯 破頂買入: ${recent_high:.2f}", annotation_position="top left", annotation_font=dict(color="white", size=13), row=1, col=1)
                        
                        counts, bins = np.histogram(df_chart['Close'], bins=30, weights=df_chart['Volume'])
                        max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                        hvn_price = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                        stop_loss = hvn_price * 0.985
                        
                        fig.add_hline(y=stop_loss, line_dash="solid", line_color="#FF4B4B", annotation_text=f"🛑 重貨區止損: ${stop_loss:.2f}", annotation_position="bottom left", annotation_font=dict(color="white", size=13), row=1, col=1)
                        
                        # 加入 10-EMA 極限止損標示
                        ema10_val = df_chart['EMA10'].iloc[-1]
                        fig.add_hline(y=ema10_val, line_dash="dot", line_color="orange", annotation_text=f"🛑 10-EMA 止損: ${ema10_val:.2f}", annotation_position="bottom right", annotation_font=dict(color="white", size=13), row=1, col=1)

                        fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(150,150,150,0.3)', name='重貨區 HVN', hoverinfo='skip', xaxis='x6', yaxis='y1'))

                        v_colors = ['#00FF00' if df_chart['Close'].iloc[i] >= df_chart['Open'].iloc[i] else '#FF0000' for i in range(len(df_chart))]
                        fig.add_trace(go.Bar(x=dates_chart, y=df_chart['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                        
                        df_chart['Vol50'] = df_chart['Volume'].rolling(50, min_periods=1).mean()
                        for i in range(len(df_chart)):
                            if df_chart['Close'].iloc[i] > df_chart['Open'].iloc[i] and df_chart['Volume'].iloc[i] > df_chart['Vol50'].iloc[i] * 1.5:
                                fig.add_annotation(x=dates_chart[i], y=df_chart['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", xanchor="center", font=dict(size=14, color="#FFD700"), row=2, col=1)

                        add_energy_subplots(fig, df_chart, row_start=3)
                        
                        fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=950, barmode='overlay',
                                          hovermode='x unified', xaxis_rangeslider_visible=False, 
                                          xaxis=dict(type='category', showticklabels=False), 
                                          xaxis6=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False),
                                          legend=dict(font=dict(color="white", size=13), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e: st.error(f"繪圖出錯: {e}")

elif st.session_state.page in ['VCP', 'TURTLE']:
    st.markdown(f"<h1 style='text-align:center;'>施工中: {st.session_state.page}</h1>", unsafe_allow_html=True)
    if st.button("⬅️ 返回總部"): st.session_state.page = 'HOME'
