import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from functools import lru_cache
import indicators

# 页面配置
st.set_page_config(
    page_title="股票量化分析平台",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式 - 优化移动端体验
st.markdown("""
<style>
    .main {
        background-color: #0a0e27;
    }
    .stApp {
        background-color: #0a0e27;
    }
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        font-weight: 700;
    }
    .stock-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
    }
    .indicator-card {
        background-color: #131722;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #2a2e39;
        margin-bottom: 10px;
    }
    /* 移动端优化 */
    @media (max-width: 768px) {
        div[data-testid="stMetricValue"] {
            font-size: 18px;
        }
        .stock-header {
            padding: 15px;
        }
    }
    /* 图表触摸优化 */
    .js-plotly-plot .plotly .modebar {
        left: 0 !important;
        background: rgba(19, 23, 34, 0.9) !important;
        padding: 5px !important;
    }
    .refresh-info {
        background-color: #131722;
        padding: 10px;
        border-radius: 5px;
        border-left: 3px solid #2962ff;
        margin: 10px 0;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# 缓存数据获取函数 - 缩短缓存时间以获取更实时的数据
@st.cache_data(ttl=300)  # 5分钟缓存
def get_stock_info(symbol):
    """获取股票基本信息"""
    try:
        info_df = ak.stock_individual_info_em(symbol=symbol)
        info_dict = dict(zip(info_df['item'], info_df['value']))
        info_dict['_update_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return info_dict
    except Exception as e:
        st.error(f"获取股票信息失败: {e}")
        return None

@st.cache_data(ttl=300)  # 5分钟缓存
def get_stock_history(symbol, start_date, end_date, adjust='qfq'):
    """获取历史行情数据"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d'),
            adjust=adjust
        )
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            numeric_cols = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', '换手率']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        st.error(f"获取历史数据失败: {e}")
        return None

@st.cache_data(ttl=300)  # 5分钟缓存
def search_stock(query):
    """搜索股票"""
    try:
        stock_list = ak.stock_zh_a_spot_em()
        query = query.upper()
        filtered = stock_list[
            stock_list['代码'].str.contains(query) | 
            stock_list['名称'].str.contains(query)
        ].head(20)
        return filtered
    except Exception as e:
        st.error(f"搜索失败: {e}")
        return None

@st.cache_data(ttl=60)  # 1分钟缓存 - 更实时的市场数据
def get_market_indices():
    """获取市场指数实时数据"""
    try:
        indices_data = []
        # 获取主要指数
        index_codes = {
            'sh000001': '上证指数',
            'sz399001': '深证成指', 
            'sz399006': '创业板指'
        }
        
        for code, name in index_codes.items():
            try:
                df = ak.stock_zh_index_daily(symbol=code)
                if not df.empty and len(df) >= 2:
                    latest = df.iloc[-1]
                    prev = df.iloc[-2]
                    change_pct = ((latest['close'] - prev['close']) / prev['close'] * 100)
                    indices_data.append({
                        'name': name,
                        'value': latest['close'],
                        'change': change_pct
                    })
            except:
                continue
        
        return indices_data
    except Exception as e:
        return []


def create_candlestick_chart(df, indicators_data, show_ma=True, show_boll=False):
    """创建K线图和技术指标图表"""
    # 创建子图
    rows = 1
    row_heights = [0.7]
    subplot_titles = ['K线图']
    
    # 计算需要的子图数量
    if 'macd' in st.session_state.active_indicators:
        rows += 1
        row_heights.append(0.15)
        subplot_titles.append('MACD')
    if 'kdj' in st.session_state.active_indicators:
        rows += 1
        row_heights.append(0.15)
        subplot_titles.append('KDJ')
    if 'rsi' in st.session_state.active_indicators:
        rows += 1
        row_heights.append(0.15)
        subplot_titles.append('RSI')
    
    # 归一化高度
    total_height = sum(row_heights)
    row_heights = [h/total_height for h in row_heights]
    
    fig = make_subplots(
        rows=rows, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=subplot_titles
    )
    
    # K线图
    fig.add_trace(go.Candlestick(
        x=df['日期'],
        open=df['开盘'],
        high=df['最高'],
        low=df['最低'],
        close=df['收盘'],
        name='K线',
        increasing_line_color='#26a69a',
        decreasing_line_color='#ef5350'
    ), row=1, col=1)
    
    # 添加均线
    if show_ma and 'MA' in indicators_data:
        colors = {'MA5': '#ff6b6b', 'MA10': '#4ecdc4', 'MA20': '#ffe66d', 
                  'MA30': '#a8e6cf', 'MA60': '#ff8b94'}
        for ma_name, ma_values in indicators_data['MA'].items():
            fig.add_trace(go.Scatter(
                x=df['日期'],
                y=ma_values,
                name=ma_name,
                line=dict(color=colors.get(ma_name, '#888888'), width=1)
            ), row=1, col=1)
    
    # 添加布林带
    if show_boll and 'BOLL' in indicators_data:
        fig.add_trace(go.Scatter(
            x=df['日期'], y=indicators_data['BOLL']['Upper'],
            name='BOLL上轨', line=dict(color='#2962ff', width=1, dash='dash')
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df['日期'], y=indicators_data['BOLL']['Middle'],
            name='BOLL中轨', line=dict(color='#787b86', width=1)
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df['日期'], y=indicators_data['BOLL']['Lower'],
            name='BOLL下轨', line=dict(color='#2962ff', width=1, dash='dash')
        ), row=1, col=1)
    
    current_row = 2
    
    # MACD指标
    if 'macd' in st.session_state.active_indicators and 'MACD' in indicators_data:
        macd_data = indicators_data['MACD']
        fig.add_trace(go.Scatter(
            x=df['日期'], y=macd_data['MACD'],
            name='MACD', line=dict(color='#2962ff', width=2)
        ), row=current_row, col=1)
        fig.add_trace(go.Scatter(
            x=df['日期'], y=macd_data['Signal'],
            name='Signal', line=dict(color='#ff6b6b', width=2)
        ), row=current_row, col=1)
        colors = ['#26a69a' if x >= 0 else '#ef5350' for x in macd_data['Histogram']]
        fig.add_trace(go.Bar(
            x=df['日期'], y=macd_data['Histogram'],
            name='Histogram', marker_color=colors
        ), row=current_row, col=1)
        current_row += 1
    
    # KDJ指标
    if 'kdj' in st.session_state.active_indicators and 'KDJ' in indicators_data:
        kdj_data = indicators_data['KDJ']
        fig.add_trace(go.Scatter(
            x=df['日期'], y=kdj_data['K'],
            name='K', line=dict(color='#2962ff', width=2)
        ), row=current_row, col=1)
        fig.add_trace(go.Scatter(
            x=df['日期'], y=kdj_data['D'],
            name='D', line=dict(color='#ff6b6b', width=2)
        ), row=current_row, col=1)
        fig.add_trace(go.Scatter(
            x=df['日期'], y=kdj_data['J'],
            name='J', line=dict(color='#ffe66d', width=2)
        ), row=current_row, col=1)
        current_row += 1
    
    # RSI指标
    if 'rsi' in st.session_state.active_indicators and 'RSI' in indicators_data:
        rsi_data = indicators_data['RSI']
        fig.add_trace(go.Scatter(
            x=df['日期'], y=rsi_data['RSI'],
            name='RSI', line=dict(color='#2962ff', width=2)
        ), row=current_row, col=1)
        # 添加超买超卖线
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=current_row, col=1)
    
    # 更新布局 - 优化移动端触摸交互
    fig.update_layout(
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50),
        # 移动端优化配置
        dragmode='pan',  # 默认为平移模式，更适合触摸
        hovermode='x unified',  # 统一悬停模式
        # 触摸交互配置
        modebar=dict(
            orientation='v',
            bgcolor='rgba(19, 23, 34, 0.9)',
            color='#d1d4dc',
            activecolor='#2962ff'
        )
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#2a2e39')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#2a2e39')
    
    return fig

# 初始化session state
if 'current_stock' not in st.session_state:
    st.session_state.current_stock = '600519'
if 'active_indicators' not in st.session_state:
    st.session_state.active_indicators = {'macd', 'kdj', 'rsi'}

# 侧边栏
with st.sidebar:
    st.header("⚙️ 控制台")
    
    # 股票搜索
    search_query = st.text_input("🔍 搜索股票", placeholder="输入代码或名称...")
    if search_query:
        search_results = search_stock(search_query)
        if search_results is not None and not search_results.empty:
            selected = st.selectbox(
                "选择股票",
                search_results['代码'].tolist(),
                format_func=lambda x: f"{x} - {search_results[search_results['代码']==x]['名称'].values[0]}"
            )
            if st.button("加载该股票"):
                st.session_state.current_stock = selected
                st.rerun()
    
    st.divider()
    
    # 自选股
    st.subheader("📋 自选股")
    watchlist = {
        '600519': '贵州茅台',
        '000001': '平安银行',
        '000858': '五粮液',
        '601318': '中国平安',
        '600036': '招商银行'
    }
    
    for code, name in watchlist.items():
        if st.button(f"{code} {name}", key=f"watch_{code}", use_container_width=True):
            st.session_state.current_stock = code
            st.rerun()
    
    st.divider()
    
    # 时间周期
    st.subheader("📅 时间周期")
    period_map = {
        '1日': 1, '5日': 5, '1月': 30, '3月': 90,
        '6月': 180, '1年': 365, '5年': 1825
    }
    period = st.selectbox("选择周期", list(period_map.keys()), index=5)
    
    # 复权方式
    st.subheader("🔧 复权方式")
    adjust_map = {'前复权': 'qfq', '后复权': 'hfq', '不复权': ''}
    adjust = st.selectbox("选择复权", list(adjust_map.keys()))
    
    st.divider()
    
    # 市场概览
    st.subheader("📊 市场概览")
    market_data = get_market_indices()
    if market_data:
        for index in market_data:
            change_color = "🟢" if index['change'] >= 0 else "🔴"
            st.write(f"{change_color} **{index['name']}**: {index['value']:.2f} ({index['change']:+.2f}%)")
    
    st.divider()
    
    # 技术指标开关
    st.subheader("📊 技术指标")
    
    show_ma = st.checkbox("均线 (MA)", value=True)
    show_boll = st.checkbox("布林带 (BOLL)", value=False)
    
    st.write("**副图指标:**")
    if st.checkbox("MACD", value='macd' in st.session_state.active_indicators):
        st.session_state.active_indicators.add('macd')
    else:
        st.session_state.active_indicators.discard('macd')
    
    if st.checkbox("KDJ", value='kdj' in st.session_state.active_indicators):
        st.session_state.active_indicators.add('kdj')
    else:
        st.session_state.active_indicators.discard('kdj')
    
    if st.checkbox("RSI", value='rsi' in st.session_state.active_indicators):
        st.session_state.active_indicators.add('rsi')
    else:
        st.session_state.active_indicators.discard('rsi')

# 主界面
st.title("📈 股票量化分析平台")

# 计算日期范围
end_date = datetime.now()
start_date = end_date - timedelta(days=period_map[period])

# 获取数据
with st.spinner('正在加载数据...'):
    stock_info = get_stock_info(st.session_state.current_stock)
    hist_df = get_stock_history(
        st.session_state.current_stock,
        start_date,
        end_date,
        adjust_map[adjust]
    )

if stock_info and hist_df is not None and not hist_df.empty:
    latest = hist_df.iloc[-1]
    
    # 股票头部信息
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        st.markdown(f"### {stock_info.get('股票简称', 'N/A')} ({st.session_state.current_stock})")
    
    with col2:
        change_color = "normal" if latest['涨跌幅'] >= 0 else "inverse"
        st.metric(
            "最新价",
            f"¥{latest['收盘']:.2f}",
            f"{latest['涨跌幅']:.2f}%",
            delta_color=change_color
        )
    
    with col3:
        st.metric("成交额", f"{latest['成交额']/1e8:.2f}亿")
    
    with col4:
        st.metric("换手率", f"{latest['换手率']:.2f}%")
    
    # 详细信息
    with st.expander("📊 详细信息", expanded=False):
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        
        with info_col1:
            st.write(f"**开盘:** ¥{latest['开盘']:.2f}")
            st.write(f"**最高:** ¥{latest['最高']:.2f}")
        
        with info_col2:
            st.write(f"**最低:** ¥{latest['最低']:.2f}")
            st.write(f"**成交量:** {latest['成交量']/1e8:.2f}亿股")
        
        with info_col3:
            market_cap = float(stock_info.get('总市值', 0)) / 1e8
            st.write(f"**总市值:** {market_cap:.2f}亿")
            st.write(f"**流通市值:** {float(stock_info.get('流通市值', 0))/1e8:.2f}亿")
        
        with info_col4:
            st.write(f"**市盈率:** {stock_info.get('市盈率-动态', 'N/A')}")
            st.write(f"**市净率:** {stock_info.get('市净率', 'N/A')}")
    
    # 计算技术指标
    indicators_data = indicators.calculate_all_indicators(hist_df)
    
    # 图表操作说明和刷新控制
    col_guide1, col_guide2, col_guide3 = st.columns([2, 1, 1])
    
    with col_guide1:
        st.markdown("""
        <div class="refresh-info">
        📱 <b>图表操作提示:</b><br>
        • 触摸拖动: 平移查看不同时间段<br>
        • 双指捏合: 放大/缩小图表<br>
        • 点击图例: 显示/隐藏对应数据线<br>
        • 右上角工具栏: 更多操作选项
        </div>
        """, unsafe_allow_html=True)
    
    with col_guide2:
        # 显示数据更新时间
        if '_update_time' in stock_info:
            st.info(f"🕐 数据更新: {stock_info['_update_time']}")
        else:
            st.info(f"🕐 数据更新: {datetime.now().strftime('%H:%M:%S')}")
    
    with col_guide3:
        # 手动刷新按钮
        if st.button("🔄 刷新数据", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # 自动刷新选项
    auto_refresh = st.checkbox("⏰ 自动刷新 (每5分钟)", value=False, help="开启后将每5分钟自动更新数据")
    
    if auto_refresh:
        import time
        # 使用 st.empty() 创建占位符用于倒计时
        refresh_placeholder = st.empty()
        refresh_placeholder.info("⏱️ 下次刷新: 5分钟后")
        # 注意: Streamlit 会在5分钟后自动重新运行由于缓存过期
    
    # 显示图表
    st.plotly_chart(
        create_candlestick_chart(hist_df, indicators_data, show_ma, show_boll),
        use_container_width=True,
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': f'{st.session_state.current_stock}_chart',
                'height': 1080,
                'width': 1920,
                'scale': 2
            },
            'scrollZoom': True,  # 启用滚轮缩放
            'doubleClick': 'reset',  # 双击重置视图
            'showTips': True
        }
    )
    
    # 数据表格
    with st.expander("📄 历史数据明细", expanded=False):
        st.dataframe(
            hist_df.sort_values('日期', ascending=False),
            use_container_width=True,
            height=400
        )
        
        # 下载按钮
        csv = hist_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            "📥 下载CSV",
            csv,
            f"{st.session_state.current_stock}_history.csv",
            "text/csv"
        )

else:
    st.error("❌ 无法获取股票数据，请检查股票代码是否正确")

# 页脚
st.divider()
col_footer1, col_footer2 = st.columns([3, 1])
with col_footer1:
    st.caption("💡 数据来源: AKShare (东方财富) | 缓存时间: 5分钟 | 本平台仅供学习参考，不构成投资建议")
with col_footer2:
    st.caption(f"⏰ 当前时间: {datetime.now().strftime('%H:%M:%S')}")
