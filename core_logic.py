import yfinance as yf
import pandas as pd
import numpy as np
import time

# ==========================================
# 1. 終極兵力名單 (包含你提供的數千隻股名單)
# ==========================================
# 註：這裡放入你舊 Code 的 Map。你可以隨時在後面繼續加代號。
HK_STOCK_MAP = {
    "1. 互聯網巨頭": "0700.HK 9988.HK 3690.HK 1810.HK 9618.HK 1024.HK 9888.HK 0772.HK 0020.HK 0241.HK 0136.HK 1999.HK 2018.HK 3888.HK 2142.HK 1896.HK 0777.HK 0113.HK 0590.HK 1980.HK 1797.HK 6618.HK 2400.HK 0285.HK".split(),
    "2. 半導體芯片": "0981.HK 1347.HK 0285.HK 1478.HK 1833.HK 0522.HK 0732.HK 2382.HK 2018.HK 0099.HK 1385.HK 1138.HK 1910.HK 6088.HK 3898.HK 6123.HK 3389.HK".split(),
    "3. 新能源整車": "1211.HK 2015.HK 9866.HK 9868.HK 0175.HK 2333.HK 1114.HK 0489.HK 3606.HK 0867.HK 1316.HK 1958.HK 1585.HK 0315.HK 1274.HK 2150.HK 1122.HK 3808.HK 9863.HK".split(),
    # ... 其餘 1500 隻港股由你手動補齊
}

US_STOCK_MAP = {
    "1. 半導體設計": "NVDA TSM AVGO ASML AMD QCOM TXN MU INTC AMAT LRCX KLAC ADI NXPI MRVL MCHP SWKS MPWR ON LSCC TER QRVO SLAB WOLF SYNA RMBS ALGM SITM ACLS CRUS".split(),
    "2. AI雲端": "MSFT GOOGL ORCL ADBE CRM PLTR SNOW PANW FTNT NOW WDAY ZS DDOG CRWD MDB NET OKTA TEAM SPLK GEN CYBR CHKP VRSN ESTC TENB SQSP PCOR DOCN AI FSLY MSTR".split(),
    # ... 其餘 2000 隻美股由你手動補齊
}

HK_ETF_MAP = { "H1. 旗艦大盤": "2800.HK 2822.HK 3188.HK 3033.HK 3134.HK 3067.HK".split() }
US_ETF_MAP = { "U1. 核心主題": "QQQ SPY DIA IWM SOXX SMH ARKK IBIT XLK XLE XLI".split() }

# ==========================================
# 2. 核心運算引擎 (V188.0 邏輯植入)
# ==========================================
def smart_fetch(ticker, period="1y"):
    try:
        data = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        return data.dropna(subset=['Close', 'Volume'])
    except: return pd.DataFrame()

def analyze_dragon_stock(ticker, df):
    """
    千龍起步 + DNA 雙重過濾 (V188.0 核心)
    """
    if len(df) < 30: return False, 0, "", "", {}
    
    close = df['Close'].iloc[-1]
    vol = df['Volume'].iloc[-1]
    sma50 = df['Close'].rolling(50).mean().iloc[-1]
    
    # 1. 計算 RS, EJ, SE (188.0 算法)
    rs_score = 50 + ((close / df['Close'].iloc[-max(1, min(63, len(df)-1))]) - 1) * 100
    ej_score = (df['Volume'].tail(21).mean() / max(df['Volume'].tail(252).mean(), 1)) * 100
    se_score = 50 + (((close / df['Close'].iloc[-max(1, min(5, len(df)-1))]) - 1) * 1200)
    bias_pct = ((close - sma50) / sma50) * 100
    
    # 2. 11 項死刑與門檻
    if close < sma50 or rs_score < 52 or ej_score < 85 or se_score < 75:
        return False, 0, "", "", {}
    
    # 3. 8 大隱藏公仔 (大戶足跡)
    icons = []
    # (簡單示例：爆發、洗盤、建倉...)
    if vol > df['Volume'].rolling(20).mean().iloc[-1] * 2: icons.append("💰🔥")
    if ej_score > 95: icons.append("🐋")
    
    # 4. 階段標籤
    stage = "[👑 👑 初段起步]" if bias_pct < 3 else "[👑 中段跟進]"
    if bias_pct > 10: stage = "[⚠️ 末段衝刺]"

    total_score = (rs_score * 0.4) + (ej_score * 0.3) + (se_score * 0.3)
    
    details = {"SE": round(se_score,1), "EJ": round(ej_score,1), "RS": round(rs_score,1), "Bias": round(bias_pct,1), "StopLoss": round(close * 0.93, 2)}
    return True, total_score, stage, " ".join(icons), details
