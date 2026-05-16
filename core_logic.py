import pandas as pd
import numpy as np
import yfinance as yf
import time

def smart_fetch(ticker_sym, period="1y"):
    try:
        time.sleep(0.2); asset = yf.Ticker(ticker_sym)
        data = asset.history(period=period, auto_adjust=True)
        if data.empty:
            time.sleep(1.0); data = asset.history(period=period, auto_adjust=True)
        if data.index.tz is not None: data.index = data.index.tz_localize(None)
        return data.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open'])
    except: return pd.DataFrame()

def check_stop_loss(df):
    if len(df) < 15: return False
    ema10 = df['Close'].ewm(span=10, adjust=False).mean()
    return df['Close'].iloc[-1] < ema10.iloc[-1] and (df['Close'].iloc[-2] >= ema10.iloc[-2] or df['Close'].iloc[-3] >= ema10.iloc[-3])

def scan_dragon_logic(df, ticker, sector_name, market="HK", force_return=False):
    if len(df) < 65: return None
    c = df['Close']; h = df['High']; l = df['Low']; o = df['Open']; v = df['Volume']
    curr_p = c.iloc[-1]; pct = c.pct_change().fillna(0)
    ma20_v = v.rolling(20).mean(); ma50_v = v.rolling(50).mean(); ma50 = c.rolling(50).mean()
    ema10 = c.ewm(span=10, adjust=False).mean()
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    
    # 🧬 核心量能
    var3 = np.maximum(h - l, 0.001)
    buyvol = v * (c - l) / var3
    sellvol = v * (h - c) / var3
    netvol = buyvol - sellvol
    netflow_20 = netvol.tail(20).sum()
    netflow_60 = netvol.tail(60).sum()
    obv = (np.sign(pct) * v).cumsum()

    is_burst = (v > ma20_v * 1.5) & (abs(pct) > 0.02)
    is_magenta = is_burst & (c <= o)

    # 🚨 第一層：死亡審判
    is_dead = False; death_reason = ""
    if is_magenta.tail(10).any(): is_dead = True; death_reason = "爆量派貨案底"
    elif pct.iloc[-1] >= 0 and netvol.iloc[-1] < 0: is_dead = True; death_reason = "今日托住走貨"
    elif (len(c) >= 10) and (c.iloc[-1] >= c.iloc[-10]) and (obv.iloc[-1] < obv.iloc[-10]): is_dead = True; death_reason = "OBV價量背離"
    elif curr_p <= ma50.iloc[-1]: is_dead = True; death_reason = "跌穿50天線"

    # 2. 8大硬指標 (龍魂核心)
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netflow_20 / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(5).sum() * 100)
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    
    display_power = buyvol.iloc[-1] / sellvol.iloc[-1] if sellvol.iloc[-1] > 0 else 1.0
    current_power = min(display_power, 4.0)

    # OBV 1到9 狀態引擎
    obv_curr = obv.iloc[-1] - obv.iloc[-21] if len(obv) > 20 else obv.iloc[-1] - obv.iloc[0]
    obv_prev = obv.iloc[-21] - obv.iloc[-41] if len(obv) > 40 else 1
    obv_pct = (obv_curr - obv_prev) / max(abs(obv_prev), 1) * 100
    p_trend = c.iloc[-1] - c.iloc[-21] if len(c) > 20 else c.iloc[-1] - c.iloc[0]
    obv_total_vol = v.tail(20).sum() or 1

    if abs(obv_curr) / obv_total_vol < 0.02: obv_state = 9
    else:
        if p_trend >= 0:
            if obv_curr > 0: obv_state = 1 if obv_pct > 20 else 2
            else: obv_state = 5 if obv_pct < -20 else 6
        else:
            if obv_curr < 0: obv_state = 3 if obv_pct < -20 else 4
            else: obv_state = 7 if obv_pct > 20 else 8
            
    if obv_state not in [1, 2, 7, 8]: is_dead = True; death_reason = f"OBV狀態非佳({obv_state})"
    if not (rs_val > 60 and ej_val > 85 and se_val > 75 and netflow_20 > 0 and conc < 70): is_dead = True; death_reason = "指標不達標"
    if buyvol.tail(10).sum() <= sellvol.tail(10).sum(): is_dead = True; death_reason = "兵力不足"

    if is_dead and not force_return: return None

    # 🔥 3. 戰鬥力排行 & 🎯 4. 戰術總分
    score = 100.0 + (rs_val * 0.35 + ej_val * 0.25)
