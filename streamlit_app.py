import pandas as pd
import numpy as np

def run_tianwai_feixian(df: pd.DataFrame) -> pd.DataFrame:
    """
    龍魂戰略總部 - 天外飛仙 (第 6 掣) Python 量化引擎 (防斷層修復版)
    """
    df = df.sort_index().copy()
    
    C = df['Close']
    O = df['Open']
    H = df['High']
    L = df['Low']
    V = df['Volume']

    # ==========================================
    # 基礎通達信函數 Python 向量化 (加入 min_periods=1 完美防斷層)
    # ==========================================
    def MA(s, n): return s.rolling(window=n, min_periods=1).mean()
    def EMA(s, n): return s.ewm(span=n, adjust=False).mean()
    def SMA(s, n, m=1): return s.ewm(alpha=m/n, adjust=False).mean()
    def HHV(s, n): return s.rolling(window=n, min_periods=1).max()
    def LLV(s, n): return s.rolling(window=n, min_periods=1).min()
    def STD(s, n): return s.rolling(window=n, min_periods=1).std()
    def CROSS(s1, s2):
        if isinstance(s2, (int, float)):
            return (s1 > s2) & (s1.shift(1).fillna(s1) <= s2)
        return (s1 > s2) & (s1.shift(1).fillna(s1) <= s2.shift(1).fillna(s2))
    def COUNT(cond, n): return cond.astype(int).rolling(window=n, min_periods=1).sum()
    def BARSLAST(cond):
        idx = np.arange(len(cond))
        last_true = pd.Series(np.where(cond, idx, np.nan), index=cond.index).ffill()
        return pd.Series(idx - last_true, index=cond.index).fillna(9999)
        
    def FORCAST(S, N):
        w = np.arange(1, N + 1) - (N + 1) / 2.0
        w2_sum = np.sum(w ** 2)
        slope_num = sum(w[i] * S.shift(N - 1 - i).bfill() for i in range(N))
        slope = slope_num / w2_sum
        return S.rolling(N, min_periods=1).mean() + slope * (N - 1) / 2.0

    # --- 共用均線 ---
    MA10, MA20 = MA(C, 10), MA(C, 20)
    MA50, MA150, MA200 = MA(C, 50), MA(C, 150), MA(C, 200)

    # ==========================================
    # 基礎 STAGE 2 結構定義
    # ==========================================
    STAGE2 = ((C > MA50) & (C > MA150) & (MA50 > MA150) & (MA150 > MA200) & 
              (MA200 > MA200.shift(20).bfill()) & (C > LLV(L, 250) * 1.3))

    # ==========================================
    # 硬條件 1: MACD 水上橙柱計時器
    # ==========================================
    DIF = EMA(C, 12) - EMA(C, 26)
    DEA = EMA(DIF, 9)
    MACD_VAL = (DIF - DEA) * 2

    STAGE2_WATER_ORANGE = STAGE2 & (MACD_VAL >= 0) & (DIF > 0) & (DEA > 0)
    MACD_ORANGE_START = STAGE2_WATER_ORANGE & (~STAGE2_WATER_ORANGE.shift(1).fillna(False))
    DAYS_SINCE_MACD_ORANGE = BARSLAST(MACD_ORANGE_START)

    # ==========================================
    # 硬條件 2: GRANDPA POWER 宏觀動能 > 0.5
    # ==========================================
    RS = 2 * C / MA(C, 63) + C / MA(C, 126) + C / MA(C, 189) + C / MA(C, 252)
    POWER = RS - 5
    POWER_STRONG = POWER > 0.5

    # ==========================================
    # 硬條件 3: TTM 橙柱雙確認
    # ==========================================
    N_TTM = 20
    VAR1 = (HHV(H, N_TTM) + LLV(L, N_TTM)) / 2 + MA(C, N_TTM)
    TTM_MOMENTUM = FORCAST(C - VAR1 / 2, N_TTM)
    
    TTM_PRICE_HOLD = COUNT(C > MA150, 3) > 0
    TTM_STAGE2_ON = TTM_PRICE_HOLD & (MA50 > MA150) & (MA150 > MA150.shift(10).bfill())
    IS_ORANGE_UP = (TTM_MOMENTUM >= 0) & TTM_STAGE2_ON & (TTM_MOMENTUM > TTM_MOMENTUM.shift(1).bfill())
    
    DAYS_SINCE_NOT_ORANGE = BARSLAST(~IS_ORANGE_UP)
    NEW_ORANGE_AFTER_CROSS = IS_ORANGE_UP & (DAYS_SINCE_NOT_ORANGE <= DAYS_SINCE_MACD_ORANGE + 1)
    HAS_ORANGE_IN_STAGE2 = NEW_ORANGE_AFTER_CROSS & STAGE2

    # ==========================================
    # 雙梯隊時間窗口判斷 (天外飛仙 核心邏輯)
    # ==========================================
    RAW_BASE_MATCH = STAGE2_WATER_ORANGE & POWER_STRONG & HAS_ORANGE_IN_STAGE2
    IS_HOT_WINDOW = RAW_BASE_MATCH & (DAYS_SINCE_MACD_ORANGE <= 2)
    IS_COOL_WINDOW = (STAGE2 & (DAYS_SINCE_MACD_ORANGE >= 3) & 
                      (DAYS_SINCE_MACD_ORANGE <= 9) & (COUNT(RAW_BASE_MATCH, 10) > 0))
    
    BASE_MATCH = IS_HOT_WINDOW | IS_COOL_WINDOW
    
    STATUS_FLAG = np.where(IS_HOT_WINDOW, 1, np.where(IS_COOL_WINDOW, 2, 0))
    BASE_RANK_SCORE = np.where(IS_HOT_WINDOW, 100, np.where(IS_COOL_WINDOW, 0, -9999))

    # ==========================================
    # 21 大非必要加分引擎
    # ==========================================
    VOL_MA20 = MA(V, 20)
    DAY_AMP = (H - L) / C.shift(1).bfill() * 100
    AMP_SQUEEZE = DAY_AMP < (MA(DAY_AMP, 20) * 0.75)
    VOL_SQUEEZE = V < (VOL_MA20 * 0.75)
    TR_VAL = pd.concat([H - L, (H - C.shift(1).bfill()).abs(), (L - C.shift(1).bfill()).abs()], axis=1).max(axis=1)
    ATR20 = MA(TR_VAL, 20)
    BOLLING_BAND = MA20 + 2 * STD(C, 20)
    KELTNER_BAND = MA20 + 1.5 * ATR20
    TTM_SQUEEZE = BOLLING_BAND < KELTNER_BAND
    WAS_SQUEEZED = COUNT(AMP_SQUEEZE & VOL_SQUEEZE & TTM_SQUEEZE, 5) >= 1
    TF_BUY_SP = C - L
    TF_SELL_SP = H - C
    INNER_POWER = (TF_BUY_SP > TF_SELL_SP) | ((C - L) / (H - L + 1e-5) > 0.60)
    STOCK_DELTA = C - C.shift(1).bfill()
    DELTA_ACC = STOCK_DELTA - STOCK_DELTA.shift(1).bfill()
    DELTA_POWER = (DELTA_ACC > 0) & (C > O)
    BETA_OK = (MA(TR_VAL, 14) / MA20) * 100 > 1.2
    SPRING_READY = STAGE2 & WAS_SQUEEZED & BETA_OK
    SPRING_SIGNAL = SPRING_READY & INNER_POWER & DELTA_POWER
    CNT_SPRING = np.where(BASE_MATCH, COUNT(SPRING_SIGNAL & (~SPRING_SIGNAL.shift(1).fillna(False)), 5), 0)

    MA200_UP = MA200 > MA200.shift(20).bfill()
    VCP_STAGE2 = (C >= MA50) & (MA50 > MA150) & (MA150 > MA200) & MA200_UP
    AMP_BIG = (HHV(H, 30) - LLV(L, 30)) / (LLV(L, 30) + 1e-5) * 100
    AMP_NARROW = (HHV(H, 8) - LLV(L, 8)) / (LLV(L, 8) + 1e-5) * 100
    VCP_READY = (AMP_NARROW <= AMP_BIG * 0.65) & (AMP_NARROW <= 10)
    SURGE_MOM = (C / LLV(L, 40).shift(10).bfill()) > 1.9
    FLAG_AMP = (HHV(H, 12) - LLV(L, 12)) / (LLV(L, 12) + 1e-5) * 100
    HTF_READY = VCP_STAGE2 & SURGE_MOM & (FLAG_AMP < 20)
    MAV20 = MA(V, 20)
    RECENT_HIGH = HHV(H, 10).shift(1).bfill()
    BREAKOUT = CROSS(C, RECENT_HIGH) & (V > MAV20 * 1.3)
    IS_VCP = BREAKOUT & VCP_READY.shift(1).fillna(False)
    IS_HTF = BREAKOUT & HTF_READY.shift(1).fillna(False)
    IS_BOTH = IS_VCP & IS_HTF
    ONLY_VCP = IS_VCP & (~IS_BOTH)
    ONLY_HTF = IS_HTF & (~IS_BOTH)
    GATHERING = HTF_READY | VCP_READY
    RECENT_GATHER = COUNT(GATHERING, 5) >= 1
    BIG_YANG = (C / C.shift(1).bfill()) > 1.04
    REAL_BREAK = (C > RECENT_HIGH) & BIG_YANG
    DRAGON = REAL_BREAK & RECENT_GATHER & (~BREAKOUT)
    EX_MEM = COUNT(GATHERING, 15) >= 1
    NEW_HIGH_15 = C > HHV(H, 15).shift(1).bfill()
    IS_SNDK = NEW_HIGH_15 & EX_MEM & (~BREAKOUT) & (~DRAGON)
    NEW_HIGH_20 = C > HHV(H, 20).shift(1).bfill()
    SINGLE_SURGE = (C / C.shift(1).bfill()) > 1.05
    IS_ULTIMATE = VCP_STAGE2 & EX_MEM & NEW_HIGH_20 & SINGLE_SURGE & (~BREAKOUT)
    PARABOLIC_TREND = (C > MA20) & (MA20 > MA50)
    RECENT_SURGE = (C / LLV(L, 30).shift(5).bfill()) > 1.5
    TODAY_STRONG_BREAK = (C > HHV(H, 10).shift(1).bfill()) & (C > O) & ((C / C.shift(1).bfill()) > 1.03)
    IS_PARABOLIC = (PARABOLIC_TREND & RECENT_SURGE & TODAY_STRONG_BREAK & 
                    (~BREAKOUT) & (~IS_ULTIMATE) & (~IS_SNDK) & (~DRAGON))
    N_YANG_COND = ((C / C.shift(1).bfill()) >= 1.04) & (C > O)
    N_PREV_DAYS = BARSLAST(N_YANG_COND).shift(1).fillna(0) + 1
    N_TARGET_HIGH = H.shift(N_PREV_DAYS.astype(int)).bfill()
    N_BREAK = (N_PREV_DAYS <= 20) & (C > N_TARGET_HIGH) & (C.shift(1).bfill() <= N_TARGET_HIGH) & (C > O)
    ALL_PREV = ONLY_VCP | ONLY_HTF | IS_BOTH | DRAGON | IS_SNDK | IS_ULTIMATE | IS_PARABOLIC
    IS_N_SHAPE = VCP_STAGE2 & N_BREAK & (~ALL_PREV)
    BULL_TREND = (MA50 > MA150) & (MA150 > MA200) & MA200_UP
    SHORT_WASH = COUNT(MA10 < MA20, 3) >= 1
    SHORT_EVE = (MA10 <= MA20) & ((MA10 + (MA10 - MA10.shift(1).bfill())) > (MA20 + (MA20 - MA20.shift(1).bfill()))) & (C > O)
    MID_WASH = COUNT(MA20 < MA50, 5) >= 1
    MID_EVE = (MA20 <= MA50) & ((MA20 + (MA20 - MA20.shift(1).bfill())) > (MA50 + (MA50 - MA50.shift(1).bfill()))) & (C > O)
    IS_AMBUSH = (BULL_TREND & ((SHORT_WASH & SHORT_EVE) | (MID_WASH & MID_EVE)) & 
                 (~ALL_PREV) & (~IS_N_SHAPE))
    BIG_MONEY_IN = (V >= MAV20 * 1.5) & (C > O)
    ANY_BUY = ALL_PREV | IS_N_SHAPE | IS_AMBUSH
    SHOW_BIG_MONEY = ANY_BUY & BIG_MONEY_IN
    CNT_MONEY_BAG = np.where(BASE_MATCH, COUNT(SHOW_BIG_MONEY, 5), 0)

    LC = C.shift(1).bfill()
    DIFF_C = C - LC
    UP_RSI = np.where(DIFF_C > 0, DIFF_C, 0)
    ABS_RSI = DIFF_C.abs()
    RSI_VAL = SMA(pd.Series(UP_RSI, index=df.index), 14) / (SMA(pd.Series(ABS_RSI, index=df.index), 14) + 1e-5) * 100
    CNT_RSI = np.where(BASE_MATCH & STAGE2 & (RSI_VAL > 50), 1, 0)

    TYP_V = (H + L + C) / 3
    V1 = np.where(TYP_V > TYP_V.shift(1).bfill(), TYP_V * V, 0)
    V2 = np.where(TYP_V < TYP_V.shift(1).bfill(), TYP_V * V, 0)
    MFI_V = 100 * pd.Series(V1).rolling(14, min_periods=1).sum() / (pd.Series(V1).rolling(14, min_periods=1).sum() + pd.Series(V2).rolling(14, min_periods=1).sum() + 1e-5)
    OBV_DIR = np.where(C > C.shift(1).bfill(), V, np.where(C < C.shift(1).bfill(), -V, 0))
    OBV_RAW = EMA(pd.Series(OBV_DIR, index=df.index).rolling(120, min_periods=1).sum(), 3)
    MAX_OBV = HHV(OBV_RAW, 120)
    MIN_OBV = LLV(OBV_RAW, 120)
    OBV_NORM = (OBV_RAW - MIN_OBV) / (MAX_OBV - MIN_OBV + 1e-5) * 100
    OBV_SIG = MA(OBV_NORM, 20)
    SMART_BUY = CROSS(OBV_NORM, OBV_SIG) & (MFI_V > 40)
    CNT_SWEEP = np.where(BASE_MATCH, COUNT(SMART_BUY, 7), 0)

    VA_OBV = pd.Series(OBV_DIR, index=df.index)
    OBV_LINE = VA_OBV.rolling(250, min_periods=1).sum()
    OBV_HHV = HHV(OBV_LINE, 30).shift(1).bfill()
    OBV_BREAK = CROSS(OBV_LINE, OBV_HHV) & STAGE2
    PRICE_NOT_HIGH = C < HHV(C, 10)
    SMART_ACC = OBV_BREAK & PRICE_NOT_HIGH
    FUND_BREAK = OBV_BREAK & (~PRICE_NOT_HIGH)
    CNT_SMART_ACC = np.where(BASE_MATCH, COUNT(SMART_ACC, 6), 0)
    CNT_FUND_BREAK = np.where(BASE_MATCH, COUNT(FUND_BREAK, 6), 0)

    POC_LINE = (TYP_V * V).rolling(50, min_periods=1).sum() / (V.rolling(50, min_periods=1).sum() + 1e-5)
    VOL_VAR = (V * (TYP_V - POC_LINE)**2).rolling(50, min_periods=1).sum() / (V.rolling(50, min_periods=1).sum() + 1e-5)
    VOL_STD = np.sqrt(VOL_VAR)
    VAH_LINE = POC_LINE + 1.0 * VOL_STD
    BULL_BREAK = STAGE2 & CROSS(C, VAH_LINE) & (V > MA(V, 5))
    CNT_BULL_BREAK = np.where(BASE_MATCH, COUNT(BULL_BREAK, 6), 0)

    VOLMA20_BIG = MA(V, 20)
    CSPRE = (C - O).abs()
    AVGS = MA(CSPRE, 20)
    ISBIG = (V > VOLMA20_BIG * 1.5) & (C > O) & (CSPRE > AVGS)
    CNT_BIG = np.where(BASE_MATCH, COUNT(ISBIG, 3), 0)

    S_EMA20 = EMA(C, 20)
    S_E5, S_E10 = EMA(C, 5), EMA(C, 10)
    S_INST_VOL = V > (MA(V, 5) * 1.2)
    S_STRONG_K = (C > O) & ((C - L) > (H - L) * 0.50)
    S_CROSS = CROSS(C, S_EMA20) | ((C > S_EMA20) & CROSS(S_E5, S_E10))
    S_PULLBACK = (L <= S_EMA20) & (C > S_EMA20) & (C > O)
    SP_BUY = STAGE2 & S_INST_VOL & S_STRONG_K & (S_CROSS | S_PULLBACK)
    CNT_SPLUS = np.where(BASE_MATCH, COUNT(SP_BUY, 3), 0)

    MAVOL20_HUGE = MA(V, 20)
    IS_HUGE_VOL = V > (MAVOL20_HUGE * 2.0)
    HUGE_VOL_SIGNAL = IS_HUGE_VOL & (C >= O)
    CNT_HUGE_VOL = np.where(BASE_MATCH, COUNT(HUGE_VOL_SIGNAL, 4), 0)

    DMI_HD = H - H.shift(1).bfill()
    DMI_LD = L.shift(1).bfill() - L
    DMP_RAW = np.where((DMI_HD > 0) & (DMI_HD > DMI_LD), DMI_HD, 0)
    DMM_RAW = np.where((DMI_LD > 0) & (DMI_LD > DMI_HD), DMI_LD, 0)
    DMI_TR = TR_VAL.rolling(14, min_periods=1).sum()
    PDI_VAL = pd.Series(DMP_RAW, index=df.index).rolling(14, min_periods=1).sum() * 100 / (DMI_TR + 1e-5)
    MDI_VAL = pd.Series(DMM_RAW, index=df.index).rolling(14, min_periods=1).sum() * 100 / (DMI_TR + 1e-5)
    ADX_RAW = MA((MDI_VAL - PDI_VAL).abs() / (MDI_VAL + PDI_VAL + 1e-5) * 100, 6)
    DMI_BULL_CROSS = CROSS(ADX_RAW, 25) & (PDI_VAL > MDI_VAL) & (PDI_VAL - MDI_VAL > 3)
    DMI_BULL_FLIP = CROSS(PDI_VAL, MDI_VAL) & (ADX_RAW >= 25) & (PDI_VAL - MDI_VAL > 3)
    DMI_IGNITE = (DMI_BULL_CROSS | DMI_BULL_FLIP) & STAGE2
    DMI_SQUEEZE = CROSS(15, ADX_RAW)
    CNT_TORNADO = np.where(BASE_MATCH, COUNT(DMI_IGNITE, 4), 0)
    CNT_NINJA = np.where(BASE_MATCH, COUNT(DMI_SQUEEZE, 4), 0)

    PZ_N = 24
    PZ_MID = MA(C, PZ_N)
    PZ_STD = STD(C, PZ_N)
    PZ_UPPER = PZ_MID + 2.5 * PZ_STD
    PZ_LOWER = PZ_MID - 2.5 * PZ_STD
    PZ_ATR = MA(TR_VAL, 20)
    PZ_EXTREME = TR_VAL > PZ_ATR * 2
    PZ_RANGE = ((PZ_UPPER - PZ_LOWER) / PZ_MID * 100) < MA((PZ_UPPER - PZ_LOWER) / PZ_MID * 100, 50)
    PZ_FORCE = (C - PZ_MID) / PZ_STD * 100
    PZ_E1 = EMA(PZ_FORCE, 13)
    PZ_E2 = EMA(PZ_E1, 13)
    PZ_SIG = 2 * PZ_E1 - PZ_E2
    PZ_BUY1 = CROSS(C, PZ_UPPER) & (PZ_SIG > 50) & (V > MA(V, 20)) & PZ_RANGE
    PZ_BUY2 = (PZ_SIG > 50) & (C > MA10) & (C > C.shift(1).bfill()) & STAGE2 & (~PZ_EXTREME)
    PZ_BUY3 = CROSS(PZ_SIG, 50) & (C > PZ_MID) & (V > MA(V, 20))
    PZ_ANY = PZ_BUY1 | PZ_BUY3 | PZ_BUY2
    CNT_PZ_ANY = np.where(BASE_MATCH, COUNT(PZ_ANY, 4), 0)

    GL_PRO_BUY = CROSS(GL_RV, GL_SV) & STAGE2 & (ADX_RAW >= 20) & (GL_RV < 15)
    CNT_GL_IGNITE = np.where(BASE_MATCH, COUNT(GL_PRO_BUY, 4), 0)

    WK_EMA200 = EMA(C, 200)
    WK_BEAR = (C < WK_EMA200) | (MA50 < WK_EMA200)
    WK_SPRING = CROSS(C, S_EMA20) & (C.shift(1).bfill() < S_EMA20) & ((V > MA(V, 5) * 1.2) | (V < MA(V, 20) * 0.6)) & (~WK_BEAR)
    CNT_WK_SPRING = np.where(BASE_MATCH, COUNT(WK_SPRING, 4), 0)

    KO_SAFE = (C > (C - ATR20 * 3.2).rolling(50, min_periods=1).max()) & (C > MA(C, 15))
    KO_RED_TRIANGLE = (V > MA(V, 5) * 1.35) & (C > O) & KO_SAFE
    CNT_KO_RED_TRIANGLE = np.where(BASE_MATCH, COUNT(KO_RED_TRIANGLE, 4), 0)

    FLOW_INST = STAGE2 & (C > C.shift(1).bfill()) & (V > V.shift(1).bfill()) & (V > MA(V, 50) * 1.5) & (C >= HHV(C.shift(1).bfill(), 20))
    FLOW_REAL_BUY = FLOW_INST & ((COUNT(V < MA(V, 50)*0.5, 10) > 0) | (TTM_MOMENTUM > TTM_MOMENTUM.shift(1).bfill()))
    CNT_FLOW_REAL_BUY = np.where(BASE_MATCH, COUNT(FLOW_REAL_BUY, 4), 0)

    NX_STAGE2 = (COUNT(C > MA150, 3) > 0) & (MA50 > MA150) & (MA150 > MA150.shift(10).bfill())
    NX_RAW = (V > MA(V, 20) * 1.5) & ((H - L) > MA(H - L, 20) * 1.5)
    NX_SAFE = NX_STAGE2 & (COUNT(V < MA(V, 20), 10) > 0) & NX_RAW & (C >= O) & ((H - C.shift(1).bfill())/C.shift(1).bfill()*100 > 4.0)
    CNT_NX_BUY_SAFE = np.where(BASE_MATCH, COUNT(NX_SAFE, 3), 0)

    VSA_DEV60 = (C - MA(C, 60)) / MA(C, 60) * 100
    VSA_START = (V > MA(V, 20) * 1.5) & (C > O) & ((C - O).abs() > MA((C - O).abs(), 20)) & (VSA_DEV60 <= 15)
    CNT_VSA_START = np.where(BASE_MATCH, COUNT(VSA_START, 4), 0)

    TF_UPPER = MA(V, 20) + 2.0 * STD(V, 20)
    TF_FIRE = (V > TF_UPPER) & (V > MA(V, 60) * 1.9) & ((C - C.shift(1).bfill()).abs() / C.shift(1).bfill() * 100 > 2.0) & (C > O) & (VSA_DEV60 <= 15)
    CNT_TF_FIRE = np.where(BASE_MATCH, COUNT(TF_FIRE, 4), 0)

    SV19_STATE = np.where((C > MA20) & (MA20 > MA50) & (MA50 > MA200), 1, 3)
    SV19_RAW_BUY = CROSS(EMA(C, 5), EMA(C, 10)) & (V > MA(V, 5) * 1.2) & ((C > O) & ((C - L) > (H - L) * 0.55)) & (ATR20 > ATR20.shift(1).bfill()) & (RSI_VAL < 78)
    SV19_BUY_GREEN = SV19_RAW_BUY & (SV19_STATE == 1)
    CNT_S19_GREEN = np.where(BASE_MATCH, COUNT(SV19_BUY_GREEN, 6), 0)

    TFM_V3 = H - L
    TFM_BUY = np.where(TFM_V3 > 0, V * (C - L) / TFM_V3, 0)
    TFM_SELL = np.where(TFM_V3 > 0, V * (H - C) / TFM_V3, 0)
    TFM_SUM_BUY = pd.Series(TFM_BUY, index=df.index).rolling(5, min_periods=1).sum()
    TFM_SUM_SELL = pd.Series(TFM_SELL, index=df.index).rolling(5, min_periods=1).sum()
    TFM_WIN = (TFM_SUM_BUY / (TFM_SUM_BUY + TFM_SUM_SELL + 1e-5)) > 0.65
    CNT_TFM_WIN = np.where(BASE_MATCH & TFM_WIN, 1, 0)

    VCX_WR = (HHV(H, 14) - C) / (HHV(H, 14) - LLV(L, 14) + 1e-5) * -100
    VCX_CLIMAX = (V > HHV(V, 60).shift(1).bfill()) & (V > MA(V, 30) * 2.5) & (H >= HHV(H, 60).shift(1).bfill()) & (VCX_WR > -10)
    CNT_CLIMAX = np.where(BASE_MATCH, COUNT(VCX_CLIMAX, 4), 0)

    # ==========================================
    # 輸出結算
    # ==========================================
    df['天外飛仙_狀態'] = pd.Series(STATUS_FLAG, index=df.index).fillna(0).astype(int)
    
    TOTAL_SCORE = (BASE_RANK_SCORE + CNT_SPRING + CNT_MONEY_BAG + CNT_RSI + CNT_SWEEP + 
                   CNT_SMART_ACC + CNT_FUND_BREAK + CNT_BULL_BREAK + CNT_BIG + CNT_SPLUS + 
                   CNT_HUGE_VOL + CNT_TORNADO + CNT_NINJA + CNT_PZ_ANY + CNT_GL_IGNITE + 
                   CNT_WK_SPRING + CNT_KO_RED_TRIANGLE + CNT_FLOW_REAL_BUY + CNT_NX_BUY_SAFE + 
                   CNT_VSA_START + CNT_TF_FIRE + CNT_S19_GREEN + CNT_TFM_WIN + CNT_CLIMAX)
                  
    df['霸王總分'] = pd.Series(TOTAL_SCORE, index=df.index).fillna(-9999).astype(float)

    return df
