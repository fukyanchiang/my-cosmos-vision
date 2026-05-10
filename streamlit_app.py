import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st

# ==========================================
# 1. 兵力名單 (請自己將幾千隻股加返落去)
# ==========================================
HK_STOCK_MAP = {"1. 互聯網": ["0700.HK", "9988.HK"]} 
US_STOCK_MAP = {"1. AI": ["NVDA", "MSFT", "TSLA"]}
HK_ETF_MAP = {"H1": ["2800.HK", "3033.HK"]}
US_ETF_MAP = {"U1": ["QQQ", "SPY"]}

@st.cache_data(ttl=3600)
def smart_fetch(ticker, period="1y"):
    try:
        data = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        return data.dropna(subset=['Close', 'Volume'])
    except: return pd.DataFrame()

# ==========================================
# 2. 🐲 龍魂掃股核心：11項死刑 + 7大海選
# ==========================================
def analyze_dragon_soul(ticker, df, market_type="HK"):
    if len(df) < 65: return False, 0, "", "", {}
    c, o, h, l, v = df['Close'], df['Open'], df['High'], df['Low'], df['Volume']
    curr_p, ma20_v = c.iloc[-1], v.rolling(20).mean().iloc[-1]
    sma50 = c.rolling(50).mean().iloc[-1]
    bias = ((curr_p - sma50) / sma50) * 100
    rs = 50 + ((curr_p / c.iloc[-63]) - 1) * 100
    ej = (v.tail(21).mean() / max(v.tail(252).mean() if len(df)>250 else v.mean(), 1)) * 100
    se = 50 + (((curr_p / c.iloc[-5]) - 1) * 1200)

    mf = ((h+l+c)/3) * v * np.where(c > c.shift(1).fillna(c), 1, -1)
    net_flow_20 = mf.tail(20).sum()
    obv = (np.sign(c.diff()) * v).fillna(0).cumsum()
    obv_slope = (obv.iloc[-1] - obv.iloc[-10]) / 10

    # 11 項死刑 Foul 制
    if (v.iloc[-1] > ma20_v*1.5 and c.iloc[-1] < o.iloc[-1]): return False, 0, "", "", {}
    if (c.iloc[-1] > o.iloc[-1] and mf.iloc[-1] < 0): return False, 0, "", "", {}
    if (v.iloc[-1] > ma20_v*3 and abs(c.iloc[-1]/o.iloc[-1]-1) < 0.02): return False, 0, "", "", {}
    if bias > 15: return False, 0, "", "", {}
    if obv_slope < 0: return False, 0, "", "", {}
    
    # 7 大海選指標
    if not (rs > 60 and ej > 85 and se > 75 and bias < 15): return False, 0, "", "", {}

    # 評分與標籤
    score = (rs * 0.35) + (ej * 0.25)
    limit = 8 if market_type == "HK" else 5
    if bias > limit: score -= (bias - limit) * 10
    
    stage = "[👑 👑 初段起步]" if bias < 2 else "[👑 中段跟進]"
    icons = "💰🔥 ⚡" if se > 90 else "💎"
    
    return True, score, stage, icons, {"RS":round(rs,1), "EJ":round(ej,1), "SE":round(se,1), "Bias":round(bias,1), "StopLoss":round(curr_p*0.92,2)}
