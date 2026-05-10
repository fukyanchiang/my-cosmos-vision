import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core_logic import scan_dragon_logic, smart_fetch, check_stop_loss

# 數據庫
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
    .data-row { font-size: 0.9rem; color: #CCCCCC; margin-top: 8px; line-height: 1.5; }
    .bear-warning { color: #FF0000 !important; font-size: 1.5rem; font-weight: 900; text-align: center; border: 3px dashed red; background-color: #220000; padding: 15px; margin: 10px 0; border-radius: 10px;}
    </style>
""", unsafe_allow_html=True)

# 舊 Code 搬過來的能量圖
def add_energy_subplots(fig, df, row_start):
    var1 = df['Close'] - df['Low']; var2 = df['High'] - df['Close']; var3 = np.maximum(df['High'] - df['Low'], 0.001)
    buyvol = df['Volume'] * var1 / var3; sellvol = df['Volume'] * var2 / var3; netvol = buyvol - sellvol
    dates = df.index.strftime('%Y-%m-%d')
    fig.add_trace(go.Bar(x=dates, y=buyvol, marker_color='#808000', name='買盤', opacity=0.6), row=row_start, col=1)
    fig.add_trace(go.Bar(x=dates, y=-sellvol, marker_color='#800000', name='賣盤', opacity=0.6), row=row_start, col=1)
    net_c = ['#00FF00' if v > 0 else '#FF0000' for v in netvol]
    fig.add_trace(go.Bar(x=dates, y=netvol, marker_color=net_c, name='淨勝方', width=0.4), row=row_start, col=1)

if 'page' not in st.session_state: st.session_state.page = 'HOME'
if 'target' not in st.session_state: st.session_state.target = 'NONE'

if st.session_state.page == 'HOME':
    st.markdown("<h1 style='text-align:center;font-size:4rem;margin-top:80px;'>🐲 龍魂戰略總部</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🐉 龍魂神殿"): st.session_state.page = 'DRAGON'
    if c2.button("📈 VCP 獵龍"): st.session_state.page = 'VCP'
    if c3.button("🐢 海龜加注"): st.session_state.page = 'TURTLE'

elif st.session_state.page == 'DRAGON':
    st.markdown("<h1 style='text-align:center;'>🐲 龍魂神殿 2.0 旗艦雷達</h1>", unsafe_allow_html=True)
    nav = st.columns(7)
    if nav[0].button("⬅️ 返回"): st.session_state.page = 'HOME'
    if nav[1].button("🇭🇰 港股"): st.session_state.target = 'HK'
    if nav[2].button("🇺🇸 美股"): st.session_state.target = 'US'
    if nav[4].button("📦 ETF"): st.session_state.target = 'ETF'
    btn_radar = nav[6].button("📡 啟動雷達")
    st.markdown("---")
    
    sl_container = st.empty()
    selected_tickers = []
    market_mode = "HK"

    # ETF 選擇
    if st.session_state.target == 'ETF':
        e1, e2 = st.columns(2)
        if e1.button("🇭🇰 掃描港股 ETF"): st.session_state.active_file = 'HK_ETF'; st.success("已選港股 ETF")
        if e2.button("🇺🇸 掃描美股 ETF"): st.session_state.active_file = 'US_ETFs.csv'; st.success("已選美股 ETF")

    if btn_radar:
        if st.session_state.target == 'HK':
            selected_tickers = [("0700.HK", "互聯網"), ("9988.HK", "科技"), ("0981.HK", "半導體"), ("3690.HK", "外賣"), ("1211.HK", "汽車")]
            market_mode = "HK"
        elif st.session_state.target == 'ETF' and getattr(st.session_state, 'active_file', '') == 'HK_ETF':
            selected_tickers = [(t, "港股ETF") for sub in HK_ETF_MAP.values() for t in sub]
            market_mode = "HK"
        # (其他名單讀取省略，同之前)

        if selected_tickers:
            results = []; sl_list = []; pb = st.progress(0)
            for i, (t, sec) in enumerate(selected_tickers[:40]):
                pb.progress((i+1)/len(selected_tickers[:40]))
                df = smart_fetch(t)
                if check_stop_loss(df): sl_list.append(t)
                res = scan_dragon_logic(df, t, sec, market_mode)
                if res: results.append(res)
            
            if sl_list:
                sl_container.markdown(f"<div class='bear-warning'>🛡️ 戰損置頂 (2日內跌穿 10-EMA): {' | '.join(sl_list)}</div>", unsafe_allow_html=True)

            if results:
                results = sorted(results, key=lambda x: (x['Score'], x['IconCount']), reverse=True)
                st.session_state.dragon_results = results
                for r in results:
                    st.markdown(f"""
                        <div class='dragon-card'>
                            <div style='font-size:1.4rem;font-weight:bold;'>{r['Status']} {r['Ticker']} <span style='color:#00FFCC;'>({r['Sector']})</span> {r['Icons']}</div>
                            <div class='data-row'>
                                <b>總分: {r['Score']}分</b> | <span style='color:#FF4B4B;'>🛑 止損(10-EMA): ${r['EMA10']}</span> | Bias: {r['Bias']}%<br>
                                📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 💰 資金流: {r['Flow']} | 🎯 集中度: {r['Conc']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

    # 5. X光圖表
    if 'dragon_results' in st.session_state:
        st.write("---")
        chart_t = st.selectbox("🎯 查看 X 光戰術圖", [r['Ticker'] for r in st.session_state.dragon_results])
        if chart_t:
            df_c = smart_fetch(chart_t, period="6mo")
            ema10 = df_c['Close'].ewm(span=10, adjust=False).mean()
            fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.5, 0.1, 0.15, 0.15, 0.1], vertical_spacing=0.02)
            
            # K線 + 止損
            fig.add_trace(go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="K線"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df_c.index, y=ema10, name="10-EMA 止損", line=dict(color='orange', dash='dot')), row=1, col=1)
            
            # 破頂買入位
            pivot = df_c['High'].tail(20).max()
            fig.add_hline(y=pivot, line_dash="dash", line_color="#00FFCC", annotation_text="🎯 買入點", row=1, col=1)
            
            # 橫向重貨區
            counts, bins = np.histogram(df_c['Close'], bins=20, weights=df_c['Volume'])
            fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(0,255,204,0.2)', name='重貨區', xaxis='x2', yaxis='y1'))
            
            # 星星邏輯
            df_c['Vol50'] = df_c['Volume'].rolling(50).mean()
            stars = df_c[(df_c['Close'] > df_c['Open']) & (df_c['Volume'] > df_c['Vol50'] * 1.5)]
            fig.add_trace(go.Scatter(x=stars.index, y=stars['Volume'], mode='markers', marker=dict(symbol='star', size=10, color='gold'), name='大戶星星'), row=2, col=1)

            add_energy_subplots(fig, df_c, row_start=3)
            fig.update_layout(height=950, template="plotly_dark", xaxis2=dict(overlaying='x', side='top', showticklabels=False), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
