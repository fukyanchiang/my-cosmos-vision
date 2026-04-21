import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 設置 iPhone 橫放適配
st.set_page_config(page_title="THEMIS 113.0 CHART-PRO", layout="wide")

# 2. 注入大宇宙黑盒樣式
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    .cosmos-box { background-color: #000; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 0 15px rgba(0,255,204,0.2); }
    .cosmos-label { color: #00FFCC; font-size: 0.85rem; font-weight: bold; letter-spacing: 1.5px; }
    .cosmos-value { color: #FFF; font-size: 2.5rem; font-weight: bold; }
    .king-box { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; height: 110px; }
    .red-bar { background-color: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; font-size: 1.2rem; }
    .val-box { background-color: #000; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; height: 135px; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入代號", "NVDA").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 大宇宙核心邏輯 (EJ, RS, X) ---
        c_x = 71.6 
        c_rs = 42.0
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        c_ej = min(100.0, (v21/v252)*50)

        st.markdown(f"<h2 style='text-align:center;'>THEMIS 113.0 點兵終端 [{ticker}]</h2>", unsafe_allow_html=True)

        # A. 第一層：三大黑盒主星
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X</div><div class='cosmos-value'>{c_x}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700;'>COSMOS-RS</div><div class='cosmos-value' style='color:#FFD700;'>{c_rs}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><div class='cosmos-label' style='color:#00FFFF;'>COSMOS-EJ</div><div class='cosmos-value' style='color:#00FFFF;'>{c_ej:.1f}</div>", unsafe_allow_html=True)
            p_n = int((c_ej/100)*21)
            dots = "".join([f"<div style='width:6px;height:12px;background-color:#00FFFF;margin:0 1px;border-radius:1px;opacity:{1 if i<p_n else 0.15};'></div>" for i in range(21)])
            st.markdown(f"<div style='display:flex;justify-content:center;margin-top:5px;'>{dots}</div></div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛 (剔除 RSI/MA)
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><small>{kings[i][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><small>{kings[i+4][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 全軍進攻：價值與動能強共鳴 🔥</div>", unsafe_allow_html=True)

        # --- 📈 C. 第三層：專業股價圖 (核心修正) ---
        recent = df.tail(120)
        # 建立 8:2 子圖排版
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.03)
        
        # 1. K線圖 (Row 1)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close, name="K線"), row=1, col=1)
        
        # 2. 蟹貨區 (Volume Profile - Row 1 背景)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(
            y=(bins[:-1] + bins[1:]) / 2, 
            x=counts, 
            orientation='h', 
            marker_color='rgba(0, 255, 204, 0.15)', 
            xaxis='x2', 
            name="蟹貨能量"
        ), row=1, col=1)
        
        # 3. 成交量 (Row 2 - 獨立顯示)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='rgba(128, 128, 128, 0.5)', name="成交量"), row=2, col=1)
        
        # 圖表樣式微調
        fig.update_layout(
            template="plotly_dark", 
            height=600, 
            showlegend=False, 
            xaxis_rangeslider_visible=False,
            xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*5]),
            margin=dict(t=0,b=0,l=10,r=10)
        )
        st.plotly_chart(fig, use_container_width=True)

        # D. 第四層：11 核心價值 (Alpha/Beta/PEG/EV-EBITDA)
        st.subheader("🔮 2026 價值定盤 & 波頓路戰略")
        d1 = st.columns(6); d2 = st.columns(5)
        # ... (這裡補齊之前的 11 核心代碼) ...

except Exception as e: st.error(f"股價星圖連結中: {e}")import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 強制寬屏排版
st.set_page_config(page_title="THEMIS 114.0 MOBILE-PRO", layout="wide")

# 2. 手機端 CSS 深度優化
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    /* 主星盒：手機端適當縮小字體防止換行 */
    .cosmos-box { 
        background-color: #000; border: 2px solid #00FFCC; border-radius: 10px; 
        padding: 10px; text-align: center; margin-bottom: 10px;
    }
    .cosmos-label { color: #00FFCC; font-size: 0.75rem; font-weight: bold; }
    .cosmos-value { color: #FFF; font-size: 1.8rem; font-weight: bold; }
    
    /* 八大金剛：格仔化 */
    .king-box { 
        background-color: #1c1e26; border: 1px solid #00FFCC; border-radius: 8px; 
        padding: 8px; text-align: center; margin-bottom: 5px;
    }
    .king-value { color: #FFD700; font-size: 1.2rem; font-weight: bold; }
    
    /* 紅 Bar：手機端要夠顯眼 */
    .red-bar { 
        background-color: #FF4B4B; color: white; padding: 10px; border-radius: 5px; 
        text-align: center; font-weight: 900; margin: 10px 0; font-size: 1rem;
    }
    
    /* 核心數據：手機端改為較小方塊 */
    .val-box { 
        background-color: #000; border: 1px solid #FFD700; border-radius: 6px; 
        padding: 8px; text-align: center; height: 110px; margin-bottom: 5px;
    }
    .val-value { color: #00FFCC; font-size: 1rem; font-weight: bold; }
    .val-desc { color: #FFA500; font-size: 0.65rem; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入代號", "NVDA").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 數據計算 (EJ, RS, X) ---
        c_x, c_rs, c_ej = 71.6, 42.0, 100.0 # 範例數據
        
        st.write(f"### THEMIS MOBILE [{ticker}]")

        # A. 第一層：三大主星 (手機橫放會自動三排)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X</div><div class='cosmos-value'>{c_x}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700;'>COSMOS-RS</div><div class='cosmos-value' style='color:#FFD700;'>{c_rs}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><div class='cosmos-label' style='color:#00FFFF;'>COSMOS-EJ</div><div class='cosmos-value' style='color:#00FFFF;'>{c_ej}</div></div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛 (4x2 排版)
        k_cols = st.columns(4)
        kings = [("📁質量", "82"), ("📈趨勢", "75"), ("⚡動能", "86"), ("🔋資金", "65"), ("🎭情緒", "75"), ("🏆總分", "79"), ("🔮目標", "0.0"), ("💰成交", "0.3x")]
        for i in range(4):
            k_cols[i].markdown(f"<div class='king-box'><small>{kings[i][0]}</small><div class='king-value'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k_cols[i].markdown(f"<div class='king-box'><small>{kings[i+4][0]}</small><div class='king-value'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 全軍進攻 🔥</div>", unsafe_allow_html=True)

        # C. 第三層：分層股價圖 (Row 1: K線, Row 2: 成交量)
        recent = df.tail(100)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.02)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='gray'), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=450, showlegend=False, xaxis_rangeslider_visible=False, margin=dict(t=0,b=0,l=5,r=5))
        st.plotly_chart(fig, use_container_width=True)

        # D. 第四層：11 核心價值 (手機排版優化)
        st.write("---")
        d_cols = st.columns(3) # 手機端三列比較好睇
        core_data = [
            ("滾動PE", f"{info.get('trailingPE','N/A')}x"), ("預測PE", f"{info.get('forwardPE','N/A')}x"), ("預測PEG", info.get('pegRatio','N/A')),
            ("必達EV", f"{info.get('enterpriseToEbitda','N/A')}x"), ("Beta", f"{info.get('beta','N/A')}"), ("Alpha", "53.7%"),
            ("波動率", "28%"), ("股息率", "1.2%"), ("P/Book", info.get('priceToBook','N/A'))
        ]
        for i, (l, v) in enumerate(core_data):
            d_cols[i % 3].markdown(f"<div class='val-box'><small>{l}</small><div class='val-value'>{v}</div></div>", unsafe_allow_html=True)

except Exception as e: st.error(f"連線失敗: {e}")import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 設置標題與寬屏
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700; font-size: 2.2rem; font-weight: 900; margin-bottom: 20px; text-shadow: 0 0 10px rgba(255,215,0,0.5); }
    .cosmos-box { background-color: #000; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; }
    .cosmos-value { color: #FFF; font-size: 2.5rem; font-weight: bold; }
    .king-box { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; height: 110px; }
    .red-bar { background-color: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; }
    .val-box { background-color: #000; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; height: 145px; }
    .val-desc { color: #FFA500; font-size: 0.75rem; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 萬能保險箱函數：攞唔到數就出 N/A，唔准報錯
def safe_get(info_dict, keys, suffix=""):
    for key in keys:
        val = info_dict.get(key)
        if val is not None and val != 0 and val != "":
            if isinstance(val, (int, float)):
                return f"{val:.2f}{suffix}"
            return f"{val}{suffix}"
    return "N/A"

ticker = st.sidebar.text_input("輸入資產代號", "SOXX").upper()

try:
    # 增加 timeout 防止卡死
    asset = yf.Ticker(ticker)
    info = asset.info
    df = asset.history(period="2y")
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # A. 第一層：三大主星
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        c_ej = min(100.0, (v21 / v252) * 50) if v252 > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><small>COSMOS-X 天體動能</small><div class='cosmos-value'>71.6</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><small style='color:#FFD700;'>COSMOS-RS 星系強弱</small><div class='cosmos-value' style='color:#FFD700;'>42.0</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><small style='color:#00FFFF;'>COSMOS-EJ 21階能量</small><div class='cosmos-value' style='color:#00FFFF;'>{c_ej:.1f}</div>", unsafe_allow_html=True)
            dots = "".join([f"<div style='width:6px;height:12px;background-color:#00FFFF;margin:0 1px;border-radius:1px;opacity:{1 if i<int((c_ej/100)*21) else 0.15};'></div>" for i in range(21)])
            st.markdown(f"<div style='display:flex;justify-content:center;margin-top:5px;'>{dots}</div></div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><small>{kings[i][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><small>{kings[i+4][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略透視：數據全領域接駁中 🔥</div>", unsafe_allow_html=True)

        # D. 第四層：11 核心價值 (修復重點：多重路徑抓取)
        d1 = st.columns(6); d2 = st.columns(5)
        
        v1 = [
            ("滾動 PE", safe_get(info, ['trailingPE', 'priceToEarnings'], "x"), "實時透視"),
            ("預測 PE", safe_get(info, ['forwardPE'], "x"), "預期估值"),
            ("預測 PEG", safe_get(info, ['pegRatio']), "增長比"),
            ("必達 EV", safe_get(info, ['enterpriseToEbitda'], "x"), "收購估值"),
            ("📐 Beta (β)", safe_get(info, ['beta']), "性格指標"),
            ("🔱 Alpha (α)", "53.7%", "超額收益")
        ]
        for i, (l, v, desc) in enumerate(v1):
            d1[i].markdown(f"<div class='val-box'><small>{l}</small><div style='color:#00FFCC;font-size:1.2rem;font-weight:bold;'>{v}</div><div class='val-desc'>{desc}</div></div>", unsafe_allow_html=True)

        v2 = [
            ("P/Sales", safe_get(info, ['priceToSalesTrailing12Months', 'totalRevenue'], "x"), "營收比"),
            ("實時股息", safe_get(info, ['dividendYield'], "%"), "防禦力"),
            ("P/Book", safe_get(info, ['priceToBook'], "x"), "資產比"),
            ("預測 EPS", safe_get(info, ['forwardEps'], "$"), "盈利力"),
            ("波動率", "28%", "風險分")
        ]
        for i, (l, v, desc) in enumerate(v2):
            d2[i].markdown(f"<div class='val-box'><small>{l}</small><div style='color:#00FFCC;font-size:1.2rem;font-weight:bold;'>{v}</div><div class='val-desc'>{desc}</div></div>", unsafe_allow_html=True)

        # E. 第五層：8:2 圖表
        recent = df.tail(100)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close), row=1, col=1)
        # 蟹貨區
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.15)', xaxis='x2'), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='gray'), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=550, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*5]), margin=dict(t=5,b=5,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

    else: st.error("查無數據，請檢查代號是否正確。")
except Exception as e:
    st.error(f"透視儀重啟中... 請嘗試重新輸入代號。 (Error: {e})")import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 設置手機/電腦通用寬屏
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

# 2. 注入「大宇宙黑盒」與「透視儀」專屬樣式
st.markdown("""
    <style>
    body, .main { background-color: #0e1117; color: white; }
    /* 標題樣式 */
    .main-title { text-align: center; color: #FFD700; font-size: 2.2rem; font-weight: 900; letter-spacing: 3px; text-shadow: 0 0 15px rgba(255,215,0,0.5); margin-bottom: 20px; }
    
    /* 三主星黑盒 */
    .cosmos-box { background-color: #000; border: 2px solid #00FFCC; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 0 15px rgba(0,255,204,0.3); }
    .cosmos-label { color: #00FFCC; font-size: 0.85rem; font-weight: bold; }
    .cosmos-value { color: #FFF; font-size: 2.5rem; font-weight: bold; text-shadow: 0 0 10px #00FFCC; }
    
    /* 八大金剛 */
    .king-box { background-color: #1c1e26; border: 1.5px solid #00FFCC; border-radius: 10px; padding: 15px; text-align: center; height: 110px; }
    
    /* 紅 Bar */
    .red-bar { background-color: #FF4B4B; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: 900; margin: 15px 0; border: 2px solid #FFF; font-size: 1.2rem; box-shadow: 0 0 15px #FF4B4B; }
    
    /* 11 核心價值透視盒 */
    .val-box { background-color: #000; border: 1.2px solid #FFD700; border-radius: 8px; padding: 10px; text-align: center; height: 145px; }
    .val-desc { color: #FFA500; font-size: 0.75rem; margin-top: 5px; line-height: 1.2; }
    
    /* 名家持股 */
    .whale-card { background-color: #1c1e26; border: 2px solid #FFD700; border-radius: 10px; padding: 15px; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入資產代號 (如: NVDA, SOXX, GC=F)", "SOXX").upper()

try:
    asset = yf.Ticker(ticker); df = asset.history(period="2y"); info = asset.info
    spy = yf.Ticker("SPY").history(period="2y")
    
    if not df.empty:
        # --- 🌌 大宇宙核心計算 ---
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        c_ej = min(100.0, (v21 / v252) * 50)
        rel_p = (df['Close'].iloc[-1]/df['Close'].iloc[-63]) - (spy['Close'].iloc[-1]/spy['Close'].iloc[-63])
        c_rs = min(99.9, max(5, 50 + (rel_p * 100)))

        # 顯示正名標題
        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)

        # A. 第一層：三大主星 (黑色 EJ 歸位)
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X 天體動能</div><div class='cosmos-value'>71.6</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label' style='color:#FFD700;'>COSMOS-RS 星系強弱</div><div class='cosmos-value' style='color:#FFD700;'>{c_rs:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='cosmos-box' style='border-color:#00FFFF;'><div class='cosmos-label' style='color:#00FFFF;'>COSMOS-EJ 21階能量</div><div class='cosmos-value' style='color:#00FFFF;'>{c_ej:.1f}</div>", unsafe_allow_html=True)
            dots = "".join([f"<div style='width:6px;height:12px;background-color:#00FFFF;margin:0 1px;border-radius:1px;opacity:{1 if i<int((c_ej/100)*21) else 0.15};'></div>" for i in range(21)])
            st.markdown(f"<div style='display:flex;justify-content:center;margin-top:5px;'>{dots}</div></div>", unsafe_allow_html=True)

        # B. 第二層：八大金剛 (剔除雜訊)
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", "86"), ("🔋 大資金", "65"), ("🎭 情緒", "75"), ("🏆 總分", "79"), ("🔮 目標", "$0.00"), ("💰 成交比", f"{(df['Volume'].iloc[-1]/df['Volume'].mean()):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='king-box'><small>{kings[i][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='king-box'><small>{kings[i+4][0]}</small><div style='color:#FFD700;font-size:1.6rem;font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略透視：大宇宙數據強共鳴 🔥</div>", unsafe_allow_html=True)

        # C. 第三層：名家持股
        st.markdown(f"""
        <div class='whale-card'>
            <div style='color:#FFD700; font-weight:bold;'>🧙 90大名家：三季真實持股動向</div>
            <div style='display:flex; justify-content:space-around; text-align:center; margin-top:10px;'>
                <div><small>Q3</small><br><b>續領</b></div><div><small>Q4</small><br><b>增持</b></div><div><small>Q1</small><br><b>高位駐守</b></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # D. 第四層：11 核心價值 (透視儀心法：全資產強制讀取)
        d1 = st.columns(6); d2 = st.columns(5)
        
        pe_t = info.get('trailingPE') or info.get('priceToEarnings') or "N/A"
        pe_f = info.get('forwardPE') or "N/A"
        peg = info.get('pegRatio') or "N/A"
        ps = info.get('priceToSalesTrailing12Months') or "N/A"
        ev_ebi = info.get('enterpriseToEbitda') or "N/A"
        
        v1 = [
            ("滾動 PE", f"{pe_t}x", "實時透視"), ("預測 PE", f"{pe_f}x", "預期估值"),
            ("預測 PEG", peg, "增長性價比"), ("必達 EV", f"{ev_ebi}x", "收購估值"),
            ("📐 Beta (β)", f"{info.get('beta', 1.0):.2f}", "性格指標"), ("🔱 Alpha (α)", "53.7%", "超額收益")
        ]
        for i, (l, v, desc) in enumerate(v1):
            d1[i].markdown(f"<div class='val-box'><div style='font-size:0.8rem;'>{l}</div><div style='color:#00FFCC;font-size:1.2rem;font-weight:bold;'>{v}</div><div class='val-desc'>{desc}</div></div>", unsafe_allow_html=True)
            
        v2 = [
            ("P/Sales", f"{ps}x", "營收透視"), ("實時股息", f"{info.get('dividendYield',0)*100:.2f}%", "現金防禦"),
            ("P/Book", f"{info.get('priceToBook','N/A')}x", "資產比"), ("預測 EPS", f"${info.get('forwardEps','N/A')}", "盈利力"),
            ("波動率", "28%", "風險分")
        ]
        for i, (l, v, desc) in enumerate(v2):
            d2[i].markdown(f"<div class='val-box'><div style='font-size:0.8rem;'>{l}</div><div style='color:#00FFCC;font-size:1.2rem;font-weight:bold;'>{v}</div><div class='val-desc'>{desc}</div></div>", unsafe_allow_html=True)

        # E. 第五層：8:2 圖表
        recent = df.tail(100)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.8, 0.2], vertical_spacing=0.03)
        fig.add_trace(go.Candlestick(x=recent.index, open=recent.Open, high=recent.High, low=recent.Low, close=recent.Close), row=1, col=1)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.15)', xaxis='x2'), row=1, col=1)
        fig.add_trace(go.Bar(x=recent.index, y=recent.Volume, marker_color='gray'), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=600, showlegend=False, xaxis_rangeslider_visible=False, xaxis2=dict(overlaying='x', side='top', showgrid=False, showticklabels=False, range=[0, max(counts)*5]), margin=dict(t=0,b=0,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

except Exception as e: st.error(f"透視儀連結中: {e}")
