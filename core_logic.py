import yfinance as yf
import pandas as pd
import numpy as np

# ==========================================
# 🐲 龍魂掃股核心 (V2.0 終極版)
# ==========================================

def analyze_dragon_soul(ticker, df, market_type="HK"):
    """
    1. 11項死刑 (Foul) 
    2. 7大硬指標海選
    3. 權重評分排序
    """
    if len(df) < 65: return False, 0, "", "", {}

    # --- A. 數據準備 ---
    c, o, h, l, v = df['Close'], df['Open'], df['High'], df['Low'], df['Volume']
    curr_p, ma20_v = c.iloc[-1], v.rolling(20).mean().iloc[-1]
    sma50 = c.rolling(50).mean().iloc[-1]
    bias = ((curr_p - sma50) / sma50) * 100
    
    # RS, EJ, SE
    rs = 50 + ((curr_p / c.iloc[-63]) - 1) * 100
    ej = (v.tail(21).mean() / max(v.tail(252).mean() if len(df)>250 else v.mean(), 1)) * 100
    se = 50 + (((curr_p / c.iloc[-5]) - 1) * 1200)

    # 兵力計算 (BuyVol vs SellVol)
    var1, var2, var3 = (c - l), (h - c), np.maximum(h - l, 0.001)
    buy_v, sell_v = (v * var1 / var3), (v * var2 / var3)
    buying_force = buy_v.tail(5).mean() / max(sell_v.tail(5).mean(), 1) * 100

    # Net Flow & OBV
    mf = ((h + l + c) / 3) * v * np.where(c > c.shift(1).fillna(c), 1, -1)
    net_flow_20 = mf.tail(20).sum()
    net_flow_60 = mf.tail(60).sum()
    obv = (np.sign(c.diff()) * v).fillna(0).cumsum()
    obv_slope = (obv.iloc[-1] - obv.iloc[-10]) / 10

    # ------------------------------------------
    # 🛑 第一層：11 項「人間蒸發」死刑 (Foul 制)
    # ------------------------------------------
    # 1-3. 即時陷阱
    if (v.iloc[-1] > ma20_v * 1.5 and c.iloc[-1] < o.iloc[-1]*0.97): return False, 0, "", "", {} # 直接派貨
    if (c.iloc[-1] > o.iloc[-1] and mf.iloc[-1] < 0): return False, 0, "", "", {} # 托住走貨
    if (v.iloc[-1] > ma20_v * 3 and abs(c.iloc[-1]/o.iloc[-1]-1) < 0.02): return False, 0, "", "", {} # 放量滯漲
    # 5. 錢流斷層
    if v.iloc[-1] > ma20_v * 2 and v.iloc[-1] < v.shift(1).iloc[-1] * 0.5: return False, 0, "", "", {}
    # 6-7. 癲狗/OBV
    if bias > 15 and v.iloc[-1] > ma20_v * 3: return False, 0, "", "", {}
    if obv_slope < 0: return False, 0, "", "", {}
    # 8. 60日萬人坑 (尋找天量陰燭)
    v_60 = v.tail(60)
    if (v_60 > ma20_v * 4).any():
        idx = v_60.argmax()
        if c.iloc[idx] < o.iloc[idx]: return False, 0, "", "", {}
    # 9-11. 981 專殺
    if v.iloc[-1] > ma20_v * 5: return False, 0, "", "", {}
    if (h.iloc[-1] - max(o.iloc[-1], c.iloc[-1])) > abs(c.iloc[-1]-o.iloc[-1]) * 2: return False, 0, "", "", {} # 長上影
    if bias > (12 if market_type=="HK" else 8): return False, 0, "", "", {}

    # ------------------------------------------
    # 🐲 第二層：龍魂海選 (7 大指標)
    # ------------------------------------------
    if not (rs > 60 and ej > 85 and se > 75 and net_flow_20 > 0 and bias < 15): return False, 0, "", "", {}

    # ------------------------------------------
    # 🏆 第三層：評分排序 (2.0 版)
    # ------------------------------------------
    score = (rs * 0.35) + (ej * 0.25) # 皇者底色
    if (net_flow_20 / abs(mf.iloc[-40:-20].sum()+1)) > 1.3: score += 10 # 點火
    if ej > 100: score += 5
    if se > 85: score += 5
    if net_flow_60 > 0: score += 10
    if net_flow_60 > net_flow_20: score += 5
    if se > 75 or buying_force > 150: score += 5
    
    # 🚨 Bias 扣分
    limit = 8 if market_type == "HK" else 5
    if bias > limit: score -= (bias - limit) * 10

    # ------------------------------------------
    # 🎨 第四層：標籤與 8 大公仔
    # ------------------------------------------
    stage = "[👑 👑 初段起步]" if bias < 2 else ("[👑 中段跟進]" if bias <= 5 else "[⚠️ 末段衝刺]")
    icons = []
    # 💰🔥, 💰🤫, 💰🛡️, 💎, 🧧, ⚡
    if se > 85 and v.iloc[-1] > ma20_v * 1.5: icons.append("💰🔥")
    if abs(c.iloc[-1]/o.iloc[-1]-1) < 0.01 and ej > 110: icons.append("💰🤫")
    if c.iloc[-1] < o.iloc[-1] and mf.iloc[-1] > 0: icons.append("💰🛡️")
    if c.iloc[-1] < o.iloc[-1]*0.97 and mf.iloc[-1] > 0 and v.iloc[-1] > ma20_v*2: icons.append("💎")
    if ej > 120 and bias < 5: icons.append("🧧")
    if v.iloc[-1] > v.iloc[-2]*2 and v.iloc[-2] < ma20_v*0.6: icons.append("⚡")
    
    return True, score, stage, " ".join(icons), {"RS":round(rs,1), "EJ":round(ej,1), "SE":round(se,1), "Bias":round(bias,1), "StopLoss":round(curr_p*0.92,2)}
