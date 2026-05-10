import streamlit as st
import pandas as pd
import os
from core_logic import analyze_dragon_soul, smart_fetch

st.set_page_config(page_title="龍魂神殿：美股終極大成版", layout="wide")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🐲 龍魂神殿：美股全方位雷達</h1>", unsafe_allow_html=True)

# 側邊欄：選擇戰場
option = st.sidebar.selectbox(
    "🎯 選擇要掃描的戰場",
    ["S&P 500 大藍籌", "Market Focus (13頁精選)", "Industry Focus (9頁行業)", "核心美股名單", "US ETFs 戰略名單"]
)

# 檔案名稱對應
file_map = {
    "S&P 500 大藍籌": "SP500_Equities.csv",
    "Market Focus (13頁精選)": "Market_Focus.csv",
    "Industry Focus (9頁行業)": "Industry_Focus.csv",
    "核心美股名單": "Core_Stocks.csv",
    "US ETFs 戰略名單": "US_ETFs.csv"
}

target_file = file_map[option]

if st.sidebar.button("🐉 啟動獵龍掃描"):
    if not os.path.exists(target_file):
        st.error(f"⚠️ 乖孫，GitHub 入面仲未見到 {target_file} 呀！請先上傳檔案。")
    else:
        try:
            # 讀取 CSV
            df_list = pd.read_csv(target_file)
            
            # 【爺爺嘅神醫修正】：自動幫所有標題除空格、變大楷
            df_list.columns = [str(c).strip().upper() for c in df_list.columns]
            
            # 檢查係咪真係有 SYMBOL 呢一欄
            if 'SYMBOL' not in df_list.columns:
                st.error(f"❌ 喺 {target_file} 入面搵唔到 'SYMBOL' 呢一欄。")
                st.write("現有欄位名：", df_list.columns.tolist())
                st.stop()
            
            tickers = df_list['SYMBOL'].dropna().astype(str).str.strip().unique().tolist()
            
            all_results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            st.info(f"🚀 正在掃描「{option}」戰場，共 {len(tickers)} 隻標的...")
            
            for i, ticker in enumerate(tickers):
                status_text.text(f"🔍 掃描中: {ticker} ({i+1}/{len(tickers)})")
                df = smart_fetch(ticker)
                if not df.empty:
                    is_dragon, score, stage, details = analyze_dragon_soul(ticker, df)
                    if is_dragon:
                        all_results.append({"代號": ticker, "得分": score, "細節": details})
                progress_bar.progress((i + 1) / len(tickers))
            
            status_text.empty()
            
            if all_results:
                st.balloons()
                st.success(f"✅ 發現 {len(all_results)} 隻符合龍魂條件的標的！")
                for res in sorted(all_results, key=lambda x: x['得分'], reverse=True):
                    with res_container := st.expander(f"🔥 {res['代號']} - 得分: {round(res['得分'],1)}"):
                        st.write(f"強度 (RS): {res['細節']['RS']}% | 現價: ${res['細節']['Price']}")
            else:
                st.warning("⚠️ 目前戰場平靜，未發現龍魂。")
                
        except Exception as e:
            st.error(f"❌ 系統錯誤：{e}")
