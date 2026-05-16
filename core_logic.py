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
    
    # 基礎數據
    c = df['Close']; h = df['High']; l = df['Low']; o = df['Open']; v = df['Volume']
    curr_p = c.iloc[-1]; pct = c.pct_change().fillna(0)
    ma20_v = v.rolling(20).mean(); ma60_v = v.rolling(60).mean(); ma50 = c.rolling(50).mean()
    v_std20 = v.rolling(20).std(); v_upper = ma20_v + (2.0 * v_std20)
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    
    # --- 100% 對應你嘅 3 組指標 Code 邏輯 ---
    var1 = c - l; var2 = h - c; var3 = np.maximum(h - l, 0.001)
    buyvol = v * var1 / var3; sellvol = v * var2 / var3; netvol = buyvol - sellvol
    change = (c - c.shift(1)) / c.shift(1) * 100
    abs_change = abs(change)
    obv = (np.sign(change) * v).fillna(0).cumsum()

    # 爆發雷達判定 (粉紅柱/粉藍柱)
    is_burst = (v > v_upper) & (v > ma60_v * 1.9) & (abs_change > 2.0)
    is_magenta = is_burst & (c <= o) # 粉紅色：爆發但收陰
    is_cyan = is_burst & (c > o)    # 粉藍色：爆發且收陽

    # =======================================================
    # 🚨 第一層：7大禁示 (20日追溯 Fouls)
    # =======================================================
    foul_points = 0
    foul_list = []
    lookback = 20
    
    # 1. 直接派貨 (粉紅柱：成交大 + 價大跌/收陰)
    if is_magenta.tail(lookback).any():
        foul_points += 10; foul_list.append("犯 1.-10")
    
    # 2. 托住走貨 (價升 + 錢流 EJ/Flow 轉負)
    stall_exit = (change > 0) & (netvol < 0)
    if stall_exit.tail(lookback).any():
        foul_points += 10; foul_list.append("犯 2.-10")
        
    # 3. 放量滯漲 (天量 + 升幅 < 2%)
    stagnant = (v > ma60_v * 2.0) & (change < 2.0) & (change >= 0)
    if stagnant.tail(lookback).any():
        foul_points += 10; foul_list.append("犯 3.-10")
        
    # 4. 板塊撤退 (個股代碼簡化版：若連續5日錢流為負)
    retreat = netvol.rolling(5).sum() < 0
    if retreat.tail(lookback).any():
        foul_points += 10; foul_list.append("犯 4.-10")
        
    # 5. 錢流斷層 (暴升 > 5% 後，次日成交縮 > 50%)
    gap = (change.shift(1) > 5.0) & (v < v.shift(1) * 0.5)
    if gap.tail(lookback).any():
        foul_points += 10; foul_list.append("犯 5.-10")
        
    # 6. 末段癲狗 (Bias > 15% + 爆天量)
    crazy_dog = (bias > 15.0) & (v > ma60_v * 3.0)
    if crazy_dog: # 呢項係即時或近期
        foul_points += 10; foul_list.append("犯 6.-10")
        
    # 7. OBV 詐騙 (價穩 10日, 但 OBV 持續向下)
    obv_scam = (c >= c.shift(10)) & (obv < obv.shift(10))
    if obv_scam.tail(lookback).any():
        foul_points += 10; foul_list.append("犯 7.-10")

    # =======================================================
    # 🏆 第四層：權重計分與扣分
    # =======================================================
    score = 100.0
    bonus_list = []
    
    # A. 狀態紅利
    ej_val = 85 + (netvol.tail(20).sum() / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(5).sum() * 100)
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    display_power = buyvol.iloc[-1] / sellvol.iloc[-1] if sellvol.iloc[-1] > 0 else 1.0

    if se_val > 75: score += 5; bonus_list.append("SE(+5)")
    if display_power > 1.5: score += 5; bonus_list.append("兵力(+5)")
    if netvol.tail(20).sum() > 0: score += 10; bonus_list.append("OBV(+10)")
    if netvol.tail(60).sum() > 0: score += 5; bonus_list.append("穩定流入(+5)")
    if rs_val >= 92.0: score += 5; bonus_list.append("RS(+5)")
    if curr_p >= h.tail(60).max(): score += 5; bonus_list.append("破頂(+5)")

    # B. 🚨 4項核心品質扣分 (今日判定)
    core_penalty = 0
    if netvol.tail(60).sum() < 0: core_penalty += 30 # 萬人坑
    
    limit = 10 if market == "HK" else 5
    if bias > limit: core_penalty += 25             # 位置虛脫
    
    if v.iloc[-1] > ma60_v.iloc[-1] * 2.5: core_penalty += 20 # 爆缸天量
    
    shadow = (h.iloc[-1] - max(c.iloc[-1], o.iloc[-1])) / var3.iloc[-1]
    if shadow > 0.5: core_penalty += 15             # 影線派貨

    # C. 🚨 安全制動 (Bias 階梯罰分 - 爺爺心法)
    bias_penalty = 0
    if bias > limit:
        bias_penalty = 50 + (bias - limit) * 10

    # D. 總結計分
    final_score = score - core_penalty - bias_penalty - foul_points

    # =======================================================
    # 🔮 徽章合併與顯示 (列出犯規項)
    # =======================================================
    icons = []
    if netvol.tail(20).sum() > 0: icons.append("🧧")
    stars = sum((v.tail(10) > ma60_v.tail(10) * 1.5))
    if stars > 0: icons.append(f"🐋({stars}/10)")
    
    icons_final = " ".join(icons)
    # 合併獎勵與犯規信息
    display_info = bonus_list + foul_list
    if display_info:
        icons_final += " | 🎖️" + ",".join(display_info)

    # 死亡審判 (即時剔除逻辑)
    is_dead = curr_p <= ma50.iloc[-1] or is_magenta.iloc[-1]
    if is_dead and not force_return: return None

    return {
        "Ticker": ticker, "Sector": sector_name, "Score": round(final_score, 1), 
        "RawPower": round(ej_val, 1), "Penalty": round(core_penalty + bias_penalty + foul_points, 1),
        "RS": round(rs_val, 1), "EJ": round(ej_val, 1), "SE": round(se_val, 1),
        "Power": round(display_power, 1), "Bias": round(bias, 1), 
        "Status": "[⚠️ 末段]" if bias > 10 else "[👑 趨勢]", 
        "Icons": icons_final, "IsDead": is_dead
    }
