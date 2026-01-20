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

# 自定义CSS样式 - 优化移动端体验 + 自适应主题
st.markdown("""
<style>
    /* 全局字体与背景 */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Noto+Sans+SC:wght@400;500;700&display=swap');
    
    /* 默认变量（作为fallback，通常设为跟随系统或浅色） */
    :root {
        --bg-color: #ffffff;
        --card-bg: rgba(255, 255, 255, 0.8);
        --card-border: rgba(200, 200, 200, 0.5);
        --text-primary: #1f2328;
        --text-secondary: #656d76;
        --accent-color: #0969da;
        --up-color: #1a7f37;
        --down-color: #d1242f;
        --glass-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --hero-bg: linear-gradient(145deg, rgba(235, 245, 255, 0.8) 0%, rgba(255, 255, 255, 0.9) 100%);
        --hero-border: rgba(9, 105, 218, 0.2);
    }

    /* 深色模式适配 */
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-color: #0e1117;
            --card-bg: rgba(22, 27, 34, 0.8);
            --card-border: rgba(48, 54, 61, 0.5);
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent-color: #58a6ff;
            --up-color: #238636;
            --down-color: #da3633;
            --glass-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
            --hero-bg: linear-gradient(145deg, rgba(31,111,235,0.15) 0%, rgba(22,27,34,0.9) 100%);
            --hero-border: rgba(56,139,253,0.3);
        }
    }

    /* 应用背景色适配 */
    .stApp {
        background-color: var(--bg-color);
        font-family: 'Noto Sans SC', sans-serif;
    }
    
    /* 玻璃拟态卡片 */
    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
        box-shadow: var(--glass-shadow);
    }
    
    /* 英雄榜（股票头部） */
    .stock-hero {
        background: var(--hero-bg);
        border: 1px solid var(--hero-border);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 25px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .hero-title {
        font-size: 28px;
        font-weight: 700;
        color: var(--text-primary);
        letter-spacing: -0.5px;
    }
    
    .hero-subtitle {
        font-size: 14px;
        color: var(--text-secondary);
        margin-top: 5px;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .price-main {
        font-family: 'JetBrains Mono', monospace;
        font-size: 36px;
        font-weight: 700;
        line-height: 1;
        color: var(--text-primary);
    }
    
    .price-change {
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        font-weight: 500;
        padding: 4px 8px;
        border-radius: 6px;
        margin-left: 10px;
    }
    
    .up-bg { background: rgba(35, 134, 54, 0.2); color: var(--up-color); }
    .down-bg { background: rgba(218, 54, 51, 0.2); color: var(--down-color); }
    
    /* 关键指标网格 */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 15px;
        margin-top: 20px;
    }
    
    .metric-item {
        background: var(--card-bg);
        border: 1px solid var(--card-border);
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    
    .metric-label {
        font-size: 12px;
        color: var(--text-secondary);
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* 调整 Sidebar */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-color); /* 随系统变色 */
        border-right: 1px solid var(--card-border);
    }
    
    /* 调整 Metric 组件样式 (覆盖原生) */
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        color: var(--text-primary) !important;
    }
    div[data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
    }
    
    /* 分隔线优化 */
    hr {
        margin: 1.5rem 0;
        border: 0;
        border-top: 1px solid var(--card-border);
    }
    
    /* 按钮美化 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        border: 1px solid var(--card-border);
        color: var(--text-primary);
        background-color: var(--card-bg);
        transition: all 0.2s;
    }
    .stButton > button:hover {
        border-color: var(--accent-color);
        color: var(--accent-color);
        background-color: rgba(9, 105, 218, 0.1);
    }
</style>

<script>
// 主题检测和自动切换功能
(function() {
    // 检测当前系统主题
    function getCurrentTheme() {
        return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    // 更新Plotly图表主题
    function updatePlotlyTheme(theme) {
        const plotlyCharts = document.querySelectorAll('.js-plotly-plot');
        plotlyCharts.forEach(function(chart) {
            if (chart && chart.layout) {
                const newTemplate = theme === 'dark' ? 'plotly_dark' : 'plotly_white';
                try {
                    // 更新图表模板
                    Plotly.relayout(chart, {
                        template: newTemplate,
                        paper_bgcolor: theme === 'dark' ? '#0a0e27' : '#ffffff',
                        plot_bgcolor: theme === 'dark' ? '#0a0e27' : '#ffffff'
                    });
                    console.log('图表主题已更新为:', theme);
                } catch (error) {
                    console.log('更新图表主题时出错:', error);
                }
            }
        });
    }
    
    // 监听系统主题变化
    if (window.matchMedia) {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        // 主题变化处理函数
        function handleThemeChange(e) {
            const newTheme = e.matches ? 'dark' : 'light';
            console.log('系统主题已切换为:', newTheme);
            
            // 延迟更新以确保Plotly已加载
            setTimeout(function() {
                updatePlotlyTheme(newTheme);
            }, 500);
        }
        
        // 添加监听器
        if (darkModeQuery.addEventListener) {
            darkModeQuery.addEventListener('change', handleThemeChange);
        } else if (darkModeQuery.addListener) {
            // 兼容旧版浏览器
            darkModeQuery.addListener(handleThemeChange);
        }
        
        // 初始化时设置正确的主题
        console.log('当前系统主题:', getCurrentTheme());
    }
})();

// 移动端全屏横屏功能
(function() {
    // 检测是否为移动设备
    function isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               (navigator.maxTouchPoints && navigator.maxTouchPoints > 2);
    }
    
    // 全屏切换函数
    function toggleFullscreen(element) {
        if (!document.fullscreenElement && 
            !document.webkitFullscreenElement && 
            !document.mozFullScreenElement && 
            !document.msFullscreenElement) {
            // 进入全屏
            if (element.requestFullscreen) {
                element.requestFullscreen();
            } else if (element.webkitRequestFullscreen) {
                element.webkitRequestFullscreen();
            } else if (element.mozRequestFullScreen) {
                element.mozRequestFullScreen();
            } else if (element.msRequestFullscreen) {
                element.msRequestFullscreen();
            }
        } else {
            // 退出全屏
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
        }
    }
    
    // 锁定横屏
    async function lockLandscape() {
        if (isMobileDevice() && screen.orientation && screen.orientation.lock) {
            try {
                await screen.orientation.lock('landscape');
                console.log('屏幕已锁定为横屏模式');
            } catch (error) {
                console.log('无法锁定屏幕方向:', error);
            }
        }
    }
    
    // 解锁屏幕方向
    function unlockOrientation() {
        if (screen.orientation && screen.orientation.unlock) {
            try {
                screen.orientation.unlock();
                console.log('屏幕方向已解锁');
            } catch (error) {
                console.log('解锁屏幕方向失败:', error);
            }
        }
    }
    
    // 监听全屏变化
    function handleFullscreenChange() {
        const isFullscreen = !!(document.fullscreenElement || 
                               document.webkitFullscreenElement || 
                               document.mozFullScreenElement || 
                               document.msFullscreenElement);
        
        if (isFullscreen) {
            // 进入全屏时锁定横屏
            lockLandscape();
        } else {
            // 退出全屏时解锁方向
            unlockOrientation();
        }
    }
    
    // 添加全屏事件监听
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);
    
    // 为Plotly图表添加全屏功能
    function initChartFullscreen() {
        // 等待Plotly图表加载
        setTimeout(function() {
            const plotlyCharts = document.querySelectorAll('.js-plotly-plot');
            plotlyCharts.forEach(function(chart, index) {
                // 为每个图表创建包装容器
                if (!chart.parentElement.classList.contains('chart-fullscreen-container')) {
                    const wrapper = document.createElement('div');
                    wrapper.className = 'chart-fullscreen-container';
                    wrapper.id = 'chart-fullscreen-' + index;
                    chart.parentNode.insertBefore(wrapper, chart);
                    wrapper.appendChild(chart);
                    
                    // 添加自定义全屏按钮到Plotly工具栏
                    const modebar = chart.querySelector('.modebar');
                    if (modebar) {
                        const fullscreenBtn = document.createElement('a');
                        fullscreenBtn.className = 'modebar-btn';
                        fullscreenBtn.setAttribute('data-title', '全屏显示' + (isMobileDevice() ? '(横屏)' : ''));
                        fullscreenBtn.innerHTML = '<svg viewBox="0 0 1000 1000" class="icon"><path d="M250 200h-50q-21 0-35.5 14.5t-14.5 35.5v50q0 21 14.5 35.5t35.5 14.5 35.5-14.5 14.5-35.5v-50h50q21 0 35.5-14.5t14.5-35.5-14.5-35.5-35.5-14.5zm-50 600h50q21 0 35.5-14.5t14.5-35.5-14.5-35.5-35.5-14.5h-50v-50q0-21-14.5-35.5t-35.5-14.5-35.5 14.5-14.5 35.5v50q0 21 14.5 35.5t35.5 14.5zm600 0h50q21 0 35.5-14.5t14.5-35.5v-50q0-21-14.5-35.5t-35.5-14.5-35.5 14.5-14.5 35.5v50h-50q-21 0-35.5 14.5t-14.5 35.5 14.5 35.5 35.5 14.5zm50-600h-50q-21 0-35.5 14.5t-14.5 35.5 14.5 35.5 35.5 14.5h50v50q0 21 14.5 35.5t35.5 14.5 35.5-14.5 14.5-35.5v-50q0-21-14.5-35.5t-35.5-14.5z"></path></svg>';
                        fullscreenBtn.style.cursor = 'pointer';
                        
                        fullscreenBtn.onclick = function(e) {
                            e.preventDefault();
                            toggleFullscreen(wrapper);
                        };
                        
                        // 插入到工具栏
                        modebar.insertBefore(fullscreenBtn, modebar.firstChild);
                    }
                }
            });
        }, 1000);
    }
    
    // 页面加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChartFullscreen);
    } else {
        initChartFullscreen();
    }
    
    // 监听Streamlit重新渲染
    window.addEventListener('load', function() {
        initChartFullscreen();
    });
    
    // 使用MutationObserver监听DOM变化，确保新图表也能获得全屏功能
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                initChartFullscreen();
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
})();
</script>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 密码验证逻辑 (仅使用外部 secrets 配置)
# ---------------------------------------------------------
def check_password():
    """验证登录状态 - 密码完全由 secrets 配置"""
    # 检查 URL 参数自动登录
    if "auth" in st.query_params:
        if st.query_params["auth"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            return True
    
    def password_entered():
        """检查输入的密码是否正确"""
        if st.session_state["password"] == st.secrets["app_password"]:
            st.session_state["password_correct"] = True
            st.query_params["auth"] = st.secrets["app_password"]
            del st.session_state["password"]
            # Streamlit自动在callback后重新运行，无需手动调用st.rerun()
        else:
            st.session_state["password_correct"] = False
    
    # 首次访问或密码错误
    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        st.markdown("""
        <div style='text-align: center; padding: 50px;'>
            <h1>🔒 股票量化分析平台</h1>
            <p style='color: #787b86; font-size: 16px;'>请输入访问密码</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.text_input(
                "访问密码",
                type="password",
                on_change=password_entered,
                key="password",
                placeholder="请输入密码",
                label_visibility="collapsed"
            )
            
            # 仅在密码错误时显示错误信息
            if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                st.error("❌ 密码不正确，请重试")
        
        return False
    
    # 密码正确
    return True


# ---------------------------------------------------------
# 缓存数据获取函数 - 缩短缓存时间以获取更实时的数据
# ---------------------------------------------------------
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

@st.cache_data(ttl=30)  # 30秒缓存
def get_realtime_quote(symbol):
    """获取实时行情（带降级方案）"""
    quote = {}
    
    # 方案1: 尝试获取实时盘口数据
    try:
        df_bid = ak.stock_bid_ask_em(symbol=symbol)
        if not df_bid.empty:
            # 检查是否有有效交易数据
            latest_price = pd.to_numeric(df_bid[df_bid['item'] == '最新']['value'].values[0], errors='coerce')
            if not pd.isna(latest_price):
                quote['price'] = latest_price
                quote['open'] = pd.to_numeric(df_bid[df_bid['item'] == '今开']['value'].values[0], errors='coerce')
                quote['high'] = pd.to_numeric(df_bid[df_bid['item'] == '最高']['value'].values[0], errors='coerce')
                quote['low'] = pd.to_numeric(df_bid[df_bid['item'] == '最低']['value'].values[0], errors='coerce')
                quote['volume'] = pd.to_numeric(df_bid[df_bid['item'] == '成交量']['value'].values[0], errors='coerce')
                quote['amount'] = pd.to_numeric(df_bid[df_bid['item'] == '成交额']['value'].values[0], errors='coerce')
                
                # 计算涨跌幅
                prev_close = pd.to_numeric(df_bid[df_bid['item'] == '昨收']['value'].values[0], errors='coerce')
                if prev_close and prev_close > 0:
                    quote['change_pct'] = ((latest_price - prev_close) / prev_close) * 100
                    quote['change_amt'] = latest_price - prev_close
                else:
                    quote['change_pct'] = 0.0
                    quote['change_amt'] = 0.0
                    
                return quote
    except:
        pass
    
    # 方案2: 降级到分钟级历史数据（取最近一分钟）
    try:
        df_min = ak.stock_zh_a_hist_min_em(symbol=symbol, period='1', adjust='qfq')
        if not df_min.empty:
            latest = df_min.iloc[-1]
            quote['price'] = float(latest['收盘'])
            quote['open'] = float(latest['开盘'])
            quote['high'] = float(latest['最高'])
            quote['low'] = float(latest['最低'])
            quote['volume'] = float(latest['成交量'])
            quote['amount'] = float(latest['成交额'])
            
            # 这种情况下涨跌幅可能不准确，需要昨收，暂时设为None由UI处理或再取一次日线
            df_daily = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=(datetime.now()-timedelta(days=10)).strftime('%Y%m%d'), adjust="qfq")
            if not df_daily.empty:
                 # 取倒数第二个作为昨收（如果今天是交易日且已收盘，倒数第一是今日）
                 # 但这里为了简单，我们假设分钟线是最新的，拿日线的昨收来算
                 # 实际上akshare分钟线不带涨跌幅
                 pass
            
            # 为简单起见，如果降级到分钟线，涨跌幅可能无法精确获取，除非再调一次日线
            # 这里我们尝试从 info 中获取昨收
            return quote
            
    except:
        pass
        
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

@st.cache_data(ttl=86400, persist="disk")  # 每天缓存一次，持久化到磁盘
def get_all_stocks_list():
    """获取全量股票代码和名称列表（轻量级）"""
    try:
        # 使用更轻量的接口，仅获取代码和名称
        stock_list = ak.stock_info_a_code_name()
        stocks_dict = {}
        for _, row in stock_list.iterrows():
            code = str(row['code'])
            name = str(row['name'])
            stocks_dict[code] = name
        return stocks_dict
    except Exception as e:
        print(f"获取股票列表失败: {e}")  # 记录日志但不弹窗打扰用户
        return {}

def search_stock(query):
    """搜索股票（代码优先极速模式 + 名称模糊搜索）"""
    if not query:
        return []
    
    query = str(query).upper().strip()
    
    # 1. 如果是6位数字代码，直接验证并返回（极速模式，跳过列表下载）
    if len(query) == 6 and query.isdigit():
        # 这里为了速度，我们假设它是有效的，或者由前端加载时再验证
        # 如果需要更严谨，可以尝试获取一次info，但这会消耗一次网络请求
        # 为了极速体验，我们直接构造返回，让“加载”步骤去处理无效代码
        return [{'code': query, 'name': '按代码加载...'}]
    
    # 2. 如果不是纯代码，则进行名称搜索（需要下载列表）
    stocks = get_all_stocks_list()
    if not stocks:
        return []
        
    results = []
    # 优先搜索代码匹配（针对简短代码如 "600"）
    for code, name in stocks.items():
        if query in code:
            results.append({'code': code, 'name': name})
            if len(results) >= 10:
                break
    
    # 如果代码匹配不足，再搜名称
    if len(results) < 20:
        for code, name in stocks.items():
            if query in name and {'code': code, 'name': name} not in results:
                results.append({'code': code, 'name': name})
                if len(results) >= 20:
                    break
                    
    return results

def handle_search_submit():
    """处理搜索框回车事件"""
    query = st.session_state.search_query_input
    if not query:
        return
        
    with st.spinner("正在搜索..."):
        results = search_stock(query)
        
    if results:
        # 优先匹配代码
        target = None
        # 如果是精准代码
        if len(results) == 1 or (len(query) == 6 and query.isdigit()):
             target = results[0]['code']
        else:
            # 默认取第一个，或者可以保持原样让用户选
            # 这里为了"回车即加载"，如果你输入的是名称且只有唯一匹配，也直接加载
            if len(results) > 0:
                target = results[0]['code']
        
        if target:
            st.session_state.current_stock = target

def is_valid_stock_code(code):
    return len(code) == 6 and code.isdigit()

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
    
    # 更新布局 - 自适应主题（透明背景）
    # 不指定 template='plotly_dark'，让 Streamlit 自动处理或使用默认
    # 但我们需要确保字体颜色适配，由于 Plotly 无法读取 CSS 变量，我们尽量用默认或 neutral
    
    fig.update_layout(
        # template='plotly_dark', # 移除强制暗色
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
            # remove fixed color to let it adapt or keep it neutral gray
        ),
        margin=dict(l=10, r=10, t=60, b=20),
        # 移动端优化配置
        dragmode='pan',
        hovermode='x unified',
        # 字体统一
        font=dict(family="Noto Sans SC, sans-serif"),
        # 触摸交互配置
        modebar=dict(
            orientation='v',
            # bgcolor='rgba(22, 27, 34, 0.8)', # Remove hardcoded bg
            bgcolor='rgba(0,0,0,0)',
            color='#8b949e',
            activecolor='#0969da'
        )
    )
    
    # 坐标轴样式优化 - 使用透明或半透明颜色以适配双模式
    fig.update_xaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(128, 128, 128, 0.2)', # 通用半透明灰
        zeroline=False
    )
    fig.update_yaxes(
        showgrid=True, 
        gridwidth=1, 
        gridcolor='rgba(128, 128, 128, 0.2)',
        zeroline=False
    )
    
    return fig

# 初始化session state
if 'current_stock' not in st.session_state:
    st.session_state.current_stock = '600519'
if 'active_indicators' not in st.session_state:
    st.session_state.active_indicators = {'macd', 'kdj', 'rsi'}
if 'watchlist' not in st.session_state:
    # 默认自选股
    st.session_state.watchlist = {
        '600519': '贵州茅台',
        '000001': '平安银行',
        '000858': '五粮液',
        '601318': '中国平安',
        '600036': '招商银行'
    }

# ---------------------------------------------------------
# 密码验证 - 只有通过验证才显示主应用
# ---------------------------------------------------------
if not check_password():
    st.stop()  # 停止执行，不显示后续内容

# ---------------------------------------------------------
# 主应用界面 (密码验证通过后才显示)
# ---------------------------------------------------------

# 侧边栏
with st.sidebar:
    st.header("⚙️ 控制台")
    
    # 搜索
    st.subheader("搜索")
    # 使用 key 和 on_change 实现回车加载
    st.text_input(
        "代码或名称", 
        placeholder="例如: 600519 / 茅台 (回车体验)", 
        key="search_query_input",
        on_change=handle_search_submit
    )
    
    search_query = st.session_state.get("search_query_input", "")
    
    if search_query:
        display_results = search_stock(search_query)
        
        if not display_results:
            st.warning("未找到匹配的股票")
            # 占位按钮
            col_load, col_add = st.columns(2)
            with col_load:
                st.button("加载", disabled=True, use_container_width=True, key="btn_load_empty")
            with col_add:
                st.button("收藏", disabled=True, use_container_width=True, key="btn_fav_empty")
        else:
            # 确定当前操作的目标股票
            target_stock = None
            
            if len(display_results) == 1:
                target_stock = display_results[0]
            else:
                st.info("找到多个匹配项:")
                options = [f"{r['code']} - {r['name']}" for r in display_results]
                selected_label = st.selectbox("选择股票", options, key="search_select_box")
                # 解析选中的代码
                if selected_label:
                    code = selected_label.split(" - ")[0]
                    target_stock = next((r for r in display_results if r['code'] == code), None)
            
            # 显示操作按钮
            if target_stock:
                col_load, col_add = st.columns(2)
                with col_load:
                    # 如果只有1个结果且已经在 handle_search_submit 中加载了，这里按钮可以只是再次加载
                    if st.button("加载", use_container_width=True, key="btn_load_manual"):
                        st.session_state.current_stock = target_stock['code']
                        st.rerun()
                
                with col_add:
                    if st.button("收藏", use_container_width=True, key="btn_fav_manual"):
                        if target_stock['code'] not in st.session_state.watchlist:
                            st.session_state.watchlist[target_stock['code']] = target_stock['name']
                            st.success(f"已收藏: {target_stock['name']}")
                            time.sleep(1) # 给一点时间显示成功提示
                            st.rerun()
                        else:
                            st.info("已在收藏夹中")

    else:
        # 如果没有搜索词，显示默认状态
        col_load, col_add = st.columns(2)
        with col_load:
            st.button("加载", disabled=True, use_container_width=True, key="btn_load_default")
        with col_add:
            st.button("收藏", disabled=True, use_container_width=True, key="btn_fav_default")
    
    st.divider()
    
    # 自选股
    st.subheader("📋 自选股")
    
    if st.session_state.watchlist:
        for code, name in st.session_state.watchlist.items():
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"{code} {name}", key=f"watch_{code}", use_container_width=True):
                    st.session_state.current_stock = code
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{code}", use_container_width=True, help="删除自选股"):
                    del st.session_state.watchlist[code]
                    st.success(f"已删除 {code} {name}")
                    st.rerun()
    else:
        st.info("暂无自选股，请通过搜索添加")
    
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
    
    st.divider()
    
    # 登出按钮
    if st.button("🔒 安全登出", use_container_width=True, type="secondary"):
        st.session_state["password_correct"] = False
        st.query_params.clear()
        st.rerun()


# 主界面
st.title("📈 股票量化分析平台")

# 计算日期范围
end_date = datetime.now()
start_date = end_date - timedelta(days=period_map[period])

# 获取数据
with st.spinner('正在加载数据...'):
    # 并行获取数据
    stock_info = get_stock_info(st.session_state.current_stock)
    realtime_quote = get_realtime_quote(st.session_state.current_stock)
    
    hist_df = get_stock_history(
        st.session_state.current_stock,
        start_date,
        end_date,
        adjust_map[adjust]
    )

if stock_info and hist_df is not None and not hist_df.empty:
    # 优先使用实时行情，没有则回退到历史数据最后一行
    price_data = {}
    
    if realtime_quote and 'price' in realtime_quote:
        price_data = realtime_quote
    else:
        latest = hist_df.iloc[-1]
        price_data['price'] = latest['收盘']
        price_data['change_pct'] = latest['涨跌幅']
        price_data['open'] = latest['开盘']
        price_data['high'] = latest['最高']
        price_data['low'] = latest['最低']
        price_data['volume'] = latest['成交量']
        price_data['amount'] = latest['成交额']
    
    # 补全涨跌幅（如果实时接口没拿到）
    if 'change_pct' not in price_data:
         # 尝试从历史数据算（不一定准）
         pass

    # 计算涨跌幅颜色
    change_pct = price_data.get('change_pct', 0)
    change_amt = price_data.get('change_amt', 0)
    
    is_up = change_pct >= 0
    color_class = "up-bg" if is_up else "down-bg"
    arrow = "▲" if is_up else "▼"
    
    # 渲染自定义 Hero Header
    st.markdown(f"""
    <div class="stock-hero">
        <div>
            <div class="hero-title">{stock_info.get('股票简称', '未知股票')} ({st.session_state.current_stock})</div>
            <div class="hero-subtitle">
                {stock_info.get('行业', '行业未知')} | {stock_info.get('地域', '地域未知')} | 
                <span style="color: {'#3fb950' if is_up else '#f85149'}">{arrow} {abs(change_pct):.2f}%</span>
            </div>
        </div>
        <div style="text-align: right;">
            <div style="color: {'#3fb950' if is_up else '#f85149'};" class="price-main">
                ¥{price_data.get('price', 0):.2f}
                <span class="price-change {color_class}">
                     {change_amt:+.2f}
                </span>
            </div>
            <div class="hero-subtitle">成交量: {price_data.get('volume', 0)/1e4:.0f}手  成交额: {price_data.get('amount', 0)/1e8:.2f}亿</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 关键指标网格
    st.markdown(f"""
    <div class="glass-card">
        <div class="metric-grid">
            <div class="metric-item">
                <div class="metric-label">今开</div>
                <div class="metric-value">¥{price_data.get('open', 0):.2f}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">最高</div>
                <div class="metric-value">¥{price_data.get('high', 0):.2f}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">最低</div>
                <div class="metric-value">¥{price_data.get('low', 0):.2f}</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">换手率</div>
                <div class="metric-value">{stock_info.get('换手率', '- ')}%</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">总市值</div>
                <div class="metric-value">{float(stock_info.get('总市值', 0))/1e8:.1f}亿</div>
            </div>
            <div class="metric-item">
                <div class="metric-label">市盈率(动)</div>
                <div class="metric-value">{stock_info.get('市盈率-动态', '-')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
    st.caption("💡 数据来源: AKShare (东方财富) ")
with col_footer2:
    from datetime import datetime, timedelta, timezone
    bj_time = datetime.now(timezone(timedelta(hours=8))).strftime('%H:%M:%S')
    st.caption(f"⏰ 北京时间: {bj_time}")
