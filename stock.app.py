import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import time

# ---------------------------------------------------------
# 自定义 CSS 样式 (保持原有高端风格并优化)
# ---------------------------------------------------------
def load_custom_css():
    st.markdown("""
    <style>
    :root {
        --primary-color: #667eea;
        --secondary-color: #764ba2;
        --success-color: #10b981;
        --danger-color: #ef4444;
        --warning-color: #f59e0b;
        --info-color: #3b82f6;
    }
    
    .main {
        background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
        padding: 2rem 1rem;
    }
    
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
    
    [data-testid="stMetric"] {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid rgba(102, 126, 234, 0.1);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }

    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. 登录验证
# ---------------------------------------------------------
def check_password():
    try:
        app_password = st.secrets["app_password"]
    except KeyError:
        app_password = "admin" 
    
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
    return True

# ---------------------------------------------------------
# 2. 数据获取与核心量化选股逻辑
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_base_info(symbol):
    try: return ak.stock_individual_info_em(symbol=symbol)
    except: return None

@st.cache_data(ttl=3600)
def get_hist_data(symbol, start, end, adjust):
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="" if adjust == "None" else adjust
        )
        if df is not None and not df.empty:
            df['日期'] = pd.to_datetime(df['日期'])
            for col in ['开盘', '收盘', '最高', '最低', '成交量', '成交额', '涨跌幅', '换手率']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except: return None

@st.cache_data(ttl=1800)
def run_growth_screener(price_max, pe_max, turnover_min):
    """集成选股脚本逻辑：稳健成长型筛选"""
    try:
        df_spot = ak.stock_zh_a_spot_em()
        df = df_spot[['代码', '名称', '最新价', '成交额', '市盈率-动态', '市净率', '总市值']]
        df.columns = ['code', 'name', 'price', 'turnover', 'pe', 'pb', 'mcap']
        
        # 过滤逻辑：价格限制、估值限制、流动性限制（亿为单位）、剔除亏损
        mask = (df['pe'] > 0) & (df['pe'] < pe_max) & \
               (df['price'] < price_max) & \
               (df['turnover'] > turnover_min * 100000000)
        
        df_filtered = df[mask].copy()
        
        # 评分模型：(1/PE * 100) + (1/PB * 5)
        df_filtered['score'] = (1 / df_filtered['pe'] * 100) + (1 / df_filtered['pb'] * 5)
        
        return df_filtered.sort_values(by='score', ascending=False).head(20)
    except:
        return None

# ---------------------------------------------------------
# 3. 辅助计算与图表函数
# ---------------------------------------------------------
def add_indicators(df):
    df['MA5'] = df['收盘'].rolling(window=5).mean()
    df['MA20'] = df['收盘'].rolling(window=20).mean()
    # MACD
    exp1 = df['收盘'].ewm(span=12, adjust=False).mean()
    exp2 = df['收盘'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']
    return df

def create_main_chart(df):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    # K线
    fig.add_trace(go.Candlestick(x=df['日期'], open=df['开盘'], high=df['最高'], low=df['最低'], close=df['收盘'], name='K线'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MA5'], name='MA5', line=dict(color='#FF6B6B', width=1.2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['日期'], y=df['MA20'], name='MA20', line=dict(color='#4ECDC4', width=1.2)), row=1, col=1)
    # MACD柱
    colors = ['#26a69a' if val >= 0 else '#ef5350' for val in df['Histogram']]
    fig.add_trace(go.Bar(x=df['日期'], y=df['Histogram'], name='MACD柱', marker_color=colors), row=2, col=1)
    fig.update_layout(height=600, template='plotly_white', margin=dict(t=20, b=20, l=10, r=10), xaxis_rangeslider_visible=False)
    return fig

# ---------------------------------------------------------
# 4. 主程序界面
# ---------------------------------------------------------
if check_password():
    st.set_page_config(page_title="量化选股分析终端", page_icon="📈", layout="wide")
    load_custom_css()
    
    # 侧边栏：功能切换与参数控制
    with st.sidebar:
        st.header("⚙️ 终端控制台")
        mode = st.radio("功能模块", ["深度行情分析", "智能量化选股"])
        st.divider()
        
        if mode == "深度行情分析":
            symbol = st.text_input("证券代码", value="600519", help="输入6位代码")
            start_date = st.date_input("起始日期", datetime.date.today() - datetime.timedelta(days=180))
            adj_options = {"前复权": "qfq", "不复权": "None"}
            adjust_type = adj_options[st.selectbox("复权方式", list(adj_options.keys()))]
            btn_refresh = st.button("更新行情", type="primary", use_container_width=True)
        else:
            st.subheader("🛠️ 选股参数 (稳健成长型)")
            p_limit = st.slider("股价上限 (元)", 10, 200, 80)
            pe_limit = st.slider("市盈率上限 (PE)", 5, 100, 40)
            t_limit = st.slider("日成交额下限 (亿元)", 1, 30, 3)
            btn_screen = st.button("开始全市场扫描", type="primary", use_container_width=True)

    # 主界面内容
    if mode == "深度行情分析":
        st.title("📈 证券行情深度看板")
        if symbol:
            with st.spinner('正在同步行情数据...'):
                info_df = get_base_info(symbol)
                hist_df = get_hist_data(symbol, start_date, datetime.date.today(), adjust_type)
            
            if info_df is not None and hist_df is not None and not hist_df.empty:
                hist_df = add_indicators(hist_df)
                info_dict = dict(zip(info_df['item'], info_df['value']))
                latest = hist_df.iloc[-1]
                
                # 核心指标卡片
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("公司简称", info_dict.get("股票简称", "未知"), symbol)
                c2.metric("最新价", f"¥{latest['收盘']:.2f}", f"{latest['涨跌幅']:.2f}%")
                c3.metric("换手率", f"{latest['换手率']:.2f}%")
                c4.metric("市盈率(动)", info_dict.get("市盈率-动态", "-"))
                
                # 图表与明细页签
                t1, t2 = st.tabs(["技术面分析 (K/MA/MACD)", "基本面/历史明细"])
                with t1:
                    st.plotly_chart(create_main_chart(hist_df), use_container_width=True)
                with t2:
                    st.dataframe(info_df, use_container_width=True, hide_index=True)
            else:
                st.error("未找到相关数据，请检查代码输入是否正确。")

    elif mode == "智能量化选股":
        st.title("🎯 智能量化选股终端")
        st.info(f"**当前策略：稳健成长型筛选** | 目标：寻找价格低于 {p_limit}元、动态PE低于 {pe_limit} 且具备流动性的高性价比标地。")
        
        if btn_screen:
            with st.spinner('全市场扫描中，请稍候...'):
                results = run_growth_screener(p_limit, pe_limit, t_limit)
            
            if results is not None and not results.empty:
                st.success(f"扫描完成！找到 {len(results)} 只符合条件的潜力种子。")
                
                # 美化结果展示
                display_df = results.copy()
                display_df['成交额(亿)'] = (display_df['turnover'] / 1e8).round(2)
                display_df['性价比评分'] = display_df['score'].round(2)
                
                st.dataframe(
                    display_df[['code', 'name', 'price', 'pe', 'pb', '成交额(亿)', '性价比评分']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "code": "代码", "name": "名称", 
                        "price": st.column_config.NumberColumn("现价", format="¥%.2f"),
                        "pe": "动态PE", "pb": "市净率", "score": "综合评分"
                    }
                )
                
                # 小白指导建议
                st.markdown("""
                ### 💡 下一步操作建议
                1. **个股复核**：复制上方代码回到“深度行情分析”，检查股价是否站稳 **MA20** 均线。
                2. **分散配置**：本金不多时，建议从结果中选择 2-3 只不同行业的个股，不要全仓押注一只。
                3. **止损设定**：成长股波动较大，建议设立 5%-8% 的止损位。
                """)
            else:
                st.warning("在此筛选条件下未找到符合标准的股票，建议尝试放宽“市盈率”或“成交额”限制。")
        else:
            st.write("点击左侧按钮开始量化扫描...")

    st.divider()
    st.caption("⚠️ 注：量化结果基于历史数据和特定逻辑计算，不构成任何买卖建议。市场有风险，入市需谨慎。")
