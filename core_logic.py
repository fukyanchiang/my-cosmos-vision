import yfinance as yf
import pandas as pd
import numpy as np

class AssetRanker:
    """
    究極資產排名運算核心 - 負責處理大批量資金流對比與熱力圖數據
    """
    
    @staticmethod
    def get_rank_and_acceleration(tickers, lookback_days, category_name):
        """
        計算資產的回報率、排名變化(超車箭咀)以及判定長線強勢股(火箭)
        """
        # 1. 根據戰區設定顯示比例 (頭尾保留 %)
        display_ratio = {
            "📦 美股 ETF (~360隻)": 1.0,
            "📦 港股 ETF (139隻)": 1.0,
            "🇭🇰 港股個股 (659隻)": 0.3,
            "🇺🇸 美股精選 (576隻)": 0.3,
            "🇺🇸 美股大藍籌 (500隻)": 0.2,
            "🏭 美股選定行業 (1029隻)": 0.2
        }
        ratio = display_ratio.get(category_name, 1.0)

        # 2. 批量下載數據 (取 1 年數據以確保足夠計算 200 天長線與 5 天平移)
        # threads=True 啟用多線程加速下載千隻股票
        data = yf.download(tickers, period="1y", progress=False, threads=True)
        
        if data.empty:
            return pd.DataFrame()

        # 處理 yfinance 單股與多股的 DataFrame 結構差異
        if isinstance(data.columns, pd.MultiIndex):
            close_df = data['Close']
        else:
            close_df = pd.DataFrame(data['Close'], columns=tickers)

        # 清洗數據：移除完全無數據的欄位，並向前填補 (ffill) 停牌或假期的空缺
        close_df = close_df.dropna(axis=1, how='all').ffill()

        # 安全檢查：確保有足夠的交易日數據 (至少需要 lookback_days + 6 日，長線最好有 205 日)
        min_required_days = lookback_days + 6
        if len(close_df) < min_required_days:
            return pd.DataFrame()

        # 3. 定義計算日基準 (今日 vs 5 個交易日前)
        # 為了避免 IndexError，我們動態確認可用的最大索引
        max_idx = len(close_df) - 1
        
        idx_current = -1
        idx_past = -(lookback_days + 1)
        idx_current_5d_ago = -6
        idx_past_5d_ago = -(lookback_days + 6)
        
        # 200天基準，如果上市不足200天則取最舊的一天
        idx_200d = -201 if len(close_df) >= 201 else -len(close_df)

        # 計算回報率 (%)
        current_ret = ((close_df.iloc[idx_current] - close_df.iloc[idx_past]) / close_df.iloc[idx_past]) * 100
        past_ret = ((close_df.iloc[idx_current_5d_ago] - close_df.iloc[idx_past_5d_ago]) / close_df.iloc[idx_past_5d_ago]) * 100
        ret_200d = ((close_df.iloc[idx_current] - close_df.iloc[idx_200d]) / close_df.iloc[idx_200d]) * 100

        # 4. 建立 DataFrame 並清理無效數據 (NaN)
        df = pd.DataFrame({
            'Ticker': close_df.columns,
            'Current_Return': current_ret.values,
            'Past_Return': past_ret.values,
            'Return_200d': ret_200d.values
        }).dropna()

        if df.empty:
            return pd.DataFrame()

        # 5. 進行排名 (1 為最強，數值越細代表排名越高)
        df['Current_Rank'] = df['Current_Return'].rank(ascending=False, method='min')
        df['Past_Rank'] = df['Past_Return'].rank(ascending=False, method='min')
        df['Rank_200d'] = df['Return_200d'].rank(ascending=False, method='min')
        
        # 計算排名變化 (正數代表超車上升，負數代表名次下跌)
        df['Rank_Change'] = df['Past_Rank'] - df['Current_Rank']

        # 計算長線 200 天的最強 Top 10% 門檻
        top_10_percent_threshold = max(1, int(len(df) * 0.1))

        # 6. 生成帶有箭咀與火箭的專屬標籤
        def generate_label(row):
            change = int(row['Rank_Change'])
            ticker = row['Ticker']
            
            # 長強短更強判定：200天排 Top 10% 且 近期排名正在上升 (超車)
            is_super_rocket = (row['Rank_200d'] <= top_10_percent_threshold) and (change > 0)
            rocket_icon = "🚀 " if is_super_rocket else ""
            
            if change > 0:
                return f"▲ {change} | {rocket_icon}{ticker}"
            elif change < 0:
                return f"▼ {abs(change)} | {ticker}"
            else:
                return f"- 0 | {ticker}"

        df['Display_Label'] = df.apply(generate_label, axis=1)

        # 7. 根據當前回報率由高至低(最強到最弱)排序
        df = df.sort_values(by='Current_Return', ascending=False).reset_index(drop=True)

        # 8. 執行戰區顯示比例過濾 (Top % 及 Bottom %)
        if ratio < 1.0:
            cutoff = max(1, int(len(df) * ratio))
            df_top = df.head(cutoff)
            df_bottom = df.tail(cutoff)
            
            # 加入虛擬的「分隔線」數據列，用於在圖表中顯示斷層
            separator = pd.DataFrame([{
                'Ticker': '...', 
                'Current_Return': 0.0, 
                'Display_Label': '✂️ 中間隱藏區域 ✂️'
            }])
            
            df = pd.concat([df_top, separator, df_bottom], ignore_index=True)

        # 9. 為了配合 Plotly 橫向 Bar Chart 預設從下往上畫的特性，將整個 DataFrame 倒轉
        df_final = df.iloc[::-1].reset_index(drop=True)
        
        return df_final
