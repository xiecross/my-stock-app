import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# ---------------------------------------------------------
# 1. 登录验证逻辑 (支持 URL 参数自动登录)
# ---------------------------------------------------------
def check_password():
    """验证登录状态"""
    if st.query_params.get("auth") == st.secrets["app_password"]:
        st.session_state["password_correct"] = True
        return True

    def password_entered():
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            st.query_params["auth"] = st.secrets["app_password"]
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
# 2. 数据获取函数集 (基于 AkShare)
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_base_info(symbol):
    """获取个股基本信息"""
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
# 3. 主程序区
# ---------------------------------------------------------
if check_password():
    st.set_page_config(page_title="AkShare 数据查询终端", layout="wide")
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 查询控制台")
        symbol = st.text_input("股票代码", value="600519", help="请输入6位 A 股代码")
        start_date = st.date_input("开始日期", datetime.date.today() - datetime.timedelta(days=365))
        end_date = st.date_input("结束日期", datetime.date.today())
        
        adj_options = {"前复权": "qfq", "后复权": "hfq", "不复权": "None"}
        adjust_display = st.selectbox("复权方式", list(adj_options.keys()))
        adjust_type = adj_options[adjust_display]
        
        btn_query = st.button("查询数据", type="primary", use_container_width=True)
        
        st.divider()
        if st.button("🔒 退出登录", use_container_width=True):
            st.session_state["password_correct"] = False
            st.query_params.clear()
            st.rerun()

    # 主界面
    st.title("📈 AkShare 金融数据看板")
    
    if btn_query or symbol:
        with st.spinner('正在调取 AkShare 数据库...'):
            info_df = get_base_info(symbol)
            hist_df = get_hist_data(symbol, start_date, end_date, adjust_type)

        if info_df is not None and hist_df is not None and not hist_df.empty:
            info_dict = dict(zip(info_df['item'], info_df['value']))
            latest = hist_df.iloc[-1]
            
            # 顶部数据概览
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("名称", info_dict.get("股票简称", "未知"))
            col2.metric("最新价", f"¥{latest['收盘']}", f"{latest['涨跌幅']}%")
            col3.metric("成交量", f"{latest['成交量']:,}")
            col4.metric("换手率", f"{latest['换手率']}%")

            # 选项卡布局
            tab_chart, tab_info, tab_raw = st.tabs(["📊 可视化图表", "📋 基本面信息", "📄 原始数据"])

            with tab_chart:
                # 绘制 K 线与成交量
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.1, row_heights=[0.7, 0.3])
                
                # K 线图
                fig.add_trace(go.Candlestick(
                    x=hist_df['日期'], open=hist_df['开盘'], high=hist_df['最高'],
                    low=hist_df['最低'], close=hist_df['收盘'], name="K线"
                ), row=1, col=1)
                
                # 成交量
                colors = ['red' if c >= o else 'green' for c, o in zip(hist_df['收盘'], hist_df['开盘'])]
                fig.add_trace(go.Bar(
                    x=hist_df['日期'], y=hist_df['成交量'], marker_color=colors, name="成交量"
                ), row=2, col=1)
                
                fig.update_layout(xaxis_rangeslider_visible=False, height=600, margin=dict(t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)

            with tab_info:
                st.write("#### 个股档案资料 (东方财富接口)")
                st.table(info_df)

            with tab_raw:
                st.write("#### 历史行情明细")
                st.dataframe(hist_df.sort_values(by="日期", ascending=False), use_container_width=True)
                
                # 下载
                csv = hist_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 下载 CSV 数据", data=csv, file_name=f"{symbol}_data.csv")
        else:
            st.error("无法获取数据，请检查代码输入或网络状态。")
    else:
        st.info("请在左侧输入股票代码并点击查询。")

    st.divider()
    st.caption("数据来源：AkShare 开源库 | 界面风格：极简可视化")
