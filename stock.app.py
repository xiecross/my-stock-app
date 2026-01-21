import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# ---------------------------------------------------------
# 自定义 CSS 样式
# ---------------------------------------------------------
def load_custom_css():
    st.markdown("""
    <style>
    /* 主题色彩 */
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --success-color: #10b981;
        --danger-color: #ef4444;
        --warning-color: #f59e0b;
        --info-color: #3b82f6;
    }
    
    /* 主容器样式 */
    .main {
        background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
        padding: 2rem 1rem;
    }
    
    /* 标题样式 */
    h1 {
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
        text-align: center;
        padding: 0.5rem 0 1.5rem 0;
        margin-bottom: 1rem;
        font-size: 2.5rem;
    }
    
    /* 子标题样式 */
    h3 {
        color: #1e293b;
        font-weight: 700;
        margin-top: 2rem;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
        border-bottom: 3px solid #667eea;
        display: inline-block;
    }
    
    /* 指标卡片容器 */
    [data-testid="stMetric"] {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid rgba(102, 126, 234, 0.1);
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
        transform: translateY(-2px);
    }
    
    /* 指标标签 */
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* 指标值 */
    [data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 800;
        color: #1e293b;
    }
    
    /* 指标变化 */
    [data-testid="stMetricDelta"] {
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 0.5rem;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"] h2 {
        color: white !important;
        font-weight: 700;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(255,255,255,0.3);
    }
    
    [data-testid="stSidebar"] label {
        color: white !important;
        font-weight: 600;
        font-size: 0.875rem;
    }
    
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] select {
        background: rgba(255,255,255,0.9) !important;
        border: none !important;
        border-radius: 8px !important;
        color: #1e293b !important;
    }
    
    /* 按钮样式 */
    .stButton>button {
        border-radius: 25px;
        font-weight: 700;
        padding: 0.6rem 2rem;
        transition: all 0.3s ease;
        border: none;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.875rem;
    }
    
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
        box-shadow: 0 4px 12px rgba(249, 115, 22, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: white;
        padding: 0.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        color: #64748b;
        background: transparent;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* 数据框样式 */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* 扩展器样式 */
    .streamlit-expanderHeader {
        background: white;
        border: 1px solid rgba(102, 126, 234, 0.2);
        border-radius: 12px;
        font-weight: 700;
        color: #1e293b;
        padding: 1rem;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(102, 126, 234, 0.05);
        border-color: #667eea;
    }
    
    /* 信息框样式 */
    .stAlert {
        border-radius: 12px;
        border-left: 5px solid;
        padding: 1rem 1.5rem;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* 复选框样式 */
    [data-testid="stSidebar"] .stCheckbox {
        background: rgba(255,255,255,0.1);
        padding: 0.5rem;
        border-radius: 8px;
        margin: 0.25rem 0;
    }
    
    /* 分隔线样式 */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid rgba(102, 126, 234, 0.2);
    }
    
    /* 卡片容器 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
    }
    
    /* 图表容器 */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. 登录验证逻辑 (支持 URL 参数自动登录)
# ---------------------------------------------------------
def check_password():
    """验证登录状态"""
    # 检查 secrets 是否配置
    try:
        app_password = st.secrets["app_password"]
    except KeyError:
        st.error("❌ 配置错误：未找到 app_password")
        st.info("""
        ### 🔧 配置说明
        
        请在 Streamlit Cloud 的 Secrets 中添加以下配置：
        
        ```toml
        app_password = "your_password_here"
        ```
        
        **本地开发**：创建 `.streamlit/secrets.toml` 文件并添加上述内容
        
        **Streamlit Cloud**：在应用设置 → Secrets 中添加上述内容
        """)
        st.stop()
        return False
    
    if st.query_params.get("auth") == app_password:
        st.session_state["password_correct"] = True
        return True

    def password_entered():
        if st.session_state["password"] == app_password:
            st.session_state["password_correct"] = True
            st.query_params["auth"] = app_password
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 访问受限")
        st.text_input("请输入访问密码", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 访问受限")
        st.text_input("密码错误，请重试", type="password", on_change=password_entered, key="password")
        st.error("❌ 密码不正确")
        return False
    else:
        return True

# ---------------------------------------------------------
# 2. 数据获取函数集
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_base_info(symbol):
    """获取个股多维度基本面信息"""
    try:
        return ak.stock_individual_info_em(symbol=symbol)
    except:
        return None

@st.cache_data(ttl=3600)
def get_hist_data(symbol, start, end, adjust):
    """获取历史行情数据"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="" if adjust == "None" else adjust
        )
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            numeric_cols = ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', '换手率']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except:
        return None

# ---------------------------------------------------------
# 3. 技术指标计算函数
# ---------------------------------------------------------
def calculate_ma(df, periods=[5, 10, 20, 60]):
    """计算移动平均线"""
    for period in periods:
        df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
    return df

def calculate_macd(df, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    exp1 = df['收盘'].ewm(span=fast, adjust=False).mean()
    exp2 = df['收盘'].ewm(span=slow, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']
    return df

def calculate_rsi(df, period=14):
    """计算RSI指标"""
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """计算布林带"""
    df['BB_Middle'] = df['收盘'].rolling(window=period).mean()
    std = df['收盘'].rolling(window=period).std()
    df['BB_Upper'] = df['BB_Middle'] + (std * std_dev)
    df['BB_Lower'] = df['BB_Middle'] - (std * std_dev)
    return df

def add_technical_indicators(df):
    """添加所有技术指标"""
    df = calculate_ma(df)
    df = calculate_macd(df)
    df = calculate_rsi(df)
    df = calculate_bollinger_bands(df)
    return df

def format_value(val, unit_type='amount'):
    """金额和数量的单位自动转换及保留两位小数"""
    try:
        val = float(val)
    except (ValueError, TypeError):
        return "-"
    
    if unit_type == 'amount':
        if abs(val) >= 1e12:
            return f"{val/1e12:.2f} 万亿"
        elif abs(val) >= 1e8:
            return f"{val/1e8:.2f} 亿"
        elif abs(val) >= 1e4:
            return f"{val/1e4:.2f} 万"
        else:
            return f"{val:.2f} 元"
    elif unit_type == 'volume':
        if abs(val) >= 1e12:
            return f"{val/1e12:.2f} 万亿股"
        elif abs(val) >= 1e8:
            return f"{val/1e8:.2f} 亿股"
        elif abs(val) >= 1e4:
            return f"{val/1e4:.2f} 万股"
        else:
            return f"{val:.2f} 股"
    return f"{val:.2f}"

# ---------------------------------------------------------
# 4. 图表创建函数
# ---------------------------------------------------------
def create_candlestick_chart(df, show_ma=True, show_bb=False):
    """创建K线图"""
    fig = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=('价格走势', 'MACD', 'RSI')
    )
    
    # K线图
    fig.add_trace(go.Candlestick(
        x=df['日期'],
        open=df['开盘'],
        high=df['最高'],
        low=df['最低'],
        close=df['收盘'],
        name='K线',
        increasing_line_color='#ef5350',
        decreasing_line_color='#26a69a'
    ), row=1, col=1)
    
    # 移动平均线
    if show_ma:
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
        for i, period in enumerate([5, 10, 20, 60]):
            if f'MA{period}' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['日期'],
                    y=df[f'MA{period}'],
                    name=f'MA{period}',
                    line=dict(color=colors[i], width=1.5),
                    opacity=0.7
                ), row=1, col=1)
    
    # 布林带
    if show_bb and 'BB_Upper' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['日期'],
            y=df['BB_Upper'],
            name='布林上轨',
            line=dict(color='rgba(250, 128, 114, 0.5)', width=1),
            showlegend=False
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df['日期'],
            y=df['BB_Lower'],
            name='布林下轨',
            line=dict(color='rgba(250, 128, 114, 0.5)', width=1),
            fill='tonexty',
            fillcolor='rgba(250, 128, 114, 0.1)',
            showlegend=False
        ), row=1, col=1)
    
    # MACD
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['日期'],
            y=df['MACD'],
            name='MACD',
            line=dict(color='#2196F3', width=1.5)
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=df['日期'],
            y=df['Signal'],
            name='Signal',
            line=dict(color='#FF9800', width=1.5)
        ), row=2, col=1)
        
        colors = ['#26a69a' if val >= 0 else '#ef5350' for val in df['Histogram']]
        fig.add_trace(go.Bar(
            x=df['日期'],
            y=df['Histogram'],
            name='Histogram',
            marker_color=colors,
            opacity=0.5
        ), row=2, col=1)
    
    # RSI
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(
            x=df['日期'],
            y=df['RSI'],
            name='RSI',
            line=dict(color='#9C27B0', width=2)
        ), row=3, col=1)
        
        # RSI 超买超卖线
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
    
    # 更新布局
    fig.update_layout(
        height=800,
        xaxis_rangeslider_visible=True,  # 启用范围滑块
        hovermode='x unified',
        template='plotly_white',
        margin=dict(t=30, b=30, l=50, r=100), # 增加右边距以容纳图例
        legend=dict(
            orientation="v",         # 纵向排列
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02                  # 移至右侧
        ),
        # 启用十字光标跟踪
        xaxis=dict(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikedash='dash',
            spikethickness=1
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Inter"
        )
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    
    return fig

def create_volume_chart(df):
    """创建成交量图表"""
    colors = ['#ef5350' if c >= o else '#26a69a' 
              for c, o in zip(df['收盘'], df['开盘'])]
    
    fig = go.Figure(data=[go.Bar(
        x=df['日期'],
        y=df['成交量'],
        marker_color=colors,
        name='成交量',
        opacity=0.7
    )])
    
    fig.update_layout(
        height=300,
        template='plotly_white',
        margin=dict(t=10, b=30, l=50, r=100), # 增加右边距
        xaxis_title='日期',
        yaxis_title='成交量',
        # 移至右侧
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        # 启用十字光标跟踪
        xaxis=dict(
            showspikes=True,
            spikemode='across',
            spikesnap='cursor',
            spikedash='dash',
            spikethickness=1
        )
    )
    
    return fig

# ---------------------------------------------------------
# 5. 主程序区
# ---------------------------------------------------------
if check_password():
    st.set_page_config(
        page_title="金融数据深度查询终端",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 加载自定义CSS
    load_custom_css()
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 终端控制台")
        
        # 股票代码输入
        symbol = st.text_input(
            "证券代码",
            value="600519",
            help="请输入6位 A 股数字代码"
        )
        
        # 日期选择
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "起始时间",
                datetime.date.today() - datetime.timedelta(days=365)
            )
        with col2:
            end_date = st.date_input(
                "结束时间",
                datetime.date.today()
            )
        
        # 复权选择
        adj_options = {"前复权": "qfq", "后复权": "hfq", "不复权": "None"}
        adjust_display = st.selectbox(
            "复权处理",
            list(adj_options.keys()),
            help="前复权保持现价连续，适合技术分析。"
        )
        adjust_type = adj_options[adjust_display]
        
        # 图表选项
        st.divider()
        st.subheader("📊 图表选项")
        show_ma = st.checkbox("显示均线", value=True)
        show_bb = st.checkbox("显示布林带", value=False)
        
        st.divider()
        btn_query = st.button("🔄 更新行情", type="primary", use_container_width=True)
        
        st.divider()
        if st.button("🔒 安全登出", use_container_width=True):
            st.session_state["password_correct"] = False
            st.query_params.clear()
            st.rerun()

    # 主界面
    st.title("📈 证券行情深度看板")
    
    if btn_query or symbol:
        with st.spinner('🔄 正在同步最新行情数据...'):
            info_df = get_base_info(symbol)
            hist_df = get_hist_data(symbol, start_date, end_date, adjust_type)

        if info_df is not None and hist_df is not None and not hist_df.empty:
            # 添加技术指标
            hist_df = add_technical_indicators(hist_df)
            
            # 数据预处理
            info_dict = dict(zip(info_df['item'], info_df['value']))
            latest = hist_df.iloc[-1]
            
            # --- 第一部分：实时核心指标 ---
            st.markdown("""
            <div style='background: white; padding: 1rem 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>
                <h3 style='margin: 0; color: #1e293b; border: none; display: flex; align-items: center;'>
                    <span style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 0.4rem 0.8rem; border-radius: 8px; margin-right: 0.75rem; font-size: 1rem;'>✓</span>
                    实时概览
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # 第一行：核心数据
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "公司简称",
                    info_dict.get("股票简称", "未知"),
                    help=f"代码: {symbol}"
                )
            
            with col2:
                price_delta = latest['涨跌幅']
                st.metric(
                    "最新价",
                    f"¥{latest['收盘']:.2f}",
                    f"{price_delta:.2f}%",
                    delta_color="normal"
                )
            
            with col3:
                st.metric(
                    "成交额",
                    format_value(latest['成交额']),
                    help="当日买卖总金额"
                )
            
            with col4:
                st.metric(
                    "换手率",
                    f"{latest['换手率']:.2f}%",
                    help="当日成交量占流通股本比例"
                )

            # 第二行：盘中价格
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("今日开盘", f"¥{latest['开盘']:.2f}")
            with col2:
                st.metric("今日最高", f"¥{latest['最高']:.2f}")
            with col3:
                st.metric("今日最低", f"¥{latest['最低']:.2f}")
            with col4:
                if len(hist_df) > 1:
                    prev_close = hist_df.iloc[-2]['收盘']
                    st.metric("昨日收盘", f"¥{prev_close:.2f}")
                else:
                    st.metric("昨日收盘", "-")
            
            
            # 第二行：技术指标
            st.markdown("""
            <div style='background: white; padding: 1rem 1.5rem; border-radius: 12px; margin-bottom: 1.5rem; margin-top: 1.5rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>
                <h3 style='margin: 0; color: #1e293b; border: none; display: flex; align-items: center;'>
                    <span style='background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: white; padding: 0.4rem 0.8rem; border-radius: 8px; margin-right: 0.75rem; font-size: 1rem;'>📊</span>
                    技术指标
                </h3>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                if 'MA5' in latest:
                    ma5_delta = ((latest['收盘'] - latest['MA5']) / latest['MA5'] * 100)
                    st.metric("MA5", f"¥{latest['MA5']:.2f}", f"{ma5_delta:.2f}%")
            
            with col2:
                if 'MA20' in latest:
                    ma20_delta = ((latest['收盘'] - latest['MA20']) / latest['MA20'] * 100)
                    st.metric("MA20", f"¥{latest['MA20']:.2f}", f"{ma20_delta:.2f}%")
            
            with col3:
                if 'RSI' in latest:
                    rsi_val = latest['RSI']
                    rsi_status = "超买" if rsi_val > 70 else "超卖" if rsi_val < 30 else "正常"
                    st.metric("RSI", f"{rsi_val:.2f}", rsi_status)
            
            with col4:
                if 'MACD' in latest:
                    st.metric("MACD", f"{latest['MACD']:.2f}", 
                             "多头" if latest['MACD'] > latest['Signal'] else "空头")
            
            with col5:
                # 计算涨跌统计
                up_days = len(hist_df[hist_df['涨跌幅'] > 0])
                total_days = len(hist_df)
                win_rate = (up_days / total_days * 100) if total_days > 0 else 0
                st.metric("上涨天数占比", f"{win_rate:.2f}%", f"{up_days}/{total_days}天")

            # --- 第二部分：深度基本面 ---
            with st.expander("📋 更多维度基本面数据", expanded=False):
                col_a, col_b, col_c, col_d = st.columns(4)
                
                with col_a:
                    st.write(f"**总市值**: {format_value(info_dict.get('总市值', 0))}")
                    st.write(f"**流通市值**: {format_value(info_dict.get('流通市值', 0))}")
                
                with col_b:
                    st.write(f"**市盈率 (静)**: {info_dict.get('市盈率-动态', '-')}")
                    st.write(f"**市净率 (P/B)**: {info_dict.get('市净率', '-')}")
                
                with col_c:
                    st.write(f"**总股本**: {format_value(info_dict.get('总股本', 0), 'volume')}")
                    st.write(f"**流通股本**: {format_value(info_dict.get('流通股本', 0), 'volume')}")
                
                with col_d:
                    st.write(f"**每股收益**: {info_dict.get('每股收益', '-')}")
                    st.write(f"**每股净资产**: {info_dict.get('每股净资产', '-')}")

            # --- 第三部分：可视化与明细 ---
            tab_chart, tab_volume, tab_raw, tab_profile = st.tabs([
                "技术分析图表",
                " 成交量分析", 
                " 历史明细",
                " 企业档案"
            ])

            with tab_chart:
                st.plotly_chart(
                    create_candlestick_chart(hist_df, show_ma, show_bb),
                    use_container_width=True,
                    config={
                        'scrollZoom': True,
                        'displaylogo': False,
                        'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'eraseshape']
                    }
                )
                
                # 新手导读
                with st.expander("📚 投资视角：指标入门导读", expanded=False):
                    st.markdown("""
                    ### 🔍 如何解读这些指标？
                    
                    *   **移动平均线 (MA)**: 趋势的“指南铁”。MA5/MA10 反应短期热度，MA20/MA60 代表中期趋势。
                        - *金叉*: 短期线上穿长期线，通常视为看多信号。
                        - *死叉*: 短期线下穿长期线，通常视为风险信号。
                    
                    *   **MACD (平滑异同移动平均线)**: 趋势的“加速器”。
                        - *红柱放量*: 动能增强；*绿柱出现*: 调整开始。
                        - *金叉/死叉*: 辅助判断趋势的反转点。
                    
                    *   **RSI (相对强弱指标)**: 市场的“温度计”。
                        - *高于 70*: 处于“超买”状态，警惕回调风险。
                        - *低于 30*: 处于“超卖”状态，可能存在反弹机会。
                    
                    *   **布林带 (Bollinger Bands)**: 价格的“护栏”。
                        - 股价运行在 **中轨** 之上为强势，触碰 **上轨** 有回踩压力，企稳 **下轨** 有反弹可能。
                    """)

            with tab_volume:
                st.plotly_chart(
                    create_volume_chart(hist_df),
                    use_container_width=True,
                    config={'displaylogo': False}
                )
                
                # 成交量统计
                st.markdown("#### 📊 成交量统计")
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_volume = hist_df['成交量'].mean()
                    st.metric("平均成交量", format_value(avg_volume, 'volume'))
                with col2:
                    max_volume = hist_df['成交量'].max()
                    st.metric("最大成交量", format_value(max_volume, 'volume'))
                with col3:
                    avg_amount = hist_df['成交额'].mean()
                    st.metric("平均成交额", format_value(avg_amount))

            with tab_raw:
                st.write("#### 📋 历史交易明细")
                
                # 数据筛选
                col1, col2 = st.columns([3, 1])
                with col1:
                    search_date = st.date_input("筛选日期", value=None, key="search_date")
                with col2:
                    sort_order = st.selectbox("排序", ["降序", "升序"])
                
                display_df = hist_df.copy()
                if search_date:
                    display_df = display_df[display_df['日期'].dt.date == search_date]
                
                ascending = (sort_order == "升序")
                display_df = display_df.sort_values(by="日期", ascending=ascending)
                
                # 格式化显示
                st.dataframe(
                    display_df.style.format({
                        '开盘': '¥{:.2f}',
                        '收盘': '¥{:.2f}',
                        '最高': '¥{:.2f}',
                        '最低': '¥{:.2f}',
                        '涨跌幅': '{:.2f}%',
                        '换手率': '{:.2f}%',
                        '成交量': lambda x: format_value(x, 'volume'),
                        '成交额': lambda x: format_value(x, 'amount')
                    }),
                    use_container_width=True,
                    height=400
                )
                
                # 下载按钮
                csv = hist_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 导出历史数据 (CSV)",
                    data=csv,
                    file_name=f"{symbol}_history_{datetime.date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            with tab_profile:
                st.write("#### 🏢 核心基本面清单")
                
                # 美化展示
                display_info = info_df.copy()
                display_info.columns = ['项目', '数值']
                
                # 对数值列进行单位转换
                def smart_format(row):
                    item = row['项目']
                    val = row['数值']
                    # 识别需要单位转换的项目
                    amount_items = ['总市值', '流通市值', '成交额']
                    volume_items = ['总股本', '流通股本', '成交量']
                    
                    if any(x in item for x in amount_items):
                        return format_value(val, 'amount')
                    elif any(x in item for x in volume_items):
                        return format_value(val, 'volume')
                    return val

                display_info['数值'] = display_info.apply(smart_format, axis=1)
                
                st.dataframe(
                    display_info,
                    use_container_width=True,
                    height=500,
                    hide_index=True
                )
        else:
            st.error("❌ 数据调取异常：请确认代码是否正确，或接口正处于维护状态。")
    else:
        # 欢迎页面
        st.info("💡 请在左侧控制台输入证券代码以获取深度行情。")
        
        st.markdown("""
        ### 🎯 功能特色
        
        - **实时行情**: 获取最新的股票价格和交易数据
        - **技术分析**: 支持MA、MACD、RSI、布林带等多种技术指标
        - **数据可视化**: 交互式K线图和成交量分析
        - **数据导出**: 支持历史数据CSV格式导出
        - **移动友好**: 响应式设计，支持手机端访问
        
        ### 📖 使用说明
        
        1. 在左侧输入6位股票代码（如：600519）
        2. 选择查询的时间范围
        3. 选择复权方式（建议技术分析使用前复权）
        4. 点击"更新行情"按钮获取数据
        5. 在不同标签页查看图表、数据和企业信息
        """)

    st.divider()
    st.caption("⚠️ 注：本终端数据同步自公开市场，仅供参考，不构成任何投资建议。")
