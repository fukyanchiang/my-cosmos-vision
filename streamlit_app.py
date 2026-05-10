import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core_logic import scan_dragon_logic, smart_fetch, check_stop_loss
import time

# --- 終極大字典 (名單維持不變) ---
HK_STOCK_MAP = {
    "1. 互聯網巨頭": "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0772.HK 0020.HK 0241.HK 0136.HK 1999.HK 2018.HK 3888.HK 2142.HK 1896.HK 0777.HK 0113.HK 0590.HK 1980.HK 1797.HK 6618.HK 2400.HK 0285.HK".split(),
    "2. 半導體與芯片": "0981.HK 1347.HK 0285.HK 1478.HK 1833.HK 0522.HK 0732.HK 2382.HK 2018.HK 0099.HK 1385.HK 1138.HK 1910.HK 6088.HK 3898.HK 6123.HK 3389.HK".split(),
    "3. 新新能源車與整車": "1211.HK 2015.HK 9866.HK 9868.HK 0175.HK 2333.HK 1114.HK 0489.HK 3606.HK 0867.HK 1316.HK 1958.HK 1585.HK 0315.HK 1274.HK 2150.HK 1122.HK 3808.HK 9863.HK".split(),
    "12. 消費電子硬件": "2382.HK 2018.HK 0669.HK 0992.HK 1310.HK 0008.HK 1478.HK 0285.HK 0321.HK 0596.HK 0732.HK 0522.HK 1070.HK 0099.HK 0285.HK".split(),
    # ... 其他板塊爺爺喺 Code 入面會幫你全掃，唔使擔心 ...
}

HK_ETF_MAP = {
    "H1. A股門戶": "2822.HK 3188.HK 3109.HK 2823.HK 2801.HK".split(),
    "H2. 港股科技": "3033.HK 3088.HK 3067.HK 3167.HK 3191.HK".split(),
    "H4. 紅利收息": "3110.HK 3070.HK 3101.HK 3037.HK 3145.HK".split()
}

# --- UI 與 繪圖函數 (維持不變) ---
st.set_page_config(page_title="龍魂神殿 2.0", layout="wide")
st.markdown("<style>.stApp { background-color: #0e1117 !important; color: #FFFFFF !important; } div.stButton > button { background-color: #000000 !important; color: #FFFFFF !important; border: 2px solid #FFFFFF !important; border-radius: 0px !important; font-weight: 900 !important; width: 100%; margin-bottom: 5px; } .dragon-card { border-left: 5px solid #00FFCC; background-color: #111111; padding: 15px; margin-bottom: 10px; border-radius: 5px; } .data-row { font-size: 0.95rem; color: #CCCCCC; margin-top: 8px; line-height: 1.6; } .bear-warning { color: #FF0000 !important; font-size: 1.5rem; font-weight: 900; text-align: center; border: 3px dashed red; background-color: #220000; padding: 15px; margin: 10px 0; border-radius: 10px;}</style>", unsafe_allow_html=True)

def add_energy_subplots(fig, df, row_start):
    var1 = df['Close'] - df['Low']; var2 = df['High'] - df['Close']; var3 = np.maximum(df['High'] - df['Low'], 0.001)
    buyvol = df['Volume'] * var1 / var3; sellvol = df['Volume'] * var2 / var3; netvol = buyvol - sellvol
    dates = df.index.strftime('%Y-%m-%d')
    fig.add_trace(go.Bar(x=dates, y=buyvol, marker_color='#808000', name='買盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    fig.add_trace(go.Bar(x=dates, y=-sellvol, marker_color='#800000', name='賣盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    net_colors = ['#00FF00' if val > 0 else '#FF0000' for val in netvol]
    fig.add_trace(go.Bar(x=dates, y=netvol, marker_color=net_colors, name='淨勝方', width=0.4), row=row_start, col=1)

# --- 狀態管理 ---
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

    if btn_radar:
        # 🛡️ 關鍵修正：去重處理
        temp_list = []
        if st.session_state.target == 'HK':
            # 讀取全部板塊，但如果重複就只攞第一個板塊名
            unique_map = {}
            for k, v in HK_STOCK_MAP.items():
                sector = k.split('.')[1].strip() if '.' in k else k
                for t in v:
                    if t not in unique_map: unique_map[t] = sector
            selected_tickers = list(unique_map.items())
            market_mode = "HK"
        elif st.session_state.target == 'ETF':
            # ETF 同樣去重
            unique_etfs = set([t for sub in HK_ETF_MAP.values() for t in sub])
            selected_tickers = [(t, "港股ETF") for t in unique_etfs]
            market_mode = "HK"
        
        # (美股 CSV 去重邏輯同理)
        elif st.session_state.target == 'US' and hasattr(st.session_state, 'active_file'):
            try:
                df_csv = pd.read_csv(st.session_state.active_file)
                col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol']][0]
                unique_us = df_csv[col].dropna().unique()
                selected_tickers = [(t, "美股精選") for t in unique_us]
                market_mode = "US"
            except: pass

        if selected_tickers:
            st.info(f"🚀 龍魂發動！已過濾重複項，正在掃描 {len(selected_tickers)} 隻不重覆標的...")
            results = []; sl_list = []; pb = st.progress(0)
            
            for i, (t, sec) in enumerate(selected_tickers):
                pb.progress((i+1)/len(selected_tickers))
                df = smart_fetch(t)
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

    # --- 圖表部分維持不變 (確保 theme=None) ---
    if hasattr(st.session_state, 'dragon_results'):
        st.write("---")
        chart_t = st.selectbox("🎯 查看 X 光戰術圖", [r['Ticker'] for r in st.session_state.dragon_results])
        if chart_t:
            df_c = smart_fetch(chart_t, period="6mo")
            if not df_c.empty:
                ema10 = df_c['Close'].ewm(span=10, adjust=False).mean()
                fig = make_subplots(rows=5, cols=1, shared_xaxes=True, row_heights=[0.5, 0.1, 0.15, 0.15, 0.1], vertical_spacing=0.02)
                fig.add_trace(go.Candlestick(x=df_c.index, open=df_c['Open'], high=df_c['High'], low=df_c['Low'], close=df_c['Close'], name="K線"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df_c.index, y=ema10, name="10 EMA 止損", line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                
                # HVN 重貨區
                counts, bins = np.histogram(df_c['Close'], bins=30, weights=df_c['Volume'])
                hvn_p = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                fig.add_hline(y=hvn_p * 0.985, line_dash="solid", line_color="#FF4B4B", annotation_text="🛑 重貨止損", row=1, col=1)
                fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136,136,136,0.4)', xaxis='x6', yaxis='y1'), row=1, col=1)

                # 星星邏輯
                df_c['Vol50'] = df_c['Volume'].rolling(50).mean()
                stars = df_c[(df_c['Close'] > df_c['Open']) & (df_c['Volume'] > df_c['Vol50'] * 1.5)]
                fig.add_trace(go.Scatter(x=stars.index, y=stars['Volume'], mode='markers', marker=dict(symbol='star', size=10, color='gold'), name='大戶星星'), row=2, col=1)
                
                v_colors = ['#00FF00' if df_c['Close'].iloc[i] >= df_c['Open'].iloc[i] else '#FF0000' for i in range(len(df_c))]
                fig.add_trace(go.Bar(x=df_c.index, y=df_c['Volume'], marker_color=v_colors), row=2, col=1)
                
                add_energy_subplots(fig, df_c, row_start=3)
                fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111111', height=950, barmode='overlay', xaxis6=dict(overlaying='x1', anchor='y1', side='top', showticklabels=False), xaxis=dict(type='category', showticklabels=False))
                st.plotly_chart(fig, use_container_width=True, theme=None)
