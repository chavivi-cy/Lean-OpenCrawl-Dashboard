import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
from datetime import datetime

# --- 1. 机构级页面配置 (Apple 极致视觉体验) ---
st.set_page_config(page_title="LEAN Executive | $1M 机构终端", layout="wide")

# 自定义 CSS：全黑背景 + 全白字体 + 现代风控卡片
st.markdown("""
    <style>
    /* 全局背景色与字体颜色 */
    [data-testid="stAppViewContainer"] { background: #0e1117; color: #ffffff !important; }
    /* 侧边栏样式 */
    [data-testid="stSidebar"] { background: #161b22; color: #ffffff !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] small { color: #ffffff !important; }
    /* 主标题与分割线样式 */
    h1, h2, h3, h4, .stCaption { color: #ffffff !important; }
    div[data-testid="stMarkdownContainer"] hr { border-color: #30363d; }
    /* Metric 指标样式：白字、科技感边框 */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] { color: #ffffff !important; }
    div[data-testid="stMetricValue"] { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; }
    /* 熔断告警卡片样式 */
    .critical-alert { background-color: #441111; padding: 25px; border-radius: 12px; border: 2px solid #ff4b4b; text-align: center; }
    /* Open Crawl 情报卡片样式 */
    .news-card { background: #1a1c24; padding: 15px; border-radius: 8px; border-left: 4px solid #00d1ff; margin-bottom: 12px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心算法：手动计算 ATR (解决 numba 报错与 $1M 风险管理) ---
def compute_technical_indicators(df, atr_period=14):
    # 计算 ATR
    high_low = df['High'] - df['Low']
    high_pc = np.abs(df['High'] - df['Close'].shift())
    low_pc = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=atr_period).mean()
    # 均线系统
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    return df

# --- 3. 实时行情与舆情数据 Feed ---
@st.cache_data(ttl=60) # 缓存 60 秒，避免频繁请求被封 IP
def get_market_feed(ticker):
    try:
        # 获取 1 分钟颗粒度数据，覆盖最近 1 天
        df = yf.download(ticker, period="1d", interval="1m")
        if not df.empty and len(df) > 20: # 确保有足够数据计算指标
            df = compute_technical_indicators(df)
            price = df['Close'].iloc[-1]
            change = (price - df['Open'].iloc[0]) / df['Open'].iloc[0] * 100
            return df, float(price), float(change)
    except:
        pass
    return None, 0.0, 0.0

@st.cache_data(ttl=300)
def open_crawl_sentiment_feed(ticker):
    # 模拟 Open Crawl：实时抓取 Yahoo Finance RSS 新闻
    feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
    news = [{"title": entry.title, "link": entry.link} for entry in feed.entries[:3]]
    return news

# --- 4. 侧边栏：$1,000,000 机构风控中控 ---
with st.sidebar:
    st.title("🏦 决策中心")
    or_api_key = st.text_input("OpenRouter API Key (sk-or-v1-...)", type="password")
    
    st.divider()
    TICKERS = {
        "黄金 (Gold)": "GC=F", "原油 (WTI)": "CL=F", "纳指100 (NAS100)": "^NDX",
        "恒生指数 (HSI)": "^HSI", "英伟达 (NVDA)": "NVDA", "ETH/USDT": "ETH-USD"
    }
    target = st.selectbox("核心分析标的", list(TICKERS.keys()))
    
    st.divider()
    capital = 1000000 
    st.write(f"💼 资产规模: **${capital:,.0f}**")
    risk_percent = st.slider("单笔风险暴露 (Risk %)", 0.5, 3.0, 1.5)
    drawdown_limit = st.slider("最大允许回撤 (%)", 1.0, 10.0, 5.0)

# --- 5. 熔断机制判定 ---
# 模拟实时回撤，实盘需接入 API
simulated_drawdown = 0.4 
is_circuit_breaker_active = simulated_drawdown >= drawdown_limit

# --- 6. 主界面布局 ---
st.title(f"🏛️ {target} 分钟级量化决策终端")

if is_circuit_breaker_active:
    st.markdown(f'<div class="critical-alert"><h2>🚨 熔断系统已激活 (Circuit Breaker)</h2><p>当前回撤 {simulated_drawdown}% 已触发上限保护。Leo 1986-08-21 风控协议已锁定所有执行权限。</p></div>', unsafe_allow_html=True)
else:
    df, price, change = get_market_feed(TICKERS[target])
    news = open_crawl_sentiment_feed(TICKERS[target])

    # A. 顶层核心决策指标看板
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("实时现价", f"${price:,.2f}" if price > 0 else "---")
    with c2: st.metric("当日波动", f"{change:+.2f}%" if price > 0 else "---")
    with c3:
        current_atr = df['ATR'].iloc[-1] if df is not None else 0
        st.metric("ATR 波动波动率", f"{current_atr:.2f}")
    with c4:
        # $1M 机构风控： Risk Dollar / (ATR * 2)
        risk_dollar = capital * (risk_percent / 100)
        pos_size = risk_dollar / (current_atr * 2) if current_atr > 0 else 0
        st.metric("建议头寸 (Units)", f"{pos_size:,.0f}", f"风控额: ${risk_dollar:,.0f}")

    # B. 交互式技术分析图表 (空白修复版)
    if df is not None and not df.empty:
        # 创建带有均线系统的 K 线图
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        # 主 K 线图
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
        # 添加均线展示
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='orange', width=1)), row=1, col=1)
        # 成交量图
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='#30363d'), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False, legend_font_color="#ffffff")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ 正在尝试连接 Yahoo Finance 行情源，请确保 Surge 网络代理通畅...")

    # C. Open Crawl 实时情报研报矩阵 (修复版)
    st.divider()
    st.subheader("🌐 Open Crawl 实时情报扫描系统")
    
    col_news, col_ai = st.columns([1, 1])
    
    with col_news:
        st.write("📡 **实时全网扫描结果：**")
        if news:
            for item in news:
                st.markdown(f'<div class="news-card"><b>{item["title"]}</b><br><small><a href="{item["link"]}" target="_blank" style="color:#00d1ff;">阅读原文</a></small></div>', unsafe_allow_html=True)
        else:
            st.write("暂无最新消息")

    with col_ai:
        if st.button("🚀 启动全球策略共识分析 (Global Consensus)", use_container_width=True):
            if not or_api_key:
                st.error("请填入 OpenRouter API Key")
            elif price == 0:
                st.error("行情数据不完整，分析中断。")
            else:
                with st.spinner("整合分钟级行情数据与实时情报流..."):
                    try:
                        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_api_key)
                        prompt = f"""
                        你是麦肯锡资深金融顾问。针对 {target}，现价 {price}。
                        实时情报: {news[0]['title'] if news else 'None'}。
                        ATR 波动率为 {current_atr:.2f}。
                        请基于 100 万美金账户规模（1.5% 风险系数）提供决策建议：
                        1. 走势定性：基于均线系统给出分钟级多空判断。
                        2. 操作建议：精确的入场参考、止损位 (SL) 和 3 级止盈位 (TP)。
                        3. 机构警示：针对 $1M 账户，给出特有的流动性或波动率警告。
                        语言风格：冷静、专业、去散户化。
                        """
                        resp = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                        st.info(resp.choices[0].message.content)
                    except Exception as e:
                        st.error(f"分析失败: {e}")

st.caption(f"麦肯锡首席顾问模式 | $1M 风险管理矩阵已激活 | 数据频率：1分钟/次 | 更新时间：{datetime.now().strftime('%H:%M:%S')}")
