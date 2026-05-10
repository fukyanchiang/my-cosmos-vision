import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# =======================================================
# 從大腦核心 (core_logic.py) 引入名單與龍魂運算邏輯
# =======================================================
from core_logic import (
    HK_STOCK_MAP, US_STOCK_MAP, HK_ETF_MAP, US_ETF_MAP,
    smart_fetch, analyze_dragon_soul
)

# =======================================================
# 1. 終極介面 CSS (絕對鎖死：黑底白字、白掣黑字)
# =======================================================
st.set_page_config(page_title="🦅 龍魂系統 V2.0", layout="wide")

st.markdown("""
    <style>
    /* 全局黑底白字 */
    .stApp { background-color: #0e1117; color: #FFFFFF; }
    h1, h2, h3, h4, p, span, label { color: #FFFFFF !important; }
    
    /* 下拉選單強制白底黑字，確保清晰可見 */
    div[data-baseweb="select"] { background-color: #FFFFFF !important; border-radius: 5px; }
    div[data-baseweb="select"] span { color: #000000 !important; font-weight: bold !important; }
    div[data-baseweb="select"] ul li { color: #000000 !important; }
    
    /* 大按鈕強制白底黑字 */
    div.stButton > button {
        background-color: #FFFFFF !important; 
        color: #000000 !important;
        border: 2px solid #FFFFFF !important; 
        border-radius: 8px;
        font-size: 24px !important; 
        font-weight: 900 !important;
        height: 80px !important; 
        width: 100% !important;
    }
    
    /* 掃描進度條顏色 */
    .stProgress > div > div > div > div { background-color: #00FFCC !important; }
    
    /* 結果卡片樣式 */
    .result-card { border: 2px solid #FFFFFF; padding: 25px; border-radius: 15px; margin-bottom: 30px; background-color: #000000; }
    .stats-text { font-size: 14px; color: #FFFFFF !important; opacity: 0.9; line-height: 1.6; }
    .sector-tag { border: 1px solid #00FFCC; color: #00FFCC !important; padding: 3px 10px; border-radius: 5px; float: right; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

if 'tactic' not in st.session_state: st.session_state.tactic = None

# =======================================================
# 2. 第一步：三大掣首頁
# =======================================================
if st.session_state.tactic is None:
    st.markdown("<h1 class='main-title' style='text-align:center; color:#FFD700 !important;'>🦅 爺孫必勝戰術指揮部</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🐲 龍魂起步\n(尋找最強爆發)"): st.session_state.tactic = "Dragon Soul"; st.rerun()
    with c2:
        if st.button("📈 VCP 形態\n(Mark Minervini)"): st.session_state.tactic = "VCP Pattern"; st.rerun()
    with c3:
        if st.button("🌊 海龜回測\n(N字型加注)"): st.session_state.tactic = "Turtle Strategy"; st.rerun()
    st.stop()

# =======================================================
# 3. 第二步：操作台與 100% 邏輯顯示
# =======================================================
st.markdown(f"## 🛠️ 戰術模式：{st.session_state.tactic}")
# 第一行 100% 顯示掃股邏輯
st.info("🐲 **龍魂羅輯：** 先安檢 11 項死刑 Foul 制 ➡️ 後海選 (RS>60, EJ>85, SE>75, OBV 1/7, 集中度<70%, 兵力勝, NetFlow>0) ➡️ 權重評分排序")

if st.button("⬅️ 返回重選戰術"): st.session_state.tactic = None; st.rerun()

st.markdown("---")
c1, c2, c3 = st.columns([1, 1, 2])
with c1: asset = st.radio("1. 資產類別", ["🏢 個股", "🧺 ETF"], horizontal=True)
with c2: mkt = st.radio("2. 掃描市場", ["🇺🇸 美股", "🇭🇰 港股"], horizontal=True)
with c3: scan_range = st.selectbox("3. 選擇範圍", ["🌐 啟動全星系大規模搜索", "🎯 監控清單"])

# =======================================================
# 4. 繪圖核心：V188.0 能量指標 (3層)
# =======================================================
def add_energy_subplots(fig, df, row_start):
    dates = df.index.strftime('%Y-%m-%d')
    
    # 1. 買賣力度 (淨勝方)
    var1 = df['Close'] - df['Low']
    var2 = df['High'] - df['Close']
    var3 = np.maximum(df['High'] - df['Low'], 0.001)
    netvol = (df['Volume'] * var1 / var3) - (df['Volume'] * var2 / var3)
    net_colors = ['#00FF00' if v > 0 else '#FF0000' for v in netvol]
    fig.add_trace(go.Bar(x=dates, y=netvol, marker_color=net_colors, name='淨勝力'), row=row_start, col=1)

    # 2. 王者能量雷達
    v_ma = df['Volume'].rolling(20, min_periods=1).mean()
    v_std = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
    ma60 = df['Volume'].rolling(60, min_periods=1).mean()
    is_burst = (df['Volume'] > (v_ma + 2.0 * v_std)) & (df['Volume'] > ma60 * 1.9)
    burst_colors = ['#00FFFF' if (is_burst.iloc[i] and df['Close'].iloc[i] > df['Open'].iloc[i]) else ('#FF00FF' if is_burst.iloc[i] else 'rgba(136,136,136,0.3)') for i in range(len(df))]
    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=burst_colors, name='能量雷達'), row=row_start+1, col=1)

    # 3. 日波幅%
    daily_change = df['Close'].pct_change() * 100
    change_colors = ['#00FF00' if val >= 0 else '#FF0000' for val in daily_change]
    fig.add_trace(go.Bar(x=dates, y=daily_change, marker_color=change_colors, name='日波幅%'), row=row_start+2, col=1)

# =======================================================
# 5. 繪圖核心：專業重裝圖表 (6層合一)
# =======================================================
def plot_v188_master_chart(ticker, df, buy_p, sl_p):
    # 配置 6 層: K線/重貨區 -> 成交量/星星/3指標 -> 淨勝方 -> 雷達 -> 波幅 -> RS線
    fig = make_subplots(rows=6, cols=1, shared_xaxes=True, vertical_spacing=0.02, 
                        row_heights=[0.35, 0.15, 0.1, 0.1, 0.1, 0.2])
    dates = df.index.strftime('%Y-%m-%d')
    
    # 【第一層】K線 + 10 EMA + 買賣線 + 蟹貨區
    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='股價'), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=df['Close'].ewm(span=10).mean(), line=dict(color='orange', width=2), name='10 EMA (止損)'), row=1, col=1)
    
    fig.add_hline(y=buy_p, line_dash="dash", line_color="#00FFCC", annotation_text=f"🎯 買入參考: {buy_p}", row=1, col=1)
    fig.add_hline(y=sl_p, line_dash="solid", line_color="#FF4B4B", annotation_text=f"🛑 止損防線: {sl_p}", row=1, col=1)

    counts, bins = np.histogram(df['Close'].tail(120), bins=25, weights=df['Volume'].tail(120))
    max_c = max(counts) if len(counts)>0 else 1
    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136, 136, 136, 0.4)', name='蟹貨區', xaxis='x7', yaxis='y1'), row=1, col=1)

    # 【第二層】成交量 + 🌟星星 + 3個重量級技術指標
    v_colors = ['#00FF00' if c >= o else '#FF0000' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name='成交量'), row=2, col=1)
    
    vol50 = df['Volume'].rolling(50, min_periods=1).mean()
    for i in range(len(df)):
        if df['Close'].iloc[i] > df['Open'].iloc[i] and df['Volume'].iloc[i] > vol50.iloc[i]*1.5:
            fig.add_annotation(x=dates[i], y=df['Volume'].iloc[i], text="🌟", showarrow=False, font=dict(color="#FFD700", size=14), yanchor="bottom", row=2, col=1)

    fig.add_trace(go.Scatter(x=dates, y=df['Volume'].rolling(5).mean(), line=dict(color='#00FFFF', width=1.5), name='短成交'), row=2, col=1)
    fig.add_trace(go.Scatter(x=dates, y=df['Volume'].rolling(20).mean(), line=dict(color='#FF00FF', width=1.5), name='中成交'), row=2, col=1)
    fig.add_trace(go.Scatter(x=dates, y=df['Volume'].rolling(60).mean(), line=dict(color='#FFA500', width=1.5), name='長成交'), row=2, col=1)

    # 【第三、四、五層】能量指標
    add_energy_subplots(fig, df, row_start=3)

    # 【第六層】RS 領先線
    fig.add_trace(go.Scatter(x=dates, y=(df['Close']/df['Close'].iloc[0]*100), line=dict(color='#BC13FE', width=2.5), name='RS線'), row=6, col=1)

    fig.update_layout(height=1100, template='plotly_dark', paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', 
                      xaxis_rangeslider_visible=False, showlegend=False, hovermode='x unified',
                      xaxis7=dict(overlaying='x1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False))
    return fig

# =======================================================
# 6. 開火掃描與顯示 (必定出 Bar)
# =======================================================
if st.button("📡 啟動雷達掃描 (一擊必殺)"):
    # 擷取名單
    if asset == "🏢 個股": target_map = US_STOCK_MAP if mkt == "🇺🇸 美股" else HK_STOCK_MAP
    else: target_map = US_ETF_MAP if mkt == "🇺🇸 美股" else HK_ETF_MAP
    
    all_t = []; sector_info = {}
    for s, l in target_map.items():
        for t in l: all_t.append(t); sector_info[t] = s.split(". ")[-1]
    
    if len(all_t) < 10:
        st.warning("⚠️ 系統載入股數極少，請確保 core_logic.py 內已貼入完整數千隻股名單！")

    st.write("---")
    st.markdown("### 🔍 雷達搜索中，請稍候...")
    
    # 進度條與狀態必定顯示
    pb = st.progress(0)
    status = st.empty()
    passed = []; sl_list = []
    
    for i, t in enumerate(all_t):
        pb.progress((i+1)/len(all_t))
        status.markdown(f"📡 **正在過濾：{t}** ({i+1}/{len(all_t)})")
        
        df = smart_fetch(t)
        if df.empty or len(df) < 65: continue
        
        # A. 止損名單：最近 20 日跌穿 10EMA
        ema10 = df['Close'].ewm(span=10).mean().iloc[-1]
        if df['Close'].iloc[-1] < ema10: sl_list.append(t)
        
        # B. 龍魂過濾 (11死刑 -> 7海選 -> 評分)
        ok, score, stage, icons, d = analyze_dragon_soul(t, df, "US" if mkt=="🇺🇸 美股" else "HK")
        if ok: 
            passed.append({"t":t, "score":score, "stage":stage, "icons":icons, "df":df, "details":d, "sector":sector_info.get(t,"未知板塊")})

    # 清除進度狀態
    status.success("✅ 雷達掃描完畢！")

    # ================== 結果展示 ==================
    # 1. 止損名單放最頂
    if sl_list: 
        st.error(f"🚨 **破防止損名單 (現價跌穿 10 EMA，建議撤退)**：\n\n {', '.join(sl_list)}")
        st.write("---")
    
    # 2. 龍魂名單
    if passed:
        # 按分數排第一，公仔排第二
        passed.sort(key=lambda x: x['score'], reverse=True)
        st.success(f"🎉 捕捉到 {len(passed)} 隻真龍標的！由高至低排列：")
        
        for s in passed:
            st.markdown(f"""
            <div class="result-card">
                <span class="sector-tag">📂 {s['sector']}</span>
                <div style="font-size:32px; font-weight:bold; color:#00FFFF;">{s['t']} {s['stage']}</div>
                <div style="font-size:30px; margin:10px 0;">{s['icons']}</div>
                <div class="stats-text">
                    🏆 龍魂分: {round(s['score'],1)} | RS: {s['details']['RS']} | EJ: {s['details']['EJ']} | SE: {s['details']['SE']} <br>
                    Bias 乖離: {s['details']['Bias']}% | 🟢 買入參考: {s['df']['Close'].iloc[-1]} | 🛑 10EMA 止損防線: {s['details']['StopLoss']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 畫圖：加入 config 開啟放大縮細功能
            fig = plot_v188_master_chart(s['t'], s['df'], s['df']['Close'].iloc[-1], s['details']['StopLoss'])
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
    else:
        st.warning("經過 11 項死刑與 7 大硬指標嚴格過濾，目前無標的符合龍魂條件。")
