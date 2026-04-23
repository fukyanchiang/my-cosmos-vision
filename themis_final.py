import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 🧬 模塊一：神級 COSMOS-DNA (股王基因)
# ==========================================
def calculate_dna(h, market_h):
    try:
        stock_returns = h['Close'].pct_change().dropna()
        market_returns = market_h['Close'].pct_change().dropna()
        
        stock_ret_60 = stock_returns.tail(60)
        market_ret_60 = market_returns.tail(60)
        stock_vol_60 = h['Volume'].tail(60)
        
        # 1. 逆市勝率 (Rebel Alpha)
        market_down_days = market_ret_60 < 0
        if market_down_days.sum() > 0:
            beat_market_prob = (stock_ret_60[market_down_days] > market_ret_60[market_down_days]).mean()
            rebel_score = max(0, min(100, (beat_market_prob - 0.4) * 166.6))
        else:
            rebel_score = 50 
            
        # 2. 大戶吸籌推力 (Institutional Thrust)
        up_days = stock_ret_60 > 0
        down_days = stock_ret_60 < 0
        if up_days.sum() > 0 and down_days.sum() > 0:
            up_vol_mean = stock_vol_60[up_days].mean()
            down_vol_mean = stock_vol_60[down_days].mean()
            thrust_ratio = up_vol_mean / (down_vol_mean + 1e-9)
            thrust_score = max(0, min(100, (thrust_ratio - 0.8) * 80))
        else:
            thrust_score = 50
            
        # 3. 波動收斂 (VCP Squeeze)
        vol_20 = stock_ret_60.tail(20).std()
        vol_5 = stock_ret_60.tail(5).std()
        if vol_5 > 0:
            squeeze_ratio = vol_20 / vol_5
            vcp_score = max(0, min(100, (squeeze_ratio - 0.5) * 50))
        else:
            vcp_score = 100 
            
        god_dna = (rebel_score * 0.4) + (thrust_score * 0.4) + (vcp_score * 0.2)
        return round(god_dna, 1)
        
    except Exception as e:
        return 0.0

# ==========================================
# 📊 模塊二：數據庫定義 (COSMOS-8D 投行精確版)
# ==========================================
stock_data_8d = {
    "6869.HK (長飛光纖)": {
        "🩸 血液純度 (營運現金流)": 8,   
        "🛡️ 免疫系統 (核心技術/生態)": 10,  
        "🏗️ 心跳頻率 (訂單/供應鏈VIP)": 9,   
        "🧬 大腦潛力 (研發/開支回報)": 9,   
        "🧱 骨架重量 (資產底價/估值)": 6,   
        "⚡ 物理底盤 (能源/算力基建)": 10,
        "💰 資本配置 (回購/派息/併購)": 7,   
        "📈 經營拐點 (毛利率/主業反轉)": 8    
    }
}

target_8d = "6869.HK (長飛光纖)" 
metrics_8d = stock_data_8d[target_8d]

# 假設你已經行咗 calculate_dna 攞到分數 (此處用模擬高分)
dna_value = 88.5 

# ==========================================
# ♾️ 模塊三：COSMOS-Ω 摩訶奇點 (起化還虛總決策)
# ==========================================
st.markdown("<hr style='border: 1px solid rgba(0, 255, 204, 0.3); margin: 20px 0;'>", unsafe_allow_html=True)

scores_8d = list(metrics_8d.values())
has_fatal_wound = any(score < 0 for score in scores_8d)
perfect_pillars = sum(1 for score in scores_8d if score >= 8)

if dna_value >= 85 and not has_fatal_wound and perfect_pillars >= 4:
    void_status = "🌟【起化還虛】大宇宙共鳴：天人合一，劍出無悔！"
    void_color = "#FFFFFF" 
    void_glow = "0 0 30px rgba(255, 255, 255, 0.8)"
    action_text = "SO HAND (全倉) / 堅定持有"
elif has_fatal_wound:
    void_status = "⚠️【凡塵劫數】陣眼破漏，大戶散貨中。"
    void_color = "#FF3131" 
    void_glow = "0 0 20px rgba(255, 49, 49, 0.6)"
    action_text = "迴避 / 止蝕離場"
else:
    void_status = "🌀【太極醞釀】萬法歸宗，積蓄動能中..."
    void_color = "#00FFCC" 
    void_glow = "0 0 15px rgba(0, 255, 204, 0.5)"
    action_text = "分批建倉 / 咬住毛巾觀察"

st.markdown(f"""
<div style="text-align: center; margin-bottom: 30px; padding: 25px; border-radius: 15px; background: linear-gradient(145deg, #0a0a0a, #111); border: 1px solid {void_color}; box-shadow: {void_glow};">
    <p style="color: #888; font-size: 0.9rem; letter-spacing: 2px; margin-bottom: 5px;">COSMOS-Ω ULTIMATE DECISION</p>
    <h2 style="color: {void_color}; font-size: 2.2rem; font-weight: 900; margin: 0; text-shadow: {void_glow};">{void_status}</h2>
    <h4 style="color: #ccc; margin-top: 15px; font-weight: 400;">宇宙意志指令：<span style="color: {void_color}; font-weight: 900;">{action_text}</span></h4>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 🖥️ 模塊四：左右排版 (左 DNA，右 8D Bar)
# ==========================================
col_dna, col_5d = st.columns([1, 2.5])

with col_dna:
    st.markdown(f"""
    <div style="border: 2px solid #FFD700; border-radius: 10px; padding: 20px; text-align: center; background-color: rgba(255, 215, 0, 0.05); height: 100%; display: flex; flex-direction: column; justify-content: center;">
        <h4 style="color: #FFD700; margin-bottom: 10px; font-size: 1.1rem;">🧬 COSMOS-DNA</h4>
        <p style="color: #ccc; font-size: 0.8rem; margin-bottom: 15px;">神級股王基因分數</p>
        <h1 style="color: #FFF; font-size: 3.5rem; margin: 0; text-shadow: 0 0 15px #FFD700;">{dna_value}</h1>
    </div>
    """, unsafe_allow_html=True)

with col_5d:
    st.markdown(f"<div style='padding-left: 15px;'><h4 style='color: #FF5A00; margin-bottom: 5px;'>🌌 {target_8d}・8D 八門底氣掃描</h4>", unsafe_allow_html=True)
    st.caption("🚨 負數(紅): 警報 | 0格(灰): 空殼 | ⚡電藍/💎銀白/🔥烈焰: 特殊狀態")

    for label, score in metrics_8d.items():
        grid_html = '<div style="display: flex; width: 100%; background-color: #111; padding: 4px; border-radius: 6px; border: 1px solid #333;">'
        
        for i in range(-5, 11):
            border_style = "border-left: 2px solid #fff;" if i == 0 else ""

            if "⚡" in label:
                active_color = "#00FFFF" if i > 7 else ("#9D00FF" if i >= 0 else "#FF3131") 
            elif "💰" in label:
                active_color = "#E0E0E0" if i > 7 else ("#A0A0A0" if i >= 0 else "#FF3131") 
            elif "📈" in label:
                active_color = "#FF5A00" if i > 7 else ("#FF9933" if i >= 0 else "#FF3131") 
            else:
                active_color = "#FFD700" if i > 7 else ("#00FFCC" if i >= 0 else "#FF3131") 

            is_active = (1 <= i <= score) if score >= 0 else (score <= i <= -1)
            opacity = 1.0 if is_active else 0.05
            glow = f"box-shadow: 0 0 8px {active_color};" if is_active else ""
            
            grid_html += f'<div style="flex: 1; height: 12px; margin: 0 1px; background-color: {active_color}; opacity: {opacity}; border-radius: 1px; {border_style} {glow}"></div>'
        
        grid_html += '</div>'

        st.markdown(f"""
            <div style="margin-bottom: 10px; padding-left: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                    <span style="font-size: 0.82rem; color: #ccc;">{label}</span>
                    <span style="font-size: 0.9rem; font-weight: 900; color: {'#FF3131' if score < 0 else active_color};">{score}</span>
                </div>
                {grid_html}
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<hr style='border: 1px solid rgba(0, 255, 204, 0.3); margin: 20px 0;'>", unsafe_allow_html=True)
