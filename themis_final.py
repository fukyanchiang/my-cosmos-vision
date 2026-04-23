import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="環球資產透維評估儀", layout="wide")

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

# 2. 視覺裝修
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
    .val-box-purple { border: 3px solid #BC13FE; border-radius: 15px; padding: 30px; background-color: #000; box-shadow: 0 0 25px #BC13FE66; margin: 25px 0; }
    .energy-bar-container-8d { display: flex; gap: 4px; margin-top: 10px; margin-bottom: 15px; }
    .energy-seg-8d { flex: 1; height: 16px; border-radius: 2px; }
    .whale-box { background-color: #000; border: 3px solid #FFD700; border-radius: 15px; padding: 35px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; }
    .whale-n { color: #FFD700; font-weight: bold; font-size: 2.5rem; }
    .whale-a { color: #00FFCC; font-size: 1.6rem; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("🚀 輸入資產代號", "6869.HK").upper()

try:
    asset = yf.Ticker(ticker); info = asset.info
    df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
    spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
    
    if not df.empty:
        curr_p = df['Close'].iloc[-1]
        
        # 🌌 COSMOS-X & RS (實時計法)
        c_tail = df['Close'].tail(125); days = np.arange(len(c_tail))
        slope, intercept = np.polyfit(days, c_tail, 1); pred = intercept + slope * len(days)
        mom = (curr_p / pred) if pred > 0 else 1.0; v_ann = max(0.001, c_tail.pct_change().std() * np.sqrt(252))
        cx_val = safe_n(((slope * 252) / c_tail.mean() / v_ann) * 29 * mom, 50.0)
        crs_val = safe_n(50 + ((curr_p / df['Close'].iloc[-63]) - (spy['Close'].iloc[-1] / spy['Close'].iloc[-63])) * 100, 50.0) if len(df) > 63 else 50.0
        
        v21 = df['Volume'].tail(21).mean(); v252 = df['Volume'].tail(252).mean()
        cej_s = safe_n((v21 / max(v252, 1)) * 100, 50.0)
        se_s = safe_n(50 + (((curr_p / df['Close'].iloc[-5]) - 1) * 1200), 50.0) if len(df) > 5 else 50.0

        st.markdown(f"""<div class='main-title'>環球資產透維評估儀 [{ticker}]</div>""", unsafe_allow_html=True)
        
        # 第一層看板
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"""<div class='cosmos-box'><div class='cosmos-label'>COSMOS-X (天體動能)</div><div class='cosmos-value'>{cx_val:.1f}</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class='cosmos-box' style='border-color:#FFD700;'><div class='cosmos-label'>COSMOS-RS (星系強弱)</div><div class='cosmos-value'>{crs_val:.1f}</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown("""<div class='cosmos-box' style='border-color:#00FFFF; padding: 20px;'>""", unsafe_allow_html=True)
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
            st.markdown(draw_triad_bar(cej_s, "EJ 錢流底氣", "#00FFFF"), unsafe_allow_html=True)
            st.markdown(draw_triad_bar(se_s, "短期能量 BAR", "#FF00FF"), unsafe_allow_html=True)
            st.markdown("""</div>""", unsafe_allow_html=True)

        # 🧬 [DNA & 8D Bar]
        st.write("---")
        d_c1, d_c2 = st.columns([1, 2.5])
        real_roe = info.get('returnOnEquity', 0)
        dna_v = round(safe_n(real_roe * 350 + 15, 23.6), 1)
        with d_c1:
            st.markdown(f"""<div class='cosmos-box' style='border-color:#FF4B4B; height:380px; display:flex; flex-direction:column; justify-content:center;'><div style='color:#FF4B4B; font-weight:900;'>🧬 COSMOS-DNA</div><div style='font-size:0.9rem; opacity:0.7; margin:10px 0;'>投行級股王基因 (100分滿分)</div><div style='font-size:6rem; font-weight:900;'>{dna_v}</div></div>""", unsafe_allow_html=True)
        with d_c2:
            st.markdown(f"""**{ticker} ・ 8D 投行精確透視 BAR**""")
            m8 = {"🩸 血液純度": int(safe_n(info.get('operatingMargins', 0)*30+3, 5)), "🛡️ 免疫系統": int(safe_n(real_roe*30+3, 7)), "🏗️ 心跳頻率": int(safe_n(info.get('revenueGrowth', 0)*20+4, 6)), "🧬 大腦潛力": int(safe_n(info.get('profitMargins', 0)*30+3, 8)), "🧱 骨架重量": int(max(1, 10 - safe_n(info.get('priceToBook', 5), 5))), "⚡ 物理底盤": 8 if safe_n(info.get('debtToEquity', 150), 150) < 80 else 3, "💰 資本配置": int(safe_n(info.get('dividendYield', 0)*200+2, 5)), "📈 經營拐點": int(safe_n(info.get('earningsGrowth', 0)*25+4, 8))}
            colors_8d = ["#00FFCC", "#00FFCC", "#00FFCC", "#00FFCC", "#FF4B4B", "#BC13FE", "#FFFFFF", "#FFD700"]
            for i, (label, score) in enumerate(m8.items()):
                sc = max(1, min(10, score))
                grid = '<div class="energy-bar-container-8d">' + "".join([f'<div class="energy-seg-8d" style="background-color:{colors_8d[i%8]}; opacity:{"1" if j<=sc else "0.1"};"></div>' for j in range(1,11)]) + '</div>'
                st.markdown(f"""<div style='display:flex; justify-content:space-between; font-weight:bold;'><span>{label}</span><span>{sc}/10</span></div>{grid}""", unsafe_allow_html=True)

        # 第二層評級
        st.write(""); k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", f"{dna_v:.0f}"), ("📈 趨勢", f"{crs_val:.0f}"), ("⚡ 動能", f"{se_s:.0f}"), ("🔋 大資金", f"{cej_s:.0f}"), ("🎭 情緒", f"{safe_n(crs_val*0.9, 50):.0f}"), ("🏆 總分", f"{(cx_val+crs_val+se_s)/3:.0f}"), ("🔮 2026目標", f"${info.get('targetMeanPrice', curr_p*1.35):.2f}"), ("💰 成交比", f"{(v21/max(v252,1)):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"""<div class='cosmos-box' style='padding:15px; border-width:2px;'><div style='color:#ccc; font-size:1.2rem;'>{kings[i][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i][1]}</div></div>""", unsafe_allow_html=True)
            k2[i].markdown(f"""<div class='cosmos-box' style='padding:15px; border-width:2px; border-color:#FFD700;'><div style='color:#ccc; font-size:1.2rem;'>{kings[i+4][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i+4][1]}</div></div>""", unsafe_allow_html=True)

        st.markdown(f"""<div class='red-bar'>🔥 戰略透視：短期動能爆發數值 [{se_s:.1f}%] 🔥</div>""", unsafe_allow_html=True)

        # 估值矩陣
        st.write("### 🏛️ 估值與風險全方位透視")
        v1, v2, v3 = st.columns(3); v4, v5, v6 = st.columns(3)
        def v_card(col, title, t_val, f_val, desc):
            col.markdown(f"""<div class='val-box'><div class='val-label'>{title}</div><div class='val-text'>TTM: <span class='val-focus'>{t_val}</span></div><div class='val-text'>2026預準: <span class='val-focus'>{f_val}</span></div><div style='color:#FFA500; font-size:0.9rem; margin-top:10px;'>{desc}</div></div>""", unsafe_allow_html=True)
        v_card(v1, "PE 獲利比", safe_s(info, ['trailingPE'], "x"), safe_s(info, ['forwardPE'], "x"), "獲利估值透視")
        v_card(v2, "PEG 增長比", safe_s(info, ['pegRatio']), "N/A", "增長性價比")
        v_card(v3, "PS 營收比", safe_s(info, ['priceToSalesTrailing12Months'], "x"), "N/A", "營收規模")
        v_card(v4, "PB 淨資產", safe_s(info, ['priceToBook'], "x"), "N/A", "賬面價值")
        v_card(v5, "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], "x"), "N/A", "企業估值")
        v_card(v6, "股息率", safe_s(info, ['dividendYield'], "%"), "N/A", "現金流回報")

        # 🔥 [修正: 真・烈火鳳凰指數] 🔥
        ttm_pe = info.get('trailingPE', 0) or 0
        if ttm_pe > 80:
            dragon_index = round(safe_n((cx_val * 0.4) + (crs_val * 0.4) + (info.get('revenueGrowth', 0) * 100), 55.5), 1)
            dragon_index = max(10.0, min(99.9, dragon_index)) 
            st.markdown(f"""<div class='val-box-purple'><div style='display:flex; justify-content:space-between; align-items:center;'><div><span style='font-size:2rem; font-weight:900;'>🔥 COSMOS-VAL 解碼：<span style='color:#BC13FE;'>烈火鳳凰</span></span><br><span style='font-size:1rem; opacity:0.8;'>（針對 TTM PE {ttm_pe:.2f}x 獨立戰術評分）</span></div><div style='text-align:right;'><span style='font-size:1.5rem;'>真龍指數：</span><br><span style='font-size:4rem; font-weight:900; color:#BC13FE;'>{dragon_index}</span></div></div></div>""", unsafe_allow_html=True)

        # Alpha/波動率 (防爆三重引號版)
        b_val = float(get_beta(info, df, spy))
        y1_r = (curr_p / df['Close'].iloc[-252] - 1) if len(df) > 252 else 0
        s_y1_r = (spy['Close'].iloc[-1] / spy['Close'].iloc[-252] - 1) if len(spy) > 252 else 0
        real_alpha = (y1_r - b_val * s_y1_r) * 100
        r1, r2, r3 = st.columns(3)
        r1.markdown(f"""<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>📐 Beta (性格)</div><div class='cosmos-value' style='font-size:3.5rem;'>{b_val:.2f}</div></div>""", unsafe_allow_html=True)
        r2.markdown(f"""<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🔱 Alpha (超額)</div><div class='cosmos-value' style='font-size:3.5rem;'>{real_alpha:.1f}%</div></div>""", unsafe_allow_html=True)
        r3.markdown(f"""<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🌊 波動率 (情緒)</div><div class='cosmos-value' style='font-size:3.5rem;'>{(v_ann*100):.1f}%</div></div>""", unsafe_allow_html=True)

        # 📊 股價圖
        st.write("### 📊 摩訶釋達・能量與籌碼透視圖")
        recent = df.tail(120); dates = recent.index.strftime('%Y-%m-%d')
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
        fig.add_trace(go.Candlestick(x=dates, open=recent['Open'], high=recent['High'], low=recent['Low'], close=recent['Close'], name='股價'), row=1, col=1)
        fig.add_trace(go.Bar(x=dates, y=recent['Volume'], marker_color=['#00FF00' if recent['Close'].iloc[i] >= recent['Open'].iloc[i] else '#FF0000' for i in range(len(recent))], name='成交量'), row=2, col=1)
        counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
        fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name='蟹貨', xaxis='x3', yaxis='y1'))
        fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, showlegend=False, xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), yaxis=dict(showgrid=True, gridcolor='#333'), yaxis2=dict(showgrid=False), xaxis3=dict(overlaying='x', side='top', range=[0, max(counts)*6], showgrid=False, showticklabels=False))
        st.plotly_chart(fig, use_container_width=True)

        # 名家清單
        st.markdown("""<div class='whale-box'><div style='color:#FFD700; font-size:2.2rem; font-weight:bold; text-align:center; margin-bottom:20px;'>🧙 90 大名家：真實申報持倉 (自動計算佔比)</div>""", unsafe_allow_html=True)
        total_shares = info.get('sharesOutstanding', 1)
        holders = asset.institutional_holders
        if holders is not None and not holders.empty and 'Holder' in holders.columns:
            for _, row in holders.head(8).iterrows():
                shares = row.get('Shares', 0)
                calc_pct = (shares / total_shares) if total_shares > 1 else 0
                val_m = row.get('Value', 0) / 1e6
                st.markdown(f"""<div class='whale-row'><span class='whale-n'>{row['Holder']}</span><span class='whale-a'>持有 {shares:,.0f} 股 | 佔比 {calc_pct:.2%} | 市值 ${val_m:.1f}M</span></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style='text-align:center; color:#888; padding:20px;'>此資產暫無公開機構申報數據</div>""", unsafe_allow_html=True)
        st.markdown("""</div>""", unsafe_allow_html=True)

except Exception as e: st.error(f"數據診斷中: {e}")
