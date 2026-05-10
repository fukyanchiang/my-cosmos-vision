import streamlit as st
import pandas as pd
from core_logic import scan_dragon_logic, smart_fetch

# --- 1. 黑魂 UI ---
st.set_page_config(page_title="龍魂神殿 2.0", layout="wide")
st.markdown("<style>.stApp{background:#000;color:#fff;} div.stButton>button{background:#000;color:#fff;border:2px solid #fff;border-radius:0;font-weight:900;width:100%; margin-bottom:5px;}</style>", unsafe_allow_html=True)

# --- 2. 導航管理 ---
if 'page' not in st.session_state: st.session_state.page = 'HOME'
if 'scan_target' not in st.session_state: st.session_state.scan_target = None
if 'market_mode' not in st.session_state: st.session_state.market_mode = 'HK'

# --- 3. 首頁：3 個大掣 ---
if st.session_state.page == 'HOME':
    st.markdown("<h1 style='text-align:center;font-size:4rem;margin-top:100px;'>🐲 龍魂戰略總部</h1>", unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns(3)
    if c1.button("🐉 龍魂神殿"): st.session_state.page = 'DRAGON'
    if c2.button("📈 VCP 形態獵龍"): st.session_state.page = 'VCP'
    if c3.button("🐢 海龜 N 字加注"): st.session_state.page = 'TURTLE'

# --- 4. 龍魂神殿專頁 ---
elif st.session_state.page == 'DRAGON':
    st.markdown("<h1 style='text-align:center;'>🐲 龍魂神殿 2.0 旗艦雷達</h1>", unsafe_allow_html=True)
    
    # --- 7 個橫向選單 (導航/設定) ---
    nav = st.columns(7)
    if nav[0].button("⬅️ 返回"): st.session_state.page = 'HOME'
    if nav[1].button("🇭🇰 港股精選"): st.session_state.scan_target = 'HK_LIST'; st.session_state.market_mode = 'HK'
    if nav[2].button("🇺🇸 美股全掃"): st.session_state.scan_target = 'US_CSV'; st.session_state.market_mode = 'US'
    if nav[3].button("🔍 個股透視"): st.session_state.scan_target = 'SINGLE'
    if nav[4].button("📦 ETF 專區"): st.session_state.scan_target = 'ETF'
    if nav[5].button("🔥 ATH 破頂"): st.session_state.scan_target = 'ATH'
    btn_radar = nav[6].button("📡 啟動雷達") # 執行掣

    st.markdown("---")
    
    # 止損警告
    st.markdown("<div style='border:2px dashed red;background:#200;padding:10px;'>🛡️ 止損警報：[9988.HK] 跌穿 10-EMA！</div>", unsafe_allow_html=True)

    # --- 設定與選項顯示 ---
    st.write(f"### ⚙️ 目前選定場景：{st.session_state.scan_target}")
    
    selected_tickers = []
    
    if st.session_state.scan_target == 'US_CSV':
        st.write("請選擇美股名單：")
        m = st.columns(5)
        files = [("SP500_Equities.csv", "大藍籌"), ("Market_Focus.csv", "精選"), ("Industry_Focus.csv", "行業"), ("Core_Stocks.csv", "核心"), ("US_ETFs.csv", "ETF")]
        for i, (f, name) in enumerate(files):
            if m[i].button(f"準備 {name}"): st.session_state.active_file = f; st.success(f"已選定 {f}")

    elif st.session_state.scan_target == 'SINGLE':
        single_t = st.text_input("輸入股票代號 (如 NVDA 或 0700.HK)")
        if single_t: st.session_state.active_file = single_t

    # --- 📡 按下雷達後真正執行掃描 ---
    if btn_radar:
        if st.session_state.scan_target == 'HK_LIST':
            selected_tickers = [("0700.HK", "互聯網"), ("9988.HK", "互聯網"), ("3690.HK", "互聯網"), ("1810.HK", "手機"), ("0981.HK", "芯片"), ("1211.HK", "汽車")]
        elif st.session_state.scan_target == 'US_CSV' and hasattr(st.session_state, 'active_file'):
            try:
                df_csv = pd.read_csv(st.session_state.active_file)
                col = [c for c in df_csv.columns if c.lower() in ['ticker', 'symbol']][0]
                selected_tickers = [(t, "美股") for t in df_csv[col].dropna().tolist()]
            except: st.error("CSV 名單讀取失敗")
        elif st.session_state.scan_target == 'SINGLE' and hasattr(st.session_state, 'active_file'):
            selected_tickers = [(st.session_state.active_file, "手動掃描")]

        if selected_tickers:
            st.info(f"🚀 龍魂發動！正在執行 11 大鐵律過濾...")
            results = []
            pb = st.progress(0)
            for idx, (t, sec) in enumerate(selected_tickers[:30]): # 測試版掃 30 隻
                pb.progress((idx+1)/30 if idx < 30 else 1.0)
                data = smart_fetch(t)
                res = scan_dragon_logic(data, t, sec, st.session_state.market_mode)
                if res: results.append(res)
            
            if results:
                for r in sorted(results, key=lambda x: x['Score'], reverse=True):
                    st.markdown(f"""
                        <div style='border-left:5px solid #00FFCC;background:#111;padding:15px;margin-bottom:10px;'>
                            <div style='font-size:1.2rem;font-weight:bold;'>{r['Status']} {r['Ticker']} ({r['Sector']}) {r['Icons']}</div>
                            <div style='font-size:0.8rem;color:#ccc;'>總分: {r['Score']} | RS: {r['RS']} | Bias: {r['Bias']}% | 資金: {r['Flow']} | 🐉 7大條件: 全中</div>
                        </div>
                    """, unsafe_allow_html=True)
            else: st.warning("目前市場無合資格真龍標的。")

# --- 開發位 ---
elif st.session_state.page in ['VCP', 'TURTLE']:
    if st.button("⬅️ 返回"): st.session_state.page = 'HOME'
    st.write(f"### {st.session_state.page} 正在施工中...")
