import streamlit as st
import pandas as pd
from core_logic import smart_fetch, scan_dragon_logic
import concurrent.futures

# ==========================================
# 🗂️ 乖孫專屬大名單 (請喺度貼返你啲心血！)
# ==========================================
# 爺爺留咗位，你將原本嗰三百幾隻港股貼喺引號入面 (用逗號分隔)
HK_300_TICKERS = "0700.HK, 9988.HK, 1109.HK, 0836.HK, 1071.HK, 2380.HK" 

# 將你嗰 110 隻 ETF 貼喺度
HK_ETF_TICKERS = "2800.HK, 2828.HK, 3033.HK, 3140.HK" 

# 美股測試名單
US_TICKERS = "ARM, NVDA, TSLA, AAPL, MSFT, AMD, GOOGL"

# ==========================================
# 🎨 UI 介面設定
# ==========================================
st.set_page_config(page_title="龍魂獵殺系統 5.0", layout="wide")
st.title("🐲 龍魂獵殺系統 5.0 (明暗雙線終極版)")

# 側邊欄設定
st.sidebar.header("⚙️ 雷達設定")
market = st.sidebar.radio("選擇市場模式 (影響 Bias 扣分標準)", ["HK", "US"])

# 名單選擇器
st.sidebar.subheader("📋 選擇掃描名單")
scan_mode = st.sidebar.selectbox("你想掃描邊批股票？", [
    "自訂輸入", 
    "🎯 港股 300 強", 
    "📈 港股 ETF (110隻)", 
    "🦅 美股精選"
])

# 根據選擇載入名單
if scan_mode == "🎯 港股 300 強":
    ticker_input = st.sidebar.text_area("名單預覽 (可手動修改)", HK_300_TICKERS, height=150)
elif scan_mode == "📈 港股 ETF (110隻)":
    ticker_input = st.sidebar.text_area("名單預覽 (可手動修改)", HK_ETF_TICKERS, height=150)
elif scan_mode == "🦅 美股精選":
    ticker_input = st.sidebar.text_area("名單預覽 (可手動修改)", US_TICKERS, height=150)
else:
    ticker_input = st.sidebar.text_area("輸入股票代號 (用逗號分隔)", "")

# ==========================================
# 🚀 執行掃描邏輯
# ==========================================
if st.sidebar.button("🔥 啟動龍魂雷達"):
    tickers = [t.strip() for t in ticker_input.split(",") if t.strip()]
    
    if not tickers:
        st.warning("請確保名單內有股票代號！")
    else:
        st.info(f"雷達啟動！正在用 5.0 引擎掃描 {len(tickers)} 隻股票... 呢度可能要等一陣 ⏳")
        
        results = []
        progress_bar = st.progress(0)
        
        # 使用多線程加快幾百隻股票嘅掃描速度
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_ticker = {executor.submit(smart_fetch, ticker): ticker for ticker in tickers}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                completed += 1
                progress_bar.progress(completed / len(tickers))
                
                df = future.result()
                if not df.empty:
                    # 呼叫 5.0 大腦進行明暗雙線計分
                    res = scan_dragon_logic(df, ticker, "板塊", market)
                    if res:
                        results.append(res)
        
        # ==========================================
        # 📊 顯示掃描結果
        # ==========================================
        if results:
            # 轉換為 DataFrame 並按「戰術總分 (Score)」由高至低排序
            df_res = pd.DataFrame(results)
            df_res = df_res.sort_values(by="Score", ascending=False).reset_index(drop=True)
            
            st.success(f"掃描完成！喺 {len(tickers)} 隻入面，成功捕捉 {len(df_res)} 隻過到七大死刑嘅真龍！")
            
            # 整理顯示欄位，加入明暗雙線視覺效果
            display_df = pd.DataFrame({
                "公仔": df_res["Icons"],
                "代號": df_res["Ticker"],
                "戰術總分 (明線)": df_res["Score"].apply(lambda x: f"🎯 {x}"),
                "原始戰力 (暗線)": df_res["RawPower"].apply(lambda x: f"🔥 {x}"),
                "家法扣分": df_res["Penalty"].apply(lambda x: f"🛑 {-x}" if x > 0 else "✅ 0"),
                "狀態": df_res["Status"],
                "RS 強度": df_res["RS"],
                "EJ 底氣": df_res["EJ"],
                "SE 能量": df_res["SE"],
                "Bias 偏離": df_res["Bias"].apply(lambda x: f"{x}%")
            })
            
            st.dataframe(
                display_df,
                use_container_width=True,
                height=600,
                hide_index=True
            )
            
            st.markdown("""
            ---
            **👴 爺爺嘅明暗雙線解讀指南：**
            * **🎯 戰術總分**：用嚟排名嘅最終分數。由高至低排，確保你買到最抵買、最安全嘅起步點。
            * **🔥 原始戰力**：舊制無上限分數。反映隻股嘅「絕對爆發力」(例如 180分)，力量越大越狂野。
            * **🛑 家法扣分**：如果偏離太遠 (Bias過熱) 或頭頂有大量蟹貨，系統會幫你自動煞車扣分。
            """)
            
        else:
            st.error("雷達掃描完畢，但無任何股票過到 5.0 系統嘅『七大死刑』同『8大硬指標』！請等大市轉好再試。")
