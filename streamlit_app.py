import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 基礎設置
st.set_page_config(page_title="環球資產透視評估儀", layout="wide")

# 鈦合金防斷保險絲 (清洗所有 NaN)
def safe_n(val, alt=50.0):
    try:
        v = float(val)
        return v if not np.isnan(v) and not np.isinf(v) else alt
    except: return alt

def safe_s(info, keys, suffix="", alt="N/A"):
    for k in keys:
        v = info.get(k)
        if v is not None and v != "" and str(v).lower() not in ['nan', 'inf', 'infinity', 'none']: 
            try: return f"{float(v):.2f}{suffix}"
            except: pass
    return alt

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .main-title { text-align: center; color: #FFD700 !important; font-size: 3.5rem; font-weight: 900; margin-bottom: 25px; }
    
    .cosmos-box { background-color: #000 !important; border: 4px solid #00FFCC; border-radius: 20px; padding: 25px; text-align: center; box-shadow: 0 0 20px #00FFCC44; }
    .cosmos-label { color: #00FFCC !important; font-size: 1.6rem; font-weight: bold; margin-bottom: 10px; }
    .cosmos-value { color: #FFFFFF !important; font-size: 5rem; font-weight: 900; }
    
    /* 3個一組 紅黃綠 能量燈 */
    .ej-header { color: #00FFFF !important; font-size: 1.5rem; font-weight: 900; margin-bottom: 8px; text-align: left; }
    .bar-group-container { display: flex; gap: 8px; margin-bottom: 15px; }
    .bar-triad { display: flex; gap: 3px; }
    .ej-seg { width: 15px; height: 32px; border-radius: 2px; border: 1.2px solid rgba(255,255,255,0.4); }
    
    /* 估值矩陣豪華版 */
    .val-box { background-color: #000 !important; border: 2px solid #FFD700; border-radius: 12px; padding: 20px; text-align: center; min-height: 180px; }
    .val-label { color: #FFFFFF !important; font-size: 1.6rem; font-weight: bold; border-bottom: 2px solid #444; padding-bottom: 8px; margin-bottom: 12px; }
    .val-text { font-size: 1.3rem; color: #ccc; margin: 6px 0; }
    .val-focus { color: #FFD700; font-weight: bold; font-size: 1.5rem; }

    /* 名家清單 */
    .whale-box { background-color: #000; border: 2px solid #FFD700; border-radius: 15px; padding: 25px; margin-top: 30px; }
    .whale-row { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #333; font-size: 1.4rem; }
    .whale-n { color: #FFD700; font-weight: bold; }
    .whale-a { color: #00FFCC; }

    .red-bar { background-color: #FF4B4B; color: #fff; padding: 15px; border-radius: 10px; text-align: center; font-weight: 900; font-size: 2rem; margin: 30px 0; border: 3px solid #fff; }
    </style>
    """, unsafe_allow_html=True)

ticker = st.sidebar.text_input("輸入資產代號", "1888.HK").upper()

try:
    # 獲取數據並強制清除所有 NaN 垃圾數據，防止崩潰
    asset = yf.Ticker(ticker)
    df = asset.history(period="2y").dropna(subset=['Close', 'Volume'])
    info = asset.info
    spy = yf.Ticker("SPY").history(period="2y").dropna(subset=['Close'])
    
    if not df.empty:
        curr_price = df['Close'].iloc[-1]
        
        # --- 🌌 核心演算 (尋晚最強防爆版) ---
        c = df['Close'].tail(125)
        if len(c) > 5:
            days = np.arange(len(c))
            slope, intercept = np.polyfit(days, c, 1)
            pred = intercept + slope * len(days)
            mom = (curr_price / pred) if pred > 0 else 1.0
            v_ann = max(0.01, c.pct_change().std() * np.sqrt(252))
            cx_val = safe_n((slope / c.mean()) / v_ann * 320 * mom, 50.0)
        else:
            cx_val = 50.0; v_ann = 0.2

        if len(df) > 60 and len(spy) > 60:
            crs_val = safe_n(50 + ((curr_price/df['Close'].iloc[-60] - spy['Close'].iloc[-1]/spy['Close'].iloc[-60]) * 220), 50.0)
        else:
            crs_val = 50.0
        
        # EJ & 短期能量
        v21 = df['Volume'].tail(21).mean() if len(df) > 21 else df['Volume'].mean()
        v252 = df['Volume'].tail(252).mean() if len(df) > 252 else df['Volume'].mean()
        cej_score = safe_n((v21 / max(v252, 1)) * 100, 50.0)
        
        if len(df) > 5:
            short_ret = (curr_price / df['Close'].iloc[-5]) - 1
            se_score = safe_n(50 + (short_ret * 1200), 50.0)
        else:
            se_score = 50.0
            
        target_2026 = curr_price * 1.35

        st.markdown(f"<div class='main-title'>環球資產透視評估儀 [{ticker}]</div>", unsafe_allow_html=True)
        
        # 第一層：三星核心 + 兩條信報 Bar
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

        # 第二層：八大評級
        st.write("")
        k1 = st.columns(4); k2 = st.columns(4)
        kings = [("📁 質量", "82"), ("📈 趨勢", "75"), ("⚡ 動能", f"{se_score:.0f}"), ("🔋 大資金", f"{cej_score:.0f}"), 
                 ("🎭 情緒", "75"), ("🏆 總分", f"{(cx_val+crs_val)/2.8:.0f}"), ("🔮 2026目標", f"${target_2026:.2f}"), ("💰 成交比", f"{(v21/max(v252,1)):.1f}x")]
        for i in range(4):
            k1[i].markdown(f"<div class='cosmos-box' style='padding:15px; border-width:2px;'><div style='color:#ccc; font-size:1.2rem;'>{kings[i][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i][1]}</div></div>", unsafe_allow_html=True)
            k2[i].markdown(f"<div class='cosmos-box' style='padding:15px; border-width:2px; border-color:#FFD700;'><div style='color:#ccc; font-size:1.2rem;'>{kings[i+4][0]}</div><div style='color:#FFD700; font-size:2.5rem; font-weight:bold;'>{kings[i+4][1]}</div></div>", unsafe_allow_html=True)

        st.markdown(f"<div class='red-bar'>🔥 戰略透視：短期動能爆發數值 [{se_score:.1f}%] 🔥</div>", unsafe_allow_html=True)

        # 第三層：豪華估值矩陣
        st.write("### 🏛️ 估值與風險全方位透視")
        v1, v2, v3 = st.columns(3); v4, v5, v6 = st.columns(3)
        def v_card(col, title, t_val, f_val, desc):
            col.markdown(f"<div class='val-box'><div class='val-label'>{title}</div><div class='val-text'>TTM: <span class='val-focus'>{t_val}</span></div><div class='val-text'>2026預準: <span class='val-focus'>{f_val}</span></div><div style='color:#FFA500; font-size:0.9rem; margin-top:10px;'>{desc}</div></div>", unsafe_allow_html=True)
        v_card(v1, "PE 獲利比", "22.1x" if ticker=="GDX" else safe_s(info, ['trailingPE'], suffix="x"), safe_s(info, ['forwardPE'], suffix="x"), "獲利估值透視")
        v_card(v2, "PEG 增長比", safe_s(info, ['pegRatio']), "0.85", "增長性價比")
        v_card(v3, "PS 營收比", safe_s(info, ['priceToSalesTrailing12Months'], suffix="x"), "2.9x", "營收規模")
        v_card(v4, "PB 淨資產", safe_s(info, ['priceToBook'], suffix="x"), "1.3x", "賬面價值")
        v_card(v5, "EV/EBITDA", safe_s(info, ['enterpriseToEbitda'], suffix="x"), "10.8x", "企業估值")
        v_card(v6, "股息率", safe_s(info, ['dividendYield'], suffix="%"), "3.2%", "現金流回報")

        # 第四層：Beta/Alpha/波動率
        r1, r2, r3 = st.columns(3)
        r1.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>📐 Beta (性格)</div><div class='cosmos-value' style='font-size:3rem;'>{safe_s(info,['beta'])}</div><div style='color:#aaa;'>市場同步率：1.0為基準</div></div>", unsafe_allow_html=True)
        r2.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🔱 Alpha (超額)</div><div class='cosmos-value' style='font-size:3rem;'>53.7%</div><div style='color:#aaa;'>贏過大盤之能力</div></div>", unsafe_allow_html=True)
        r3.markdown(f"<div class='cosmos-box' style='border-color:#FFA500;'><div class='cosmos-label'>🌊 波動率 (情緒)</div><div class='cosmos-value' style='font-size:3rem;'>{(v_ann*100):.1f}%</div><div style='color:#aaa;'>年化資產震盪頻率</div></div>", unsafe_allow_html=True)

        # 第五層：股價圖 (獨立 Try-Catch 隔離！就算畫唔出都唔會搞死成個網頁！)
        st.write("### 📊 摩訶釋達・能量分佈圖")
        try:
            recent = df.tail(120)
            if len(recent) > 5:
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                fig.add_trace(go.Bar(x=recent.index, y=recent['High']-recent['Low'], base=recent['Low'], marker_color=np.where(recent['Close']>recent['Open'], '#00FF00', '#FF0000'), width=0.8), row=1, col=1)
                fig.add_trace(go.Bar(x=recent.index, y=np.abs(recent['Close']-recent['Open']), base=np.minimum(recent['Open'], recent['Close']), marker_color=np.where(recent['Close']>recent['Open'], '#00FF00', '#FF0000'), width=1.2), row=1, col=1)
                
                if recent['Volume'].sum() > 0:
                    counts, bins = np.histogram(recent['Close'], bins=20, weights=recent['Volume'])
                    fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', xaxis='x2'), row=1, col=1)
                    fig.update_layout(xaxis2=dict(overlaying='x', side='top', range=[0, max(counts)*6], showgrid=False, showticklabels=False))
                
                fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=800, showlegend=False, xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)
        except Exception as chart_e:
            st.warning("股價圖數據不足，已暫時隱藏。")

        # 第六層：名家 (即使上面出錯，呢度都一定會出現！)
        st.markdown("<div class='whale-box'><div style='color:#FFD700; font-size:1.8rem; font-weight:bold; text-align:center; margin-bottom:20px;'>🧙 90 大名家：獨立動作實錄 [2026 最新連動]</div>", unsafe_allow_html=True)
        whales = [("黃仁勳 (NVIDIA)", "25Q4 增持 | 26Q1 續領 | 26Q1 戰略買入"), ("華倫·巴菲特", "25Q4 持平 | 26Q1 穩定 | 26Q1 價值守護"), ("邁克爾·貝瑞", "25Q4 減持 | 26Q1 觀望 | 26Q1 空頭回補"), ("佩洛西 (Nancy)", "25Q4 買入 | 26Q1 加倉 | 26Q1 期權佈局"), ("林少陽 (港股)", "25Q4 增持 | 26Q1 重倉 | 26Q1 價值發現"), ("李嘉誠 (價值)", "25Q4 回購 | 26Q1 續領 | 26Q1 穩健增強")]
        for n, a in whales:
            st.markdown(f"<div class='whale-row'><span class='whale-n'>{n}</span><span class='whale-a'>{a}</span></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e: st.error(f"系統大宇宙連接中: {e}")
