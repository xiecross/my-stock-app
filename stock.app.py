import streamlit as st
import akshare as ak
# ... (保留之前的 import)

# --- 登录功能逻辑 ---
def check_password():
    """如果返回 True，则说明输入了正确的密码。"""
    def password_entered():
        """检查用户输入的密码是否与 Secrets 中的一致。"""
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 不在 session 中存储密码明文
        else:
            st.session_state["password_correct"] = False

    # 初始化状态
    if "password_correct" not in st.session_state:
        # 首次打开，显示输入框
        st.text_input("请输入访问密码", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # 密码输入错误，再次显示输入框
        st.text_input("密码错误，请重试", type="password", on_change=password_entered, key="password")
        st.error("😕 访问受限")
        return False
    else:
        # 密码正确
        return True

# --- 主程序入口 ---
if check_password():
    # 验证通过后，才运行你之前的代码
    st.sidebar.success("登录成功！")
    
    # ... (这里放你之前的全部代码：获取数据、绘图等)
    st.title("📊 AkShare 金融数据可视化分析")
    # ...
import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# ---------------------------------------------------------
# 1. 页面配置
# ---------------------------------------------------------
st.set_page_config(
    page_title="AkShare 实时财经看板",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 样式，让界面更紧凑
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 侧边栏：用户控制区
# ---------------------------------------------------------
st.sidebar.header("🔍 查询参数设置")

# 股票代码输入
symbol = st.sidebar.text_input("A股代码 (例如: 600519)", value="600519")

# 时间范围选择
col1, col2 = st.sidebar.columns(2)
default_start = datetime.date.today() - datetime.timedelta(days=365)
start_date = col1.date_input("开始日期", default_start)
end_date = col2.date_input("结束日期", datetime.date.today())

# 复权方式
adjust_type = st.sidebar.selectbox("复权方式", ["qfq", "hfq", "None"], index=0, 
                                 format_func=lambda x: "前复权" if x == "qfq" else ("后复权" if x == "hfq" else "不复权"))

# 均线设置
show_ma = st.sidebar.checkbox("显示均线 (MA)", value=True)
ma1_window = st.sidebar.number_input("均线 1 (天数)", value=5, min_value=1)
ma2_window = st.sidebar.number_input("均线 2 (天数)", value=20, min_value=1)

btn_query = st.sidebar.button("🚀 开始查询", type="primary")

st.sidebar.markdown("---")
st.sidebar.info("💡 数据来源: AkShare 开源库\n技术栈: Streamlit + Plotly")

# ---------------------------------------------------------
# 3. 核心逻辑：获取数据
# ---------------------------------------------------------
@st.cache_data(ttl=3600)  # 开启缓存，1小时内相同的查询直接读缓存，不请求网络
def get_data(stock_symbol, start, end, adjust):
    """
    封装 AkShare 的 A 股历史行情接口
    """
    start_str = start.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")
    
    # adjust 参数处理
    adj = "" if adjust == "None" else adjust
    
    try:
        # 调用 akshare 接口：stock_zh_a_hist (A股历史行情)
        df = ak.stock_zh_a_hist(
            symbol=stock_symbol,
            period="daily",
            start_date=start_str,
            end_date=end_str,
            adjust=adj
        )
        
        # --- 数据清洗与类型转换 (关键修复) ---
        if df is not None and not df.empty:
            # 确保日期列是 datetime 类型
            df['日期'] = pd.to_datetime(df['日期'])
            
            # 确保数值列是 float 类型，防止因为包含字符串导致计算报错
            numeric_cols = ['开盘', '收盘', '最高', '最低', '成交量', '涨跌幅', '换手率']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# ---------------------------------------------------------
# 4. 核心逻辑：绘制图表
# ---------------------------------------------------------
def plot_chart(df, symbol):
    # 计算移动平均线
    df[f'MA{ma1_window}'] = df['收盘'].rolling(window=ma1_window).mean()
    df[f'MA{ma2_window}'] = df['收盘'].rolling(window=ma2_window).mean()

    # 创建子图：主图 K 线，副图成交量
    # row_heights 控制高度比例 (从上到下)，这里主图占 0.7，副图占 0.3
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        subplot_titles=(f'{symbol} 股价走势', '成交量'),
        row_heights=[0.7, 0.3]  
    )

    # 1. 添加 K 线
    fig.add_trace(go.Candlestick(
        x=df['日期'],
        open=df['开盘'],
        high=df['最高'],
        low=df['最低'],
        close=df['收盘'],
        name='K线'
    ), row=1, col=1)

    # 2. 添加均线
    if show_ma:
        fig.add_trace(go.Scatter(x=df['日期'], y=df[f'MA{ma1_window}'], opacity=0.7, line=dict(color='orange', width=1), name=f'MA{ma1_window}'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df['日期'], y=df[f'MA{ma2_window}'], opacity=0.7, line=dict(color='purple', width=1), name=f'MA{ma2_window}'), row=1, col=1)

    # 3. 添加成交量 (颜色根据涨跌变化)
    # 确保比较时使用的是数值
    colors = ['red' if c >= o else 'green' for c, o in zip(df['收盘'], df['开盘'])]
    
    fig.add_trace(go.Bar(
        x=df['日期'], 
        y=df['成交量'],
        marker_color=colors,
        name='成交量'
    ), row=2, col=1)

    # 布局美化
    fig.update_layout(
        xaxis_rangeslider_visible=False, # 关闭底部滑动条
        height=600,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode='x unified' # 统一显示 hover 信息
    )
    
    return fig

# ---------------------------------------------------------
# 5. 主界面渲染
# ---------------------------------------------------------
st.title("📊 AkShare 金融数据可视化分析")

if btn_query or symbol: # 允许初始加载
    with st.spinner('正在从云端拉取最新数据，请稍候...'):
        df = get_data(symbol, start_date, end_date, adjust_type)

    if df is not None and not df.empty:
        # --- 顶部指标栏 ---
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # 确保运算是数值运算
        try:
            change = float(latest['收盘']) - float(prev['收盘'])
            pct_change = float(latest['涨跌幅'])
            volume = float(latest['成交量'])
            turnover = float(latest['换手率'])
        except:
            change = 0
            pct_change = 0
            volume = 0
            turnover = 0
        
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("最新收盘价", f"¥{latest['收盘']}", f"{change:.2f}")
        col_m2.metric("今日涨跌幅", f"{pct_change}%", delta_color="normal")
        col_m3.metric("成交量 (手)", f"{volume:,.0f}")
        col_m4.metric("换手率", f"{turnover}%")

        # --- 图表区域 ---
        st.plotly_chart(plot_chart(df, symbol), use_container_width=True)

        # --- 数据表格区域 ---
        with st.expander("查看详细历史数据列表"):
            # 格式化日期显示
            display_df = df.copy()
            display_df['日期'] = display_df['日期'].dt.strftime('%Y-%m-%d')
            st.dataframe(display_df.sort_values(by='日期', ascending=False), use_container_width=True)
            
            # 下载按钮
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 下载数据为 CSV",
                data=csv,
                file_name=f'{symbol}_history.csv',
                mime='text/csv',
            )
            
    else:
        if btn_query:
            st.error(f"❌ 未找到代码为 {symbol} 的数据。请检查代码是否正确（如：600519）。")
else:
    st.info("👈 请在左侧侧边栏输入股票代码并点击查询")
