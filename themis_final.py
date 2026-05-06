# =========================================================================
# 🛡️ 模式 B：環球市底大師指揮塔 
# =========================================================================
elif app_mode == "🛡️ 環球市底大師指揮塔":
    st.markdown("<h1 class='main-title'>🛡️ 環球市底大師指揮塔</h1>", unsafe_allow_html=True)
    
    st.markdown("<span style='color:white; font-size:16px; font-weight:bold;'>請選擇大盤陣營：</span>", unsafe_allow_html=True)
    market_choice = st.radio("", ["🇭🇰 港股市寬系統", "🇺🇸 美股市寬系統"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("<span style='color:white; font-size:16px; font-weight:bold;'>請選擇指數：</span>", unsafe_allow_html=True)
    if "港股" in market_choice: idx_choice = st.radio("", ["恒指", "科指"], horizontal=True, label_visibility="collapsed")
    else: idx_choice = st.radio("", ["道指", "標指", "納市", "IWM"], horizontal=True, label_visibility="collapsed")
    st.write("---")
    
    HSI_71 = (HK_STOCK_MAP["1. 互聯網巨頭"] + HK_STOCK_MAP["5. 國有大行與金融"] + HK_STOCK_MAP["10. 房地產開發"] + HK_STOCK_MAP["13. 核心消費與餐飲"])[:71]
    TECH_30 = (HK_STOCK_MAP["1. 互聯網巨頭"] + HK_STOCK_MAP["2. 半導體與芯片"] + HK_STOCK_MAP["12. 消費電子硬件"])[:30]
    DOW_30 = "AAPL MSFT UNH JNJ XOM JPM V PG HD CVX MRK KO ABBV BAC AVGO PEP TMO COST CSCO MCD CRM DIS LIN ABT ACN AMD WFC NFLX INTC CAT".split()
    SPX_80 = (DOW_30 + US_STOCK_MAP["2. AI與大數據雲端"] + US_STOCK_MAP["11. 核心消費品"] + US_STOCK_MAP["22. 商業銀行巨頭"])[:80]
    NDX_43 = (US_STOCK_MAP["2. AI與大數據雲端"] + US_STOCK_MAP["1. 半導體設備與設計"] + US_STOCK_MAP["6. 通訊與網絡設備"])[:43]
    IWM_32 = (US_STOCK_MAP["49. 小型爆發精選"] + US_STOCK_MAP["50. 超微型探索 (Micro)"])[:32]

    if "恒指" in idx_choice: ticker_sym = "2800.HK"; b_tickers = HSI_71 
    elif "科指" in idx_choice: ticker_sym = "3032.HK"; b_tickers = TECH_30
    elif "道指" in idx_choice: ticker_sym = "DIA"; b_tickers = DOW_30
    elif "標指" in idx_choice: ticker_sym = "SPY"; b_tickers = SPX_80
    elif "納市" in idx_choice: ticker_sym = "QQQ"; b_tickers = NDX_43
    else: ticker_sym = "IWM"; b_tickers = IWM_32

    with st.spinner(f"⏳ 大宗師正在計算市寬數據... 請稍候 ☕🚀"):
        try:
            idx_df = smart_fetch(ticker_sym, period="2y")
            if not idx_df.empty:
                idx_df['20MA'] = idx_df['Close'].rolling(20).mean()
                idx_df['50MA'] = idx_df['Close'].rolling(50).mean()
                idx_df['150MA'] = idx_df['Close'].rolling(150).mean()
                idx_df['200MA'] = idx_df['Close'].rolling(200).mean()
                
                clean_recent = idx_df.tail(250).copy()
                dates = clean_recent.index.strftime('%Y-%m-%d')
                
                if len(clean_recent) > 150:
                    curr_50 = clean_recent['50MA'].iloc[-1]
                    curr_150 = clean_recent['150MA'].iloc[-1]
                    past_150 = clean_recent['150MA'].iloc[-10] 
                    if curr_50 < curr_150 and curr_150 < past_150:
                        st.markdown("<div class='bear-warning'>🚨 警告：已進入熊市 (10周線跌穿30周線，且30周線向下) 🚨</div>", unsafe_allow_html=True)
                
                b_stats = get_breadth_data(b_tickers)
                v_count = b_stats['valid']
                
                st.markdown(f"### 🌊 {idx_choice} - 內部成份股市寬健康度")
                st.markdown(f"<div style='color: white; font-size:1.1rem; margin-bottom:15px;'>（系統真實成功掃描：<b style='color:#00FFCC;'>{v_count}</b> 隻核心成份股）</div>", unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style='display: flex; justify-content: space-between; text-align: center; background-color: #111; padding: 20px; border-radius: 15px;'>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>20市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['20MA']/v_count)*100:.1f}%</span></div>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>50市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['50MA']/v_count)*100:.1f}%</span></div>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>150市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['150MA']/v_count)*100:.1f}%</span></div>
                    <div><span style='color: #00FFCC; font-size: 1.2rem; font-weight: bold;'>200市寬線之上</span><br><span style='color: white; font-size: 3rem; font-weight: 900;'>{(b_stats['200MA']/v_count)*100:.1f}%</span></div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<h4 style='color:#FFF; margin-top:20px; margin-bottom:5px;'>📊 最近 20 日市寬變化趨勢</h4>", unsafe_allow_html=True)
                fig_trend = go.Figure()
                
                x_dates = clean_recent.index[-20:].strftime('%m-%d').tolist()
                if len(x_dates) < 20: 
                    x_dates = [f"D{i}" for i in range(-19, 1)]
                
                y_20 = [(v/v_count)*100 for v in b_stats['hist_20MA']]
                y_50 = [(v/v_count)*100 for v in b_stats['hist_50MA']]
                y_150 = [(v/v_count)*100 for v in b_stats['hist_150MA']]
                y_200 = [(v/v_count)*100 for v in b_stats['hist_200MA']]

                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_20, mode='lines+markers', name='20市寬線', line=dict(color='white', width=2)))
                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_50, mode='lines+markers', name='50市寬線', line=dict(color='yellow', width=2)))
                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_150, mode='lines+markers', name='150市寬線', line=dict(color='cyan', width=2)))
                fig_trend.add_trace(go.Scatter(x=x_dates, y=y_200, mode='lines+markers', name='200市寬線', line=dict(color='magenta', width=2)))
                
                fig_trend.add_annotation(x=x_dates[-1], y=y_20[-1], text="20市寬", showarrow=False, xanchor="left", xshift=10, font=dict(color="white", size=12))
                fig_trend.add_annotation(x=x_dates[-1], y=y_50[-1], text="50市寬", showarrow=False, xanchor="left", xshift=10, font=dict(color="yellow", size=12))
                fig_trend.add_annotation(x=x_dates[-1], y=y_150[-1], text="150市寬", showarrow=False, xanchor="left", xshift=10, font=dict(color="cyan", size=12))
                fig_trend.add_annotation(x=x_dates[-1], y=y_200[-1], text="200市寬", showarrow=False, xanchor="left", xshift=10, font=dict(color="magenta", size=12))

                fig_trend.update_layout(
                    template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=300,
                    margin=dict(l=20, r=60, t=10, b=20), 
                    xaxis=dict(title="", showgrid=True, gridcolor='#333', type='category'),
                    yaxis=dict(title="市寬 %", range=[0, 105], showgrid=True, gridcolor='#333'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

                st.write("")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.05)
                
                o_col = clean_recent['Open'].values; c_col = clean_recent['Close'].values
                h_col = clean_recent['High'].values; l_col = clean_recent['Low'].values
                v_col = clean_recent['Volume'].values

                if show_b_idx: fig.add_trace(go.Candlestick(x=dates, open=o_col, high=h_col, low=l_col, close=c_col, name=f'{ticker_sym} 基準指數'), row=1, col=1)
                else: fig.add_trace(go.Scatter(x=dates, y=c_col, mode='lines', name='隱藏基準', line=dict(color='rgba(255,255,255,0)')), row=1, col=1)

                if show_b_ma20: fig.add_trace(go.Scatter(x=dates, y=clean_recent['20MA'], mode='lines', name='20市寬線', line=dict(color='white', width=1.5, dash='dot')), row=1, col=1)
                if show_b_ma50: fig.add_trace(go.Scatter(x=dates, y=clean_recent['50MA'], mode='lines', name='50市寬線', line=dict(color='yellow', width=1.5, dash='dot')), row=1, col=1)
                
                if show_b_ma150: 
                    fig.add_trace(go.Scatter(x=dates, y=clean_recent['150MA'], mode='lines', name='150市寬線', line=dict(color='cyan', width=2, dash='dot')), row=1, col=1)
                    if len(clean_recent) > 10 and clean_recent['150MA'].iloc[-1] < clean_recent['150MA'].iloc[-10]:
                        fig.add_annotation(x=dates[-1], y=clean_recent['150MA'].iloc[-1], ax=0, ay=-40, xref="x", yref="y", showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=3, arrowcolor="red", text="⬇")

                if show_b_ma200: 
                    fig.add_trace(go.Scatter(x=dates, y=clean_recent['200MA'], mode='lines', name='200市寬線', line=dict(color='magenta', width=2, dash='dot')), row=1, col=1)
                    if len(clean_recent) > 10 and clean_recent['200MA'].iloc[-1] < clean_recent['200MA'].iloc[-10]:
                        fig.add_annotation(x=dates[-1], y=clean_recent['200MA'].iloc[-1], ax=0, ay=-40, xref="x", yref="y", showarrow=True, arrowhead=3, arrowsize=2, arrowwidth=3, arrowcolor="red", text="⬇")

                colors = ['#00FF00' if c_col[i] >= o_col[i] else '#FF0000' for i in range(len(clean_recent))]
                fig.add_trace(go.Bar(x=dates, y=v_col, marker_color=colors, name='成交量'), row=2, col=1)
                counts, bins = np.histogram(c_col, bins=20, weights=v_col)
                max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                fig.add_trace(go.Bar(y=(bins[:-1] + bins[1:]) / 2, x=counts, orientation='h', marker_color='rgba(0, 255, 204, 0.4)', name='蟹貨區', xaxis='x3', yaxis='y1'))

                fig.update_layout(
                    template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', height=750, 
                    showlegend=True, legend=dict(font=dict(color="white"), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis_rangeslider_visible=False, xaxis=dict(type='category', showgrid=False), 
                    yaxis=dict(showgrid=True, gridcolor='#333'), xaxis3=dict(overlaying='x', side='top', range=[0, max_c*1.1], showgrid=False, showticklabels=False)
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                if ("科指" in idx_choice or "道指" in idx_choice) and b_stats['above_50_list']:
                    st.markdown(f"<h3 style='color: white;'>🏆 逆市名單 ({idx_choice.split(' ')[0]}) - 企穩 50天線之上</h3>", unsafe_allow_html=True)
                    cols = st.columns(6)
                    for i, t in enumerate(b_stats['above_50_list'][:30]):
                        cols[i % 6].info(t)
        except Exception as e: st.error(f"⚠️ 數據載入失敗：{e}")

# =========================================================================
# 🔍 模式 C/F/G：起步尋龍雷達 (個股/ETF) (🌟 修改點 1: 掃股邏輯)
# =========================================================================
elif "雷達" in app_mode and "Mode E" not in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    
    c_mkt, c_sec, c_strat = st.columns([1, 1, 1.5])
    if app_mode == "🔍 千龍起步尋龍雷達 (個股)":
        with c_mkt: m_choice = st.radio("1. 選擇市場", ["🇺🇸 美股", "🇭🇰 港股"])
        is_us = "美股" in m_choice
        is_etf = False
    else:
        is_us = "美股" in app_mode
        is_etf = True
        with c_mkt: st.info(f"鎖定 {app_mode.split(' ')[1]}")
        
    bench_sym = "SPY" if is_us else "^HSI"
    target_dict = (US_ETF_MAP if is_etf else US_STOCK_MAP) if is_us else (HK_ETF_MAP if is_etf else HK_STOCK_MAP)
    
    with c_sec: s_choice = st.selectbox("2. 選擇掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()))
    with c_strat: t_strat = st.radio("3. 戰術過濾 (機變)", ["🔥 極致新高 (ATH)", "🐉 潛龍伏躍 (10-20% 空間)"])
    
    if st.button("📡 發射撒網尋龍電波！"):
        bench_data = smart_fetch(bench_sym, period="2y")
        tickers_to_scan = list(set([t for sub in target_dict.values() for t in sub])) if "全星系" in s_choice else target_dict[s_choice]
        
        found = False; pb = st.progress(0)
        with st.spinner("⏳ 慢速引擎過濾中，請稍候..."):
            for idx, t in enumerate(tickers_to_scan):
                pb.progress((idx + 1) / len(tickers_to_scan))
                if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                try:
                    d_full = smart_fetch(t, period="1y")
                    if len(d_full) > 100:
                        d = d_full.tail(63)
                        curr_p = d['Close'].iloc[-1]
                        ath = d_full['High'].tail(252).max()
                        
                        if t_strat == "🔥 極致新高 (ATH)":
                            if (curr_p / ath) < 0.93: continue
                        else: 
                            if not (0.75 <= (curr_p / ath) <= 0.90): continue

                        tp = (d['High']+d['Low']+d['Close'])/3; nf = tp*d['Volume']*np.where(d['Close']>d['Close'].shift(1).fillna(d['Close']),1,-1)
                        net_flow_20 = nf.tail(20).sum(); conc_20 = (abs(nf.tail(20)).max()/max(abs(nf.tail(20)).sum(), 1))*100
                        obv = (np.sign(d['Close'].diff())*d['Volume']).fillna(0).cumsum()
                        obv_curr = obv.iloc[-1]-obv.iloc[-21]; obv_prev = obv.iloc[-21]-obv.iloc[-41]
                        obv_pct = cap_pct((obv_curr-obv_prev)/max(abs(obv_prev), 1)*100)
                        p_trend = d['Close'].iloc[-1]-d['Close'].iloc[-21]; state = 9
                        if p_trend>=0: state = 1 if obv_pct>20 else 2
                        else: state = 7 if obv_pct>20 else 8
                        
                        crs = safe_n(50+((curr_p/d['Close'].iloc[-min(63, len(d))])-(bench_data['Close'].iloc[-1]/bench_data['Close'].iloc[-min(63, len(bench_data))]))*100)
                        ej = safe_n((d['Volume'].tail(21).mean()/max(d['Volume'].tail(252).mean() if len(d)>200 else d['Volume'].mean(),1))*100)
                        se = safe_n(50+(((curr_p/d['Close'].iloc[-min(5, len(d))])-1)*1200))

                        # 🌟 修改點 1: 完美保留大戶掃貨邏輯！
                        if net_flow_20 > 0 and conc_20 < 50 and state in [1, 2, 7, 8, 9]:
                            if se > 75 and ej > 85 and crs > 52:
                                found = True
                                st.markdown(f"<div class='scan-card-fire'><h2>🎯 {t} | 符合大戶佈局！</h2><p>💰 資金流: {net_flow_20/1e8:.1f}億 | 🎯 集中度: {conc_20:.1f}% | 🌊 OBV: {state}<br>⚡ SE: {se:.1f} | 🔋 EJ: {ej:.1f} | 📈 RS: {crs:.1f}</p></div>", unsafe_allow_html=True)
                except: pass
        if not found: st.warning("💤 雷達掃描完畢，目前未有起飛目標。(此過濾條件為潛龍必勝模式，要求大戶真實佈局)")

# =========================================================================
# 📡 拔河熱力圖 
# =========================================================================
elif "熱力圖" in app_mode:
    st.markdown(f"<h1 class='main-title'>{app_mode}</h1>", unsafe_allow_html=True)
    m_view = st.sidebar.radio("選擇星系", ["🇺🇸 美股陣列", "🇭🇰 港股陣列"])
    is_us = "美股" in m_view; bench_sym = "SPY" if is_us else "^HSI"
    target_map = (US_ETF_MAP if "ETF" in app_mode else US_STOCK_MAP) if is_us else (HK_ETF_MAP if "ETF" in app_mode else HK_STOCK_MAP)
    with st.spinner('拔河排名計算中，慢速防封鎖引擎已啟動...'):
        try:
            bench_df = smart_fetch(bench_sym, period="60d")['Close'].dropna(); results = []
            for name, tickers in target_map.items():
                for idx, t in enumerate(tickers):
                    try:
                        d = smart_fetch(t, period="60d")['Close'].dropna()
                        if len(d) >= 20:
                            rs = 50 + ((d.iloc[-1]/d.iloc[-20]) - (bench_df.iloc[-1]/bench_df.iloc[-20])) * 100
                            results.append({"版塊": name, "RS強弱": round(rs, 1)}); break
                    except: continue
            if results:
                df_rs = pd.DataFrame(results).sort_values("RS強弱", ascending=True)
                fig = go.Figure(go.Bar(x=df_rs["RS強弱"], y=df_rs["版塊"], orientation='h', marker=dict(color=df_rs["RS強弱"], colorscale='Portland')))
                fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font=dict(color='white'), height=700)
                st.plotly_chart(fig, use_container_width=True, theme=None, config={'displayModeBar': False})
        except: pass

# =========================================================================
# 📈 模式 D：VCP 形態戰術掃描 & 防守圖
# =========================================================================
elif app_mode == "📈 VCP 形態戰術掃描 & 防守圖":
    st.markdown("<h1 class='main-title'>📈 VCP 形態戰術掃描 & 防守圖</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background-color:#111; padding:15px; border-radius:10px; border-left: 5px solid #BC13FE; margin-bottom: 20px;'>
        <h3 style='color:#BC13FE; margin-top:0;'>🐉 終極獵龍引擎 (Mark Minervini)</h3>
        <p style='color:#ddd; margin-bottom:0;'>海選：50>150>200多頭排列 | RS Rating > 80 | 大戶掃貨標籤<br>
        狙擊：VCP 形態偵測 | HVN 重貨區動態止損 | 獨立 RS 領先線 | 雙戰術過濾</p>
    </div>
    """, unsafe_allow_html=True)

    c_cat, c_mkt, c_sec, c_strat = st.columns([1, 1, 1.5, 1.5])
    with c_cat: asset_type = st.radio("1. 資產類別", ["🏢 領頭個股", "🧺 優質 ETF"])
    with c_mkt: market_choice = st.radio("2. 掃描市場", ["🇺🇸 美股", "🇭🇰 港股"])
    
    is_us = "美股" in market_choice
    is_etf = "ETF" in asset_type
    bench_sym = "SPY" if is_us else "2800.HK"
    
    if is_etf: target_dict = US_ETF_MAP if is_us else HK_ETF_MAP
    else: target_dict = US_STOCK_MAP if is_us else HK_STOCK_MAP
    
    with c_sec: s_choice = st.selectbox("3. 選擇掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()))
    with c_strat: vcp_strat = st.radio("4. 戰術過濾 (機變)", ["🔥 極致新高 (ATH)", "🐉 潛龍伏躍 (10-20% 空間)"])

    if 'vcp_scanned_stocks' not in st.session_state:
        st.session_state.vcp_scanned_stocks = []

    if st.button("📡 [神掣] 發射！執行核心 RS 海選與大戶偵測"):
        tickers_to_scan = list(set([t for sub in target_dict.values() for t in sub])) if "全星系" in s_choice else target_dict[s_choice]
        found_stocks = []
        pb = st.progress(0)
        
        with st.spinner("⏳ 慢速防封鎖引擎已啟動，正在對比大盤 RS 同尋找大戶足跡..."):
            try:
                bench_df = smart_fetch(bench_sym, period="1y")['Close'].dropna()
                yearly_returns = {}
                valid_dfs = {}
                for idx, t in enumerate(tickers_to_scan):
                    pb.progress((idx + 1) / len(tickers_to_scan))
                    if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                    try:
                        df_t = smart_fetch(t, period="1y")
                        if len(df_t) > 150:
                            ret = (df_t['Close'].iloc[-1] / df_t['Close'].iloc[0]) - 1
                            yearly_returns[t] = ret
                            valid_dfs[t] = df_t
                    except: continue

                if yearly_returns:
                    all_rets = pd.Series(list(yearly_returns.values()))
                    for t, ret in yearly_returns.items():
                        df_vcp = valid_dfs[t]
                        df_vcp['MA50'] = df_vcp['Close'].rolling(50).mean()
                        df_vcp['MA150'] = df_vcp['Close'].rolling(150).mean()
                        df_vcp['MA200'] = df_vcp['Close'].rolling(200).mean()
                        curr = df_vcp.iloc[-1]
                        ath = df_vcp['High'].tail(252).max()
                        
                        if not (curr['Close'] > df_vcp['MA50'].iloc[-1] and df_vcp['MA50'].iloc[-1] > df_vcp['MA150'].iloc[-1]): continue
                        
                        if vcp_strat == "🔥 極致新高 (ATH)":
                            if not (df_vcp['MA150'].iloc[-1] > df_vcp['MA200'].iloc[-1]): continue
                            if (curr['Close'] / ath) < 0.93: continue
                        else:
                            if not (0.75 <= (curr['Close'] / ath) <= 0.90): continue

                        rs_rating = int((all_rets[all_rets <= ret].count() / len(all_rets)) * 99)
                        if rs_rating < 80: continue
                        
                        df_vcp['Vol50'] = df_vcp['Volume'].rolling(50).mean()
                        whale_count = len(df_vcp.tail(10)[(df_vcp.tail(10)['Close'] > df_vcp.tail(10)['Open']) & (df_vcp.tail(10)['Volume'] > df_vcp.tail(10)['Vol50'] * 1.5)])
                        
                        found_stocks.append({
                            'Ticker': t, 'RS Rating': rs_rating, 'Tags': f"🔥 大戶掃貨 ({whale_count}/10)" if whale_count >= 3 else "",
                            'Pivot': df_vcp['High'].tail(20).max()
                        })
                st.session_state.vcp_scanned_stocks = sorted(found_stocks, key=lambda x: x['RS Rating'], reverse=True)
            except Exception as e: st.error(f"掃描受限: {e}")

    if st.session_state.vcp_scanned_stocks:
        st.success(f"🎉 成功尋獲 {len(st.session_state.vcp_scanned_stocks)} 隻終極潛力標的！")
        
        st.markdown("### 🏆 領頭羊精銳名單")
        for s in st.session_state.vcp_scanned_stocks:
            bg = "scan-card-super" if '🔥' in s['Tags'] else "scan-card-fire"
            st.markdown(f"<div class='{bg}'><div style='display:flex; justify-content:space-between;'><span style='font-size:1.5rem; font-weight:bold; color:white;'>[{s['Ticker']}] 趨勢: ✅ | RS Rating: <span style='color:#00FFCC;'>{s['RS Rating']}</span></span><span style='font-size:1.2rem; font-weight:bold; color:#FFD700;'>{s['Tags']}</span></div></div>", unsafe_allow_html=True)

        st.write("---")
        selected_stock = st.selectbox("🎯 選擇目標查看「3 層視覺化戰術儀表板」", [s['Ticker'] for s in st.session_state.vcp_scanned_stocks])
        if selected_stock:
            sel_data = next((item for item in st.session_state.vcp_scanned_stocks if item["Ticker"] == selected_stock), None)
            pivot_price = sel_data['Pivot']
            
            with st.spinner("正在繪製 K線、重貨區 HVN 及 RS 領先線..."):
                try:
                    df = smart_fetch(selected_stock, period="6mo")
                    b_df = smart_fetch(bench_sym, period="6mo")['Close']
                    df['MA50'] = df['Close'].rolling(50).mean()
                    df['Vol50'] = df['Volume'].rolling(50).mean()
                    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
                    
                    df_a, b_a = df['Close'].align(b_df, join='inner')
                    rs_line = (df_a / b_a).reindex(df.index).ffill().bfill() 
                    
                    counts, bins = np.histogram(df['Close'], bins=25, weights=df['Volume'])
                    hvn_price = (bins[np.argmax(counts)] + bins[np.argmax(counts)+1]) / 2
                    stop_loss = hvn_price * 0.985
                    
                    df['H-L'] = df['High'] - df['Low']
                    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
                    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
                    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
                    df['ATR'] = df['TR'].rolling(14).mean()
                    atr_stop = df['Close'].iloc[-1] - (1.5 * df['ATR'].iloc[-1]) if not pd.isna(df['ATR'].iloc[-1]) else stop_loss
                    
                    risk_pct = ((df['Close'].iloc[-1] - stop_loss) / df['Close'].iloc[-1]) * 100

                    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[0.6, 0.2, 0.2], vertical_spacing=0.03)
                    dates = df.index.strftime('%Y-%m-%d')
                    
                    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['MA50'], mode='lines', name='50MA (黃實線)', line=dict(color='yellow', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['EMA10'], mode='lines', name='10 EMA (橙虛線)', line=dict(color='orange', width=1.5, dash='dot')), row=1, col=1)
                    
                    fig.add_hline(y=pivot_price, line_dash="dash", line_color="#00FFCC", annotation_text=f"🎯 買入 (Pivot): ${pivot_price:.2f}", annotation_position="top left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    fig.add_hline(y=stop_loss, line_dash="solid", line_color="#FF4B4B", annotation_text=f"🛑 重貨區止損: ${stop_loss:.2f}", annotation_position="bottom left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    fig.add_hline(y=atr_stop, line_dash="dash", line_color="#BC13FE", annotation_text=f"🛡️ 1.5 ATR 止損: ${atr_stop:.2f}", annotation_position="bottom right", annotation_font=dict(color="white", size=13), row=1, col=1)
                    
                    max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(136, 136, 136, 0.4)', name='重貨區 HVN', hoverinfo='skip', xaxis='x4', yaxis='y1'))
                    
                    v_colors = ['#00FF00' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF0000' for i in range(len(df))]
                    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    for i in range(len(df)):
                        if df['Close'].iloc[i] > df['Open'].iloc[i] and df['Volume'].iloc[i] > df['Vol50'].iloc[i]*1.5:
                            fig.add_annotation(x=dates[i], y=df['Volume'].iloc[i], text="🌟", showarrow=False, yanchor="bottom", xanchor="center", font=dict(size=14, color="#FFD700"), row=2, col=1)

                    fig.add_trace(go.Scatter(x=dates, y=rs_line, mode='lines', line=dict(color='#BC13FE', width=2), name="RS線"), row=3, col=1)
                    if df['Close'].iloc[-1] < df['Close'].tail(20).max() * 0.98 and rs_line.iloc[-1] >= rs_line.tail(20).max() * 0.99:
                        fig.add_annotation(x=dates[-1], y=rs_line.iloc[-1], text="🌟 起步點！", showarrow=True, ax=-40, ay=-30, font=dict(color="white", size=14), row=3, col=1)

                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=850,
                                      hovermode='x unified',
                                      xaxis_rangeslider_visible=False, 
                                      xaxis=dict(type='category', showticklabels=False, showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      xaxis2=dict(type='category', showticklabels=False, showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'),
                                      xaxis3=dict(type='category', title="日期", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      yaxis=dict(title="股價", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      yaxis2=dict(title="成交量", showticklabels=False),
                                      yaxis3=dict(title="RS Rating", showticklabels=False),
                                      xaxis4=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False),
                                      legend=dict(font=dict(color="white", size=13), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True)

                    risk_alert = f"<span style='color:#FF4B4B;'>⚠️ 長線防波堤極限風險 ({risk_pct:.1f}%)，請相應縮小買入倉位！</span>" if risk_pct > 7.0 else f"<span style='color:#00FFCC;'>✅ 長線防波堤風險可控 ({risk_pct:.1f}%)</span>"
                    st.markdown(f"<div style='background-color:#111; padding:20px; border-radius:10px; border:2px solid #FFD700;'><h4 style='color:#FFD700; margin-top:0;'>🛡️ 三重防線管理</h4><p style='font-size:1.2rem; color:white;'>🎯 設定買入觸發價 (Pivot)： <b style='color:#00FFCC;'>${pivot_price:.2f}</b></p><hr style='border-color:#333;'><p style='font-size:1.1rem; color:white;'>1️⃣ 極限短炒止盈 (10 EMA)： <b style='color:orange;'>${df['EMA10'].iloc[-1]:.2f}</b></p><p style='font-size:1.1rem; color:white;'>2️⃣ 波段抗震止損 (1.5 ATR)： <b style='color:#BC13FE;'>${atr_stop:.2f}</b></p><p style='font-size:1.1rem; color:white;'>3️⃣ 終極底線止損 (HVN 重貨區)： <b style='color:#FF4B4B;'>${stop_loss:.2f}</b></p><p>{risk_alert}</p></div>", unsafe_allow_html=True)
                except Exception as e: st.error(f"繪圖出錯: {e}")

# =========================================================================
# 🌊 模式 E：海龜回測加注雷達 (雙戰術升級版)
# =========================================================================
elif app_mode == "🌊 海龜回測加注雷達 (Mode E)":
    st.markdown("<h1 class='main-title'>🌊 海龜回測加注雷達 (Mode E)</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background-color:#111; padding:15px; border-radius:10px; border-left: 5px solid #00FFCC; margin-bottom: 20px;'>
        <h3 style='color:#00FFCC; margin-top:0;'>🐢 N字型突破加注法 (1-2-3 Continuation)</h3>
        <p style='color:#ddd; margin-bottom:0;'>此雷達已實裝「真龍基因過濾」：先過濾最強 RS，再搵 <b>N字回測 10 EMA</b>。<br>
        確保踢走所有弱勢股，只搵強者回調嘅黃金加注機會！</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1, 1.5])
    with c1: asset_type = st.radio("1. 掃描對象", ["🏢 領頭個股", "🧺 優質 ETF"])
    with c2: market_choice = st.radio("2. 掃描市場", ["🇺🇸 美股", "🇭🇰 港股"])
    with c3: turtle_strat = st.radio("3. 海龜戰術 (機變)", ["🔥 極致真龍 (ATH 回測)", "🐉 潛龍初醒 (剛入強勢)"])

    is_us = "美股" in market_choice
    is_etf = "ETF" in asset_type
    target_dict = (US_ETF_MAP if is_etf else US_STOCK_MAP) if is_us else (HK_ETF_MAP if is_etf else HK_STOCK_MAP)
    s_choice = st.selectbox("4. 選擇掃描範圍", ["🌐 啟動全星系大規模搜索"] + list(target_dict.keys()))

    if 'e_scanned_stocks' not in st.session_state:
        st.session_state.e_scanned_stocks = []

    if st.button("📡 發射真龍 N 字雷達！"):
        tickers = list(set([t for sub in target_dict.values() for t in sub])) if "星系" in s_choice else target_dict[s_choice]
        found = []
        pb = st.progress(0)
        
        with st.spinner("⏳ 雷達正在慢速穩定過濾「去弱留強」 N 字加注點..."):
            yearly_returns = {}
            valid_dfs = {}
            for idx, t in enumerate(tickers):
                pb.progress((idx + 1) / len(tickers))
                if idx > 0 and idx % 10 == 0: time.sleep(1.0)
                try:
                    df_t = smart_fetch(t, period="1y")
                    if len(df_t) > 150:
                        ret = (df_t['Close'].iloc[-1] / df_t['Close'].iloc[0]) - 1
                        yearly_returns[t] = ret
                        valid_dfs[t] = df_t
                except: continue
            
            if yearly_returns:
                all_rets = pd.Series(list(yearly_returns.values()))
                for t, ret in yearly_returns.items():
                    df = valid_dfs[t]
                    curr_p = df['Close'].iloc[-1]
                    ma50 = df['Close'].rolling(50).mean().iloc[-1]
                    ma150 = df['Close'].rolling(150).mean().iloc[-1]
                    ma200 = df['Close'].rolling(200).mean().iloc[-1]
                    ema10 = df['Close'].ewm(span=10, adjust=False).mean().iloc[-1]
                    ath = df['High'].tail(252).max()
                    
                    rs_rating = int((all_rets[all_rets <= ret].count() / len(all_rets)) * 99)
                    
                    # 1. 趨勢過濾
                    if not (curr_p > ma50 and ma50 > ma150): continue
                    
                    # 2. 戰術過濾
                    if turtle_strat == "🔥 極致真龍 (ATH 回測)":
                        if not (ma150 > ma200): continue 
                        if (curr_p / ath) < 0.90: continue
                        if rs_rating < 80: continue
                    else: # 🐉 潛龍初醒
                        if not (0.75 <= (curr_p / ath) <= 0.92): continue 
                        if rs_rating < 70: continue

                    # 3. N字回測過濾
                    last_20_high = df['High'].tail(20).max()
                    high_idx = df['High'].tail(20).argmax()
                    days_since_high = 19 - high_idx
                    
                    if 2 <= days_since_high <= 15: # 回落中
                        pullback_pct = ((curr_p - last_20_high) / last_20_high) * 100
                        if -15 <= pullback_pct <= -1:
                            if ema10 * 0.98 <= curr_p <= ema10 * 1.04: # 企穩 10 EMA
                                swing_low = df['Low'].iloc[-days_since_high:].min()
                                found.append({
                                    'Ticker': t, 'Price': curr_p, 'High': last_20_high,
                                    'Low': swing_low, 'Pullback': pullback_pct, 'EMA10': ema10,
                                    'Days Since High': days_since_high
                                })
            
            st.session_state.e_scanned_stocks = sorted(found, key=lambda x: x['Pullback'], reverse=True)

    if st.session_state.e_scanned_stocks:
        st.success(f"🎉 捕捉到 {len(st.session_state.e_scanned_stocks)} 隻健康回測中嘅目標！")
        for p in st.session_state.e_scanned_stocks:
            st.markdown(f"""
            <div class='pullback-card'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <span style='font-size:1.8rem; font-weight:bold; color:white;'>🎯 [{p['Ticker']}]</span>
                    <span style='font-size:1.2rem; font-weight:bold; color:#00FFCC;'>現價: ${p['Price']:.2f}</span>
                </div>
                <hr style='border-color:#444; margin:10px 0;'>
                <div style='display:flex; justify-content:space-between;'>
                    <span>📈 前高阻力 (海龜買入點): <b style='color:#00FFCC;'>${p['High']:.2f}</b> <span style='font-size:0.9rem;'>({p['Days Since High']} 日前)</span></span>
                    <span>📉 回落幅度: <b style='color:#FF4B4B;'>{p['Pullback']:.1f}%</b></span>
                </div>
                <div style='display:flex; justify-content:space-between; margin-top:5px;'>
                    <span>🛡️ 極限防守 (10 EMA): <b style='color:orange;'>${p['EMA10']:.2f}</b></span>
                    <span>🛑 N字波谷底 (海龜止損): <b style='color:#FF00FF;'>${p['Low']:.2f}</b></span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("---")
        sel = st.selectbox("🎯 選擇目標查看 X 光戰術圖", [s['Ticker'] for s in st.session_state.e_scanned_stocks])
        if sel:
            p_data = next(x for x in st.session_state.e_scanned_stocks if x['Ticker'] == sel)
            with st.spinner("正在為您繪製專屬海龜回測戰術圖表..."):
                try:
                    df = smart_fetch(sel, period="6mo")
                    df['MA50'] = df['Close'].rolling(50).mean()
                    df['EMA10'] = df['Close'].ewm(span=10, adjust=False).mean()
                    
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
                    dates = df.index.strftime('%Y-%m-%d')
                    
                    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['MA50'], mode='lines', name='50MA (黃實線)', line=dict(color='yellow', width=1.5)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=dates, y=df['EMA10'], mode='lines', name='10 EMA (橙虛線)', line=dict(color='orange', width=2, dash='dot')), row=1, col=1)
                    
                    fig.add_hline(y=p_data['High'], line_dash="dash", line_color="#00FFCC", annotation_text=f"🐢 破頂買入: ${p_data['High']:.2f}", annotation_position="top left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    fig.add_hline(y=p_data['Low'], line_dash="solid", line_color="#FF00FF", annotation_text=f"🛑 波谷止損: ${p_data['Low']:.2f}", annotation_position="bottom left", annotation_font=dict(color="white", size=13), row=1, col=1)
                    
                    counts, bins = np.histogram(df['Close'], bins=30, weights=df['Volume'])
                    max_c = max(counts) if len(counts) > 0 and max(counts) > 0 else 1
                    fig.add_trace(go.Bar(y=(bins[:-1]+bins[1:])/2, x=counts, orientation='h', marker_color='rgba(150,150,150,0.3)', name='重貨區', hoverinfo='skip', xaxis='x4', yaxis='y1'))

                    v_colors = ['#00FF00' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#FF0000' for i in range(len(df))]
                    fig.add_trace(go.Bar(x=dates, y=df['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)
                    
                    fig.update_layout(template="plotly_dark", paper_bgcolor='#0e1117', plot_bgcolor='#111', height=650,
                                      hovermode='x unified',
                                      xaxis_rangeslider_visible=False, 
                                      xaxis=dict(type='category', showticklabels=False, showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      xaxis2=dict(type='category', title="日期", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      xaxis4=dict(overlaying='x1', anchor='y1', side='top', range=[0, max_c*4], showgrid=False, showticklabels=False),
                                      yaxis=dict(title="股價", showspikes=True, spikemode='across', spikecolor="white", spikethickness=1, spikedash='dot'), 
                                      yaxis2=dict(title="成交量", showticklabels=False),
                                      legend=dict(font=dict(color="white", size=13), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e: st.error(f"繪圖出錯: {e}")
    else:
        st.warning("💤 雷達掃描完畢，未有符合雙重過濾之標的。")
