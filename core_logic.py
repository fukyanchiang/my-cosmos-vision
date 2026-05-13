import pandas as pd
import numpy as np
import yfinance as yf
import time

# ==========================================
# 🛠️ 基礎工具函數
# ==========================================

def smart_fetch(ticker_sym, period="1y"):
    """智能抓取數據，包含重試機制"""
    try:
        time.sleep(0.3) 
        ticker = yf.Ticker(ticker_sym)
        data = ticker.history(period=period, auto_adjust=True)
        if data.empty:
            time.sleep(1.0) 
            data = ticker.history(period=period, auto_adjust=True)
        return data.dropna(subset=['Close', 'Volume', 'Open', 'High', 'Low'])
    except:
        return pd.DataFrame()

def check_stop_loss(df):
    """檢查今日是否跌穿 10-EMA 止損線"""
    if df.empty or len(df) < 10: return False
    ema10 = df['Close'].ewm(span=10, adjust=False).mean()
    return df['Close'].iloc[-1] < ema10.iloc[-1]

# ==========================================
# 🐲 龍魂 5.0 核心引擎 (明暗雙線版)
# ==========================================

def scan_dragon_logic(df, ticker, sector, market_mode):
    """
    龍魂 5.0 五層全邏輯引擎 (明暗雙線策略)
    1. 七大禁示 (60日死刑)
    2. 8大硬指標 (全中准入)
    3. 暗線 (Raw Power 無上限) + 明線 (135分封頂)
    4. 家法扣分 (Bias階梯/萬人坑)
    5. Status與公仔標籤
    """
    if df.empty or len(df) < 65: return None
    
    # --- 1. 基礎神級指標計算 (三組指標為魂) ---
    c = df['Close']
    o = df['Open']
    h = df['High']
    l = df['Low']
    v = df['Volume']
    
    # 第一組：買賣力道 (NETVOL)
    denom = np.maximum(h - l, 0.001)
    buyvol = v * (c - l) / denom
    sellvol = v * (h - c) / denom
    netvol = buyvol - sellvol
    netma = netvol.rolling(10, min_periods=1).mean()
    
    # 第二組：能量雷達 (Burst)
    v_ma20 = v.rolling(20).mean()
    v_std20 = v.rolling(20).std()
    v_upper = v_ma20 + (2.0 * v_std20)
    v_ma60 = v.rolling(60).mean()
    chg = c.pct_change() * 100
    
    # 雷達判定
    is_burst = (v > v_upper) & (v > v_ma60 * 1.9) & (abs(chg) > 2.0)
    is_cyan = is_burst & (c > o)
    is_magenta = is_burst & (c <= o)
    
    # 第三組：Bias 與 均線
    ma20 = c.rolling(20).mean()
    bias = ((c / ma20) - 1) * 100
    ma50 = c.rolling(50).mean()
    ma50_bias = ((c / ma50) - 1) * 100
    
    # OBV 與 資金流
    obv = (np.sign(c.diff()) * v).fillna(0).cumsum()
    tp = (h + l + c) / 3
    flow_daily = tp * v * np.where(c > c.shift(1).fillna(c), 1, -1)
    net_flow_20 = flow_daily.tail(20).sum()
    
    # RS 計算 (這裡用簡化版 RS 運算)
    rs_val = 50 + (chg.tail(63).sum()) 
    rs_val = max(0, min(99, rs_val)) # RS 限制在 0-99

    # ---------------------------------------------------------
    # 🛡️ 第一層：七大禁示 (60個交易日一票否決)
    # ---------------------------------------------------------
    lookback = 60
    if (is_magenta.tail(lookback) & (chg.tail(lookback) < 0)).any(): return None      # 1. 直接派貨
    if ((chg.tail(lookback) > 0) & (netvol.tail(lookback) < 0)).any(): return None   # 2. 托住走貨
    if (is_cyan.tail(lookback) & (chg.tail(lookback) < 2.0)).any(): return None      # 3. 放量滯漲
    
    # 5. 錢流斷層
    for i in range(1, min(lookback, len(is_burst)-1)):
        if is_burst.iloc[-(i+1)] and v.iloc[-i] < (v.iloc[-(i+1)] * 0.5): return None
        
    if ((bias.tail(lookback) > 15) & is_burst.tail(lookback)).any(): return None    # 6. 末段癲狗
    if ((abs(chg.tail(5)) < 0.5) & (netma.tail(5).diff() < 0)).any(): return None    # 7. OBV 詐騙

    # ---------------------------------------------------------
    # 🐲 第二層：龍魂核心 (8大硬指標生存海選)
    # ---------------------------------------------------------
    if rs_val < 60: return None
    
    ej_score = (v.tail(21).mean() / max(v_ma60.iloc[-1], 1)) * 100
    if ej_score < 85: return None
    
    # SE 短期能量 (無上限原始數值)
    se_score = 50 + ((c.iloc[-1] / c.iloc[-5]) - 1) * 1200
    if se_score < 75: return None
    
    # OBV 狀態 1/7
    obv_20 = obv.iloc[-1] - obv.iloc[-21]
    price_20 = c.iloc[-1] - c.iloc[-21]
    if price_20 >= 0 and obv_20 > 0: obv_state = 1
    elif price_20 < 0 and obv_20 > 0: obv_state = 7
    else: return None
    
    # 集中度
    conc = (abs(flow_daily.tail(20)).max() / max(abs(flow_daily.tail(20)).sum(), 1)) * 100
    if conc > 70: return None
    
    # 買盤兵力 (Power)
    power = buyvol.iloc[-1] / max(sellvol.iloc[-1], 1)
    if power < 1.0: return None
    
    if net_flow_20 <= 0: return None  # Net Flow > 0
    if c.iloc[-1] <= ma50.iloc[-1]: return None # Price > MA50

    # ---------------------------------------------------------
    # 🔥 第三層 (暗線)：原始戰鬥力 (Raw Power - 無上限)
    # ---------------------------------------------------------
    # 完美還原舊制瘋狂分數，等你可以睇到隻股有幾「癲」
    raw_power = (rs_val * 0.6) + (ej_score * 0.4) + (se_score * 0.5) + (power * 5)

    # ---------------------------------------------------------
    # 📈 第三層 (明線)：135 分戰術封頂計分
    # ---------------------------------------------------------
    score = 0
    # 皇者底色 (50)
    score += min(25, (rs_val / 100) * 25)
    score += min(25, (ej_score / 150) * 25)
    
    # 加速度 (50)
    score += min(15, (se_score / 120) * 15)
    score += 12.5 if flow_daily.iloc[-1] > 0 else 0 # 資金點火
    score += 12.5 if netma.iloc[-1] > netma.iloc[-2] else 0 # EJ抬升
    score += 10 if obv_state == 1 else 5 # OBV腳印
    
    # 長線穩定 (15)
    score += 10 if flow_daily.tail(60).sum() > 0 else 0
    score += 5 if (v.tail(10).std() / v.tail(10).mean()) < 0.2 else 0 # VCP
    
    # 巔峰紅利 (10)
    if se_score > 95: score += 5
    if power > 1.5: score += 5
    
    # 溢價 (10)
    if c.iloc[-1] > h.tail(20).max() * 0.99: score += 5
    if rs_val > 97: score += 5

    # ---------------------------------------------------------
    # 🛑 第四層：家法扣分 (安全制動)
    # ---------------------------------------------------------
    penalty = 0
    
    # 1. 💀 60日萬人坑
    counts, bins = np.histogram(c.tail(252), bins=30, weights=v.tail(252))
    upper_mask = (bins[:-1] > c.iloc[-1]) & (bins[:-1] < c.iloc[-1] * 1.05)
    if counts.sum() > 0 and (counts[upper_mask].sum() / counts.sum()) > 0.3: 
        penalty += 30
    
    # 2. 🚨 位置虛脫
    if ma50_bias > 15: penalty += 25
    
    # 3. 💥 爆缸天量
    if is_magenta.iloc[-1]: penalty += 20
    
    # 4. 🖋️ 影線派貨
    if ((h.iloc[-1] - max(c.iloc[-1], o.iloc[-1])) / denom.iloc[-1]) > 0.6 and c.iloc[-1] > o.iloc[-1]:
        penalty += 15
        
    # 5. ⚖️ Bias 階梯罰分 (核心鎖定)
    curr_bias = bias.iloc[-1]
    bias_limit = 5 if market_mode == "US" else 8
    if curr_bias > bias_limit: 
        penalty += (curr_bias - bias_limit) * 5

    final_score = score - penalty

    # ---------------------------------------------------------
    # 👑 第五層：Status 標籤與 8 大公仔
    # ---------------------------------------------------------
    # A. Status 狀態
    if curr_bias < 2 and se_score > 85 and netvol.iloc[-1] > 0: status = "[👑👑 初段起步]"
    elif 2 <= curr_bias <= 5 and rs_val > 95: status = "[👑 中段跟進]"
    elif curr_bias > 10: status = "[⚠️ 末段衝刺]"
    else: status = "[📈 趨勢行進]"

    # B. 六大橫財公仔 (3組指標判定)
    icons = []
    if is_cyan.iloc[-1] and chg.iloc[-1] > 2: icons.append("💰🔥")
    if v.iloc[-1] > v.iloc[-2] * 2 and chg.iloc[-1] > 1.5: icons.append("⚡")
    if abs(chg.iloc[-1]) < 0.5 and netvol.iloc[-1] > 0 and netma.iloc[-1] > netma.iloc[-2]: icons.append("💰🤫")
    if v.iloc[-1] < v_ma60.iloc[-1] and (netma.tail(3).diff() > 0).all(): icons.append("🧧")
    if chg.iloc[-1] < 0 and netvol.iloc[-1] > 0: icons.append("💰🛡️")
    if chg.iloc[-1] < -2 and is_magenta.iloc[-1] and netvol.iloc[-1] > netvol.tail(20).mean() * 2: icons.append("💎")
    
    # C. 鯨魚星星 (10日內 1.5倍兵力陽燭次數)
    v_ma50 = v.rolling(50).mean()
    stars = ((c.tail(10) > o.tail(10)) & (v.tail(10) > v_ma50.tail(10) * 1.5)).sum()
    if stars > 0: icons.append(f"🌟x{stars}")

    return {
        'Ticker': ticker,
        'Score': round(final_score, 1),
        'RawPower': round(raw_power, 1),  # 暗線：原始戰鬥力
        'Penalty': round(penalty, 1),     # 扣分：家法懲罰
        'Status': status,
        'Sector': sector,
        'Icons': "".join(icons),
        'EMA10': round(c.ewm(span=10, adjust=False).mean().iloc[-1], 2),
        'Bias': round(curr_bias, 1),
        'RS': round(rs_val, 1),
        'EJ': round(ej_score, 1),
        'SE': round(se_score, 1),
        'OBV': f"{obv_state}",
        'Flow': f"${net_flow_20/1e6:.1f}M",
        'Conc': f"{conc:.1f}%",
        'Power': round(power, 1)
    }
