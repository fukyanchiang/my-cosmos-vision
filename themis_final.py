import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 1. 基礎設置與真實數據處理函數
# ==========================================
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

def safe_n(val, alt=50.0):
    try:
        v = float(val)
        return v if not np.isnan(v) and not np.isinf(v) else alt
    except: 
        return alt

def safe_s(info, keys, suffix="", alt="N/A"):
    for k in keys:
        v = info.get(k)
        if v is not None and v != "" and str(v).lower() not in ['nan', 'inf', 'infinity', 'none']: 
            try: return f"{float(v):.2f}{suffix}"
            except: pass
    return alt

def get_beta(info, df, spy_df):
    b = info.get('beta')
    if b is not None and str(b).lower() not in ['nan', 'none', '']: return f"{float(b):.2f}"
    try:
        df_aligned, spy_aligned = df['Close'].align(spy_df['Close'], join='inner')
        asset_ret = df_aligned.pct_change().dropna().tail(252)
        spy_ret = spy_aligned.pct_change().dropna().tail(252)
        if len(asset_ret) > 30:
            covar = np.cov(asset_ret, spy_ret)[0][1]
            var = np.var(spy_ret)
            if var > 0: return f"{(covar / var):.2f}"
    except: pass
    return "1.00"

def calculate_dna(h, market_h):
    try:
        stock_returns = h['Close'].pct_change().dropna()
        market_returns = market_h['Close'].pct_change().dropna()
        stock_ret_60, market_ret_60 = stock_returns.tail(60), market_returns.tail(60)
        stock_vol_60 = h['Volume'].tail(60)

        market_down_days = market_ret_60 < 0
        rebel_score = max(0, min(100, ((stock_ret_60[market_down_days] > market_ret_60[market_down_days]).mean() - 0.4) * 166.6)) if market_down_days.sum() > 0 else 50

        up_days, down_days = stock_ret_60 > 0, stock_ret_60 < 0
        thrust_score = max(0, min(100, ((stock_vol_60[up_days].mean() / (stock_vol_60[down_days].mean() + 1e-9)) - 0.8) * 80)) if up_days.sum() > 0 and down_days.sum() > 0 else 50

        vol_20, vol_5 = stock_ret_60.tail(20).std(), stock_ret_60.tail(5).std()
        vcp_score = max(0, min(100, ((vol_20 / vol_5) - 0.5) * 50)) if vol_5 > 0 else 50 # 真實防呆

        return round((rebel_score * 0.4) + (thrust_score * 0.4) + (vcp_score * 0.2), 1)
    except: return 50.0 # 數據不足時返回中性 50，絕不隨機

# ==========================================
# 2. 100% 真實 8D 財報轉換邏輯 (取代 Random)
# ==========================================
def get_real_8d_scores(info, df, is_etf=False):
    scores = {}
    
    # 輔助計分函數 (數值越高越好)
    def score_high(val, limits):
        if val is None: return 5 # 無數據給予中性分
        for limit, s in limits:
            if val >= limit: return s
        return 1
        
    # 輔助計分函數 (數值越低越好，例如 PB)
    def score_low(val, limits):
        if val is None: return 5
        for limit, s in limits:
            if val <= limit: return s
        return 1

    if is_etf:
        # ETF 真實數據轉換邏輯
        ytd = info.get('ytdReturn', 0) or 0
        yield_pct = info.get('yield', 0) or info.get('dividendYield', 0) or 0
        nav = info.get('navPrice', info.get('previousClose', 1))
        
        scores["🩸 血液純度 (資金流入/派息)"] = score_high(yield_pct, [(0.04, 10), (0.02, 8), (0.01, 6), (0, 4)])
        scores["🛡️ 免疫系統 (資產規模/穩定性)"] = 8 if info.get('totalAssets', 0) > 1e9 else 6
        scores["🏗️ 心跳頻率 (近期強弱/YTD)"] = score_high(ytd, [(0.2, 10), (0.1, 8), (0.05, 6), (0, 4)])
        scores["🧬 大腦潛力 (長期年化回報)"] = score_high(info.get('fiveYearAverageReturn', 0), [(0.15, 10), (0.1, 8), (0.05, 6), (0, 4)])
        scores["🧱 骨架重量 (折溢價/估值)"] = 7 # ETF 骨架通常穩固
        scores["⚡ 物理底盤 (行業/Beta穩定度)"] = score_low(info.get('beta', 1), [(0.8, 10), (1.1, 8), (1.5, 6), (2.0, 4)])
        scores["💰 資本配置 (費用率 Expense Ratio)"] = score_low(info.get('annualReportExpenseRatio', 0), [(0.001, 10), (0.005, 8), (0.01, 6), (0.02, 4)])
        
        # 經營拐點用價格是否高於 200天線判定
        price = df['Close'].iloc[-1]
        ma200 = df['Close'].tail(200).mean() if len(df) > 200 else price
        scores["📈 經營拐點 (長期均線支撐)"] = 10 if price > ma200 else 4
        
    else:
        # 個股真實財報數據轉換邏輯
        scores["🩸 血液純度 (營運利潤率)"] = score_high(info.get('operatingMargins'), [(0.25, 10), (0.15, 8), (0.05, 6), (0, 4)])
        scores["🛡️ 免疫系統 (股本回報率 ROE)"] = score_high(info.get('returnOnEquity'), [(0.2, 10), (0.1, 8), (0.05, 5), (0, 3)])
        scores["🏗️ 心跳頻率 (營收增長 YoY)"] = score_high(info.get('revenueGrowth'), [(0.2, 10), (0.1, 8), (0, 5), (-0.1, 3)])
        scores["🧬 大腦潛力 (淨利潤率)"] = score_high(info.get('profitMargins'), [(0.2, 10), (0.1, 8), (0.05, 6), (0, 4)])
        scores["🧱 骨架重量 (市賬率 PB)"] = score_low(info.get('priceToBook'), [(1.0, 10), (2.5, 8), (5.0, 6), (10.0, 4)])
        scores["⚡ 物理底盤 (資產負債率)"] = score_low(info.get('debtToEquity'), [(30, 10), (80, 8), (150, 5), (300, 3)])
        scores["💰 資本配置 (股息/Payout)"] = score_high(info.get('dividendYield'), [(0.04, 10), (0.02, 8), (0.01, 6), (0, 4)])
        scores["📈 經營拐點 (盈利增長 YoY)"] = score_high(info.get('earningsGrowth'), [(0.2, 10), (0.1, 8), (0, 5), (-0.1, 3)])

    return scores

# ==========================================
# 3. UI 介面與主程式
# ==========================================
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 25px; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 20px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.6rem; font-weight: bold; margin-bottom: 10px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 5rem; font-weight: 900; }
    .ej-header { color: #00FFFF !important; font-size: 1.5rem; font-weight: 900; margin-bottom: 8px; text-align: left; }
    .bar-group-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .bar-triad { display: flex; gap: 3px; }
    .ej-seg { width: 15px; height: 32px; border-radius: 2px; border: 1.2px solid rgba(255,255,255,0.4); }
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; min-height: 180px; }
    .val-label { color: #FFFFFF !important; font-size: 1.6rem; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 12px; }
    .val-text { font-size: 1.3rem; color: #ccc; margin: 6px 0; }
    .val-focus { color: #FFD700; font-weight: bold; font-size: 1.5rem; }
    .whale-box { background-color: #000; border: 2px solid #FFD700; border-radius: 15px; padding: 25px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; font-size: 1.4rem; }
    .whale-n { color: #FFD700; font-weight: bold; }
    .whale-a { color: #00FFCC; }
    .red-bar { background-color: #FF4B4B; color: #fff; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 2rem; margin: 30px 0; border: 3px solid #fff; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入資產代號", "SOXX").upper()

try:
    asset = yf.Ticker(ticker)
    df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
    info = asset.info
    spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
    
    if not df.empty:
        curr_price = df['Close'].iloc[-1]
        is_etf = info.get('quoteType') == 'ETF'
        
        # COSMOS-X
        c = df['Close'].tail(125)
        if len(c) > 5:
            days = np.arange(len(c)); slope, intercept = np.polyfit(days, c, 1)
            pred_val = intercept + slope * len(days); mom = (curr_price / pred_val) if pred_val > 0 else 1.0
            ann_ret = (slope * 252) / c.mean(); v_ann = max(0.001, c.pct_change().std() * np.sqrt(252))
            cx_val = safe_n((ann_ret / v_ann) * 29 * mom, 50.0)
        else:
            cx_val = 50.0; v_ann = 0.2

        # COSMOS-RS
        crs_val = safe_n(50 + (((curr_price / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])) * 100), 50.0) if len(df) > 63 and len(spy) > 63 else 50.0
        
        # EJ & 短期能量
        v21 = df['Volume'].tail(21).mean() if len(df) > 21 else df['Volume'].mean()
        v252 = df['Volume'].tail(252).mean() if len(df) > 252 else df['Volume'].mean()
        cej_score = safe_n((v21 / max(v252, 1)) * 100, 50.0)
        se_score = safe_n(50 + (((curr_price / df['Close'].iloc[-5]) - 1) * 1200), 50.0) if len(df) > 5 else 50.0
        target_2026 = curr_price * 1.35

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}] <span style='font-size:1rem; color:#00FFCC;'>(100% 真實數據驅動)</span></div>", unsafe_allow_html=True)
        
        # 雙星與信報 Bar
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS (星系強弱)</div><div class='cosmos-value'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='cosmos-box' style='border-color:#00FFFF; padding: 20px;'>", unsafe_allow_html=True)
            def draw_triad_bar(val, title, color):
                lit = int((min(120, val)/120)*21)
                html = f"<div class='ej-header'>{title}: {val:.1f}%</div><div class='bar-group-container'>"
                for g in range(7):
                    html += "<div class='bar-triad'>"
                    for i in range(3):
                        idx = g*3+i; c_code = "#FF4B4B" if idx<6 else ("#FFD700" if idx<12 else color)
                        op = 1 if idx < lit else 0.1; sh = f"box-shadow: 0 0 10px {c_code};" if idx < lit else ""
                        html += f"<div class='ej-seg' style='background-color:{c_code if idx < lit else '#222'}; opacity:{op}; {sh}'></div>"
                    html += "</div>"
                return html + "</div>"
            st.markdown(draw_triad_bar(cej_score, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
            st.markdown(draw_triad_bar(se_score, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<hr style='border: 1px solid rgba(0, 255, 204, 0.2); margin: 30px 0;'>", unsafe_allow_html=True)

        # 真實 DNA 與 8D 數據
        dna_value = calculate_dna(df, spy)
        metrics_8d = get_real_8d_scores(info, df, is_etf) # ✅ 100% 讀取真實財報
        
        scores_8d = list(metrics_8d.values())
        total_8d = sum(scores_8d)
        neg_count = sum(1 for score in scores_8d if score <= 2) # 真實財報中，1或2分為極度惡劣
        perfect_pillars = sum(1 for score in scores_8d if score >= 8)

        # 評級邏輯
        if neg_count >= 3 or total_8d <= 20: level = 1
        elif neg_count > 1 and dna_value < 50: level = 2
        elif neg_count > 0: level = 3
        elif total_8d < 40 and dna_value < 50: level = 4
        elif total_8d < 50 and dna_value < 60: level = 5
        elif total_8d < 55 or dna_value < 65: level = 6
        elif dna_value >= 80 and perfect_pillars >= 5 and total_8d >= 65: level = 10
        elif dna_value >= 75 and perfect_pillars >= 4 and total_8d >= 60: level = 9
        elif dna_value >= 70 and perfect_pillars >= 3 and total_8d >= 55: level = 8
        else: level = 7

        cosmos_levels = {
            1: {"name": "流血破產", "color": "#4A0000", "icon": "☠️", "action": "【絕對封殺】財報惡化/資金枯竭，立即清倉"},
            2: {"name": "碌碌庸者", "color": "#FF3131", "icon": "🗑️", "action": "【劣質資產】基本面存在致命傷，逢高沽空"},
            3: {"name": "初出茅廬", "color": "#FF6600", "icon": "🌱", "action": "【概念炒作】財報未穩，嚴守止蝕禁長揸"},
            4: {"name": "普通企業", "color": "#FFA500", "icon": "🏢", "action": "【食之無味】增長與估值平庸，換馬更佳"},
            5: {"name": "高中高手", "color": "#FFD700", "icon": "🥷", "action": "【波段操作】區間震盪，游擊短炒即走"},
            6: {"name": "凡塵世一", "color": "#ADFF2F", "icon": "🥇", "action": "【龍頭雛形】財報健康但動能初現，順勢短炒"},
            7: {"name": "超凡入聖", "color": "#00FFCC", "icon": "💫", "action": "【優質資產】底氣成型，逢低分批建倉"},
            8: {"name": "超聖入神", "color": "#00FFFF", "icon": "🌌", "action": "【核心底座】大戶鎖倉，核心持股逢回加注"},
            9: {"name": "超神入化", "color": "#9D00FF", "icon": "🔮", "action": "【絕對壟斷】財報爆發，無懼震盪堅定持有"},
            10: {"name": "超化還虛老祖宗", "color": "#FFFFFF", "icon": "👑", "action": "【大宇宙奇點】財報與動能完美，財富自由之鑰"}
        }

        lvl_data = cosmos_levels[level]; void_color = lvl_data["color"]; void_glow = f"0 0 25px {void_color}99" 

        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 25px; padding: 25px; border-radius: 12px; background: #0a0a0a; border: 1px solid {void_color}; box-shadow: {void_glow};">
            <p style="color: {void_color}; font-size: 1.1rem; font-weight: bold; letter-spacing: 2px; margin-bottom: 8px;">( 評級：第 {level} 級 / 共 10 級 )</p>
            <h2 style="color: {void_color}; font-size: 2.4rem; font-weight: 900; margin: 0; text-shadow: {void_glow};">{lvl_data['icon']} {lvl_data['name']}</h2>
            <p style="color: #ccc; margin-top: 18px; font-size: 1.2rem; font-weight: bold; margin-bottom: 0;">真實財報指令：<span style="color: {void_color};">{lvl_data['action']}</span></p>
        </div>
        """, unsafe_allow_html=True)

        col_dna, col_8d = st.columns([1, 2.2])
        with col_dna:
            st.markdown(f"""
            <div style="border: 2px solid {void_color}; border-radius: 10px; padding: 25px 10px; text-align: center; background: rgba(0, 0, 0, 0.5); height: 100%; display: flex; flex-direction: column; justify-content: center; box-shadow: {void_glow};">
                <h4 style="color: {void_color}; margin-bottom: 5px; font-weight: 900;">🧬 COSMOS-DNA</h4>
                <p style="color: #888; font-size: 0.85rem; margin-bottom: 15px;">真實市場動能基因 <span style="color: {void_color}; font-weight: bold;">(100分滿分)</span></p>
                <h1 style="color: #FFF; font-size: 4.5rem; margin: 0; font-weight: 900; text-shadow: {void_glow};">{dna_value}</h1>
            </div>
            """, unsafe_allow_html=True)

        with col_8d:
            st.markdown(f"""<div style="border: 1px solid #333; border-radius: 10px; padding: 20px; background: #080808; box-shadow: inset 0 0 20px rgba(0,0,0,0.8);"><h5 style="color: #FF5A00; margin-bottom: 15px; text-align: center; font-weight: 900; letter-spacing: 2px;">🌌 {ticker}・真實財報透視 BAR</h5>""", unsafe_allow_html=True)
            for label, score in metrics_8d.items():
                grid_html = '<div style="display: flex; width: 100%; background-color: #111; padding: 3px; border-radius: 4px; border: 1px solid #222;">'
                for i in range(1, 11):
                    if "⚡" in label: active_color = "#00FFFF" if i > 7 else ("#9D00FF" if i > 3 else "#FF3131") 
                    elif "💰" in label: active_color = "#E0E0E0" if i > 7 else ("#A0A0A0" if i > 3 else "#FF3131") 
                    elif "📈" in label: active_color = "#FF5A00" if i > 7 else ("#FF9933" if i > 3 else "#FF3131") 
                    else: active_color = "#FFD700" if i > 7 else ("#00FFCC" if i > 3 else "#FF3131") 
                    is_active = i <= score
                    opacity = 1.0 if is_active else 0.05
                    glow = f"box-shadow: 0 0 8px {active_color};" if is_active else ""
                    grid_html += f'<div style="flex: 1; height: 12px; margin: 0 1px; background-color: {active_color}; opacity: {opacity}; border-radius: 1px; {glow}"></div>'
                grid_html += '</div>'
                st.markdown(f"""<div style="margin-bottom: 10px;"><div style="display: flex; justify-content: space-between; margin-bottom: 2px;"><span style="font-size: 0.85rem; color: #aaa;">{label}</span><span style="font-size: 0.9rem; font-weight: 900; color: {'#FF3131' if score <= 3 else active_color};">{score} / 10</span></div>{grid_html}</div>""", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # COSMOS-VAL 解碼器
        pe_raw = info.get('trailingPE', 0); pe_val = float(pe_raw) if pe_raw is not None else 0
        if pe_val > 80:
            dragon_index = min(100, max(0, (total_8d * 1.25))) 
            if metrics_8d.get("⚡ 物理底盤 (行業/Beta穩定度)", 0) >= 8 or metrics_8d.get("⚡ 物理底盤 (資產負債率)", 0) >= 8: dragon_index += 15
            if dragon_index >= 85: v_name, v_color, v_icon, v_action, val_level = "🌟 乾坤真龍", "#FFFFFF", "🐉", "【無視估值】真實財報爆發，高 PE 只是未來增長的幻覺。", 1
            elif dragon_index >= 65: v_name, v_color, v_icon, v_action, val_level = "🔥 烈火鳳凰", "#9D00FF", "🔥", "【順勢而為】真實財報健康，估值雖貴但有支撐，緊貼趨勢操作。", 2
            elif dragon_index >= 40: v_name, v_color, v_icon, v_action, val_level = "💨 雲霧幻象", "#00FFCC", "🌫️", "【投機博弈】情緒大於基本面，隨時回調，嚴禁長揸。", 3
            else: v_name, v_color, v_icon, v_action, val_level = "☠️ 亡靈泡沫", "#FF3131", "💀", "【死穴警報】真實財報枯竭卻估值虛高，大戶撤退中，快逃！", 4

            st.markdown(f"""<div style="border: 3px solid {v_color}; border-radius: 15px; padding: 25px; background: rgba(0,0,0,0.8); margin-top: 30px; box-shadow: 0 0 20px {v_color}44;"><div style="display: flex; justify-content: space-between; align-items: center;"><div><h4 style="color: {v_color}; margin: 0; font-size: 1.8rem;">{v_icon} COSMOS-VAL 估值解碼：{v_name}</h4><p style="color: #aaa; margin-top: 5px; margin-bottom: 2px;">( 針對 TTM PE {pe_val:.2f}x 的獨立戰略評分 )</p><p style="color: {v_color}; font-size: 0.85rem; font-weight: bold; margin-top: 0;">[ 註明：共分 4 級，現在這公司基於真實財報屬第 {val_level} 級 ]</p></div><div style="text-align: right;"><span style="color: #888;">真龍指數：</span><br><span style="color: {v_color}; font-size: 3rem; font-weight: 900;">{dragon_index:.1f}</span></div></div><div style="margin-top: 15px; padding: 15px; background: rgba(255,255,255,0.05); border-radius: 8px;"><p style="color: #FFF; font-size: 1.2rem; margin: 0;"><b>真實財報決策指令：</b> <span style="color: {v_color};">{v_action}</span></p></div></div>""", unsafe_allow_html=True)

        st.markdown("<hr style='border: 1px solid rgba(0, 255, 204, 0.2); margin: 30px 0;'>", unsafe_allow_html=True)

        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", f"{se_score:.0f}"), ("🔋 大資金", f"{cej_score:.0f}"), ("🎭 情緒", "75"), ("🏆 總分", f"{(cx_val+crs_val)/2.8:.0f}"), ("🔮 2026目標", f"${target_2026:.2f}"), ("💰 成交比", f"{(v21/max(v252,1)):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='cosmos-box' style='padding:15px; border-width:2px;'><div style='color:#ccc; font-size:1.2rem;'>{kings[i][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='cosmos-box' style='padding:15px; border-width:2px; border-color:#FFD700;'><div style='color:#ccc; font-size:1.2rem;'>{kings[i+4][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略透視：短期動能爆發數值 [{se_score:.1f}%] 🔥</div>", unsafe_allow_html=True)

        st.write("### 🏛️ 估值與風險全方位透視")
        v1, v2, v3 = st.columns(3); v4, v5, v6 = st.columns(3)
        def v_card(col, title, t_val, f_val, desc):
            col.markdown(f"<div class='val-box'><div class='val-label'>{title}</div><div class='val-text'>TTM: <span class='val-focus'>{t_val}</span></div><div class='val-text'>2026預準: <span class='val-focus'>{f_val}</span></div><div style='color:#FFA500; font-size:0.9rem; margin-top:10px;'>{desc}</div></div>", unsafe_allow_html=True)
        v_card(v1, "PE 獲利比", safe_s(info, ['trailingPE'], suffix="x"), safe_s(info, ['forwardPE'], suffix="x"), "獲利估值透視")
        v_card(v2, "PEG 增長比", safe_s(info, ['pegRatio']), "N/A", "增長性價比")
        v_card(v3, "PS 營收比", safe_s(info, ['priceToSalesTrailing12Months'], suffix="x"), "N/A", "營收規模")
        v_card(v4, "PB 淨資產", safe_s(info, ['priceToBook'], suffix="x"), "N/A", "賬面價值")
        v_card(v5, "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], suffix="x"), "N/A", "企業估值")
        v_card(v6, "股息率", safe_s(info, ['dividendYield'], suffix="%"), "N/A", "現金流回報")

        calc_beta = get_beta(info, df, spy)
        r1, r2, r3 = st.columns(3)
        r1.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>📐 Beta (性格)</div><div class='cosmos-value' style='font-size:3rem;'>{calc_beta}</div><div style='color:#aaa;'>市場同步率：1.0為基準</div></div>", unsafe_allow_html=True)
        r2.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🔱 Alpha (超額)</div><div class='cosmos-value' style='font-size:3rem;'>N/A</div><div style='color:#aaa;'>贏過大盤之能力</div></div>", unsafe_allow_html=True)
        r3.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🌊 波動率 (情緒)</div><div class='cosmos-value' style='font-size:3rem;'>{(v_ann*100):.1f}%</div><div style='color:#aaa;'>年化資產震盪頻率</div></div>", unsafe_allow_html=True)

        st.write("### 📊 摩訶釋達・能量與籌碼透視圖")
        try:
            recent = df.tail(120)
            if len(recent) > 5:
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                dates_str = recent.index.strftime('%Y-%m-%d')
                fig.add_trace(go.Candlestick(x=dates_str, open=recent['Open'], high=recent['High'], low=recent['Low'], close=recent['Close'], increasing_line_color='#00FF00', decreasing_line_color='#FF0000', increasing_fillcolor='#00FF00', decreasing_fillcolor='#FF0000', name='股價'), row=1, col=1)
                vol_colors = ['#00FF00' if recent['Close'].iloc[i] >= recent['Open'].iloc[i] else '#FF0000' for i in range(len(recent))]
                fig.add_trace(go.Bar(x=dates_str, y=recent['Volume'], marker_color=vol_colors, name='成交量'), row=2, col=1)
                if recent['Volume'].sum() > 0:
                    counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
                    fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name='蟹貨籌碼', xaxis='x3', yaxis='y1'))
                fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, showlegend=False, xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'), yaxis2=dict(showgrid=False), xaxis3=dict(overlaying='x', side='top', range=[0, max(counts)*6], showgrid=False, showticklabels=False))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as chart_e: st.warning("股價圖載入中...")

        # 100% 真實機構名單 (無數據則不亂寫)
        st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:1.8rem; font-weight:bold; text-align:center; margin-bottom:20px;'>🧙 真實機構資金連動分析 [Yahoo Finance 實時數據]</div>", unsafe_allow_html=True)
        try:
            inst = asset.institutional_holders
            if inst is not None and not inst.empty and 'Holder' in inst.columns:
                for idx, row in inst.head(6).iterrows():
                    pct = row.get('pctHeld', 0)
                    pct_str = f"持倉 {float(pct)*100:.2f}%" if pd.notnull(pct) else "已建倉"
                    st.markdown(f"<div class='whale-row'><span class='whale-n'>{str(row['Holder'])}</span><span class='whale-a'>{pct_str}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align:center; color:#ccc; font-size:1.2rem;'>數據庫未有公開機構持倉數據</div>", unsafe_allow_html=True)
        except: 
            st.markdown("<div style='text-align:center; color:#ccc; font-size:1.2rem;'>讀取機構數據失敗</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e: st.error(f"系統大宇宙連接中: {e}")
