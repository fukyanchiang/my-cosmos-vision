import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="COSMOS 戰略指揮部 V42", layout="wide")

# --- 基礎工具函數 ---
def safe_n(val, alt=50.0):
    try:
        v = float(val)
        return v if not np.isnan(v) and not np.isinf(v) else alt
    except: return alt

def safe_s(info, keys, suffix="", alt="N/A"):
    for k in keys:
        v = info.get(k)
        if v is not None and v != "" and str(v).lower() not in ['nan', 'inf', 'none']: 
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

# --- 乖孫的美股版塊地圖 ---
US_SECTOR_MAP = {
    "太陽能 (TAN)": "TAN", "公用事業 (XLU)": "XLU", "油服 (OIH)": "OIH",
    "工業 (XLI)": "XLI", "必消 (XLP)": "XLP", "房地產 (XLRE)": "XLRE",
    "銀行 (KRE)": "KRE", "建築 (ITB)": "ITB", "半導體 (SMH)": "SMH",
    "能源 (XLE)": "XLE", "醫療 (XLV)": "XLV", "通訊 (XLC)": "XLC",
    "金融 (XLF)": "XLF", "可選消費 (XLY)": "XLY", "科技 (XLK)": "XLK",
    "生技 (IBB)": "IBB", "黃金礦工 (GDX)": "GDX"
}

# 2. 視覺裝修 (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 25px; }
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 20px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 5rem; font-weight: 900; }
    .ej-header { color: #00FFFF !important; font-size: 1.8rem; font-weight: 900; margin-bottom: 8px; }
    .bar-group-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .bar-triad { display: flex; gap: 3px; }
    .ej-seg { width: 16px; height: 35px; border-radius: 2px; border: 1.2px solid rgba(255,255,255,0.4); }
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; min-height: 200px; }
    .val-label { color: #FFFFFF !important; font-size: 1.6rem; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 12px; }
    .val-text { font-size: 1.3rem; color: #ccc; margin: 8px 0; }
    .val-focus { color: #FFD700; font-weight: bold; font-size: 1.8rem; }
    .red-bar { background-color: #FF4B4B; color: #fff; padding: 20px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 2.5rem; margin: 30px 0; border: 3px solid #fff; }
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700; font-weight: bold; font-size: 2.5rem; }
    .whale-a { color: #00FFCC; font-size: 1.6rem; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# 3. 側邊欄控制
st.sidebar.markdown("## 🛰️ 模式選擇")
app_mode = st.sidebar.selectbox("切換戰術視角", ["📡 版塊強勢熱力圖", "🚀 個股 DNA 深度透視"])

# --- 模式 A：版塊掃描 ---
if app_mode == "📡 版塊強勢熱力圖":
    st.markdown("<h1 class='main-title'>🛰️ 全美星系版塊能量分布</h1>", unsafe_allow_html=True)
    spy_data = yf.Ticker("SPY").history(period="60d")['Close']
    results = []
    with st.spinner('爺爺正在掃描全美版塊...'):
        for name, sym in US_SECTOR_MAP.items():
            try:
                d = yf.Ticker(sym).history(period="60d")['Close']
                if len(d) >= 20:
                    rs = 50 + ((d.iloc[-1]/d.iloc[-20]) - (spy_data.iloc[-1]/spy_data.iloc[-20])) * 100
                    results.append({"版塊": name, "RS強弱": round(rs, 1)})
            except: pass
    df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=False)
    fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["版塊"], orientation='h', marker=dict(color=df_rs["RS強弱"], colorscale='Portland')))
    fig.update_layout(template="plotly_dark", height=700)
    st.plotly_chart(fig, use_container_width=True)
    st.success(f"👴 爺爺提示：目前最強戰場在【{df_rs.iloc[0]['版塊']}】！")

# --- 模式 B：個股透視 ---
else:
    ticker = st.sidebar.text_input("🚀 輸入狙擊代號", "NVDA").upper()
    detect_btn = st.sidebar.button("📡 掃描趨勢爆發起點")
    
    try:
        asset = yf.Ticker(ticker); info = asset.info
        df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
        spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
        
        if not df.empty:
            curr_p = df['Close'].iloc[-1]
            # 核心計算
            c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
            slope, intercept = np.polyfit(days, c_tail, 1)
            v_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
            cx_val = safe_n(((slope * 252) / c_tail.mean() / v_ann) * 29, 50.0)
            crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])) * 100, 50.0)
            v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
            cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
            se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0)

            if detect_btn:
                if se_s > 85 and cej_s > 110: st.warning("🎯 偵測到【起步訊號】！趨勢剛啟動。")
                else: st.info("📡 尚未到達爆發起點。")

            st.markdown(f"<div class='main-title'>環球資產透維儀 [{ticker}]</div>", unsafe_allow_html=True)
            
            # 看板
            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X</div><div class='cosmos-value'>{cx_val:.1f}</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS</div><div class='cosmos-value'>{crs_val:.1f}</div></div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div class='cosmos-box' style='border-color:#00FFFF; padding: 20px;'>", unsafe_allow_html=True)
                st.markdown(draw_triad_bar(cej_s, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
                st.markdown(draw_triad_bar(se_s, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # DNA & 8D Bar
            st.write("---")
            d_c1, d_c2 = st.columns([1, 2.5])
            is_etf = info.get('quoteType') == 'ETF'
            real_roe = info.get('returnOnEquity')
            if is_etf or real_roe is None:
                dna_v = round(safe_n((cx_val * 0.5) + (crs_val * 0.5), 50.0), 1)
                m8 = {"🩸 資金流動": int(cej_s/10), "🛡️ 抗跌系統": int(crs_val/10), "🏗️ 動能頻率": int(cx_val/10), "🧬 趨勢潛力": int(se_s/10), "🧱 資產規模": 8, "⚡ 波幅底盤": 7, "💰 派息配置": 5, "📈 相對拐點": 6}
            else:
                dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)
                m8 = {"🩸 血液純度": int(safe_n(info.get('operatingMargins', 0)*30+3, 5)), "🛡️ 免疫系統": int(safe_n(real_roe*30+3, 7)), "🏗️ 心跳頻率": int(safe_n(info.get('revenueGrowth', 0)*20+4, 6)), "🧬 大腦潛力": int(safe_n(info.get('profitMargins', 0)*30+3, 8)), "🧱 骨架重量": int(max(1, 10 - safe_n(info.get('priceToBook', 5), 5))), "⚡ 物理底盤": 8 if safe_n(info.get('debtToEquity', 150), 150) < 80 else 3, "💰 資本配置": int(safe_n(info.get('dividendYield', 0)*200+2, 5)), "📈 經營拐點": int(safe_n(info.get('earningsGrowth', 0)*25+4, 8))}

            if dna_v >= 80: d_lv, d_desc = "第 2 級", "🌟 星系霸主"
            elif dna_v >= 50: d_lv, d_desc = "第 5 級", "⚖️ 凡骨平庸"
            else: d_lv, d_desc = "第 9 級", "☠️ 黑洞邊緣"

            with d_c1:
                st.markdown(f"<div class='cosmos-box' style='border-color:#FF4B4B; height:380px; display:flex; flex-direction:column; justify-content:center;'><div style='color:#FF4B4B; font-weight:900;'>🧬 DNA: {dna_v}</div><div style='color:#FFD700; font-size:1rem; font-weight:bold; margin-top:10px;'>[ 註明：共分 10 級，現屬 {d_lv} ]<br><span style='font-size:1.6rem; color:#FFF;'>{d_desc}</span></div></div>", unsafe_allow_html=True)
            with d_c2:
                st.markdown(f"**{ticker} ・ 8D 投行精確透視 BAR**")
                for i, (label, score) in enumerate(m8.items()):
                    sc = max(1, min(10, score))
                    grid = '<div class="energy-bar-container-8d">' + "".join([f'<div class="energy-seg-8d" style="background-color:#00FFCC; opacity:{"1" if j<=sc else "0.1"};"></div>' for j in range(1,11)]) + '</div>'
                    st.markdown(f"<div style='display:flex; justify-content:space-between; font-weight:bold;'><span>{label}</span><span>{sc}/10</span></div>{grid}", unsafe_allow_html=True)

            # 12M 目標與評級
            st.write(""); k1 = st.columns(4); k2 = st.columns(4)
            val_target_str = f"${info.get('targetMeanPrice'):.2f}" if info.get('targetMeanPrice') else "N/A"
            kings = [("📁 質量", f"{dna_v:.0f}"), ("📈 趨勢", f"{crs_val:.0f}"), ("⚡ 動能", f"{se_s:.0f}"), ("🔋 大資金", f"{cej_s:.0f}"), ("🎭 情緒", f"{(crs_val*0.9):.0f}"), ("🏆 總分", f"{(cx_val+crs_val+se_s)/3:.0f}"), ("🔮 12M目標", val_target_str), ("💰 成交比", f"{(v21/max(v252,1)):.1f}x")]
            for i in range(4):
                k1[i].markdown(f"<div class='cosmos-box' style='padding:15px; border-width:2px;'><div style='color:#ccc;'>{kings[i][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
                k2[i].markdown(f"<div class='cosmos-box' style='padding:15px; border-width:2px; border-color:#FFD700;'><div style='color:#ccc;'>{kings[i+4][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

            # 烈火鳳凰
            ttm_pe = info.get('trailingPE', 0) or 0
            if ttm_pe > 80 and not is_etf:
                dragon_index = round((dna_v * 0.4) + (cx_val * 0.3) + (crs_val * 0.3), 1)
                if dragon_index >= 80: t_lv, t_desc, val_title, val_color = "第 1 級", "極致真龍", "🔥 烈火鳳凰", "#BC13FE"
                elif dragon_index >= 40: t_lv, t_desc, val_title, val_color = "第 3 級", "中庸凡骨", "⚠️ 海市蜃樓", "#FFA500"
                else: t_lv, t_desc, val_title, val_color = "第 4 級", "高危泥鰍", "☠️ 末路狂花", "#FF4B4B"
                st.markdown(f"<div style='border: 4px solid {val_color}; border-radius: 15px; padding: 30px; background-color: #000; box-shadow: 0 0 30px {val_color}66; margin: 25px 0;'><span style='font-size:2rem; font-weight:900;'>COSMOS-VAL 解碼：<span style='color:{val_color};'>{val_title}</span></span><br><span style='font-size:1.1rem; color:#FFD700;'>[ 註明：共分 4 級，現屬 {t_lv} ({t_desc}) ]</span><br><span style='font-size:4rem; color:{val_color}; font-weight:900;'>{dragon_index}</span></div>", unsafe_allow_html=True)

            # 名家清單
            st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center;'>🧙 90 大名家：真實申報持倉</div>", unsafe_allow_html=True)
            holders = asset.institutional_holders
            if holders is not None and not holders.empty:
                for _, row in holders.head(8).iterrows():
                    calc_pct = (row.get('Shares', 0) / info.get('sharesOutstanding', 1))
                    st.markdown(f"<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>佔比 {calc_pct:.2%}</span></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    except Exception as e: st.error(f"系統診斷中: {e}")

# 4. 全局頁腳
st.markdown("<div style='text-align:center; color:#555;'>COSMOS V42.0 戰略指揮部 | 爺爺出品，必屬精品</div>", unsafe_allow_html=True)
