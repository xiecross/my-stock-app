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
# 2. 数据获取函数集
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_base_info(symbol):
    """获取个股基本信息 (个股个股资料-东方财富)"""
    try:
        info_df = ak.stock_individual_info_em(symbol=symbol)
        return info_df
    except:
        return None

@st.cache_data(ttl=3600)
def get_hist_data(symbol, start, end, adjust):
    """获取历史 K 线数据"""
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
            numeric_cols = ['开盘', '收盘', '最高', '最低', '成交量', '涨跌幅', '换手率']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except:
        return None

@st.cache_data(ttl=3600)
def get_dividend_data(symbol):
    """获取分红派息数据"""
    try:
        # 获取分红配股数据
        df = ak.stock_fhps_em(symbol=symbol)
        return df
    except:
        return None

# ---------------------------------------------------------
# 3. 主程序区
# ---------------------------------------------------------
if check_password():
    st.set_page_config(page_title="金融数据深度查询终端", layout="wide")
    
    if st.sidebar.button("登出账户"):
        st.session_state["password_correct"] = False
        st.query_params.clear()
        st.rerun()

    st.title("🏦 金融数据深度查询终端")
    st.caption("基于 AkShare 开源数据库 | 专业名词已添加中文注释")

    # --- 侧边栏查询配置 ---
    st.sidebar.header("🔍 查询设置")
    symbol = st.sidebar.text_input("请输入A股代码", value="600519", help="输入6位数字代码，如贵州茅台请输入 600519")
    
    col_date1, col_date2 = st.sidebar.columns(2)
    start_date = col_date1.date_input("开始日期", datetime.date.today() - datetime.timedelta(days=365))
    end_date = col_date2.date_input("结束日期", datetime.date.today())
    
    adj_map = {"前复权": "qfq", "后复权": "hfq", "不复权": "None"}
    adjust_display = st.sidebar.selectbox(
        "复权方式", 
        list(adj_map.keys()),
        help="【前复权】保持现价不变，降低历史价格，使股价走势连续；\n【后复权】保持上市初价格不变，调高现价；\n【不复权】显示原始成交价格。"
    )
    adjust_type = adj_map[adjust_display]
    
    btn_query = st.sidebar.button("🚀 获取深度数据", type="primary")

    # --- 逻辑处理 ---
    if btn_query or symbol:
        with st.spinner('正在调取数据库...'):
            info_df = get_base_info(symbol)
            hist_df = get_hist_data(symbol, start_date, end_date, adjust_type)
            div_df = get_dividend_data(symbol)

        if info_df is not None:
            # 转换基本信息为字典方便调用
            info_dict = dict(zip(info_df['item'], info_df['value']))
            
            # 顶部核心指标
            st.markdown("### 📌 实时核心指标")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("股票名称", info_dict.get("股票简称", "-"))
            m2.metric("行业板块", info_dict.get("行业", "-"))
            m3.metric("总市值", f"{info_dict.get('总市值', 0)/1e8:.2f} 亿", help="该公司的总资产价值：总股数 × 当前股价")
            m4.metric("流通市值", f"{info_dict.get('流通市值', 0)/1e8:.2f} 亿", help="在市场上可以自由买卖的股票部分对应的总价值")

            # 分栏展示
            tab1, tab2, tab3 = st.tabs(["📉 行情走势", "🏢 公司档案", "💰 分红融资"])

            with tab1:
                if hist_df is not None and not hist_df.empty:
                    # 绘制 K 线图
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                        vertical_spacing=0.08, row_heights=[0.7, 0.3])
                    
                    fig.add_trace(go.Candlestick(x=hist_df['日期'], open=hist_df['开盘'], high=hist_df['最高'],
                                                 low=hist_df['最低'], close=hist_df['收盘'], name="K线"), row=1, col=1)
                    
                    colors = ['red' if c >= o else 'green' for c, o in zip(hist_df['收盘'], hist_df['开盘'])]
                    fig.add_trace(go.Bar(x=hist_df['日期'], y=hist_df['成交量'], marker_color=colors, name="成交量"), row=2, col=1)
                    
                    fig.update_layout(xaxis_rangeslider_visible=False, height=600, margin=dict(t=30, b=10), hovermode='x unified')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("#### 📖 走势数据注释")
                    st.info("""
                    - **换手率 (Turnover Rate)**：当日成交量占流通总股数的比例。反映股票活跃程度。
                    - **成交量 (Volume)**：交易买卖的总股数。
                    - **涨跌幅 (%)**：当前价格相对于前一交易日收盘价的变化比例。
                    """)
                    st.dataframe(hist_df.sort_values(by="日期", ascending=False), use_container_width=True)
                else:
                    st.error("未能获取到行情数据，请检查代码或网络。")

            with tab2:
                st.markdown("#### 📋 公司基本面资料")
                col_left, col_right = st.columns(2)
                with col_left:
                    st.write(f"**上市日期**：{info_dict.get('上市时间', '-')}")
                    st.write(f"**股票代码**：{info_dict.get('股票代码', '-')}")
                with col_right:
                    st.write(f"**当前股价**：¥{info_dict.get('最新价', '-')}")
                    st.write(f"**流通股本**：{info_dict.get('流通股本', 0)/1e8:.2f} 亿股")
                
                st.markdown("---")
                st.write("**更多基础财务数据查询结果：**")
                st.table(info_df)

            with tab3:
                st.markdown("#### 💵 历史分红送配记录")
                if div_df is not None and not div_df.empty:
                    # 整理表格列名
                    display_div = div_df[['公告日期', '送股比例', '转增比例', '派息比例', '股权登记日', '除权除息日']].copy()
                    st.dataframe(display_div, use_container_width=True)
                    st.warning("注：分红派息比例通常以'每10股'为基准。例如'派10元'即每股分红1元。")
                else:
                    st.info("该个股暂无历史分红数据或接口获取失败。")
        else:
            st.error(f"❌ 无法连接到 AkShare 数据库，或代码 {symbol} 错误。请确保输入的是正确的6位代码。")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 名词小百科")
    with st.sidebar.expander("什么是市盈率 (PE)?"):
        st.write("股价 / 每股收益。反映投资者愿意为每1元利润支付的价格。PE越高，通常意味着预期越高或存在泡沫。")
    with st.sidebar.expander("什么是复权?"):
        st.write("由于分红送股会导致股价'跳水'，复权是通过计算消除这种缺口，让历史价格具有可比性。")
