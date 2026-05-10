import streamlit as st
import pandas as pd
import os
from core_logic import analyze_dragon_soul, smart_fetch

# 網頁設定
st.set_page_config(page_title="龍魂神殿：美股終極版", layout="wide")

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🐲 龍魂神殿：美股全方位雷達</h1>", unsafe_allow_html=True)

# 側邊欄：選擇戰場
# 爺爺已經幫你預留咗 ETF 嘅位
option = st.sidebar.selectbox(
    "🎯 選擇要掃描的戰場",
    ["S&P 500 大藍籌", "Market Focus 精選", "US ETFs 戰略名單"]
)

# 檔案名稱對應
file_map = {
    "S&P 500 大藍籌": "SP500_Equities.csv",
    "Market Focus 精選": "Market_Focus.csv",
    "US ETFs 戰略名單": "US_ETFs.csv"
}

target_file = file_map[option]

if st.sidebar.button("🐉 啟動獵龍掃描"):
    # 檢查 GitHub 入面有無呢份 CSV 檔案
    if not os.path.exists(target_file):
        st.error(f"⚠️ 乖孫，GitHub 入面仲未見到 {target_file} 呀！請先上傳檔案。")
    else:
        try:
            # 讀取名單
            df_list = pd.read_csv(target_file)
            # 確保代號格式正確
            tickers = df_list['SYMBOL'].dropna().astype(str).str.strip().unique().tolist()
            
            all_results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            st.info(f"🚀 正在進入「{option}」戰場，準備偵測 {len(tickers)} 隻標的...")
            
            for i, ticker in enumerate(tickers):
                status_text.text(f"🔍 掃描中: {ticker} ({i+1}/{len(tickers)})")
                
                # 去網上搵數據
                df = smart_fetch(ticker)
                if not df.empty:
                    # 用爺爺嘅龍魂邏輯分析
                    is_dragon, score, stage, details = analyze_dragon_soul(ticker, df)
                    if is_dragon:
                        all_results.append({"代號": ticker, "得分": score, "細節": details})
                
                # 更新進度條
                progress_bar.progress((i + 1) / len(tickers))
            
            status_text.empty()
            
            # 顯示結果
            if all_results:
                st.balloons()
                st.success(f"✅ 掃描完畢！喺 {len(tickers)} 隻入面發現 {len(all_results)} 隻龍魂股！")
                
                # 按照得分高低排位
                sorted_res = sorted(all_results, key=lambda x: x['得分'], reverse=True)
                for res in sorted_res:
                    with st.expander(f"🔥 {res['代號']} - 得分: {round(res['得分'],1)}"):
                        st.write(f"強度 (RS): {res['細節']['RS']}% | 現價: ${res['細節']['Price']}")
            else:
                st.warning("⚠️ 目前戰場平靜，未發現符合龍魂覺醒條件的標的。")
                
        except Exception as e:
            st.error(f"❌ 讀取 CSV 失敗，請確保標題行有 'SYMBOL'。錯誤訊息: {e}")
