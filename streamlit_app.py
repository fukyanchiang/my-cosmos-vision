import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from core_logic import (
    HK_STOCK_MAP, US_STOCK_MAP, HK_ETF_MAP, US_ETF_MAP,
    smart_fetch, analyze_dragon_soul
)

st.set_page_config(page_title="🦅 龍魂神殿 V2.0", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #FFFFFF; }
    h1, h2, h3, h4, p, span, label { color: #FFFFFF !important; }
    div[data-testid="stSidebar"] * { color: #FFFFFF !important; }
    div[data-baseweb="select"] { background-color: #FFFFFF !important; border-radius: 5px; }
    div[data-baseweb="select"] span, div[data-baseweb="select"] ul li { color: #000000 !important; font-weight: bold !important; }
    div.stButton > button { background-color: #FFFFFF !important; color: #000000 !important; border: 2px solid #FFFFFF !important; border-radius: 8px; font-size: 22px !important; font-weight: 900 !important; height: 75px !important; width: 100% !important; }
    .stProgress > div > div > div > div { background-color: #00FFCC !important; }
    .sector-tag { border: 1px solid #00FFCC; color: #00FFCC !important; padding: 3px 10px; border-radius: 5px; float: right; font-size: 14px; }
    </style>
""", unsafe_allow_html=True)

if 'tactic' not in st.session_state: st.session_state.tactic = None

if st.session_state.tactic is None:
    st.markdown("<h1 style='text-align:center; color:#FFD700 !important;'>🦅 龍魂神殿戰術中心</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🐲 龍魂起步"): st.session_state.tactic = "Dragon Soul"; st.rerun()
    with c2:
        if st.button("📈 VCP 形態"): st.session_state.tactic = "VCP Pattern"; st.rerun()
    with c3:
        if st.button("🌊 海龜回測"): st.session_state.tactic = "Turtle Strategy"; st.rerun()
    st.stop()

st.sidebar.title("🦅 戰術指揮部")
if st.sidebar.button("⬅️ 返回重選"): st.session_state.tactic = None; st.rerun()
asset = st.sidebar.radio("資產類別", ["🏢 個股", "🧺 ETF"], horizontal=True)
mkt = st.sidebar.radio("交易市場", ["🇺🇸 美股", "🇭🇰 港股"], horizontal=True)
scan_range = st.sidebar.selectbox("選擇範圍", ["🌐 啟動全星系大規模搜索", "🎯 監控清單"])

st.markdown(f"## 🛠️ 戰術模式：{st.session_state.tactic}")

# ==============================================================
# 100% 復活 V188.0 圖表邏輯 (4色買賣力、星星、蟹貨區精準疊加)
# ==============================================================
def add_energy_subplots(fig, df, row_start):
    var1 = df['Close'] - df['Low']
    var2 = df['High'] - df['Close']
    var3 = np.maximum(df['High'] - df['Low'], 0.001)
    buyvol = np.where(var3 > 0, df['Volume'] * var1 / var3, 0)
    sellvol = np.where(var3 > 0, df['Volume'] * var2 / var3, 0)
    netvol = buyvol - sellvol
    netma = pd.Series(netvol).rolling(10, min_periods=1).mean()
    dates = df.index.strftime('%Y-%m-%d')
    
    # 【層3】立體 4 色買賣力
    fig.add_trace(go.Bar(x=dates, y=buyvol, marker_color='#808000', name='買盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    fig.add_trace(go.Bar(x=dates, y=-sellvol, marker_color='#800000', name='賣盤背景', opacity=0.6, hoverinfo='skip'), row=row_start, col=1)
    net_colors = ['#00FF00' if val > 0 else '#FF0000' for val in netvol]
    fig.add_trace(go.Bar(x=dates, y=netvol, marker_color=net_colors, name='淨勝方', width=0.4), row=row_start, col=1)
    fig.add_trace(go.Scatter(x=dates, y=netma, mode='lines', line=dict(color='white', width=2), name='氣脈10MA'), row=row_start, col=1)

    # 【層4】王者能量雷達
    v_ma = df['Volume'].rolling(20, min_periods=1).mean()
    v_std = df['Volume'].rolling(20, min_periods=1).std().fillna(0)
    v_upper = v_ma + (2.0 * v_std)
    ma60 = df['Volume'].rolling(60, min_periods=1).mean()
    roc = abs(df['Close'].pct_change()) * 100
    is_burst = (df['Volume'] > v_upper) & (df['Volume'] > ma60 * 1.9) & (roc > 2.0)
    burst_colors = ['#00FFFF' if (is_burst.iloc[i] and df['Close'].iloc[i] > df['Open'].iloc[i]) else ('#FF00FF' if is_burst.iloc[i] else 'rgba(136,136,136,0.3)') for i in range(len(df))]
    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=burst_colors, name='能量雷達'), row=row_start+1, col=1)

    # 【層5】日波幅%
    daily_change = df['Close'].pct_change() * 100
    change_colors = ['#00FF00' if val >= 0 else '#FF0000' for val in daily_change]
    fig.add_trace(go.Bar(x=dates, y=daily_change, marker_color=change_colors, name='日波幅%'), row=row_start+2, col=1)


def plot_v188_master_chart(ticker, df, buy_p, sl_p):
    # 總共 6 行。注意 Plotly 中 xaxis 會排到 x6
    # 為免衝突，我哋用 'x7' 嚟疊加蟹貨區橫條！
    fig = make_subplots(rows=6, cols=1, shared_xaxes=True, vertical_spacing=0.02, 
                        row_heights=[0.35, 0.15, 0.15, 0.1, 0.1, 0.15])
    dates = df.index.strftime('%Y-%m-%d')
    
    # 【層1】K線 + 10 EMA + 買入止損線 + 蟹貨區
    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='股價'), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=df['Close'].ewm(span=10).mean(), line=dict(color='orange', width=2), name='10 EMA'), row=1, col=1)
    fig.add_hline(y=buy_p, line_dash="dash", line_color="#00FFCC", annotation_text=f"🎯 買入參考: {buy_p:.2f}", row=1, col=1)
    fig.add_hline(y=sl_p, line_dash="solid", line_color="#FF4B4B", annotation_text=f"🛑 10EMA 止損: {sl_p:.2f}", row=1, col=1)

    # 完美修復：使用 xaxis='x7' 疊加
    counts, bins = np.histogram(df['Close'].tail(120), bins=25, weights=df['Volume'].tail(120))
    max_c = max(counts) if len(counts)>0 and max(counts)>0 else 1
    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(255, 255, 255, 0.25)', name='蟹貨區', xaxis='x7', yaxis='y1'), row=1, col=1)

    # 【層2】成交量 + 🌟星星
    v_colors = ['#00FF00' if c >= o else '#FF0000' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name='成交量'), row=2, col=1)
    
    df['Vol50'] = df['Volume'].rolling(50, min_periods=1).mean()
    for i in range(len(df)):
        if df['Close'].iloc[i] > df['Open'].iloc[i] and df['Volume'].iloc[i] > df['Vol50'].iloc[i]*1.5:
            fig.add_annotation(x=dates[i], y=df['Volume'].iloc[i], text="🌟", showarrow=False, font=dict(color="#FFD700", size=14), yanchor="bottom", row=2, col=1)

    # 【層3-5】呼叫 188.0 經典能量指標 (3行)
    add_energy_subplots(fig, df, row_start=3)

    # 【層6】RS 領先線
    fig.add_trace(go.Scatter(x=dates, y=(df['Close']/df['Close'].iloc[0]*100), line=dict(color='#BC13FE', width=2.5), name='RS線'), row=6, col=1)

    fig.update_layout(height=1100, template='plotly_dark', paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', barmode='overlay',
                      xaxis_rangeslider_visible=False, showlegend=False, hovermode='x unified',
                      xaxis=dict(type='category', showgrid=False),
                      xaxis7=dict(overlaying='x1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False))
    return fig

# ================= 6. 雷達掃描 =================
if st.sidebar.button("📡 啟動神殿雷達"):
    target_map = (US_STOCK_MAP if mkt == "🇺🇸 美股" else HK_STOCK_MAP) if asset == "🏢 個股" else (US_ETF_MAP if mkt == "🇺🇸 美股" else HK_ETF_MAP)
    all_t = []; sector_info = {}
    for s, l in target_map.items():
        for t in l: all_t.append(t); sector_info[t] = s.split(". ")[-1]
    
    st.write("---")
    st.markdown(f"### 🔍 掃描中... 總兵力: {len(all_t)} 隻")
    pb = st.progress(0); status = st.empty(); passed = []; sl_list = []
    
    for i, t in enumerate(all_t):
        pb.progress((i+1)/len(all_t))
        status.markdown(f"📡 正在透視莊家：**{t}** ({i+1}/{len(all_t)})")
        
        df = smart_fetch(t)
        if df.empty or len(df) < 65: continue
        
        if df['Close'].iloc[-1] < df['Close'].ewm(span=10).mean().iloc[-1]: sl_list.append(t)
        
        ok, score, stage, _, d = analyze_dragon_soul(t, df, "US" if mkt=="🇺🇸 美股" else "HK")
        if ok: passed.append({"t":t, "score":score, "stage":stage, "df":df, "details":d, "sector":sector_info.get(t,"未知")})

    status.success("✅ 雷達掃描完畢！")

    if sl_list: 
        st.error(f"🚨 **跌穿 10EMA 止損名單：** {', '.join(sl_list[:30])}")
        st.write("---")
    
    if passed:
        passed.sort(key=lambda x: x['score'], reverse=True)
        for s in passed:
            p_score = s['details']['PenaltyScore']
            if p_score == 0:
                border_color = "#FFD700" 
                icon_tag = "✨ 龍魂覺醒：純金狀態"
            elif p_score <= 30:
                border_color = "#00FFCC" 
                icon_tag = f"🌫️ 帶傷上陣：{s['details']['Penalties_Text']}"
            else:
                border_color = "#FF4B4B" 
                icon_tag = f"🌚 極度陰險：{s['details']['Penalties_Text']}"

            st.markdown(f"""
            <div style="border: 3px solid {border_color}; padding: 25px; border-radius: 15px; margin-bottom: 30px; background-color: #000000; box-shadow: 0 0 15px {border_color}44;">
                <span class="sector-tag">📂 {s['sector']}</span>
                <div style="font-size:32px; font-weight:bold; color:{border_color};">{s['t']} {s['stage']}</div>
                <div style="font-size:24px; font-weight:bold; margin:10px 0; color:{border_color};">{icon_tag}</div>
                <div style="font-size:14px; color:#FFF; opacity:0.9;">
                    🏆 總分: {round(s['score'],1)} (扣減 {p_score} 分) | RS: {s['details']['RS']} | EJ: {s['details']['EJ']} <br>
                    🟢 買入價: {s['df']['Close'].iloc[-1]} | 🛑 10EMA 止損: {s['details']['StopLoss']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.plotly_chart(plot_v188_master_chart(s['t'], s['df'], s['df']['Close'].iloc[-1], s['details']['StopLoss']), use_container_width=True, config={'scrollZoom': True, 'displayModeBar': True})
    else:
        st.warning("11 項死刑安檢後，目前無純種龍魂存活。")
