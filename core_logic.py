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
    ma20_v = v.rolling(20).mean(); ma50 = c.rolling(50).mean()
    ema10 = c.ewm(span=10, adjust=False).mean()
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    
    # 🧬 核心 3 項成交量指標
    var3 = np.maximum(h - l, 0.001)
    buyvol = v * (c - l) / var3
    sellvol = v * (h - c) / var3
    netvol = buyvol - sellvol
    netflow_20 = netvol.tail(20).sum()
    netflow_60 = netvol.tail(60).sum() # 60日累積錢流
    obv = (np.sign(pct) * v).cumsum()

    # --- 🐲 第一層：7 大禁示 (絕對死刑 - 中一即 Foul) ---
    if v.iloc[-1] > ma20_v.iloc[-1] * 1.2 and pct.iloc[-1] <= -0.02: return None # 直接派貨
    if pct.iloc[-1] > 0 and netvol.iloc[-1] < 0: return None # 托住走貨 (絕殺0981)
    if v.iloc[-1] > ma20_v.iloc[-1] * 1.5 and 0 < pct.iloc[-1] < 0.02: return None # 放量滯漲
    if len(pct) > 2 and pct.iloc[-2] > 0.04 and v.iloc[-1] <= v.iloc[-2] * 0.5: return None # 錢流斷層
    if bias > 15 and v.iloc[-1] >= v.tail(252).max() * 0.9: return None # 末段癲狗
    if abs(pct.iloc[-1]) < 0.015 and obv.iloc[-1] < obv.iloc[-5]: return None # OBV 詐騙

    # --- 🐲 第二層：8 大硬指標 (生存海選) ---
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netflow_20 / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(5).sum() * 100)
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    if not (rs_val > 60 and ej_val > 85 and se_val > 75 and netflow_20 > 0 and conc < 70): return None
    if buyvol.tail(10).sum() <= sellvol.tail(10).sum(): return None # 買盤兵力勝出

    # --- 🏆 第三層：權重計分 ---
    score = 100.0
    score += (rs_val * 0.35 + ej_val * 0.25) # 1. 皇者底色
    if c.iloc[-1] > c.iloc[-20] * 1.3: score += 10 # 2. 加速度
    if netflow_20 > 0: score += 5
    if se_val > 80: score += 5
    
    # 🌊 3. 長線底氣 (新加入)
    if netflow_60 > 0: score += 10 # 大後勁
    if netflow_60 > netflow_20: score += 5 # 長線莊家
    
    # 🛡️ 4. 狀態紅利 (買點安全)
    if se_val > 75: score += 5 # 彈簧
    if buyvol.iloc[-1] > sellvol.iloc[-1] * 1.5: score += 5 # 兵力

    # --- 🚨 第四層：品質扣分 (30/25/20/15) ---
    # 💀 60日萬人坑
    if (v.tail(60) > ma20_v.tail(60)*4).any() and (c.tail(60) < o.tail(60)).any(): score -= 30
    # 🚨 位置虛脫
    bias_limit = 5 if market == "US" else 10
    if bias > bias_limit * 1.5: score -= 25
    # 💥 爆缸天量
    if v.iloc[-1] > ma20_v.iloc[-1] * 5: score -= 20
    # 🖋️ 影線派貨
    if (h.iloc[-1] - max(o.iloc[-1], c.iloc[-1])) > (h.iloc[-1] - l.iloc[-1]) * 0.5: score -= 15

    # --- Bias 安全制動 (階梯罰分) ---
    if bias > bias_limit:
        if bias > bias_limit + 5: score -= 50 # 一劍封喉
        else: score -= (bias - bias_limit) * 10

    # --- 🔮 公仔與標籤 ---
    icons = []
    if rs_val > 90 and ej_val > 90: icons.append("💰🔥")
    stars = sum((c.tail(10) > o.tail(10)) & (v.tail(10) > v.rolling(50).mean().tail(10) * 1.5))
    if stars > 0: icons.append(f"🐋({stars}/10)")

    # 🏷️ 三段位標籤 (依據你給的精準條件)
    if bias < 2 and se_val > 85: status = "[👑 👑 初段起步]"
    elif 2 <= bias <= 5 and rs_val > 95: status = "[👑 中段跟進]"
    elif bias > 10 and rs_val >= 99: status = "[⚠️ 末段衝刺]"
    else: status = "[👑 趨勢行進]"

    return {
        "Ticker": ticker, "Sector": sector_name, "Score": round(score, 1), "RS": round(rs_val, 1),
        "EJ": round(ej_val, 1), "SE": round(se_val, 1), "Flow": f"{netflow_20/1e6:.1f}M", 
        "Conc": f"{conc:.1f}%", "Bias": round(bias, 1), "EMA10": round(ema10.iloc[-1], 2),
        "Status": status, "Icons": " ".join(icons), "IconCount": len(icons)
    }
