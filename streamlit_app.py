import streamlit as st
import plotly.express as px
from core_logic import AssetRanker  # 確保 core_logic.py 喺同一個資料夾

# ==========================================
# 📦 數據庫：請替換為你真實的 Ticker 列表
# ==========================================
LIST_HK_STOCKS = ["0700.HK", "9988.HK", "3690.HK", "1810.HK"]  # 替換為你的 659 隻港股
LIST_HK_ETF = ["2800.HK", "3033.HK", "3140.HK"]                # 替換為你的 139 隻港股 ETF
LIST_US_SELECT = ["AAPL", "NVDA", "TSLA", "META"]              # 替換為你的 576 隻美股精選
LIST_US_BLUECHIP = ["MSFT", "JNJ", "PG", "V"]                  # 替換為你的 500 隻美股藍籌
LIST_US_SECTOR = ["XLE", "XLF", "XLK", "XLV"]                  # 替換為你的 1029 隻選定行業
LIST_US_ETF = ["SPY", "QQQ", "UFO", "ARKG", "TLT"]             # 替換為你的 ~360 隻美股 ETF

# ==========================================
# 🎛️ 側邊欄 (Sidebar) - 戰術控制台
# ==========================================
with st.sidebar:
    st.markdown("### 🎛️ 戰術控制台 (V188.0)")
    
    # 操作主模式切換
    operation_mode = st.radio(
        "請選擇操作:", 
        ["龍魂神殿 5.0 雷達", "📊 究極資產拔河龍虎榜"]
    )
    
    st.markdown("---")
    st.caption("👴 爺爺的空軍指揮中心")

# ==========================================
# 🚀 主畫面邏輯：龍魂神殿 5.0 (保留你原本的功能)
# ==========================================
if operation_mode == "龍魂神殿 5.0 雷達":
    st.title("🐉 龍魂神殿 5.0 雷達")
    st.write("呢度保留你原本嘅 N字突破 / VCP 掃描功能...")
    # TODO: 貼返你原本 5.0 雷達嘅介面代碼喺度

# ==========================================
# 🔥 主畫面邏輯：究極資產拔河龍虎榜
# ==========================================
elif operation_mode == "📊 究極資產拔河龍虎榜":
    st.title("🔥 全宇宙資金流熱力矩陣")
    
    # 頂部控制面板
    col1, col2 = st.columns([2, 1])
    
    with col1:
        target_category = st.selectbox(
            "📍 選擇掃描戰區",
            [
                "📦 美股 ETF (~360隻)",
                "📦 港股 ETF (139隻)",
                "🇭🇰 港股個股 (659隻)",
                "🇺🇸 美股精選 (576隻)",
                "🇺🇸 美股大藍籌 (500隻)",
                "🏭 美股選定行業 (1029隻)"
            ]
        )
        
    with col2:
        lookback_str = st.selectbox(
            "⏳ 戰術時間窗",
            ["5天", "10天", "20天", "40天", "60天", "200天"]
        )
        lookback_days = int(lookback_str.replace("天", ""))

    # 啟動按鈕
    if st.button("🚀 啟動熱力掃描！", use_container_width=True):
        
        # 對應所選戰區的 Ticker List
        if target_category == "📦 美股 ETF (~360隻)":
            current_tickers = LIST_US_ETF 
        elif target_category == "📦 港股 ETF (139隻)":
            current_tickers = LIST_HK_ETF
        elif target_category == "🇭🇰 港股個股 (659隻)":
            current_tickers = LIST_HK_STOCKS
        elif target_category == "🇺🇸 美股精選 (576隻)":
            current_tickers = LIST_US_SELECT
        elif target_category == "🇺🇸 美股大藍籌 (500隻)":
            current_tickers = LIST_US_BLUECHIP
        elif target_category == "🏭 美股選定行業 (1029隻)":
            current_tickers = LIST_US_SECTOR
            
        with st.spinner(f"正在連線華爾街深網，計算 {target_category} 的資金拔河..."):
            
            # 呼叫 core_logic 進行核心運算
            df_result = AssetRanker.get_rank_and_acceleration(current_tickers, lookback_days, target_category)
            
            if df_result.empty:
                st.error("⚠️ 無法獲取足夠數據，請檢查網絡或 Ticker 列表是否正確。")
            else:
                # ==========================================
                # 📊 繪製究極龍虎榜
                # ==========================================
                fig = px.bar(
                    df_result, 
                    x='Current_Return', 
                    y='Display_Label', 
                    orientation='h',
                    color='Current_Return', 
                    color_continuous_scale='YlOrRd', # 深紅至金黃配色
                    text=df_result['Current_Return'].apply(lambda x: f"{x:.1f}%" if x != 0.0 else "")
                )

                # 美化佈局，確保深色模式極致高尚
                fig.update_layout(
                    title=f"📊 {target_category} - {lookback_days}日 拔河龍虎榜",
                    title_font=dict(size=22, color="white"),
                    plot_bgcolor='#0e1117',
                    paper_bgcolor='#0e1117',
                    font=dict(color="white"),
                    height=max(600, len(df_result) * 28), # 動態高度，防字體擠壓
                    xaxis=dict(showgrid=False, zeroline=True, zerolinecolor='#333', title="回報率 (%)"),
                    yaxis=dict(showgrid=False, title="", tickfont=dict(size=14, color="white", family="Courier New")),
                    coloraxis_showscale=False, # 隱藏右側色條，保持乾淨
                    margin=dict(l=20, r=20, t=60, b=20)
                )

                # 確保文字標籤顯示在 Bar 的外側
                fig.update_traces(textposition='outside', textfont=dict(color='white'))
                
                # 輸出圖表
                st.plotly_chart(fig, use_container_width=True)
                
                st.success("✅ 資金流向掃描完成！準備執行狙擊！")
