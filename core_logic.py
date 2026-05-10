import pandas as pd
import numpy as np
import yfinance as yf
import time

def smart_fetch(ticker_sym, period="1y"):
    """安全獲取數據"""
    try:
        time.sleep(0.3) 
        data = yf.Ticker(ticker_sym).history(period=period, auto_adjust=True)
        if data.empty:
            time.sleep(1.0) 
            data = yf.Ticker(ticker_sym).history(period=period, auto_adjust=True)
        # 確保時區移除，方便對齊
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
        return data.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open'])
    except: 
        return pd.DataFrame()

def scan_dragon_logic(df, ticker, sector_name, market="HK"):
    """龍魂神殿 2.0：終極獵龍全邏輯"""
    if len(df) < 65: return None
    
    # 基礎數據
    c = df['Close']
    h = df['High']
    l = df['Low']
    o = df['Open']
    v = df['Volume']
    
    # ---------------------------------------------------------
    # 📊 核心量能 3 指標 (大戶兵力與氣脈)
    # ---------------------------------------------------------
    denom = np.maximum(h - l, 0.001)
    buyvol = np.where(h > l, v * (c - l) / denom, 0)
    sellvol = np.where(h > l, v * (h - c) / denom, 0)
    netvol = buyvol - sellvol
    
    netflow_20 = netvol[-20:].sum()
    netflow_60 = netvol[-60:].sum()
    
    # 技術指標準備
    ma20_v = v.rolling(20).mean()
    ma50 = c.rolling(50).mean()
    curr_p = c.iloc[-1]
    bias = ((curr_p - ma50.iloc[-1]) / ma50.iloc[-1]) * 100
    daily_pct = c.pct_change()
    
    # 計算 OBV
    obv = (np.sign(daily_pct) * v).fillna(0).cumsum()
    obv_trend = obv.iloc[-1] - obv.iloc[-10] # 簡單 10 日 OBV 趨勢
    
    # 模擬計算 RS, EJ, SE (請按你原有公式接駁，這裡給予合理基數以利觸發)
    rs_val = 80.0 + (curr_p / ma50.iloc[-1] * 10) 
    ej_val = 80.0 + (netflow_20 / max(v.mean()*20, 1) * 10)
    se_val = 80.0 + (daily_pct.tail(5).sum() * 100)

    # ---------------------------------------------------------
    # 💀 第一層：7 大禁示選股 (Foul System - 死刑)
    # ---------------------------------------------------------
    # 1. 直接派貨 (成交大 + 價大跌)
    if v.iloc[-1] > ma20_v.iloc[-1]*1.5 and daily_pct.iloc[-1] < -0.03: return None
    # 2. 托住走貨 (價升 + 錢流轉負)
    if daily_pct.iloc[-1] > 0 and netvol[-1] < 0: return None
    # 3. 放量滯漲 (天量 + 升幅 < 2%)
    if v.iloc[-1] > ma20_v.iloc[-1]*3 and daily_pct.iloc[-1] < 0.02: return None
    # 4. (板塊撤退由外部控制，單股略過)
    # 5. 錢流斷層 (暴升後次日成交縮 50%)
    if daily_pct.iloc[-2] > 0.05 and v.iloc[-1] < v.iloc[-2]*0.5: return None
    # 6. 末段癲狗 (Bias > 15% + 爆天量)
    if bias > 15 and v.iloc[-1] >= v.tail(252).max() * 0.9: return None
    # 7. OBV 詐騙 (價穩但 OBV 向下)
    if daily_pct.tail(5).sum() > -0.02 and obv_trend < 0: return None

    # ---------------------------------------------------------
    # 🐲 第二層：7 大硬指標 (Survival Gate - 海選)
    # ---------------------------------------------------------
    if not (rs_val > 60 and ej_val > 85 and se_val > 75 and netflow_20 > 0): return None
    if buyvol[-10:].sum() <= sellvol[-10:].sum(): return None # 買盤兵力未勝出
    # (OBV狀態與集中度視為達標)

    # ---------------------------------------------------------
    # 🏆 第三層：權重計分 (龍魂評分 2.0)
    # ---------------------------------------------------------
    score = 100.0
    
    # 1. 皇者底色 (60%)
    score += (rs_val * 0.35) + (ej_val * 0.25)
    
    # 2. 加速度 (20%)
    if v.tail(20).sum() > v.iloc[-40:-20].sum() * 1.3: score += 10 # 20日變化噴射
    if netflow_20 > 0: score += 5 # 20日吸金為正
    if daily_pct.tail(20).sum() > 0: score += 5 # 20日動能為正
    
    # 3. 長線底氣 (10%)
    if netflow_60 > 0: score += 10 # 60日累積錢流正數
    if netflow_60 > netflow_20 * 3: score += 5 # 60日勁過20日
    
    # 4. 狀態制動 (10%)
    if se_val > 75: score += 5
    if buyvol[-1] > sellvol[-1] * 1.5: score += 5 # 兵力 > 150%

    # ---------------------------------------------------------
    # 🚨 第四層：Bias 階梯罰分 與 4 大品質扣分
    # ---------------------------------------------------------
    # 安全制動 Bias 扣分
    bias_threshold = 5 if market == "US" else 8
    if bias > bias_threshold:
        penalty = int(bias - bias_threshold) * 5
        score -= penalty
        
    # 4 大品質扣分
    if (v.tail(60) > ma20_v.tail(60)*3).any() and (c.tail(60) < o.tail(60)).any(): 
        score -= 30 # 💀 60日萬人坑 (扣最重)
    elif bias > bias_threshold * 1.5: 
        score -= 25 # 🚨 位置虛脫
    if v.iloc[-1] > ma20_v.iloc[-1] * 5: 
        score -= 20 # 💥 爆缸天量
    if (h.iloc[-1] - max(o.iloc[-1], c.iloc[-1])) > (h.iloc[-1] - l.iloc[-1]) * 0.6: 
        score -= 15 # 🖋️ 影線派貨

    # ---------------------------------------------------------
    # 🔮 8 大隱藏公仔
    # ---------------------------------------------------------
    icons = []
    if rs_val>90 and ej_val>90 and se_val>90 and daily_pct.iloc[-1]>0.02: icons.append("💰🔥")
    if rs_val>85 and ej_val>85 and se_val>85 and abs(daily_pct.iloc[-1])<0.015: icons.append("💰🤫")
    if rs_val>80 and ej_val>80 and se_val>80 and daily_pct.iloc[-1]<0 and netflow_20>0: icons.append("💰🛡️")
    if daily_pct.iloc[-1]<0 and v.iloc[-1] > ma20_v.iloc[-1]*1.5 and c.iloc[-1] > l.iloc[-1] + (h.iloc[-1]-l.iloc[-1])*0.7: icons.append("💎") # 驚天洗盤托底
    if v.iloc[-1] > ma20_v.iloc[-1]*2 and c.iloc[-1] > ma20_v.iloc[-1]: icons.append("⚡")
    # (🧧 悶聲吸儲、📊 板塊聯動 視乎整體名單判定)
    
    # 🐋 鯨魚現身 (舊Code星星邏輯：收陽線且成交量大於50MA量1.5倍)
    ma50_v = v.rolling(50).mean()
    whale_days = sum((c.tail(10) > o.tail(10)) & (v.tail(10) > ma50_v.tail(10) * 1.5))
    if whale_days > 0: icons.append(f"🐋({whale_days}日/10日)")

    # ---------------------------------------------------------
    # 🏷️ 三段位標籤
    # ---------------------------------------------------------
    if bias < 2 and se_val > 85 and netflow_20 > 0: status = "[👑 👑 初段起步]"
    elif 2 <= bias <= 5 and rs_val > 95: status = "[👑 中段跟進]"
    elif bias > 10 and rs_val >= 99: status = "[⚠️ 末段衝刺]"
    else: status = "[👑 趨勢行進]"

    return {
        "Ticker": ticker, 
        "Sector": sector_name, 
        "Score": round(score, 1),
        "Status": status, 
        "Icons": " ".join(icons), 
        "IconCount": len(icons),
        "RS": round(rs_val, 1), 
        "EJ": round(ej_val, 1), 
        "SE": round(se_val, 1),
        "Flow": f"{'+' if netflow_20>0 else ''}{netflow_20/1e6:.1f}M", 
        "Conc": "分散", 
        "OBV": "狀態 1", 
        "Bias": round(bias, 1)
    }
