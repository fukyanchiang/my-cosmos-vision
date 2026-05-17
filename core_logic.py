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

def scan_dragon_logic(df, ticker, sector_name, market="HK", mode='NORMAL', force_return=False):
    if len(df) < 65: return None
    
    # =======================================================
    # 0. 基礎數據準備
    # =======================================================
    c = df['Close']; h = df['High']; l = df['Low']; o = df['Open']; v = df['Volume']
    curr_p = c.iloc[-1]; pct = c.pct_change().fillna(0); change = pct * 100
    ma20_v = v.rolling(20).mean(); ma60_v = v.rolling(60).mean(); ma50 = c.rolling(50).mean()
    v_std20 = v.rolling(20).std(); v_upper = ma20_v + (2.0 * v_std20)
    ema10 = c.ewm(span=10, adjust=False).mean()
    ema20 = c.ewm(span=20, adjust=False).mean() # 👵 爺爺加載：預留給 VCP 多頭排列使用
    
    # 計算買賣兵力 (VAR1-3)
    var1 = c - l; var2 = h - c; var3 = np.maximum(h - l, 0.001)
    buyvol = v * var1 / var3; sellvol = v * var2 / var3; netvol = buyvol - sellvol
    netma10 = netvol.rolling(10).mean() # 氣脈黑線
    obv = (np.sign(pct) * v).cumsum()

    # 爆發雷達 (粉紅柱/粉藍柱判定)
    is_burst = (v > v_upper) & (v > ma60_v * 1.9) & (abs(change) > 2.0)
    is_magenta = is_burst & (c <= o)
    is_cyan = is_burst & (c > o) # 粉藍柱判定
    
    # =======================================================
    # 🌟 第二階段雙劍合璧 (PRUDEN + WEIS)
    # =======================================================
    # PRUDEN 趨勢門神 3.1
    e50 = c.ewm(span=50, adjust=False).mean()
    e150 = c.ewm(span=150, adjust=False).mean()
    e200 = c.ewm(span=200, adjust=False).mean()
    pruden_score = (c > e50).astype(int) + (e50 > e150).astype(int) + (e50 > e200).astype(int) + (((c - e50)/e50*100) > 0).astype(int)
    pruden_break = (pruden_score == 4) & (pruden_score.shift(1) < 4) # 剛剛升至100分
    
    # WEIS 量能波浪 (淨推力)
    weis_dir = np.sign(c - c.shift(1))
    weis_vol = abs(v * weis_dir)
    buy_f = pd.Series(np.where(weis_dir > 0, weis_vol, 0), index=c.index).rolling(5).sum()
    sell_f = pd.Series(np.where(weis_dir < 0, weis_vol, 0), index=c.index).rolling(5).sum()
    net_thrust = buy_f - sell_f

    # 信號條件 1: WEIS 淨推力連續三天遞增，且第一天需大於 0.3M (即 300,000 股)
    thrust_3_inc = (net_thrust > net_thrust.shift(1)) & (net_thrust.shift(1) > net_thrust.shift(2)) & (net_thrust.shift(2) > (0.3 * 1e6))
    
    # 信號條件 2: 過去 14 天內，PRUDEN 曾經突破過
    pruden_recent_14 = pruden_break.rolling(14).max().fillna(0).astype(bool)
    
    # 結合：當日正式形成「第二階段」信號
    stage_2_signal = thrust_3_inc & pruden_recent_14

    # =======================================================
    # 🚨 第一層：7大歷史禁示 (20日追蹤 - 歷史罰分) —— 100% 原汁原味保留！
    # =======================================================
    foul_points = 0; foul_list = []
    lookback = 20
    if is_magenta.tail(lookback).any(): foul_points += 10; foul_list.append("犯1(-10)")
    if ((change > 0) & (netvol < 0)).tail(lookback).any(): foul_points += 10; foul_list.append("犯2(-10)")
    if ((v > ma60_v * 2.0) & (change < 2.0) & (change >= 0)).tail(lookback).any(): foul_points += 10; foul_list.append("犯3(-10)")
    if (netvol.rolling(5).sum() < 0).tail(lookback).any(): foul_points += 10; foul_list.append("犯4(-10)")
    if ((change.shift(1) > 5.0) & (v < v.shift(1) * 0.5)).tail(lookback).any(): foul_points += 10; foul_list.append("犯5(-10)")
    if ((((c - ma50)/ma50)*100 > 15) & (v > ma60_v * 3.0)).tail(lookback).any(): foul_points += 10; foul_list.append("犯6(-10)")
    if ((c >= c.shift(10)) & (obv < obv.shift(10))).tail(lookback).any(): foul_points += 10; foul_list.append("犯7(-10)")

    # =======================================================
    # 🐉 第二層：龍魂硬指標 (即時死刑判定) —— 100% 原汁原味保留！
    # =======================================================
    rs_val = 80 + (curr_p / ma50.iloc[-1] * 10)
    ej_val = 85 + (netvol.tail(20).sum() / max(ma20_v.iloc[-1]*20, 1) * 5)
    se_val = 75 + (pct.tail(20).sum() * 100) # 20日累積動能
    conc = (abs(netvol.tail(20)).max() / max(abs(netvol.tail(20)).sum(), 1)) * 100
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    ret_40d = (curr_p - c.iloc[-40]) / c.iloc[-40] if len(c) > 40 else 0 # 👴 爺爺加載：提早計好 40 日相對強度
    
    # OBV 狀態 (👿 地獄模式: 50% 門檻)
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

    # 🛑 死亡審判
    is_dead = False; death_reason = ""
    if curr_p <= ma50.iloc[-1]: is_dead = True; death_reason = "跌穿50天線"
    elif is_magenta.iloc[-1]: is_dead = True; death_reason = "今日粉紅爆缸"
    elif not (rs_val > 60 and ej_val > 85 and se_val > 75 and netvol.tail(20).sum() > 0): 
        is_dead = True; death_reason = "SE或錢流不達標"
    elif obv_state not in [1, 2, 7, 8]: is_dead = True; death_reason = f"OBV狀態({obv_state})"
    
    if is_dead and not force_return: return None

    # =======================================================
    # 🏆 第三及四層：權重計分與地獄扣分 (根據 mode 自動變身！)
    # =======================================================
    score = 100.0; bonus_list = []
    core_p = 0
    bias_p = 0
    
    # 🔄 模式開關分流
    if mode == 'VCP':
        score = 0.0 # 🚀 VCP 高勝率獵龍模式：採用全新勝率排位計分法
        
        # 1. 趨勢維度: 多頭排列 (40日中線波段核心)
        if curr_p > ema10.iloc[-1] and ema10.iloc[-1] > ema20.iloc[-1] and ema20.iloc[-1] > ma50.iloc[-1]:
            score += 50
            bonus_list.append("VCP趨勢👑(+50)")
            
        # 2. 動能維度: 量能爆發 (1-10日短線爆發核心)
        power_val = buyvol.iloc[-1]/sellvol.iloc[-1] if sellvol.iloc[-1]>0 else 1.0
        if v.iloc[-1] > (ma20_v.iloc[-1] * 1.5) and power_val > 1.2 and curr_p > o.iloc[-1]:
            score += 30
            bonus_list.append("VCP爆量⚡(+30)")
            
        # 3. 強度維度: 40日相對強度 (RS 龍頭確認)
        if ret_40d > 0.15:
            score += 20
            bonus_list.append("VCP強勢🔥(+20)")
            
        # 4. 防禦項與 Bias 階梯扣分 (防追高)
        core_p = 30 if netvol.tail(60).sum() < 0 else 0
        limit = 10 if market == "HK" else 5
        if bias > limit:
            score -= 40
            core_p += 25
            bias_p = 50 + (bias - limit) * 10
            
        final_score = score - core_p - bias_p - foul_points
        
        # 🚨 門神加強：只要中咗 7 大歷史禁令任何一條 (有扣分)，再重罰 100 分！確保絕對不能排在最頂！
        if foul_points > 0:
            final_score -= 100
            
    else:
        # 🤖 NORMAL 模式：100% 完全保留你原本所有的計分與扣分邏輯
        # 🎯 終極神技加分：第二階段 ♂(+30) 
        if stage_2_signal.tail(4).any():
            score += 30; bonus_list.append("第二階段 ♂(+30)")
        
        if se_val >= 90.0: score += 5; bonus_list.append("動能(+5)")
        if (buyvol.iloc[-1] / (sellvol.iloc[-1] if sellvol.iloc[-1]>0 else 0.1)) > 1.5: score += 5; bonus_list.append("兵力(+5)")
        if obv_state in [1, 7]: score += 10; bonus_list.append("OBV(+10)")
        
        total_v60 = max(v.tail(60).sum(), 1)
        if netvol.tail(60).sum() > (total_v60 * 0.12): score += 5; bonus_list.append("穩定流入(+5)") 
        if rs_val >= 92.0: score += 5; bonus_list.append("RS(+5)")
        if curr_p >= h.tail(60).max(): score += 5; bonus_list.append("破頂(+5)")

        # 🚨 核心扣分與 Bias 階梯罰分
        core_p = 30 if netvol.tail(60).sum() < 0 else 0
        limit = 10 if market == "HK" else 5
        if bias > limit: core_p += 25
        if v.iloc[-1] > ma60_v.iloc[-1] * 2.5: core_p += 20
        if (var2.iloc[-1] / var3.iloc[-1]) > 0.5: core_p += 15
        bias_p = 50 + (bias - limit) * 10 if bias > limit else 0
        final_score = score - core_p - bias_p - foul_points

    # =======================================================
    # 🔮 第五層：6 大隱藏公仔 + 鯨魚 —— 100% 原封不動，完美重現！
    # =======================================================
    hidden_icons = []
    
    cond_cyan = is_cyan & (netvol > netvol.rolling(10).mean())
    cond_narrow = (netma10 > netma10.shift(1)) & ((var3 / l * 100) < 1.5)
    cond_shield = (change < 0) & (netvol > 0)
    cond_pit = (change < -1) & is_magenta
    cond_vcp = (netma10 > 0) & (netma10.shift(1) < 0) & (v < ma20_v)
    cond_lightning = (v > v_upper) & (buyvol > sellvol * 2)

    # 執行時間窗口判定
    if cond_cyan.tail(4).any(): hidden_icons.append("💰🔥")
    if cond_narrow.tail(4).any(): hidden_icons.append("💰🤫")
    if cond_shield.tail(4).any(): hidden_icons.append("💰🛡️")
    if cond_vcp.tail(4).any(): hidden_icons.append("🧧")
    if cond_lightning.tail(4).any(): hidden_icons.append("⚡")
    if cond_pit.tail(20).any(): hidden_icons.append("💎/😱")
    
    # 鯨魚現身
    whale_days = sum((v.tail(10) > ma60_v.tail(10) * 1.5) & (netvol.tail(10) > 0))
    if whale_days > 0: hidden_icons.append(f"🐋({whale_days}/10)")
    
    # 基本資金流紅包
    if netvol.tail(20).sum() > 0 and "🧧" not in hidden_icons: hidden_icons.append("🧧")

    # 🎀 重新將隱藏公仔同勳章合併
    icons_final = " ".join(hidden_icons)
    display_info = bonus_list + foul_list
    if display_info: icons_final += " | 🎖️" + ",".join(display_info)

    return {
        "Ticker": ticker, "Sector": sector_name, "Score": round(final_score, 1), 
        "RawPower": round(ej_val, 1), "Penalty": round(core_p + bias_p + foul_points, 1),
        "RS": round(rs_val, 1), "EJ": round(ej_val, 1), "SE": round(se_val, 1),
        "Flow": f"{netvol.tail(20).sum()/1e6:.1f}M", "Conc": f"{conc:.1f}%", "OBV": f"狀態 {obv_state}",
        "Power": round(buyvol.iloc[-1]/sellvol.iloc[-1] if sellvol.iloc[-1]>0 else 1, 1), 
        "Bias": round(bias, 1), "EMA10": round(ema10.iloc[-1], 2),
        "Status": f"[☠️ 落選: {death_reason}]" if is_dead else ("[⚠️ 末段]" if bias > limit else "[👑 趨勢]"), 
        "Icons": icons_final, "IsDead": is_dead
    }
