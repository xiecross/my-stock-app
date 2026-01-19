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
# 3. 主程序区
# ---------------------------------------------------------
if check_password():
    st.set_page_config(page_title="金融数据深度查询终端", layout="wide")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 终端控制台")
        symbol = st.text_input("证券代码", value="600519", help="请输入6位 A 股数字代码")
        
        # 针对手机端紧凑化日期选择
        start_date = st.date_input("起始时间", datetime.date.today() - datetime.timedelta(days=365))
        end_date = st.date_input("结束时间", datetime.date.today())
        
        adj_options = {"前复权": "qfq", "后复权": "hfq", "不复权": "None"}
        adjust_display = st.selectbox("复权处理", list(adj_options.keys()), help="前复权保持现价连续，适合技术分析。")
        adjust_type = adj_options[adjust_display]
        
        btn_query = st.button("更新行情", type="primary", use_container_width=True)
        
        st.divider()
        if st.button("🔒 安全登出", use_container_width=True):
            st.session_state["password_correct"] = False
            st.query_params.clear()
            st.rerun()

    # 主界面
    st.title("📈 证券行情深度看板")
    
    if btn_query or symbol:
        with st.spinner('正在同步最新行情数据...'):
            info_df = get_base_info(symbol)
            hist_df = get_hist_data(symbol, start_date, end_date, adjust_type)

        if info_df is not None and hist_df is not None and not hist_df.empty:
            # 数据预处理
            info_dict = dict(zip(info_df['item'], info_df['value']))
            latest = hist_df.iloc[-1]
            
            # --- 第一部分：实时核心指标 (适配竖屏) ---
            st.markdown("### 实时概览")
            # 手机端建议使用 columns 但内部元素不宜过多
            row1_1, row1_2 = st.columns(2)
            row1_1.metric("公司简称", info_dict.get("股票简称", "未知"))
            row1_2.metric("最新价", f"¥{latest['收盘']}", f"{latest['涨跌幅']}%")
            
            row2_1, row2_2 = st.columns(2)
            row2_1.metric("成交额", f"{latest['成交额']/1e8:.2f} 亿元", help="当日买卖总金额")
            row2_2.metric("换手率", f"{latest['换手率']}%", help="当日成交量占流通股本比例")

            # --- 第二部分：深度基本面 (折叠显示或直接展示) ---
            with st.expander("更多维度基本面数据", expanded=True):
                col_a, col_b, col_c = st.columns(3)
                col_a.write(f"**总市值**: {info_dict.get('总市值', 0)/1e8:.2f} 亿元")
                col_a.write(f"**市盈率 (静)**: {info_dict.get('市盈率', '-')} 倍")
                
                col_b.write(f"**流通市值**: {info_dict.get('流通市值', 0)/1e8:.2f} 亿元")
                col_b.write(f"**市净率 (P/B)**: {info_dict.get('市净率', '-')} 倍")
                
                col_c.write(f"**总股本**: {info_dict.get('总股本', 0)/1e8:.2f} 亿股")
                col_c.write(f"**流通股本**: {info_dict.get('流通股本', 0)/1e8:.2f} 亿股")

            # --- 第三部分：可视化与明细 ---
            tab_chart, tab_raw, tab_profile = st.tabs(["📊 行情图表", "📄 历史明细", "🏢 企业档案"])

            with tab_chart:
                # 针对手机端，图表高度适中
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.05, row_heights=[0.7, 0.3])
                
                # K 线图
                fig.add_trace(go.Candlestick(
                    x=hist_df['日期'], open=hist_df['开盘'], high=hist_df['最高'],
                    low=hist_df['最低'], close=hist_df['收盘'], name="价格走势"
                ), row=1, col=1)
                
                # 成交量
                colors = ['red' if c >= o else 'green' for c, o in zip(hist_df['收盘'], hist_df['开盘'])]
                fig.add_trace(go.Bar(
                    x=hist_df['日期'], y=hist_df['成交量'], marker_color=colors, name="成交股数"
                ), row=2, col=1)
                
                fig.update_layout(
                    xaxis_rangeslider_visible=False, 
                    height=500, 
                    margin=dict(t=10, b=10, l=0, r=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab_raw:
                st.write("#### 历史交易明细")
                st.dataframe(hist_df.sort_values(by="日期", ascending=False), use_container_width=True)
                
                # 下载
                csv = hist_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 导出历史数据 (CSV)", data=csv, file_name=f"{symbol}_history.csv")

            with tab_profile:
                st.write("#### 核心基本面清单")
                # 汉化与单位展示
                display_info = info_df.copy()
                st.table(display_info)
        else:
            st.error("数据调取异常：请确认代码是否正确，或接口正处于维护状态。")
    else:
        st.info("💡 请在左侧控制台输入证券代码以获取深度行情。")

    st.divider()
    st.caption("注：本终端数据同步自公开市场，仅供参考，不构成任何投资建议。")
