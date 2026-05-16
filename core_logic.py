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

    # 🚨 能量雷達 (粉紅柱判定)
    is_burst = (v > ma20_v * 1.5) & (abs(pct) > 0.02)
    is_magenta = is_burst & (c <= o)

    # =======================================================
    # 🚨 1. 7大禁示 (絕對死刑) - 100% 嚴格過濾版
    # =======================================================
    death_lookback = 10
    hist_bias = ((c - ma50) / ma50) * 100
    rule5_cond = (pct.shift(1) > 0.05) & (v < v.shift(1) * 0.5)

    # 1. 直接派貨 (近10日有爆量派貨案底)
    if is_magenta.tail(death_lookback).any(): return None 
    # 2. 托住走貨 (今日價升但錢流轉負)
    if pct.iloc[-1] >= 0 and netvol.iloc[-1] < 0: return None 
    # 3. 放量滯漲 (近10日曾天量但升幅<2%)
    if ((v > ma20_v * 2.0) & (pct >= 0) & (pct < 0.02)).tail(death_lookback).any(): return None
    # 4. 板塊撤退 (單股無法掃描，留白)
    # 5. 錢流斷層 (近10日曾暴升後次日成交急縮50%)
    if rule5_cond.tail(death_lookback).any(): return None
    # 6. 末段癲狗 (近10日Bias>15%且爆天量)
    if ((hist_bias > 15) & (v > ma20_v * 3.0)).tail(death_lookback).any(): return None
    # 7. OBV詐騙 (近10日價穩但OBV持續向下)
    if (len(c) >= 10) and (c.iloc[-1] >= c.iloc[-10]) and (obv.iloc[-1] < obv.iloc[-10]): return None
    
    # 基本生命線防守
    if curr_p <= ma50.iloc[-1]: return None

    # =======================================================
    # 2. 8大硬指標
    # =======================================================
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netflow_20 / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(5).sum() * 100)
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    buy_sum_10 = buyvol.tail(10).sum()
    sell_sum_10 = sellvol.tail(10).sum()
    
    # 👇 爺爺唯一加嘅金剛罩 (保護層3唔暴走，UI顯示照舊)
    display_power = buyvol.iloc[-1] / sellvol.iloc[-1] if sellvol.iloc[-1] > 0 else 1.0
    current_power = min(display_power, 4.0)

    if not (rs_val > 60 and ej_val > 85 and se_val > 75 and netflow_20 > 0 and conc < 70): return None
    if buy_sum_10 <= sell_sum_10: return None

    # =======================================================
    # 🔥 3. 原始戰力 (Raw Power) - 舊邏輯無上限計法 (已受金剛罩保護)
    # =======================================================
    raw_power = (rs_val * 0.6) + (ej_val * 0.4) + (se_val * 0.5) + (current_power * 5)

    # =======================================================
    # 🎯 4. 戰術總分 (Tactical Score)
    # =======================================================
    score = 100.0 + (rs_val * 0.35 + ej_val * 0.25)
    if c.iloc[-1] > c.iloc[-20] * 1.3: score += 10 
    if netflow_20 > 0: score += 5                  
    if se_val > 80: score += 5                     
    if netflow_60 > 0: score += 10                 
    if netflow_60 > netflow_20: score += 5         
    if se_val > 75: score += 5                     
    if current_power > 1.5: score += 5             

    # =======================================================
    # 🛑 5. 家法扣分 (Penalty)
    # =======================================================
    penalty = 0
    if (v.tail(60) > ma20_v.tail(60)*4).any() and (c.tail(60) < o.tail(60)).any(): penalty += 30 
    
    bias_limit = 5 if market == "US" else 10
    if bias > bias_limit * 1.5: penalty += 25 
    if v.iloc[-1] > ma20_v.iloc[-1] * 5: penalty += 20 
    if (h.iloc[-1] - max(o.iloc[-1], c.iloc[-1])) > (h.iloc[-1] - l.iloc[-1]) * 0.5: penalty += 15 

    if bias > bias_limit:
        if bias > bias_limit + 5: penalty += 50 
        else: penalty += (bias - bias_limit) * 10

    # 最終出戰分數
    final_score = score - penalty

    # =======================================================
    # 🔮 6. 隱藏公仔與狀態標籤
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

    if bias < 2 and se_val > 85: status = "[👑 👑 初段起步]"
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
        "Power": round(display_power, 1), # 👇 呢度畀 UI 讀取未封頂嘅數值
        "Bias": round(bias, 1), 
        "EMA10": round(ema10.iloc[-1], 2),
        "Status": status, 
        "Icons": " ".join(icons), 
        "IconCount": len(icons)
    }
