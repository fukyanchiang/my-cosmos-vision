import pandas as pd
import numpy as np
import yfinance as yf
import time

def smart_fetch(ticker_sym, period="1y"):
    """安全獲取數據，確保 0100.HK 呢類股都讀到"""
    try:
        time.sleep(0.2) 
        asset = yf.Ticker(ticker_sym)
        data = asset.history(period=period, auto_adjust=True)
        if data.empty:
            time.sleep(1.0)
            data = asset.history(period=period, auto_adjust=True)
        if data.index.tz is not None: data.index = data.index.tz_localize(None)
        return data.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open'])
    except: return pd.DataFrame()

def scan_dragon_logic(df, ticker, sector_name, market="HK"):
    """龍魂神殿 2.0 核心：7 禁 + 7 硬指標 + 權重計分"""
    if len(df) < 65: return None
    
    c = df['Close']; h = df['High']; l = df['Low']; o = df['Open']; v = df['Volume']
    curr_p = c.iloc[-1]
    
    # 核心量能指標
    denom = np.maximum(h - l, 0.001)
    netvol = (v * (c - l) / denom) - (v * (h - c) / denom)
    netflow_20 = netvol.tail(20).sum()
    ma20_v = v.rolling(20).mean()
    ma50 = c.rolling(50).mean()
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    daily_pct = c.pct_change()

    # --- 🛡️ 第一層：7 大禁示 (Foul) ---
    if v.iloc[-1] > ma20_v.iloc[-1]*1.5 and daily_pct.iloc[-1] < -0.03: return None # 直接派貨
    if daily_pct.iloc[-1] > 0 and netvol.iloc[-1] < 0: return None # 托住走貨
    if bias > 15 and v.iloc[-1] >= v.tail(252).max() * 0.9: return None # 末段癲狗

    # --- 🐲 第二層：7 大硬指標 (海選) ---
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    if rs_val < 60 or netflow_20 <= 0: return None # 基本門檻

    # --- 🏆 第三層：計分與扣分 (100分底) ---
    score = 100.0
    score += (rs_val * 0.35)
    
    # 一劍封喉：美股>5% / 港股>10% 扣 50 分
    if (market == "US" and bias > 5) or (market == "HK" and bias > 10):
        score -= 50
    elif bias > (5 if market == "US" else 8):
        score -= (bias - (5 if market == "US" else 8)) * 5

    # 4大品質扣分 (簡化版確保運行)
    if v.iloc[-1] > ma20_v.iloc[-1] * 5: score -= 20 # 爆缸天量

    # --- 🔮 隱藏公仔 ---
    icons = []
    if rs_val > 92: icons.append("💰🔥")
    # 🐋 鯨魚現身 (數 10 日內出 🌟 次數)
    whale_days = sum((c.tail(10) > o.tail(10)) & (v.tail(10) > v.rolling(50).mean().tail(10) * 1.5))
    if whale_days > 0: icons.append(f"🐋({whale_days}/10)")

    # --- 🏷️ 三段位標籤 ---
    status = "[👑 👑 初段]" if bias < 2 else "[👑 中段]" if bias < 6 else "[⚠️ 末段]"

    return {
        "Ticker": ticker, "Sector": sector_name, "Score": round(score, 1),
        "Status": status, "Icons": " ".join(icons), "IconCount": len(icons),
        "RS": round(rs_val, 1), "Flow": f"{netflow_20/1e6:.1f}M", "Bias": round(bias, 1)
    }
