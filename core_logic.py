import pandas as pd
import numpy as np
import yfinance as yf
import time

def smart_fetch(ticker_sym, period="1y"):
    try:
        time.sleep(0.2)
        asset = yf.Ticker(ticker_sym)
        data = asset.history(period=period, auto_adjust=True)
        if data.empty:
            time.sleep(1.0); data = asset.history(period=period, auto_adjust=True)
        if data.index.tz is not None: data.index = data.index.tz_localize(None)
        return data.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open'])
    except: return pd.DataFrame()

def check_stop_loss(df):
    """戰損置頂：偵測最近 2 日跌穿 10-EMA"""
    if len(df) < 15: return False
    ema10 = df['Close'].ewm(span=10, adjust=False).mean()
    c1 = df['Close'].iloc[-1] < ema10.iloc[-1]
    c2 = df['Close'].iloc[-2] >= ema10.iloc[-2]
    c3 = df['Close'].iloc[-2] < ema10.iloc[-2] and df['Close'].iloc[-3] >= ema10.iloc[-3]
    return c1 and (c2 or c3)

def scan_dragon_logic(df, ticker, sector_name, market="HK"):
    """龍魂神殿 2.0 - 絕對死刑版"""
    if len(df) < 65: return None
    
    c = df['Close']; h = df['High']; l = df['Low']; o = df['Open']; v = df['Volume']
    curr_p = c.iloc[-1]
    pct = c.pct_change().fillna(0)
    ma20_v = v.rolling(20).mean(); ma50_v = v.rolling(50).mean(); ma50 = c.rolling(50).mean()
    ema10 = c.ewm(span=10, adjust=False).mean()
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    
    # --- 🧬 量能 DNA ---
    var1 = c - l; var2 = h - c; var3 = np.maximum(h - l, 0.001)
    buyvol = pd.Series(np.where(var3 > 0, v * var1 / var3, 0), index=v.index)
    sellvol = pd.Series(np.where(var3 > 0, v * var2 / var3, 0), index=v.index)
    netvol = buyvol - sellvol
    netflow_20 = netvol.tail(20).sum(); netflow_60 = netvol.tail(60).sum()
    obv = (np.sign(pct) * v).cumsum()
    
    # =========================================================
    # 🐲 第一層：7 大禁示 (絕對死刑 - 中一項即 Foul 出局)
    # =========================================================
    # 1. 直接派貨：成交大 ＋ 價大跌
    if v.iloc[-1] > ma20_v.iloc[-1] * 1.2 and pct.iloc[-1] <= -0.02: return None
    
    # 2. 托住走貨：價升 ＋ 錢流轉負 (NetVol < 0)
    if pct.iloc[-1] > 0 and netvol.iloc[-1] < 0: return None
    
    # 3. 放量滯漲：天量 ＋ 升幅 < 2%
    if v.iloc[-1] > ma20_v.iloc[-1] * 1.5 and 0 < pct.iloc[-1] < 0.02: return None
    
    # 5. 錢流斷層：暴升後次日成交即縮 50%
    if pct.iloc[-2] > 0.04 and v.iloc[-1] <= v.iloc[-2] * 0.5: return None
    
    # 6. 末段癲狗：Bias > 15% ＋ 再爆歷史天量
    if bias > 15 and v.iloc[-1] >= v.tail(252).max() * 0.9: return None
    
    # 7. OBV 詐騙：價穩但 OBV 軌跡持續向下
    if abs(pct.iloc[-1]) < 0.015 and obv.iloc[-1] < obv.iloc[-5]: return None
    # =========================================================

    # --- 🐲 第二層：8 大硬指標 ---
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netflow_20 / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(5).sum() * 100)
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    
    if not (rs_val > 60 and ej_val > 85 and se_val > 75): return None
    if obv.iloc[-1] <= obv.iloc[-20]: return None
    if conc >= 70: return None
    if buyvol.tail(10).sum() <= sellvol.tail(10).sum(): return None
    if netflow_20 <= 0: return None

    # --- 🏆 第三層：權重打分 ---
    score = 100.0 + (rs_val * 0.35) + (ej_val * 0.25)
    if c.iloc[-1] > c.iloc[-20] * 1.3: score += 10
    if netflow_20 > 0: score += 5
    if se_val > 80: score += 5
    if netflow_60 > 0: score += 10
    if netflow_60 > netflow_20: score += 5
    if se_val > 75: score += 5
    if buyvol.iloc[-1] > sellvol.iloc[-1] * 1.5: score += 5

    # --- 🚨 第四層：品質扣分 ---
    if (market == "US" and bias > 5) or (market == "HK" and bias > 10): score -= 50
    else:
        bias_start = 5 if market == "US" else 10
        if bias > bias_start: score -= (bias - bias_start) * 10
            
    if (v.tail(60) > ma20_v.tail(60)*4).any() and (c.tail(60) < o.tail(60)).any(): score -= 30
    if bias > (5 if market == "US" else 10) * 1.5: score -= 25
    if v.iloc[-1] > ma20_v.iloc[-1] * 5: score -= 20
    if (h.iloc[-1] - max(o.iloc[-1], c.iloc[-1])) > (h.iloc[-1] - l.iloc[-1]) * 0.5: score -= 15

    # --- 🔮 第五層：8 大隱藏公仔 ---
    icons = []
    if rs_val > 90 and ej_val > 90 and se_val > 90 and pct.iloc[-1] > 0.02: icons.append("💰🔥")
    if rs_val > 85 and ej_val > 85 and se_val > 85 and (h.iloc[-1] - l.iloc[-1])/l.iloc[-1] < 0.015: icons.append("💰🤫")
    if rs_val > 80 and ej_val > 80 and se_val > 80 and pct.iloc[-1] < 0 and netflow_20 > 0: icons.append("💰🛡️")
    if pct.iloc[-1] < 0 and netvol.iloc[-1] > ma20_v.iloc[-1] * 1.5: icons.append("💎")
    if conc < 40 and netflow_20 > netflow_60 * 0.3 and netflow_20 > 0: icons.append("🧧")
    if v.iloc[-1] > ma20_v.iloc[-1] * 2 and v.iloc[-2] < ma20_v.iloc[-2]: icons.append("⚡")
    stars = sum((c.tail(10) > o.tail(10)) & (v.tail(10) > ma50_v.tail(10) * 1.5))
    if stars > 0: icons.append(f"🐋({stars}/10)")

    # --- 🏷️ 標籤回傳 ---
    if bias < 2 and se_val > 85 and netflow_20 > 0: status = "[👑 👑 初段起步]"
    elif 2 <= bias <= 5 and rs_val > 95: status = "[👑 中段跟進]"
    elif bias > 10 and rs_val >= 99: status = "[⚠️ 末段衝刺]"
    else: status = "[👑 趨勢行進]"

    return {
        "Ticker": ticker, "Sector": sector_name if sector_name else "綜合", "Score": round(score, 1), 
        "Status": status, "Icons": " ".join(icons), "IconCount": len(icons), "RS": round(rs_val, 1), 
        "EJ": round(ej_val, 1), "SE": round(se_val, 1), "Flow": f"{netflow_20/1e6:.1f}M", 
        "Conc": f"{conc:.1f}%", "OBV": "狀態 1", "Bias": round(bias, 1),
        "EMA10": round(ema10.iloc[-1], 2) # 加入 10 天 EMA 止損位
    }
