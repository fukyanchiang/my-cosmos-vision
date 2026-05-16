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

# 🛡️ 爺爺修正：加返 force_return 參數落去，解決 TypeError！
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
    is_dead = False
    death_reason = ""
    death_lookback = 10
    
    if is_magenta.tail(death_lookback).any(): 
        is_dead = True; death_reason = "近10日有爆量派貨案底"
    elif pct.iloc[-1] >= 0 and netvol.iloc[-1] < 0: 
        is_dead = True; death_reason = "今日托住走貨"
    elif (len(c) >= 10) and (c.iloc[-1] >= c.iloc[-10]) and (obv.iloc[-1] < obv.iloc[-10]):
        is_dead = True; death_reason = "OBV價量背離(散水)"
    elif curr_p <= ma50.iloc[-1]: 
        is_dead = True; death_reason = "跌穿50天線"

    # 2. 8大硬指標
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netflow_20 / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(5).sum() * 100)
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    buy_sum_10 = buyvol.tail(10).sum()
    sell_sum_10 = sellvol.tail(10).sum()
    display_power = buyvol.iloc[-1] / sellvol.iloc[-1] if sellvol.iloc[-1] > 0 else 1.0
    current_power = min(display_power, 4.0)

    # OBV 1到9 狀態引擎
    obv_curr = obv.iloc[-1] - obv.iloc[-21] if len(obv) > 20 else obv.iloc[-1] - obv.iloc[0]
    obv_prev = obv.iloc[-21] - obv.iloc[-41] if len(obv) > 40 else 1
    obv_pct = (obv_curr - obv_prev) / max(abs(obv_prev), 1) * 100
    p_trend = c.iloc[-1] - c.iloc[-21] if len(c) > 20 else c.iloc[-1] - c.iloc[0]
    obv_total_vol = v.tail(20).sum() if v.tail(20).sum() > 0 else 1

    if abs(obv_curr) / obv_total_vol < 0.02: obv_state = 9
    else:
        if p_trend >= 0:
            if obv_curr > 0: obv_state = 1 if obv_pct > 20 else 2
            else: obv_state = 5 if obv_pct < -20 else 6
        else:
            if obv_curr < 0: obv_state = 3 if obv_pct < -20 else 4
            else: obv_state = 7 if obv_pct > 20 else 8
            
    if obv_state not in [1, 2, 7, 8]: 
        is_dead = True; death_reason = f"OBV狀態非佳({obv_state})"
    if not (rs_val > 60 and ej_val > 85 and se_val > 75 and netflow_20 > 0 and conc < 70):
        is_dead = True; death_reason = "硬指標不達標"
    if buy_sum_10 <= sell_sum_10:
        is_dead = True; death_reason = "沽盤兵力大於買盤"

    # 🛡️ 如果陣亡且唔係強制回傳，就踢走
    if is_dead and not force_return: return None

    # 🔥 3. 原始戰力 & 🎯 4. 戰術總分
    raw_power = (rs_val * 0.6) + (ej_val * 0.4) + (se_val * 0.5) + (current_power * 5)
    score = 100.0 + (rs_val * 0.35 + ej_val * 0.25)
    
    if c.iloc[-1] > c.iloc[-20] * 1.3: score += 10 
    if netflow_20 > 0: score += 5                  
    if se_val > 80: score += 5                     
    if netflow_60 > 0: score += 10                 
    if netflow_60 > netflow_20: score += 5         
    if current_power > 1.5: score += 5             

    # 3 大紅利加分 & 文字化標牌
    bonus_list = []
    if obv_state in [1, 7]: 
        score += 10
        bonus_list.append("OBV(+10)")
    if rs_val >= 90.0: 
        score += 5
        bonus_list.append("RS(+5)")
    if curr_p >= h.tail(60).max(): 
        score += 5
        bonus_list.append("破頂(+5)")

    # 🛑 5. 家法扣分
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

    # 🔮 6. 隱藏公仔 & 暴力合併
    icons = []
    if rs_val > 90 and ej_val > 90 and se_val > 90 and pct.iloc[-1] > 0.02: icons.append("💰🔥")
    if conc < 40 and netflow_20 > 0: icons.append("🧧")
    stars = sum((c.tail(10) > o.tail(10)) & (v.tail(10) > ma50_v.tail(10) * 1.5))
    if stars > 0: icons.append(f"🐋({stars}/10)")

    icons_final = " ".join(icons)
    if bonus_list: icons_final += " | 🎖️" + ",".join(bonus_list)

    if is_dead: status = f"[☠️ 落選: {death_reason}]"
    elif bias < 2: status = "[👑 👑 初段起步]"
    elif bias > 10: status = "[⚠️ 末段衝刺]"
    else: status = "[👑 趨勢行進]"

    return {
        "Ticker": ticker, "Sector": sector_name, "Score": round(final_score, 1), 
        "RawPower": round(raw_power, 1), "Penalty": round(penalty, 1),
        "RS": round(rs_val, 1), "EJ": round(ej_val, 1), "SE": round(se_val, 1),
        "Flow": f"{netflow_20/1e6:.1f}M", "Conc": f"{conc:.1f}%", "OBV": f"狀態 {obv_state}",
        "Power": round(display_power, 1), "Bias": round(bias, 1), 
        "EMA10": round(ema10.iloc[-1], 2), "Status": status, 
        "Icons": icons_final, "IsDead": is_dead
    }
