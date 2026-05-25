import pandas as pd
import numpy as np
import yfinance as yf
import time

# 確保獲取 2 年數據，令 252 日線 (秘法引擎) 有足夠數據運作
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

def scan_dragon_logic(df, ticker, sector_name, market="HK", mode='NORMAL', force_return=False):
    # 確保有足夠數據計秘法
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
    # 🏎️ 乖孫專屬：秘法開車與墜機系統
    # =======================================================
    ma63 = c.rolling(63).mean(); ma126 = c.rolling(126).mean()
    ma189 = c.rolling(189).mean(); ma252 = c.rolling(252).mean()
    
    rs_secret = (2 * c / ma63.replace(0, np.nan)) + (c / ma126.replace(0, np.nan)) + (c / ma189.replace(0, np.nan)) + (c / ma252.replace(0, np.nan))
    power_secret = rs_secret - 5
    
    gt_05 = power_secret > 0.5
    new_entry_7d = (gt_05.rolling(7).sum() == 7) & (~gt_05.shift(7).fillna(True))
    power_inc = power_secret > power_secret.shift(1)
    inc_3_in_7 = power_inc.rolling(7).sum() >= 3
    secret_trigger = new_entry_7d & inc_3_in_7
    
    recent_high_pow = power_secret.rolling(30).max() >= 5
    drop_below_3 = (power_secret < 3).rolling(3).sum() == 3
    airplane_crash = recent_high_pow & drop_below_3

    # =======================================================
    # 🚀 TTM 2.0 嚴格版：擠壓釋放 + 第一爆發點 + 雙重熄火
    # =======================================================
    # 1. 計算 Squeeze 狀態 (布林 vs 肯特納)
    n_ttm = 20
    std_ttm = c.rolling(n_ttm).std()
    ma_ttm = c.rolling(n_ttm).mean()
    atr_ttm = (h - l).rolling(n_ttm).mean() 

    bb_upper = ma_ttm + (2.0 * std_ttm)
    bb_lower = ma_ttm - (2.0 * std_ttm)
    kc_upper = ma_ttm + (1.5 * atr_ttm)
    kc_lower = ma_ttm - (1.5 * atr_ttm)

    # 判斷是否擠壓中，及剛剛解除擠壓的瞬間
    is_squeezing = (bb_upper < kc_upper) & (bb_lower > kc_lower)
    squeeze_fired = (is_squeezing.shift(1) == True) & (is_squeezing == False)

    # 2. 計算動能 (Linear Regression 替代法)
    weights_20 = np.arange(1, 21) / 210.0
    var1_ttm = (h.rolling(20).max() + l.rolling(20).min()) / 2 + ma_ttm
    delta_ttm = c - (var1_ttm / 2)
    wma20_ttm = delta_ttm.rolling(20).apply(lambda x: np.dot(x, weights_20), raw=True)
    sma20_ttm = delta_ttm.rolling(20).mean()
    var2_ttm = 3 * wma20_ttm - 2 * sma20_ttm 

    # 3. MACD 判定
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    dif_up = (dif > dea) & (dif > dif.shift(1))

    # 4. 終極嚴格觸發：剛剛解除擠壓 (紅轉綠) OR 動能剛剛由負轉正 (第一藍柱)
    ttm_2_trigger = (squeeze_fired | ((var2_ttm > 0) & (var2_ttm.shift(1) <= 0))) & dif_up
    
    # 🛡️ 雙重保險熄火機制：就算喺 6 日記憶期內...
    # 只要 (1) 動能跌落負數，或者 (2) MACD 出現死叉 (DIF <= DEA)，火箭即刻沒收！
    ttm_2_active = (ttm_2_trigger.rolling(6).sum() > 0) & (var2_ttm > 0) & (dif > dea)

    # =======================================================
    # 🔄 IND1 回升(紅箭) 與 回落(綠箭) 系統
    # =======================================================
    llv55 = l.rolling(55).min()
    hhv55 = h.rolling(55).max()
    ema2 = c.ewm(span=2, adjust=False).mean()
    
    denom = (hhv55 - llv55).replace(0, np.nan)
    ind1_raw = (ema2 - llv55) / denom
    ind1 = ind1_raw.ewm(span=13, adjust=False).mean()
    
    up_arrow = (ind1 > 0.501) & (ind1.shift(1) <= 0.501) & (ind1 >= ind1.rolling(2).max())
    down_arrow = (ind1 < 0.499) & (ind1.shift(1) >= 0.499) & (ind1 <= ind1.rolling(2).min())
    
    last_up = -1; last_down = -1
    for i in range(1, 31):
        if i <= len(ind1):
            if last_up == -1 and up_arrow.iloc[-i]: last_up = i
            if last_down == -1 and down_arrow.iloc[-i]: last_down = i
            
    is_rebound_active = (last_up != -1) and (last_up <= 6)
    is_weak_active = (last_down != -1) and (last_down <= 30)
    if is_weak_active and (last_up != -1) and (last_up < last_down):
        is_weak_active = False # 破地獄抵消魔咒

    # =======================================================
    # 第二階段 (PRUDEN + WEIS)
    # =======================================================
    e50 = c.ewm(span=50, adjust=False).mean()
    e150 = c.ewm(span=150, adjust=False).mean()
    e200 = c.ewm(span=200, adjust=False).mean()
    pruden_score = (c > e50).astype(int) + (e50 > e150).astype(int) + (e150 > e200).astype(int) + (((c - e50)/e50*100) > 0).astype(int)
    pruden_break = (pruden_score == 4) & (pruden_score.shift(1) < 4)
    
    weis_dir = np.sign(c - c.shift(1))
    weis_vol = abs(v * weis_dir)
    buy_f = pd.Series(np.where(weis_dir > 0, weis_vol, 0), index=c.index).rolling(5).sum()
    sell_f = pd.Series(np.where(weis_dir < 0, weis_vol, 0), index=c.index).rolling(5).sum()
    net_thrust = buy_f - sell_f
    thrust_3_inc = (net_thrust > net_thrust.shift(1)) &
