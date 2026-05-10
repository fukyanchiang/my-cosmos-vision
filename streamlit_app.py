import streamlit as st
import pandas as pd
import os
from core_logic import analyze_dragon_soul, smart_fetch

st.set_page_config(page_title="龍魂神殿：美股終極版", layout="wide")

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
        st.error(f"⚠️ 找不到檔案：{target_file}。請確保 GitHub 已上傳。")
    else:
        try:
            # 讀取並自動清洗標題
            df_list = pd.read_csv(target_file, encoding='utf-8-sig')
            df_list.columns = df_list.columns.str.strip().str.upper()
            
            if 'SYMBOL' not in df_list.columns:
                st.error(f"❌ 喺 {target_file} 入面認唔到 SYMBOL 標題。")
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
                    # 【爺爺嘅百寶袋】：後面加多個 *_，大腦畀第5件、第6件嘢都照單全收唔會死機！
                    is_dragon, score, stage, details, *_ = analyze_dragon_soul(ticker, df)
                    
                    if is_dragon:
                        all_results.append({"代號": ticker, "得分": score, "細節": details})
                progress_bar.progress((i + 1) / len(tickers))
            
            status_text.empty()
            
            if all_results:
                st.balloons()
                st.success(f"✅ 發現 {len(all_results)} 隻龍魂標的！")
                for res in sorted(all_results, key=lambda x: x['得分'], reverse=True):
                    with st.expander(f"🔥 {res['代號']} - 得分: {round(res['得分'],1)}"):
                        st.write(f"強度 (RS): {res['細節'].get('RS', 'N/A')}% | 現價: ${res['細節'].get('Price', 'N/A')}")
            else:
                st.warning("⚠️ 目前戰場未發現龍魂。")
                
        except Exception as e:
            st.error(f"❌ 系統錯誤：{e}")
