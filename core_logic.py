import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

# 1. 兵力名單 (爺爺幫你預留位，請在此處補齊你舊 Code 的字典)
HK_STOCK_MAP = {"1. 互聯網巨頭": "0700.HK 9988.HK 3690.HK 1810.HK".split(), "2. 半導體": "0981.HK 1347.HK".split()}
US_STOCK_MAP = {"1. 半導體設計": "NVDA TSM AVGO ASML AMD".split(), "2. AI雲端": "MSFT GOOGL PLTR MSTR".split()}
HK_ETF_MAP = {"H1. 旗艦大盤": "2800.HK 3033.HK 3134.HK".split()}
US_ETF_MAP = {"U1. 核心主題": "QQQ SPY SOXX SMH".split()}

@st.cache_data(ttl=3600)
def smart_fetch(ticker, period="1y"):
    try:
        data = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        return data.dropna(subset=['Close', 'Volume'])
    except: return pd.DataFrame()

# ==========================================
# 🐲 龍魂掃股核心邏輯 (V2.0 終極版)
# ==========================================
def analyze_dragon_soul(ticker, df, market_type="HK"):
    if len(df) < 65: return False, 0, "", "", {}

    # --- A. 指標計算 ---
    c, o, h, l, v = df['Close'], df['Open'], df['High'], df['Low'], df['Volume']
    curr_p, ma20_v = c.iloc[-1], v.rolling(20).mean().iloc[-1]
    sma50 = c.rolling(50).mean().iloc[-1]
    bias = ((curr_p - sma50) / sma50) * 100
    rs = 50 + ((curr_p / c.iloc[-63]) - 1) * 100
    ej = (v.tail(21).mean() / max(v.tail(252).mean() if len(df)>250 else v.mean(), 1)) * 100
    se = 50 + (((curr_p / c.iloc[-5]) - 1) * 1200)

    # 資金流、OBV、集中度
    mf = ((h+l+c)/3) * v * np.where(c > c.shift(1).fillna(c), 1, -1)
    net_flow_20, net_flow_60 = mf.tail(20).sum(), mf.tail(60).sum()
    obv = (np.sign(c.diff()) * v).fillna(0).cumsum()
    obv_slope = (obv.iloc[-1] - obv.iloc[-10]) / 10
    conc = (abs(mf.tail(20)).max() / max(abs(mf.tail(20)).sum(), 1)) * 100
    buy_v, sell_v = (v*(c-l)/np.maximum(h-l,0.001)), (v*(h-c)/np.maximum(h-l,0.001))
    force_win = buy_v.tail(5).sum() > sell_v.tail(5).sum()

    # ------------------------------------------
    # 🛑 第一層：11 項「人間蒸發」死刑 (Foul 制)
    # ------------------------------------------
    if (v.iloc[-1] > ma20_v*1.5 and c.iloc[-1] < o.iloc[-1]*0.97): return False, 0, "", "", {} # 直接派貨
    if (c.iloc[-1] > o.iloc[-1] and mf.iloc[-1] < 0): return False, 0, "", "", {} # 托住走貨
    if (v.iloc[-1] > ma20_v*3 and abs(c.iloc[-1]/o.iloc[-1]-1) < 0.02): return False, 0, "", "", {} # 放量滯漲
    if (v.iloc[-1] > ma20_v*2 and v.iloc[-1] < v.shift(1).iloc[-1]*0.5): return False, 0, "", "", {} # 錢流斷層
    if bias > 15 and v.iloc[-1] > ma20_v*3: return False, 0, "", "", {} # 末段癲狗
    if obv_slope < 0: return False, 0, "", "", {} # OBV 詐騙
    v_60 = v.tail(60); max_v_idx = v_60.argmax()
    if (v_60.iloc[max_v_idx] > ma20_v*4) and (c.tail(60).iloc[max_v_idx] < o.tail(60).iloc[max_v_idx]): return False, 0, "", "", {} # 蟹貨
    if v.iloc[-1] > ma20_v*5: return False, 0, "", "", {} # 爆缸天量
    if (h.iloc[-1] - max(o.iloc[-1], c.iloc[-1])) > abs(c.iloc[-1]-o.iloc[-1])*2: return False, 0, "", "", {} # 影線派貨
    if bias > (12 if market_type=="HK" else 8): return False, 0, "", "", {} # 位置虛脫

    # ------------------------------------------
    # 🐲 第二層：龍魂海選 (7 大硬指標)
    # ------------------------------------------
    if not (rs > 60 and ej > 85 and se > 75 and net_flow_20 > 0 and bias < 15 and force_win and conc < 70):
        return False, 0, "", "", {}

    # ------------------------------------------
    # 🏆 第三層：評分排序
    # ------------------------------------------
    score = (rs * 0.35) + (ej * 0.25)
    if net_flow_20 > mf.iloc[-40:-20].sum()*1.3: score += 10 # 點火
    if ej > 100: score += 5
    if se > 85: score += 5
    if net_flow_60 > 0: score += 10
    if se > 75: score += 5
    limit = 8 if market_type == "HK" else 5
    if bias > limit: score -= (bias - limit) * 10

    # 🎨 第四層：標籤與 8 大公仔
    stage = "[👑 👑 初段起步]" if bias < 2 else ("[👑 中段跟進]" if bias <= 5 else "[⚠️ 末段衝刺]")
    icons = []
    if se > 85 and v.iloc[-1] > ma20_v * 1.5: icons.append("💰🔥")
    if abs(c.iloc[-1]/o.iloc[-1]-1) < 0.01 and ej > 110: icons.append("💰🤫")
    if c.iloc[-1] < o.iloc[-1] and mf.iloc[-1] > 0: icons.append("💰🛡️")
    if c.iloc[-1] < o.iloc[-1]*0.97 and mf.iloc[-1] > 0 and v.iloc[-1] > ma20_v*2: icons.append("💎")
    if ej > 120 and bias < 5: icons.append("🧧")
    if v.iloc[-1] > v.iloc[-2]*2 and v.iloc[-2] < ma20_v*0.6: icons.append("⚡")
    
    return True, score, stage, " ".join(icons), {"RS":round(rs,1), "EJ":round(ej,1), "SE":round(se,1), "Bias":round(bias,1), "StopLoss":round(curr_p*0.92,2)}
