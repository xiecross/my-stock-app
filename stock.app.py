import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# ---------------------------------------------------------
# 1. 登录验证逻辑
# ---------------------------------------------------------
def check_password():
    """Returns True if the user has entered the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Clear password from session state
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
# 2. 量化计算工具函数
# ---------------------------------------------------------
def calculate_indicators(df):
    """计算常用的量化技术指标"""
    # 均线
    df['MA5'] = df['收盘'].rolling(window=5).mean()
    df['MA20'] = df['收盘'].rolling(window=20).mean()
    df['MA60'] = df['收盘'].rolling(window=60).mean()
    
    # 布林带
    df['std'] = df['收盘'].rolling(window=20).std()
    df['Upper'] = df['MA20'] + (df['std'] * 2)
    df['Lower'] = df['MA20'] - (df['std'] * 2)
    
    # RSI (14日)
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['收盘'].ewm(span=12, adjust=False).mean()
    exp2 = df['收盘'].ewm(span=26, adjust=False).mean()
    df['DIF'] = exp1 - exp2
    df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD'] = (df['DIF'] - df['DEA']) * 2
    
    # 收益率与风险指标
    df['Daily_Return'] = df['收盘'].pct_change()
    df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod()
    
    return df

def get_quant_metrics(df):
    """计算量化统计摘要"""
    if df.empty: return {}
    
    total_return = (df['Cumulative_Return'].iloc[-1] - 1)
    # 简单年化处理
    days = (df['日期'].iloc[-1] - df['日期'].iloc[0]).days
    annual_return = (1 + total_return) ** (365.25 / max(days, 1)) - 1
    
    # 波动率与夏普比
    volatility = df['Daily_Return'].std() * np.sqrt(252)
    sharpe = annual_return / volatility if volatility != 0 else 0
    
    # 最大回撤
    cumulative_max = df['Cumulative_Return'].cummax()
    drawdown = (df['Cumulative_Return'] - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min()
    
    return {
        "Total Return": total_return,
        "Annual Return": annual_return,
        "Max Drawdown": max_drawdown,
        "Volatility": volatility,
        "Sharpe Ratio": sharpe
    }

# ---------------------------------------------------------
# 3. 主程序区
# ---------------------------------------------------------
if check_password():
    st.set_page_config(page_title="AkShare 量化看板", layout="wide")
    
    if st.sidebar.button("登出账户"):
        st.session_state["password_correct"] = False
        st.rerun()

    st.title("📊 AkShare 增强量化看板")

    # --- 侧边栏设置 ---
    st.sidebar.header("🔍 查询设置")
    symbol = st.sidebar.text_input("A股代码", value="600519")
    
    col_date1, col_date2 = st.sidebar.columns(2)
    start_date = col_date1.date_input("开始日期", datetime.date.today() - datetime.timedelta(days=365))
    end_date = col_date2.date_input("结束日期", datetime.date.today())
    
    adjust_type = st.sidebar.selectbox("复权方式", ["qfq", "hfq", "None"])
    
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ 指标开关")
    show_ma = st.sidebar.checkbox("显示均线 (MA)", value=True)
    show_boll = st.sidebar.checkbox("显示布林带 (BOLL)", value=False)
    sub_indicator = st.sidebar.radio("副图指标", ["成交量", "MACD", "RSI"])
    
    btn_query = st.sidebar.button("🚀 运行分析", type="primary")

    # --- 数据获取函数 ---
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
                # 注入量化计算
                df = calculate_indicators(df)
            return df
        except Exception:
            return None

    # --- 界面渲染逻辑 ---
    if btn_query or symbol:
        with st.spinner('量化数据计算中...'):
            df = get_stock_data(symbol, start_date, end_date, adjust_type)

        if df is not None and not df.empty:
            # 1. 顶部基础指标
            latest = df.iloc[-1]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("收盘价", f"¥{latest['收盘']}", f"{latest['涨跌幅']}%")
            m2.metric("成交量", f"{latest['成交量']:,}")
            m3.metric("RSI(14)", f"{latest['RSI']:.2f}")
            m4.metric("MACD(DIF)", f"{latest['DIF']:.2f}")

            # 2. 量化统计卡片
            metrics = get_quant_metrics(df)
            st.markdown("### 📈 量化统计摘要")
            sm1, sm2, sm3, sm4, sm5 = st.columns(5)
            sm1.metric("区间总收益", f"{metrics['Total Return']:.2%}")
            sm2.metric("年化收益率", f"{metrics['Annual Return']:.2%}")
            sm3.metric("最大回撤", f"{metrics['Max Drawdown']:.2%}")
            sm4.metric("年化波动率", f"{metrics['Volatility']:.2%}")
            sm5.metric("夏普比率", f"{metrics['Sharpe Ratio']:.2f}")

            # 3. 增强图表绘制
            st.markdown("---")
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.08, row_heights=[0.7, 0.3])
            
            # 主图：K线
            fig.add_trace(go.Candlestick(x=df['日期'], open=df['开盘'], high=df['最高'],
                                         low=df['最低'], close=df['收盘'], name="K线"), row=1, col=1)
            
            # 主图：叠加指标
            if show_ma:
                fig.add_trace(go.Scatter(x=df['日期'], y=df['MA5'], name="MA5", line=dict(width=1, color='orange')), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['日期'], y=df['MA20'], name="MA20", line=dict(width=1, color='purple')), row=1, col=1)
            
            if show_boll:
                fig.add_trace(go.Scatter(x=df['日期'], y=df['Upper'], name="Boll上轨", line=dict(dash='dash', color='gray', width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['日期'], y=df['Lower'], name="Boll下轨", line=dict(dash='dash', color='gray', width=1), fill='tonexty'), row=1, col=1)
            
            # 副图：根据选择显示
            if sub_indicator == "成交量":
                colors = ['red' if c >= o else 'green' for c, o in zip(df['收盘'], df['开盘'])]
                fig.add_trace(go.Bar(x=df['日期'], y=df['成交量'], marker_color=colors, name="成交量"), row=2, col=1)
            elif sub_indicator == "MACD":
                fig.add_trace(go.Bar(x=df['日期'], y=df['MACD'], name="MACD柱"), row=2, col=1)
                fig.add_trace(go.Scatter(x=df['日期'], y=df['DIF'], name="DIF", line=dict(width=1)), row=2, col=1)
                fig.add_trace(go.Scatter(x=df['日期'], y=df['DEA'], name="DEA", line=dict(width=1)), row=2, col=1)
            elif sub_indicator == "RSI":
                fig.add_trace(go.Scatter(x=df['日期'], y=df['RSI'], name="RSI(14)", line=dict(color='orange')), row=2, col=1)
                # 添加 30/70 超买超卖线
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
            
            fig.update_layout(xaxis_rangeslider_visible=False, height=700, margin=dict(t=30, b=10), hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
            
            with st.expander("查看原始及计算后的完整数据"):
                st.dataframe(df.sort_values(by="日期", ascending=False))
        else:
            st.warning("查无此代码或接口受限，请稍后再试。")
