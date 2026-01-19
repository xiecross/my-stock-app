import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# ---------------------------------------------------------
# 1. 登录验证逻辑 (必须放在最前面)
# ---------------------------------------------------------
def check_password():
    """返回 True 表示用户已验证成功"""

    def password_entered():
        """检查输入的密码是否正确"""
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 清除输入框缓存
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # 首次访问：显示输入框
        st.title("🔒 访问受限")
        st.text_input("请输入访问密码", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # 密码错误：提示并重显输入框
        st.title("🔒 访问受限")
        st.text_input("密码错误，请重试", type="password", on_change=password_entered, key="password")
        st.error("❌ 密码不正确")
        return False
    else:
        # 验证通过
        return True

# ---------------------------------------------------------
# 2. 主程序区 (只有验证通过才会运行)
# ---------------------------------------------------------
if check_password():
    # 页面配置
    st.set_page_config(page_title="AkShare 实时看板", layout="wide")
    
    # 侧边栏登出按钮
    if st.sidebar.button("登出账户"):
        st.session_state["password_correct"] = False
        st.rerun()

    st.title("📊 AkShare 金融数据可视化分析")

    # --- 侧边栏设置 ---
    st.sidebar.header("🔍 查询设置")
    symbol = st.sidebar.text_input("A股代码", value="600519")
    
    col_date1, col_date2 = st.sidebar.columns(2)
    start_date = col_date1.date_input("开始日期", datetime.date.today() - datetime.timedelta(days=365))
    end_date = col_date2.date_input("结束日期", datetime.date.today())
    
    adjust_type = st.sidebar.selectbox("复权方式", ["qfq", "hfq", "None"])
    btn_query = st.sidebar.button("🚀 开始查询", type="primary")

    # --- 数据获取函数 (带缓存) ---
    @st.cache_data(ttl=3600)
    def get_stock_data(stock_symbol, start, end, adjust):
        try:
            df = ak.stock_zh_a_hist(
                symbol=stock_symbol,
                period="daily",
                start_date=start.strftime("%Y%m%d"),
                end_date=end.strftime("%Y%m%d"),
                adjust="" if adjust == "None" else adjust
            )
            if df is not None and not df.empty:
                df['日期'] = pd.to_datetime(df['日期'])
                for col in ['开盘', '收盘', '最高', '最低', '成交量', '涨跌幅']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        except Exception:
            return None

    # --- 界面渲染逻辑 ---
    if btn_query or symbol:
        with st.spinner('数据加载中...'):
            df = get_stock_data(symbol, start_date, end_date, adjust_type)

        if df is not None and not df.empty:
            # 顶部指标
            latest = df.iloc[-1]
            m1, m2, m3 = st.columns(3)
            m1.metric("当前价格", f"¥{latest['收盘']}")
            m2.metric("涨跌幅", f"{latest['涨跌幅']}%")
            m3.metric("成交量", f"{latest['成交量']:,}")

            # K线图
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.05, row_heights=[0.7, 0.3])
            
            fig.add_trace(go.Candlestick(x=df['日期'], open=df['开盘'], high=df['最高'],
                                         low=df['最低'], close=df['收盘'], name="K线"), row=1, col=1)
            
            colors = ['red' if c >= o else 'green' for c, o in zip(df['收盘'], df['开盘'])]
            fig.add_trace(go.Bar(x=df['日期'], y=df['成交量'], marker_color=colors, name="成交量"), row=2, col=1)
            
            fig.update_layout(xaxis_rangeslider_visible=False, height=600, margin=dict(t=30, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("查看原始数据"):
                st.dataframe(df.sort_values(by="日期", ascending=False))
        else:
            st.warning("查无此代码或接口受限，请稍后再试。")
