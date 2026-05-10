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

def scan_dragon_logic(df, ticker, sector_name, market="HK"):
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

    # 1. 7大禁示 (絕對死刑)
    if v.iloc[-1] > ma20_v.iloc[-1] * 1.2 and pct.iloc[-1] <= -0.02: return None 
    if pct.iloc[-1] >= 0 and netvol.iloc[-1] < 0: return None # 絕殺 0981
    if v.iloc[-1] > ma20_v.iloc[-1] * 1.5 and 0 <= pct.iloc[-1] < 0.02: return None 
    if len(pct) > 2 and pct.iloc[-2] > 0.04 and v.iloc[-1] <= v.iloc[-2] * 0.5: return None 
    if bias > 15 and v.iloc[-1] >= v.tail(252).max() * 0.9: return None 
    if abs(pct.iloc[-1]) < 0.015 and obv.iloc[-1] < obv.iloc[-5]: return None 

    # 2. 8大硬指標
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netflow_20 / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(5).sum() * 100)
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    buy_sum_10 = buyvol.tail(10).sum()
    sell_sum_10 = sellvol.tail(10).sum()
    current_power = buyvol.iloc[-1] / sellvol.iloc[-1] if sellvol.iloc[-1] > 0 else 1.0

    if not (rs_val > 60 and ej_val > 85 and se_val > 75 and netflow_20 > 0 and conc < 70): return None
    if buy_sum_10 <= sell_sum_10: return None
    if curr_p <= ma50.iloc[-1]: return None

    # 3. 權重計分 (補足 60日錢流 + 狀態紅利)
    score = 100.0 + (rs_val * 0.35 + ej_val * 0.25)
    if c.iloc[-1] > c.iloc[-20] * 1.3: score += 10 
    if netflow_20 > 0: score += 5                  
    if se_val > 80: score += 5                     
    if netflow_60 > 0: score += 10                 
    if netflow_60 > netflow_20: score += 5         
    if se_val > 75: score += 5                     
    if current_power > 1.5: score += 5             

    # 4. 品質扣分
    if (v.tail(60) > ma20_v.tail(60)*4).any() and (c.tail(60) < o.tail(60)).any(): score -= 30 
    bias_limit = 5 if market == "US" else 10
    if bias > bias_limit * 1.5: score -= 25 
    if v.iloc[-1] > ma20_v.iloc[-1] * 5: score -= 20 
    if (h.iloc[-1] - max(o.iloc[-1], c.iloc[-1])) > (h.iloc[-1] - l.iloc[-1]) * 0.5: score -= 15 

    if bias > bias_limit:
        if bias > bias_limit + 5: score -= 50 
        else: score -= (bias - bias_limit) * 10

    # =======================================================
    # 🔮 第五層：8 大隱藏公仔 (前 7 個，第 8 個在 UI 層)
    # =======================================================
    icons = []
    # 1. 💰🔥 爆發點火
    if rs_val > 90 and ej_val > 90 and se_val > 90 and pct.iloc[-1] > 0.02: icons.append("💰🔥")
    # 2. 💰🤫 窄位建倉
    if rs_val > 85 and ej_val > 85 and se_val > 85 and (h.iloc[-1] - l.iloc[-1])/l.iloc[-1] < 0.015: icons.append("💰🤫")
    # 3. 💰🛡️ 托底錢袋
    if rs_val > 80 and ej_val > 80 and se_val > 80 and pct.iloc[-1] < 0 and netflow_20 > 0: icons.append("💰🛡️")
    # 4. 💎 驚天洗盤 (紫色托底柱)
    if pct.iloc[-1] < 0 and netvol.iloc[-1] > ma20_v.iloc[-1] * 1.5: icons.append("💎")
    # 5. 🧧 悶聲吸儲 (VCP末端)
    if conc < 40 and netflow_20 > netflow_60 * 0.3 and netflow_20 > 0: icons.append("🧧")
    # 6. ⚡ 閃電點火
    if v.iloc[-1] > ma20_v.iloc[-1] * 2 and v.iloc[-2] < ma20_v.iloc[-2]: icons.append("⚡")
    # 7. 🐋 鯨魚現身
    stars = sum((c.tail(10) > o.tail(10)) & (v.tail(10) > ma50_v.tail(10) * 1.5))
    if stars > 0: icons.append(f"🐋({stars}/10)")
    # =======================================================

    if bias < 2 and se_val > 85: status = "[👑 👑 初段起步]"
    elif 2 <= bias <= 5 and rs_val > 95: status = "[👑 中段跟進]"
    elif bias > 10 and rs_val >= 99: status = "[⚠️ 末段衝刺]"
    else: status = "[👑 趨勢行進]"

    return {
        "Ticker": ticker, "Sector": sector_name, "Score": round(score, 1), 
        "RS": round(rs_val, 1), "EJ": round(ej_val, 1), "SE": round(se_val, 1),
        "Flow": f"{netflow_20/1e6:.1f}M", "Conc": f"{conc:.1f}%", "OBV": "狀態 1",
        "Power": round(current_power, 1), "Bias": round(bias, 1), "EMA10": round(ema10.iloc[-1], 2),
        "Status": status, "Icons": " ".join(icons), "IconCount": len(icons)
    }
