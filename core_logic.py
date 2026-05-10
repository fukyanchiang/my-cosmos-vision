import pandas as pd
import numpy as np
import yfinance as yf
import streamlit as st
import glob
import os
import time

# ==========================================
# 1. 自動化軍火庫 (動態讀取 CSV)
# ==========================================
HK_STOCK_MAP = {
    "1. 互聯網巨頭": "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0772.HK 0020.HK 0241.HK 0136.HK 1999.HK 2018.HK 3888.HK 2142.HK 1896.HK 0777.HK 0113.HK 0590.HK 1980.HK 1797.HK 6618.HK 2400.HK 0285.HK".split(),
    "2. 半導體與芯片": "0981.HK 1347.HK 0285.HK 1478.HK 1833.HK 0522.HK 0732.HK 2382.HK 2018.HK 0099.HK 1385.HK 1138.HK 1910.HK 6088.HK 3898.HK 6123.HK 3389.HK".split(),
    "3. 新能源車與整車": "1211.HK 2015.HK 9866.HK 9868.HK 0175.HK 2333.HK 1114.HK 0489.HK 3606.HK 0867.HK 1316.HK 1958.HK 1585.HK 0315.HK 1274.HK 2150.HK 1122.HK 3808.HK 9863.HK".split(),
    "4. 國有大行與金融": "0005.HK 0939.HK 1398.HK 3988.HK 2318.HK 2388.HK 0011.HK 3968.HK 3328.HK 0998.HK 0023.HK 2016.HK 1658.HK 6198.HK 0410.HK 6066.HK 1551.HK 1963.HK 1988.HK 3866.HK".split()
}
HK_ETF_MAP = {
    "H1. 旗艦大盤": "2800.HK 3033.HK 3134.HK 2822.HK 3188.HK 3066.HK 2828.HK".split()
}

# 預設底線名單 (防止無 CSV 時系統崩潰)
US_STOCK_MAP = {"1. AI與雲端": ["NVDA", "MSFT", "AAPL", "PLTR"]}
US_ETF_MAP = {"U1. 核心": ["QQQ", "SPY", "DIA", "IWM"]}

def load_csv_lists():
    """自動掃描目錄下的 CSV，提取 SYMBOL 並去重"""
    global US_STOCK_MAP, US_ETF_MAP
    csv_files = glob.glob("*.csv")
    if not csv_files: return
    
    us_eq_map, us_etf_map = {}, {}
    seen_equities, seen_etfs = set(), set()
    
    for file in csv_files:
        try:
            is_etf = "ETF" in file.upper()
            category = file.split(" - ")[-1].replace(".csv", "") if " - " in file else file.replace(".csv", "")
            
            # 搵 Header 行
            df_temp = pd.read_csv(file, on_bad_lines='skip', engine='python', nrows=15)
            header_idx = next((i for i in range(len(df_temp)) if "SYMBOL" in str(df_temp.iloc[i].values)), None)
            
            if header_idx is not None:
                df = pd.read_csv(file, skiprows=header_idx+1)
            else:
                df = pd.read_csv(file)
            
            if 'SYMBOL' in df.columns:
                symbols = df['SYMBOL'].dropna().astype(str).tolist()
                clean_symbols = [s.strip() for s in symbols if s.strip() and " " not in s]
                
                unique_for_cat = []
                for s in clean_symbols:
                    target_set = seen_etfs if is_etf else seen_equities
                    if s not in target_set:
                        target_set.add(s)
                        unique_for_cat.append(s)
                
                if unique_for_cat:
                    if is_etf: us_etf_map[category] = unique_for_cat
                    else: us_eq_map[category] = unique_for_cat
        except: continue
            
    if us_eq_map: US_STOCK_MAP.clear(); US_STOCK_MAP.update(us_eq_map)
    if us_etf_map: US_ETF_MAP.clear(); US_ETF_MAP.update(us_etf_map)

# 系統啟動時自動吸血
load_csv_lists()

@st.cache_data(ttl=3600)
def smart_fetch(ticker, period="1y"):
    try:
        time.sleep(0.1) 
        data = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        return data.dropna(subset=['Close', 'Volume', 'High', 'Low', 'Open'])
    except: return pd.DataFrame()

# ==========================================
# 2. 神殿羅輯：7死刑 + 4扣分
# ==========================================
def analyze_dragon_soul(ticker, df, market_type="HK"):
    if len(df) < 65: return False, 0, "", "", {}

    c, o, h, l, v = df['Close'], df['Open'], df['High'], df['Low'], df['Volume']
    curr_p, ma20_v = c.iloc[-1], v.rolling(20).mean().iloc[-1]
    sma50 = c.rolling(50).mean().iloc[-1]
    
    bias = ((curr_p - sma50) / sma50) * 100
    rs = 50 + ((curr_p / c.iloc[-63]) - 1) * 100
    ej = (v.tail(21).mean() / max(v.tail(252).mean() if len(df)>250 else v.mean(), 1)) * 100
    se = 50 + (((curr_p / c.iloc[-5]) - 1) * 1200)

    tp = (h + l + c) / 3
    mf = tp * v * np.where(c > c.shift(1).fillna(c), 1, -1)
    net_flow_20 = mf.tail(20).sum()
    obv = (np.sign(c.diff()) * v).fillna(0).cumsum()
    obv_slope = (obv.iloc[-1] - obv.iloc[-10]) / 10

    # 🛑 7 項鐵律死刑 (一票否決)
    if v.iloc[-1] > ma20_v*1.5 and c.iloc[-1] < o.iloc[-1]*0.97: return False, 0, "", "", {} # 直接派貨
    if c.iloc[-1] > o.iloc[-1] and mf.iloc[-1] < 0: return False, 0, "", "", {} # 托住走貨
    if v.iloc[-1] > ma20_v*3 and abs(c.iloc[-1]/o.iloc[-1]-1) < 0.02: return False, 0, "", "", {} # 放量滯漲
    if v.iloc[-1] > ma20_v*2 and v.iloc[-1] < v.shift(1).iloc[-1]*0.5: return False, 0, "", "", {} # 錢流斷層
    v_60 = v.tail(60); max_v_idx = v_60.argmax()
    if v_60.iloc[max_v_idx] > ma20_v*4 and c.tail(60).iloc[max_v_idx] < o.tail(60).iloc[max_v_idx]: return False, 0, "", "", {} # 60日萬人坑
    if v.iloc[-1] > ma20_v*5: return False, 0, "", "", {} # 爆缸天量
    if (h.iloc[-1] - max(o.iloc[-1], c.iloc[-1])) > abs(c.iloc[-1]-o.iloc[-1])*2: return False, 0, "", "", {} # 影線派貨

    # 🐲 海選基礎門檻
    if not (rs > 55 and ej > 75 and se > 65 and net_flow_20 > 0):
        return False, 0, "", "", {}

    # 🏆 分數與 4 項扣分 (陰險標記)
    score = (rs * 0.4) + (ej * 0.3) + (se * 0.3)
    penalty_score = 0
    penalties = []

    if mf.iloc[-1] < mf.tail(5).mean(): penalty_score += 15; penalties.append("🌧️ 板塊疲軟")
    if bias > 15: penalty_score += 40; penalties.append("🌑 末段癲狗")
    if obv_slope < 0: penalty_score += 30; penalties.append("🕸️ OBV詐騙")
    limit = 12 if market_type=="HK" else 8
    if bias > limit and bias <= 15: penalty_score += 20; penalties.append("🕳️ 位置虛脫")

    final_score = score - penalty_score
    stage = "[⛩️ 初段起步]" if bias < 2 else ("[⛩️⛩️ 中段跟進]" if bias <= 5 else "[⛩️⛩️⛩️ 末段衝刺]")
    
    d_details = {
        "RS":round(rs,1), "EJ":round(ej,1), "SE":round(se,1), 
        "Bias":round(bias,1), "StopLoss":round(curr_p*0.92,2),
        "PenaltyScore": penalty_score,
        "Penalties_Text": " | ".join(penalties) if penalties else "籌碼乾淨"
    }
    
    return True, final_score, stage, "", d_details
