import yfinance as yf
import pandas as pd
import numpy as np

def smart_fetch(ticker, period="1y"):
    try:
        # 如果是港股且沒有後綴，自動補上 .HK
        if ticker.isdigit() and len(ticker) <= 5:
            ticker = f"{ticker.zfill(4)}.HK"
        df = yf.download(ticker, period=period, progress=False)
        if df.empty: return pd.DataFrame()
        # 清理欄位
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
        return df
    except:
        return pd.DataFrame()

def check_stop_loss(df):
    if df.empty or len(df) < 10: return False
    close = df['Close'].iloc[-1]
    ema10 = df['Close'].ewm(span=10, adjust=False).mean().iloc[-1]
    return close < ema10

def scan_dragon_logic(df, ticker, sector, market_mode, mode='NORMAL', force_return=False):
    if df.empty or len(df) < 50:
        return None
        
    close = df['Close'].iloc[-1]
    open_price = df['Open'].iloc[-1]
    volume = df['Volume'].iloc[-1]
    
    # 計算均線
    ema10 = df['Close'].ewm(span=10, adjust=False).mean().iloc[-1]
    ema20 = df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
    ma50 = df['Close'].rolling(50).mean().iloc[-1]
    vol_20ma = df['Volume'].rolling(20).mean().iloc[-1]
    
    # 計算買盤力 (Power)
    var1 = df['Close'].iloc[-1] - df['Low'].iloc[-1]
    var2 = df['High'].iloc[-1] - df['Close'].iloc[-1]
    var3 = max(df['High'].iloc[-1] - df['Low'].iloc[-1], 0.001)
    buy_vol = volume * var1 / var3 if var3 > 0 else 0
    sell_vol = volume * var2 / var3 if var3 > 0 else 0
    power = round(buy_vol / sell_vol if sell_vol > 0 else 1.0, 2)
    
    # 乖離率 (Bias)
    bias = round((close - ema10) / ema10 * 100, 2)
    
    # 判斷生死
    is_dead = close < ema10
    
    # 初始化分數與圖示
    score = 0
    raw_power = 0
    penalty = 0
    icons = ""
    status = "☠️ [落選]" if is_dead else "🟢 [過關]"
    
    # ==========================================
    # 🧠 爺爺秘傳：VCP 高勝率排位邏輯
    # ==========================================
    if mode == 'VCP':
        # 1. 趨勢維度: 多頭排列 (40日核心)
        if close > ema10 and ema10 > ema20 and ema20 > ma50:
            score += 50
            raw_power += 50
            icons += " 👑"
            
        # 2. 動能維度: 量能爆發 (1-10日核心)
        if volume > (vol_20ma * 1.5) and power > 1.2 and close > open_price:
            score += 30
            raw_power += 30
            icons += " ⚡"
            
        # 3. 強度維度: RS 相對強度 (40日升幅)
        ret_40d = (close - df['Close'].iloc[-40]) / df['Close'].iloc[-40] if len(df) > 40 else 0
        if ret_40d > 0.15:
            score += 20
            raw_power += 20
            icons += " 🔥"
            
        # 4. 防禦扣分: 防止追高
        if bias > 8:
            score -= 40
            penalty += 40
            icons += " ⚠️"
            
    # ==========================================
    # 🤖 舊有 NORMAL 模式邏輯 (保留作對比)
    # ==========================================
    else:
        if close > ema10: score += 30; raw_power += 30
        if close > ma50: score += 20; raw_power += 20
        if power > 1.5: score += 20; raw_power += 20; icons += " 🔥"
        if bias > 10: score -= 30; penalty += 30; icons += " ⚠️"
        
    # 生死判決 (跌穿 EMA10 直接扣成負分)
    if is_dead:
        score -= 100
        penalty += 100
        icons += " 🛑"
        
    # 回傳結果 (如果是大批掃描且落選，就丟棄)
    if not force_return and is_dead:
        return None
        
    return {
        "Ticker": ticker,
        "Sector": sector,
        "Score": round(score, 1),
        "Icons": icons,
        "Status": status,
        "RawPower": raw_power,
        "Penalty": penalty,
        "EMA10": round(ema10, 2),
        "Bias": bias,
        "RS": round(ret_40d * 100 if 'ret_40d' in locals() else 0, 1),
        "EJ": 0, # 留空備用
        "SE": 0, # 留空備用
        "Power": power,
        "IsDead": is_dead
    }
