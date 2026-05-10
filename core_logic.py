import pandas as pd
import yfinance as yf
import streamlit as st

@st.cache_data(ttl=3600)
def smart_fetch(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1y")
        return data if not data.empty else pd.DataFrame()
    except: 
        return pd.DataFrame()

def analyze_dragon_soul(ticker, df):
    if len(df) < 60: 
        return False, 0, "", {}
        
    c = df['Close']
    curr_p = c.iloc[-1]
    sma50 = c.rolling(50).mean().iloc[-1]
    sma200 = c.rolling(200).mean().iloc[-1]
    
    rs = ((curr_p / c.iloc[-60]) - 1) * 100 
    
    is_dragon = rs > 15 and curr_p > sma50 and sma50 > sma200
    
    if is_dragon:
        score = rs 
        return True, score, "🐉 龍魂覺醒", {"RS": round(rs, 1), "Price": round(curr_p, 2)}
        
    return False, 0, "", {}
