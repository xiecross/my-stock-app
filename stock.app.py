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
    """获取个股基本信息 (东方财富 F10)"""
    try:
        info_df = ak.stock_individual_info_em(symbol=symbol)
        return info_df
    except:
        return None

@st.cache_data(ttl=3600)
def get_hist_data(symbol, start, end, adjust):
    """获取历史行情数据并计算均线"""
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
            
            # 仿照同花顺计算均线
            df['MA5'] = df['收盘'].rolling(5).mean()
            df['MA10'] = df['收盘'].rolling(10).mean()
            df['MA20'] = df['收盘'].rolling(20).mean()
        return df
    except:
        return None

# ---------------------------------------------------------
# 3. UI 辅助函数
# ---------------------------------------------------------
def style_metric(label, value, delta=None, help_text=None):
    """自定义指标显示样式"""
    # 同花顺风格配色
    delta_color = "normal"
    if delta:
        try:
            val = float(delta.strip('%'))
            if val > 0: delta_color = "normal" # 红色
            elif val < 0: delta_color = "inverse" # 绿色
        except: pass
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color, help=help_text)

# ---------------------------------------------------------
# 4. 主程序区
# ---------------------------------------------------------
if check_password():
    st.set_page_config(page_title="量化深度终端·数据看板", layout="wide")
    
    # 注入 CSS 模拟同花顺红绿配色和紧凑布局
    st.markdown("""
        <style>
        .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 5px solid #f63538; }
        [data-testid="stMetricDelta"] > div:nth-child(2) { color: #f63538 !important; } /* 强制上涨为红 */
        </style>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🔒 登出系统"):
        st.session_state["password_correct"] = False
        st.query_params.clear()
        st.rerun()

    # --- 侧边栏面板 ---
    st.sidebar.header("📊 终端控制台")
    symbol = st.sidebar.text_input("证券代码", value="600519", help="请输入6位数字代码")
    
    with st.sidebar.expander("📅 时间范围 & 复权", expanded=True):
        start_date = st.date_input("开始日期", datetime.date.today() - datetime.timedelta(days=365))
        end_date = st.date_input("结束日期", datetime.date.today())
        adj_map = {"前复权": "qfq", "后复权": "hfq", "不复权": "None"}
        adjust_display = st.selectbox("复权类型", list(adj_map.keys()), index=0)
        adjust_type = adj_map[adjust_display]
    
    btn_query = st.sidebar.button("🔍 刷新行情数据", type="primary", use_container_width=True)

    # --- 数据逻辑 ---
    if btn_query or symbol:
        # 这里修改了原有的提示方案
        with st.spinner('正在从 AkShare 金融数据库同步实时行情...'):
            info_df = get_base_info(symbol)
            hist_df = get_hist_data(symbol, start_date, end_date, adjust_type)

        if info_df is not None and hist_df is not None:
            info_dict = dict(zip(info_df['item'], info_df['value']))
            latest = hist_df.iloc[-1]
            
            # --- 顶部行情快照 (Header) ---
            st.subheader(f"🏷️ {info_dict.get('股票简称', '未知')} ({symbol})")
            
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1: style_metric("最新价", f"¥{latest['收盘']}", f"{latest['涨跌幅']}%")
            with c2: style_metric("成交额", f"{latest['成交额']/1e8:.2f}亿", help_text="当日买卖总金额")
            with c3: style_metric("换手率", f"{latest['换手率']}%", help_text="反映市场活跃程度")
            with c4: style_metric("总市值", f"{info_dict.get('总市值', 0)/1e8:.2f}亿")
            with c5: style_metric("市盈率(静)", f"{info_dict.get('市盈率', '-')}", help_text="PE：股价/每股收益")
            with c6: style_metric("行业板块", info_dict.get("行业", "-"))

            # --- 主工作区 ---
            tab1, tab2, tab3 = st.tabs(["📈 深度行情分析", "📄 个股资料(F10)", "📊 核心财务摘要"])

            with tab1:
                # 绘制同花顺风格 K 线
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.03, row_heights=[0.7, 0.3])
                
                # 1. K线主体
                fig.add_trace(go.Candlestick(
                    x=hist_df['日期'], open=hist_df['开盘'], high=hist_df['最高'],
                    low=hist_df['最低'], close=hist_df['收盘'], 
                    name="K线图",
                    increasing_line_color='#f63538', increasing_fillcolor='#f63538',
                    decreasing_line_color='#30b455', decreasing_fillcolor='#30b455'
                ), row=1, col=1)
                
                # 2. 均线 (MA5, MA10, MA20)
                fig.add_trace(go.Scatter(x=hist_df['日期'], y=hist_df['MA5'], name="MA5", line=dict(color='#ff7f0e', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=hist_df['日期'], y=hist_df['MA10'], name="MA10", line=dict(color='#17becf', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=hist_df['日期'], y=hist_df['MA20'], name="MA20", line=dict(color='#e377c2', width=1)), row=1, col=1)
                
                # 3. 成交量
                vol_colors = ['#f63538' if c >= o else '#30b455' for c, o in zip(hist_df['收盘'], hist_df['开盘'])]
                fig.add_trace(go.Bar(x=hist_df['日期'], y=hist_df['成交量'], marker_color=vol_colors, name="成交量"), row=2, col=1)
                
                fig.update_layout(
                    xaxis_rangeslider_visible=False, 
                    height=650, 
                    margin=dict(t=10, b=10, l=10, r=10),
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                st.markdown("#### 🏢 企业基本信息深度档案")
                f1, f2 = st.columns(2)
                with f1:
                    st.info(f"**公司简称**：{info_dict.get('股票简称', '-')}")
                    st.info(f"**上市日期**：{info_dict.get('上市时间', '-')}")
                with f2:
                    st.success(f"**流通股本**：{info_dict.get('流通股本', 0)/1e8:.2f}亿股")
                    st.success(f"**总股本**：{info_dict.get('总股本', 0)/1e8:.2f}亿股")
                
                st.dataframe(info_df, use_container_width=True)

            with tab3:
                st.markdown("#### 📋 实时财务与估值概览")
                st.warning("注：此模块直接透传 AkShare 原始报表数据...")
                st.table(info_df[info_df['item'].str.contains('净利润|总资产|负债|收益|市', na=False)])

        else:
            st.error(f"❌ 数据库调用失败，请检查证券代码 {symbol} 或稍后再试。")

    # --- 底部知识库 ---
    st.markdown("---")
    with st.expander("📚 财经指标科普 (点击展开)"):
        st.markdown("""
        * **数据源**：本项目核心数据由 **AkShare** 驱动，主要接口涵盖东方财富、新浪财经等公开渠道。
        * **前复权**：以当前价格为基准，保持历史价格趋势的连续性，是技术派看盘的首选。
        * **换手率**：日成交量/流通股本。通常换手率 > 5% 表明资金高度活跃。
        * **MA均线**：移动平均线，MA20 常被视为个股的“生命线”。
        """)
