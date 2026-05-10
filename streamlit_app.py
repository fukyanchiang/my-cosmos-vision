import streamlit as st
import pandas as pd
import numpy as np
from core_logic import scan_dragon_logic, smart_fetch

# --- 1. 極致黑魂視覺 ---
st.set_page_config(page_title="龍魂神殿 2.0", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #FFFFFF; }
    div.stButton > button {
        background-color: #000000 !important; color: #FFFFFF !important;
        border: 2px solid #FFFFFF !important; border-radius: 0px !important;
        font-weight: 900 !important; font-size: 1.1rem !important; width: 100%;
    }
    div.stButton > button:hover { background-color: #FFFFFF !important; color: #000000 !important; }
    .dragon-card { border-left: 5px solid #00FFCC; background: #111; padding: 15px; margin-bottom: 10px; border-radius: 5px; }
    .stop-loss-box { border: 2px dashed #FF4B4B; background: #220000; padding: 15px; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. 狀態管理 (導航控制) ---
if 'page' not in st.session_state:
    st.session_state.page = 'HOME'

# --- 3. 首頁：三大戰術門戶 ---
if st.session_state.page == 'HOME':
    st.markdown("<h1 style='text-align: center; font-size: 4rem;'>🐲 龍魂戰略總部</h1>", unsafe_allow_html=True)
    st.write("")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🐉 龍魂神殿 (11鐵律掃描)"): st.session_state.page = 'DRAGON'
    with col2:
        if st.button("📈 VCP 形態獵龍"): st.session_state.page = 'VCP'
    with col3:
        if st.button("🐢 海龜 N 字加注"): st.session_state.page = 'TURTLE'

# --- 4. 龍魂神殿：旗艦掃描頁面 ---
elif st.session_state.page == 'DRAGON':
    st.markdown("<h1 style='text-align: center;'>🐲 龍魂神殿 2.0 旗艦大腦</h1>", unsafe_allow_html=True)
    
    # 7 大橫向導航掣
    nav = st.columns(7)
    if nav[0].button("⬅️ 返回首頁"): st.session_state.page = 'HOME'
    btn_hk = nav[1].button("🇭🇰 港股精選")
    btn_us_all = nav[2].button("🇺🇸 美股全掃")
    btn_stock = nav[3].button("🔍 個股透視")
    btn_etf = nav[4].button("📦 ETF 專區")
    btn_ath = nav[5].button("🔥 ATH 破頂")
    btn_radar = nav[6].button("📡 實時雷達")

    st.markdown("---")
    
    # 戰損置頂 (最近 20 日止損警報)
    st.markdown("""
        <div class='stop-loss-box'>
            <h3 style='color: #FF4B4B; margin:0;'>🛡️ 戰損置頂警報 (10-EMA 跌穿監控)</h3>
            <p style='margin:5px 0 0 0;'>⚠️ <b>[9988.HK] 阿里巴巴</b> 今日收市跌穿 10-EMA，請執行止損紀律！</p>
        </div>
    """, unsafe_allow_html=True)

    # 美股 5 套名單專屬掣 (當按了 "🇺🇸 美股" 後出現)
    st.write("### 🇺🇸 美股戰略名單掃描")
    csv_cols = st.columns(5)
    csv_list = [
        ("SP500_Equities.csv", "大藍籌"),
        ("Market_Focus.csv", "13頁精選"),
        ("Industry_Focus.csv", "9頁行業"),
        ("Core_Stocks.csv", "核心名單"),
        ("US_ETFs.csv", "戰略 ETF")
    ]
    
    scan_target = None
    for i, (file, name) in enumerate(csv_list):
        if csv_cols[i].button(f"掃描 {name}"):
            scan_target = file

    # 執行掃描羅輯
    if scan_target or btn_hk:
        st.info(f"📡 龍魂雷達啟動！正在掃描 {scan_target if scan_target else '港股名單'}...")
        
        # 這裡爺爺幫你模擬讀 CSV (實際你要確保 GitHub 有呢啲 File)
        try:
            if scan_target:
                df_list = pd.read_csv(scan_target)
                tickers = df_list['Ticker'].tolist()
            else:
                tickers = ["0700.HK", "0981.HK", "1211.HK"] # 港股暫用住呢啲先
            
            results = []
            pb = st.progress(0)
            for idx, t in enumerate(tickers[:20]): # 測試先掃 20 隻
                pb.progress((idx+1)/20)
                data = smart_fetch(t)
                res = scan_dragon_logic(data, t, "科技/半導體", "US" if scan_target else "HK")
                if res: results.append(res)
            
            if results:
                # 排序 (總分 > 公仔數 > RS)
                results = sorted(results, key=lambda x: (x['Score'], x['IconCount'], x['RS']), reverse=True)
                for r in results:
                    st.markdown(f"""
                        <div class='dragon-card'>
                            <div style='font-size:1.4rem; font-weight:bold;'>{r['Status']} {r['Ticker']} ({r['Sector']}) {r['Icons']}</div>
                            <div style='font-size:0.85rem; color:#ccc; margin-top:8px;'>
                                <b>總分: {r['Score']}分</b> (Bias: {r['Bias']}%) | 📈 RS: {r['RS']} | 🔋 EJ: {r['EJ']} | ⚡ SE: {r['SE']} | 
                                💰 資金流: {r['Flow']} | 🎯 集中度: {r['Conc']} | 🌊 OBV: {r['OBV']} | 🐉 7大條件: <span style='color:#00FFCC;'>全中</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("💤 萬人坑內無生還者。")
        except Exception as e:
            st.error(f"讀取名單失敗: {e} (請確保 GitHub 內有 {scan_target})")

# --- 5. VCP 與 海龜 (暫代位) ---
elif st.session_state.page == 'VCP':
    if st.button("⬅️ 返回總部"): st.session_state.page = 'HOME'
    st.markdown("<h1>📈 VCP 形態獵龍 (開發中)</h1>", unsafe_allow_html=True)

elif st.session_state.page == 'TURTLE':
    if st.button("⬅️ 返回總部"): st.session_state.page = 'HOME'
    st.markdown("<h1>🐢 海龜 N 字加注 (開發中)</h1>", unsafe_allow_html=True)
