import pandas as pd
import numpy as np
import yfinance as yf
import time

def smart_fetch(ticker_sym, period="2y"):
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

def scan_dragon_logic(df, ticker, sector_name, market="HK", mode='NORMAL', force_return=False, vcp_52w=False, vcp_ath=False):
    if len(df) < 252: return None 
    
    # =======================================================
    # 0. 基礎數據準備
    # =======================================================
    c = df['Close']; h = df['High']; l = df['Low']; o = df['Open']; v = df['Volume']
    curr_p = c.iloc[-1]; pct = c.pct_change().fillna(0); change = pct * 100
    ma20_v = v.rolling(20).mean(); ma60_v = v.rolling(60).mean(); ma50 = c.rolling(50).mean()
    v_std20 = v.rolling(20).std(); v_upper = ma20_v + (2.0 * v_std20)
    ema10 = c.ewm(span=10, adjust=False).mean()
    ema20 = c.ewm(span=20, adjust=False).mean()
    
    var1 = c - l; var2 = h - c; var3 = np.maximum(h - l, 0.001)
    buyvol = v * var1 / var3; sellvol = v * var2 / var3; netvol = buyvol - sellvol
    netma10 = netvol.rolling(10).mean()
    obv = (np.sign(pct) * v).cumsum()

    is_burst = (v > v_upper) & (v > ma60_v * 1.9) & (abs(change) > 2.0)
    is_magenta = is_burst & (c <= o)
    is_cyan = is_burst & (c > o)
    
    # =======================================================
    # 🏎️ 秘法 3.7 終極狀態機版 
    # =======================================================
    ma63 = c.rolling(63).mean(); ma126 = c.rolling(126).mean()
    ma189 = c.rolling(189).mean(); ma252 = c.rolling(252).mean()
    
    rs_secret = (2 * c / ma63.replace(0, np.nan)) + (c / ma126.replace(0, np.nan)) + (c / ma189.replace(0, np.nan)) + (c / ma252.replace(0, np.nan))
    power_secret = rs_secret - 5
    current_power = power_secret.iloc[-1]
    
    gt_05 = power_secret > 0.5
    block_id = (~gt_05).cumsum()
    power_inc = power_secret > power_secret.shift(1)
    is_base_car = (gt_05.rolling(7).sum() == 7) & (power_inc.rolling(7).sum() >= 3)
    
    whale_buy = (v > ma20_v) & (c > o) & (c > c.shift(1))
    whale_in_7d = whale_buy.rolling(7).sum() >= 2
    
    ignition_pulse = is_base_car & (power_secret.shift(7) <= 0.5) & whale_in_7d
    ignited_in_block = ignition_pulse.groupby(block_id).cummax().fillna(False)
    
    is_secret_bonus = ignited_in_block & (ignition_pulse.rolling(10).sum() > 0)
    is_secret_cruise = ignited_in_block & (~is_secret_bonus) & gt_05
    
    recent_high_pow = power_secret.rolling(30).max() >= 5
    drop_below_3 = (power_secret < 3).rolling(3).sum() == 3
    airplane_crash = recent_high_pow & drop_below_3

    # =======================================================
    # 🚀 TTM 2.0 雙重保險版
    # =======================================================
    n_ttm = 20
    ma_ttm = c.rolling(n_ttm).mean()
    std_ttm = c.rolling(n_ttm).std()
    atr_ttm = (h - l).rolling(n_ttm).mean()
    is_squeezing = (ma_ttm + 2*std_ttm < ma_ttm + 1.5*atr_ttm) & (ma_ttm - 2*std_ttm > ma_ttm - 1.5*atr_ttm)
    squeeze_fired = (is_squeezing.shift(1) == True) & (is_squeezing == False)

    weights_20 = np.arange(1, 21) / 210.0
    var1_ttm = (h.rolling(20).max() + l.rolling(20).min()) / 2 + ma_ttm
    delta_ttm = c - (var1_ttm / 2)
    var2_ttm = 3 * delta_ttm.rolling(20).apply(lambda x: np.dot(x, weights_20), raw=True) - 2 * delta_ttm.rolling(20).mean()

    ema12 = c.ewm(span=12, adjust=False).mean(); ema26 = c.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26; dea = dif.ewm(span=9, adjust=False).mean()
    dif_up = (dif > dea) & (dif > dif.shift(1))

    ttm_2_trigger = (squeeze_fired | ((var2_ttm > 0) & (var2_ttm.shift(1) <= 0))) & dif_up
    ttm_2_active = (ttm_2_trigger.rolling(6).sum() > 0) & (var2_ttm > 0) & (dif > dea)

    # =======================================================
    # 🔄 IND1 回升/回落
    # =======================================================
    llv55 = l.rolling(55).min(); hhv55 = h.rolling(55).max()
    denom = (hhv55 - llv55).replace(0, np.nan)
    ema2 = c.ewm(span=2, adjust=False).mean()
    ind1_raw = (ema2 - llv55) / denom
    ind1 = ind1_raw.ewm(span=13, adjust=False).mean()
    
    up_arrow = (ind1 > 0.501) & (ind1.shift(1) <= 0.501) & (ind1 >= ind1.rolling(2).max())
    down_arrow = (ind1 < 0.499) & (ind1.shift(1) >= 0.499) & (ind1 <= ind1.rolling(2).min())
    
    last_up_idx = -1; last_down_idx = -1
    for i in range(1, 31):
        idx = -i
        if len(ind1) >= i:
            if last_up_idx == -1 and up_arrow.iloc[idx]: last_up_idx = i
            if last_down_idx == -1 and down_arrow.iloc[idx]: last_down_idx = i
                
    is_rebound_active = (last_up_idx != -1) and (last_up_idx <= 6)
    is_weak_active = (last_down_idx != -1) and (last_down_idx <= 30)
    if is_weak_active and (last_up_idx != -1) and (last_up_idx < last_down_idx): is_weak_active = False

    # =======================================================
    # 第二階段 (PRUDEN + WEIS)
    # =======================================================
    e50 = c.ewm(span=50, adjust=False).mean(); e150 = c.ewm(span=150, adjust=False).mean(); e200 = c.ewm(span=200, adjust=False).mean()
    pruden_score = (c > e50).astype(int) + (e50 > e150).astype(int) + (e150 > e200).astype(int) + (((c - e50)/e50*100) > 0).astype(int)
    pruden_break = (pruden_score == 4) & (pruden_score.shift(1) < 4)
    weis_dir = np.sign(c - c.shift(1)); weis_vol = abs(v * weis_dir)
    buy_f = pd.Series(np.where(weis_dir > 0, weis_vol, 0), index=c.index).rolling(5).sum()
    sell_f = pd.Series(np.where(weis_dir < 0, weis_vol, 0), index=c.index).rolling(5).sum()
    net_thrust = buy_f - sell_f
    thrust_3_inc = (net_thrust > net_thrust.shift(1)) & (net_thrust.shift(1) > net_thrust.shift(2)) & (net_thrust.shift(2) > (0.3 * 1e6))
    stage_2_signal = thrust_3_inc & pruden_break.rolling(14).max().fillna(0).astype(bool)

    # =======================================================
    # 🚨 第一層：7大禁示 + 死線判定
    # =======================================================
    foul_points = 0; foul_list = []
    if is_magenta.tail(20).any(): foul_points += 10; foul_list.append("犯1(-10)")
    if ((change > 0) & (netvol < 0)).tail(20).any(): foul_points += 10; foul_list.append("犯2(-10)")
    if ((v > ma60_v * 2.0) & (change < 2.0) & (change >= 0)).tail(20).any(): foul_points += 10; foul_list.append("犯3(-10)")
    if (netvol.rolling(5).sum() < 0).tail(20).any(): foul_points += 10; foul_list.append("犯4(-10)")
    if ((change.shift(1) > 5.0) & (v < v.shift(1) * 0.5)).tail(20).any(): foul_points += 10; foul_list.append("犯5(-10)")
    if ((((c - ma50)/ma50)*100 > 15) & (v > ma60_v * 3.0)).tail(20).any(): foul_points += 10; foul_list.append("犯6(-10)")
    if ((c >= c.shift(10)) & (obv < obv.shift(10))).tail(20).any(): foul_points += 10; foul_list.append("犯7(-10)")

    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netvol.tail(20).sum() / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(20).sum() * 100)
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    
    obv_curr = obv.iloc[-1] - obv.iloc[-21] if len(obv)>20 else 0
    obv_prev = obv.iloc[-21] - obv.iloc[-41] if len(obv)>40 else 1
    obv_pct = (obv_curr - obv_prev) / max(abs(obv_prev), 1) * 100
    p_trend = c.iloc[-1] - c.iloc[-21]
    if p_trend >= 0:
        if obv_curr > 0: obv_state = 1 if obv_pct > 50 else 2
        else: obv_state = 5 if obv_pct < -50 else 6
    else:
        if obv_curr < 0: obv_state = 3 if obv_pct < -50 else 4
        else: obv_state = 7 if obv_pct > 50 else 8

    is_dead = False; death_reason = ""
    if curr_p <= ma50.iloc[-1]: is_dead = True; death_reason = "跌穿50天線"
    elif is_magenta.iloc[-1]: is_dead = True; death_reason = "今日粉紅爆缸"
    elif not (rs_val > 60 and ej_val > 85 and se_val > 75 and netvol.tail(20).sum() > 0): 
        is_dead = True; death_reason = "SE或錢流不達標"
    elif obv_state not in [1, 2, 7, 8]: is_dead = True; death_reason = f"OBV狀態({obv_state})"
    
    high_52w = h.tail(252).max()
    pct_from_52w_high = ((high_52w - curr_p) / high_52w) * 100
    if not is_dead and vcp_52w and (pct_from_52w_high > 25.0):
        is_dead = True; death_reason = f"距離52週高位太遠({pct_from_52w_high:.1f}%)"
    if not is_dead and vcp_ath and (curr_p < h.max() * 0.98):
        is_dead = True; death_reason = "未達歷史新高(ATH)極致區"
        
    if is_dead and not force_return: return None

    # =======================================================
    # 🏆 核心計分系統
    # =======================================================
    bonus_list = []; core_p = 0; bias_p = 0
    is_vcp_trend = False; is_vcp_burst_7d = False
    
    if mode == 'VCP':
        score = 0.0 
        ret_40d = (curr_p - c.iloc[-40]) / c.iloc[-40] if len(c) > 40 else 0
        if curr_p > ema10.iloc[-1] > ema20.iloc[-1] > ma50.iloc[-1]:
            score += 50; bonus_list.append("VCP趨勢👑(+50)"); is_vcp_trend = True
        power_series = buyvol / np.where(sellvol > 0, sellvol, 0.1)
        vcp_burst_cond = (v > ma20_v * 1.5) & (power_series > 1.2) & (c > o)
        if vcp_burst_cond.tail(7).any():
            score += 30; bonus_list.append("VCP爆量⚡(+30)"); is_vcp_burst_7d = True 
        if ret_40d > 0.15:
            score += 20; bonus_list.append("VCP強勢🔥(+20)")
    else:
        score = 100.0 

    if is_secret_bonus.iloc[-1]: score += 20; bonus_list.append("秘法起步🏎️(+20)")
    if airplane_crash.iloc[-1]: core_p += 50; foul_list.append("高位墜機🛬(-50)")
    if is_rebound_active: score += 10; bonus_list.append("回升(+10)")
    if is_weak_active: core_p += 60; foul_list.append("弱勢(-60)")
    if ttm_2_active.iloc[-1]: score += 15; bonus_list.append("TTM🚀(+15)")

    if stage_2_signal.tail(4).any(): score += 30; bonus_list.append("第二階段 ♂(+30)")
    if se_val >= 90.0: score += 5; bonus_list.append("動能(+5)")
    if (buyvol.iloc[-1] / (sellvol.iloc[-1] if sellvol.iloc[-1]>0 else 0.1)) > 1.5: score += 5; bonus_list.append("兵力(+5)")
    if obv_state in [1, 7]: score += 10; bonus_list.append("OBV(+10)")
    total_v60 = max(v.tail(60).sum(), 1)
    if netvol.tail(60).sum() > (total_v60 * 0.12): score += 5; bonus_list.append("穩定流入(+5)") 
    if rs_val >= 92.0: score += 5; bonus_list.append("RS(+5)")
    if curr_p >= h.tail(60).max(): score += 5; bonus_list.append("破頂(+5)")

    limit = 10 if market == "HK" else 5
    if bias > limit:
        core_p += 25; bias_p = 50 + (bias - limit) * 10
        if mode == 'VCP': score -= 40 
    elif mode == 'VCP' and bias > 8: score -= 40
    
    if mode != 'VCP': 
        if netvol.tail(60).sum() < 0: core_p += 30
        if v.iloc[-1] > ma60_v.iloc[-1] * 2.5: core_p += 20
        if (var2.iloc[-1] / var3.iloc[-1]) > 0.5: core_p += 15

    # =======================================================
    # 🔮 隱藏公仔裝盤 
    # =======================================================
    hidden_icons = []
    if is_squeezing.iloc[-1]: hidden_icons.append("🤐(蓄勢)")
    if is_secret_cruise.iloc[-1]: hidden_icons.append("🏎️")
        
    cond_cyan = is_cyan & (netvol > netvol.rolling(10).mean())
    cond_narrow = (netma10 > netma10.shift(1)) & ((var3 / l * 100) < 1.5)
    cond_shield = (change < 0) & (netvol > 0)
    cond_pit = (change < -1) & is_magenta
    cond_vcp = (netma10 > 0) & (netma10.shift(1) < 0) & (v < ma20_v)
    cond_lightning = (v > v_upper) & (buyvol > sellvol * 2)
    whale_days = sum((v.tail(10) > ma60_v.tail(10) * 1.5) & (netvol.tail(10) > 0))

    if cond_cyan.tail(4).any(): hidden_icons.append("💰🔥")
    if cond_narrow.tail(4).any(): hidden_icons.append("💰🤫")
    if cond_shield.tail(4).any(): hidden_icons.append("💰🛡️")
    if cond_vcp.tail(4).any(): hidden_icons.append("🧧")
    if cond_lightning.tail(4).any(): hidden_icons.append("⚡")
    if cond_pit.tail(20).any(): hidden_icons.append("💎/😱")
    if whale_days > 0: hidden_icons.append(f"🐋({whale_days}/10)")
    if netvol.tail(20).sum() > 0 and "🧧" not in hidden_icons: hidden_icons.append("🧧")

    # =======================================================
    # 🪃 事後動態過濾：N 字突破 (捕捉第1日及第2日)
    # =======================================================
    # 取過去一週半的最高點作為「阻力前頂」(排除今昨2日，給予洗盤空間)
    lookback = 8 
    a_point = h.shift(2).rolling(lookback).max().iloc[-1]
    a_point_yest = h.shift(3).rolling(lookback).max().iloc[-1]
    
    # Day 1: 今日剛突破
    is_breakout_today = (c.iloc[-1] > a_point) and (c.iloc[-2] <= a_point)
    # Day 2: 昨日剛突破 (供考慮即日高追)
    is_breakout_yest = (c.iloc[-2] > a_point_yest) and (c.iloc[-3] <= a_point_yest)
    
    if is_breakout_today or is_breakout_yest:
        score += 20
        bonus_list.append("N字突破🪃(+20)")
        hidden_icons.append("🪃")

    # =======================================================
    # 結算與回傳
    # =======================================================
    status_prefix = ""
    if mode == 'VCP':
        if is_vcp_trend and cond_narrow.tail(4).any() and cond_vcp.tail(4).any() and ((whale_days > 0) or cond_lightning.tail(4).any()) and is_vcp_burst_7d:
            status_prefix = "🐲 [真龍 VCP 股出現！請注意！] "
            score += 50 

    final_score = score - core_p - bias_p - foul_points
    icons_final = " ".join(hidden_icons)
    display_info = bonus_list + foul_list
    if display_info: icons_final += " | 🎖️" + ",".join(display_info)
    base_status = f"[☠️ 落選: {death_reason}]" if is_dead else ("[⚠️ 末段]" if bias > limit else "[👑 趨勢]")

    return {
        "Ticker": ticker, "Sector": sector_name, "Score": round(final_score, 1), 
        "RawPower": round(ej_val, 1), "Penalty": round(core_p + bias_p + foul_points, 1),
        "RS": round(rs_val, 1),
        "EJ": round(current_power, 3), 
        "SE": round(se_val, 1),
        "Flow": f"{netvol.tail(20).sum()/1e6:.1f}M", "Conc": f"{conc:.1f}%", "OBV": f"狀態 {obv_state}",
        "Power": round(buyvol.iloc[-1]/sellvol.iloc[-1] if sellvol.iloc[-1]>0 else 1, 1), 
        "Bias": round(bias, 1), "EMA10": round(ema10.iloc[-1], 2),
        "Status": status_prefix + base_status, 
        "Icons": icons_final, "IsDead": is_dead
    }
