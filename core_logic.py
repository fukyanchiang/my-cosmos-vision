import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=3600)
def smart_fetch(ticker):
    try:
        # 抓取 1 年數據，足夠計算龍魂指標
        data = yf.Ticker(ticker).history(period="1y")
        return data if not data.empty else pd.DataFrame()
    except: 
        return pd.DataFrame()

def analyze_dragon_soul(ticker, df):
    # 如果上市日數唔夠 60 日，就唔分析
    if len(df) < 60: 
        return False, 0, "", {}
        
    c = df['Close']
    curr_p = c.iloc[-1]
    sma50 = c.rolling(50).mean().iloc[-1]
    sma200 = c.rolling(200).mean().iloc[-1]
    
    # 龍魂核心邏輯：RS 強度、均線排位
    # RS (Relative Strength): 計算過去 60 個交易日（約 3 個月）嘅漲幅
    rs = ((curr_p / c.iloc[-60]) - 1) * 100 
    
    # 龍魂門檻：
    # 1. RS > 15 (3個月內升超過15%，極度強勢) 
    # 2. 股價企穩喺 50 天線上 
    # 3. 50 天線高於 200 天線 (長線多頭排列)
    is_dragon = rs > 15 and curr_p > sma50 and sma50 > sma200
    
    if is_dragon:
        score = rs # 以強度作為得分，越高分排越前
        return True, score, "🐉 龍魂覺醒", {"RS": round(rs, 1), "Price": round(curr_p, 2)}
        
    return False, 0, "", {}
