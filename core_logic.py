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

    # ---------------------------------------------------------
    # 🚨 死亡審判 (記錄肥佬原因，如果 force_return=True 就照出分)
    # ---------------------------------------------------------
    is_dead = False
    death_reason = ""
    death_lookback = 10
    
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netflow_20 / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(5).sum() * 100)
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    buy_sum_10 = buyvol.tail(10).sum()
    sell_sum_10 = sellvol.tail(10).sum()
    current_power = buyvol.iloc[-1] / sellvol.iloc[-1] if sellvol.iloc[-1] > 0 else 1.0

    if is_magenta.tail(death_lookback).any(): is_dead = True; death_reason = "近期有爆量派貨案底"
    elif pct.iloc[-1] >= 0 and netvol.iloc[-1] < 0: is_dead = True; death_reason = "托住走貨 (量價背離)"
    elif curr_p <= ma50.iloc[-1]: is_dead = True; death_reason = "跌穿 50 天線 (生命線)"
    elif not (rs_val > 60 and ej_val > 85 and se_val > 75 and netflow_20 > 0 and conc < 70): is_dead = True; death_reason = "硬指標動力不足"
    elif buy_sum_10 <= sell_sum_10: is_dead = True; death_reason = "近期買盤弱於沽盤"

    # 如果非個股掃描且陣亡，直接踢走
    if is_dead and not force_return:
        return None

    # ---------------------------------------------------------
    # 計分系統
    # ---------------------------------------------------------
    raw_power = (rs_val * 0.6) + (ej_val * 0.4) + (se_val * 0.5) + (current_power * 5)
    score = 100.0 + (rs_val * 0.35 + ej_val * 0.25)
    
    if c.iloc[-1] > c.iloc[-20] * 1.3: score += 10 
    if netflow_20 > 0: score += 5                  
    if se_val > 80: score += 5                     
    if netflow_60 > 0: score += 10                 
    if netflow_60 > netflow_20: score += 5         
    if se_val > 75: score += 5                     
    if current_power > 1.5: score += 5             

    penalty = 0
    if (v.tail(60) > ma20_v.tail(60)*4).any() and (c.tail(60) < o.tail(60)).any(): penalty += 30 
    bias_limit = 5 if market == "US" else 10
    if bias > bias_limit * 1.5: penalty += 25 
    if v.iloc[-1] > ma20_v.iloc[-1] * 5: penalty += 20 
    if (h.iloc[-1] - max(o.iloc[-1], c.iloc[-1])) > (h.iloc[-1] - l.iloc[-1]) * 0.5: penalty += 15 
    if bias > bias_limit:
        if bias > bias_limit + 5: penalty += 50 
        else: penalty += (bias - bias_limit) * 10

    final_score = score - penalty

    icons = []
    if rs_val > 90 and ej_val > 90 and se_val > 90 and pct.iloc[-1] > 0.02: icons.append("💰🔥")
    if rs_val > 85 and ej_val > 85 and se_val > 85 and (h.iloc[-1] - l.iloc[-1])/l.iloc[-1] < 0.015: icons.append("💰🤫")
    if rs_val > 80 and ej_val > 80 and se_val > 80 and pct.iloc[-1] < 0 and netflow_20 > 0: icons.append("💰🛡️")
    if pct.iloc[-1] < 0 and netvol.iloc[-1] > ma20_v.iloc[-1] * 1.5: icons.append("💎")
    if conc < 40 and netflow_20 > netflow_60 * 0.3 and netflow_20 > 0: icons.append("🧧")
    if v.iloc[-1] > ma20_v.iloc[-1] * 2 and v.iloc[-2] < ma20_v.iloc[-2]: icons.append("⚡")
    stars = sum((c.tail(10) > o.tail(10)) & (v.tail(10) > ma50_v.tail(10) * 1.5))
    if stars > 0: icons.append(f"🐋({stars}/10)")

    if is_dead: status = f"[☠️ 肥佬落選: {death_reason}]"
    elif bias < 2 and se_val > 85: status = "[👑 👑 初段起步]"
    elif 2 <= bias <= 5 and rs_val > 95: status = "[👑 中段跟進]"
    elif bias > 10 and rs_val >= 99: status = "[⚠️ 末段衝刺]"
    else: status = "[👑 趨勢行進]"

    return {
        "Ticker": ticker, 
        "Sector": sector_name, 
        "Score": round(final_score, 1), 
        "RawPower": round(raw_power, 1), 
        "Penalty": round(penalty, 1),
        "RS": round(rs_val, 1), 
        "EJ": round(ej_val, 1), 
        "SE": round(se_val, 1),
        "Flow": f"{netflow_20/1e6:.1f}M", 
        "Conc": f"{conc:.1f}%", 
        "OBV": "狀態 1",
        "Power": round(current_power, 1), 
        "Bias": round(bias, 1), 
        "EMA10": round(ema10.iloc[-1], 2),
        "Status": status, 
        "Icons": " ".join(icons),
        "IsDead": is_dead
    }
