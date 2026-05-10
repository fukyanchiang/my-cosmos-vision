import pandas as pd
import numpy as np
import yfinance as yf
import time

# --- 1. 基礎數據抓取 ---
def smart_fetch(ticker_sym, period="1y"):
    try:
        time.sleep(0.2) 
        data = yf.Ticker(ticker_sym).history(period=period, auto_adjust=True)
        if data.empty:
            time.sleep(1.0)
            data = yf.Ticker(ticker_sym).history(period=period, auto_adjust=True)
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        return data.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open'])
    except:
        return pd.DataFrame()

# --- 2. 龍魂核心掃描引擎 ---
def scan_dragon_logic(df, ticker, sector_name, market="HK"):
    if len(df) < 65: return None
    
    # --- A. 初始化數據 ---
    c = df['Close']; h = df['High']; l = df['Low']; o = df['Open']; v = df['Volume']
    curr_p = c.iloc[-1]
    daily_pct = c.pct_change()
    
    # --- B. 核心 3 項量能指標 (大戶兵力) ---
    denom = np.maximum(h - l, 0.001)
    buyvol = np.where(h > l, v * (c - l) / denom, 0)
    sellvol = np.where(h > l, v * (h - c) / denom, 0)
    netvol = buyvol - sellvol
    
    netflow_20 = netvol[-20:].sum()
    netflow_60 = netvol[-60:].sum()
    
    # 技術指標
    ma20_v = v.rolling(20).mean()
    ma50_v = v.rolling(50).mean() # 用嚟計鯨魚星星
    ma50 = c.rolling(50).mean()
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    
    # 模擬計算 RS, EJ, SE (依據 2.0 邏輯)
    rs_val = 80.0 + (curr_p / ma50.iloc[-1] * 10) 
    ej_val = 85.0 + (netflow_20 / max(v.mean()*20, 1) * 5)
    se_val = 75.0 + (daily_pct.tail(5).sum() * 100)
    
    # 計算 OBV
    obv = (np.sign(daily_pct) * v).fillna(0).cumsum()
    obv_trend = obv.iloc[-1] - obv.iloc[-10]

    # --- C. 第一層：7 大禁示選股 (死刑 Foul) ---
    # 1. 直接派貨
    if v.iloc[-1] > ma20_v.iloc[-1]*1.5 and daily_pct.iloc[-1] < -0.03: return None
    # 2. 托住走貨
    if daily_pct.iloc[-1] > 0 and netvol[-1] < 0: return None
    # 3. 放量滯漲
    if v.iloc[-1] > ma20_v.iloc[-1]*3 and daily_pct.iloc[-1] < 0.02: return None
    # 5. 錢流斷層
    if daily_pct.iloc[-2] > 0.05 and v.iloc[-1] < v.iloc[-2]*0.5: return None
    # 6. 末段癲狗
    if bias > 15 and v.iloc[-1] >= v.tail(252).max() * 0.9: return None
    # 7. OBV 詐騙
    if daily_pct.tail(5).sum() > -0.01 and obv_trend < 0: return None
    
    # --- D. 第二層：7 大硬指標 (海選) ---
    if not (rs_val > 60 and ej_val > 85 and se_val > 75 and netflow_20 > 0): return None
    if buyvol[-10:].sum() <= sellvol[-10:].sum(): return None # 買盤勝出

    # --- E. 第三層：龍魂評分 2.0 (權重排位) ---
    score = 100.0
    score += (rs_val * 0.35) + (ej_val * 0.25) # 皇者底色
    if v.tail(20).sum() > v.iloc[-40:-20].sum() * 1.3: score += 10 # 加速度
    if netflow_20 > 0: score += 5
    if netflow_60 > 0: score += 10 # 長線底氣
    if se_val > 85: score += 5
    if buyvol[-1] > sellvol[-1] * 1.5: score += 5 # 兵力 > 150%

    # --- F. 第四層：安全制動 Bias 與 4 大品質扣分 ---
    # 1. 一劍封喉 (絕對死線)
    if (market == "US" and bias > 5) or (market == "HK" and bias > 10):
        score -= 50 # 直接扣 50 分
    
    # 2. 安全制動 (階梯罰分)
    bias_limit = 5 if market == "US" else 8
    if bias > bias_limit:
        score -= (bias - bias_limit) * 5
        
    # 3. 4 大品質扣分
    # 💀 60日萬人坑
    if (v.tail(60) > ma20_v.tail(60)*4).any() and (c.tail(60) < o.tail(60)).any(): score -= 30 
    # 🚨 位置虛脫
    if bias > bias_limit * 1.8: score -= 25
    # 💥 爆缸天量
    if v.iloc[-1] > ma20_v.iloc[-1] * 5: score -= 20
    # 🖋️ 影線派貨
    if (h.iloc[-1] - max(o.iloc[-1], c.iloc[-1])) > (h.iloc[-1] - l.iloc[-1]) * 0.5: score -= 15

    # --- G. 🔮 8 大隱藏公仔 ---
    icons = []
    if rs_val > 90 and ej_val > 90 and daily_pct.iloc[-1] > 0.02: icons.append("💰🔥")
    if abs(daily_pct.iloc[-1]) < 0.015 and rs_val > 85: icons.append("💰🤫")
    if daily_pct.iloc[-1] < 0 and netflow_20 > 0: icons.append("💰🛡️")
    if v.iloc[-1] > ma20_v.iloc[-1]*2 and c.iloc[-1] > ma20_v.iloc[-1]: icons.append("⚡")
    
    # 🐋 鯨魚現身 (統計 10 日內星星數)
    whale_days = sum((c.tail(10) > o.tail(10)) & (v.tail(10) > ma50_v.tail(10) * 1.5))
    if whale_days > 0:
        icons.append(f"🐋({whale_days}日/10日)")

    # --- H. 🏷️ 三段位標籤 (最置前顯示) ---
    if bias < 2 and se_val > 85: status = "[👑 👑 初段起步]"
    elif 2 <= bias <= 5 and rs_val > 95: status = "[👑 中段跟進]"
    elif bias > 10 and rs_val >= 99: status = "[⚠️ 末段衝刺]"
    else: status = "[👑 趨勢行進]"

    return {
        "Ticker": ticker, "Sector": sector_name, "Score": round(score, 1),
        "Status": status, "Icons": " ".join(icons), "IconCount": len(icons),
        "RS": round(rs_val, 1), "EJ": round(ej_val, 1), "SE": round(se_val, 1),
        "Flow": f"{'+' if netflow_20>0 else ''}{netflow_20/1e6:.1f}M", 
        "Conc": "分散", "OBV": "狀態 1", "Bias": round(bias, 1)
    }
