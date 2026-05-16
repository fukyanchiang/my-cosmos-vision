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

def scan_dragon_logic(df, ticker, sector_name, market="HK", force_return=False):
    if len(df) < 65: return None
    
    # 1. 基礎數據 (對應你 3 組指標)
    c = df['Close']; h = df['High']; l = df['Low']; o = df['Open']; v = df['Volume']
    curr_p = c.iloc[-1]; pct = c.pct_change().fillna(0)
    ma20_v = v.rolling(20).mean(); ma60_v = v.rolling(60).mean(); ma50 = c.rolling(50).mean()
    v_std20 = v.rolling(20).std(); v_upper = ma20_v + (2.0 * v_std20)
    
    var1 = c - l; var2 = h - c; var3 = np.maximum(h - l, 0.001)
    buyvol = v * var1 / var3; sellvol = v * var2 / var3; netvol = buyvol - sellvol
    change = (c - c.shift(1)) / c.shift(1) * 100
    obv = (np.sign(pct) * v).cumsum()

    # 爆發雷達 (粉紅柱/粉藍柱判定)
    is_burst = (v > v_upper) & (v > ma60_v * 1.9) & (abs(change) > 2.0)
    is_magenta = is_burst & (c <= o) # 粉紅色

    # =======================================================
    # 🚨 第一層：7大禁示 (20日歷史追蹤 - 扣分制)
    # =======================================================
    foul_points = 0; foul_list = []
    lookback = 20
    
    if is_magenta.tail(lookback).any(): foul_points += 10; foul_list.append("犯 1.-10")
    if ((change > 0) & (netvol < 0)).tail(lookback).any(): foul_points += 10; foul_list.append("犯 2.-10")
    if ((v > ma60_v * 2.0) & (change < 2.0) & (change >= 0)).tail(lookback).any(): foul_points += 10; foul_list.append("犯 3.-10")
    if (netvol.rolling(5).sum() < 0).tail(lookback).any(): foul_points += 10; foul_list.append("犯 4.-10")
    if ((change.shift(1) > 5.0) & (v < v.shift(1) * 0.5)).tail(lookback).any(): foul_points += 10; foul_list.append("犯 5.-10")
    if ((((c - ma50)/ma50)*100 > 15) & (v > ma60_v * 3.0)).tail(lookback).any(): foul_points += 10; foul_list.append("犯 6.-10")
    if ((c >= c.shift(10)) & (obv < obv.shift(10))).tail(lookback).any(): foul_points += 10; foul_list.append("犯 7.-10")

    # =======================================================
    # 🐉 第二層：龍魂硬指標 (踢人門檻)
    # =======================================================
    is_dead = False; death_reason = ""
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netvol.tail(20).sum() / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(5).sum() * 100)
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    
    # OBV 完整 1-9 狀態
    obv_curr = obv.iloc[-1] - obv.iloc[-21]
    obv_prev = obv.iloc[-21] - obv.iloc[-41] if len(obv)>40 else 1
    obv_pct = (obv_curr - obv_prev) / max(abs(obv_prev), 1) * 100
    p_trend = c.iloc[-1] - c.iloc[-21]
    if p_trend >= 0:
        if obv_curr > 0: obv_state = 1 if obv_pct > 20 else 2
        else: obv_state = 5 if obv_pct < -20 else 6
    else:
        if obv_curr < 0: obv_state = 3 if obv_pct < -20 else 4
        else: obv_state = 7 if obv_pct > 20 else 8

    # 🛑 死亡審判
    if curr_p <= ma50.iloc[-1]: is_dead = True; death_reason = "跌穿50天線"
    elif is_magenta.iloc[-1]: is_dead = True; death_reason = "今日粉紅爆缸"
    elif not (rs_val > 60 and ej_val > 85 and se_val > 75 and netvol.tail(20).sum() > 0): 
        is_dead = True; death_reason = "SE或錢流不達標"
    elif obv_state not in [1, 2, 7, 8]: is_dead = True; death_reason = f"OBV狀態佳({obv_state})"

    if is_dead and not force_return: return None

    # =======================================================
    # 🏆 第四層：權重計分與扣分
    # =======================================================
    score = 100.0
    bonus_list = []
    
    # 加分項
    if se_val > 75: score += 5; bonus_list.append("SE(+5)")
    if (buyvol.iloc[-1] / sellvol.iloc[-1] if sellvol.iloc[-1]>0 else 1) > 1.5: score += 5; bonus_list.append("兵力(+5)")
    if obv_state in [1, 7]: score += 10; bonus_list.append("OBV(+10)")
    if netvol.tail(60).sum() > 0: score += 5; bonus_list.append("穩定流入(+5)")
    if rs_val >= 92.0: score += 5; bonus_list.append("RS(+5)")
    if curr_p >= h.tail(60).max(): score += 5; bonus_list.append("破頂(+5)")

    # 4大核心品質扣分 (今日)
    core_penalty = 0
    if netvol.tail(60).sum() < 0: core_penalty += 30      # 萬人坑
    limit = 10 if market == "HK" else 5
    if bias > limit: core_penalty += 25                  # 位置虛脫
    if v.iloc[-1] > ma60_v.iloc[-1] * 2.5: core_penalty += 20 # 爆缸天量
    if (h.iloc[-1] - max(c.iloc[-1], o.iloc[-1])) / var3.iloc[-1] > 0.5: core_penalty += 15 # 影線派貨

    # Bias 階梯罰分
    bias_penalty = 50 + (bias - limit) * 10 if bias > limit else 0

    final_score = score - core_penalty - bias_penalty - foul_points

    # 🔮 徽章合併
    icons = []
    if netvol.tail(20).sum() > 0: icons.append("🧧")
    stars = sum((v.tail(10) > ma60_v.tail(10) * 1.5))
    if stars > 0: icons.append(f"🐋({stars}/10)")
    
    icons_final = " ".join(icons)
    display_info = bonus_list + foul_list
    if display_info: icons_final += " | 🎖️" + ",".join(display_info)

    return {
        "Ticker": ticker, "Sector": sector_name, "Score": round(final_score, 1), 
        "RawPower": round(ej_val, 1), "Penalty": round(core_penalty + bias_penalty + foul_points, 1),
        "RS": round(rs_val, 1), "EJ": round(ej_val, 1), "SE": round(se_val, 1),
        "Power": round(buyvol.iloc[-1]/sellvol.iloc[-1] if sellvol.iloc[-1]>0 else 1, 1), 
        "Bias": round(bias, 1), "Status": f"[☠️ 落選: {death_reason}]" if is_dead else "[👑 趨勢]", 
        "Icons": icons_final, "IsDead": is_dead
    }
