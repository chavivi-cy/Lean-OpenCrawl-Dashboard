import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
from datetime import datetime

# --- 1. 机构级页面配置 (Apple 极致视觉 + 深度风控) ---
st.set_page_config(page_title="LEAN Quantum Core | $1M Institutional", layout="wide")

# 核心 CSS 修复：强制按钮可见，优化白字黑底
st.markdown("""
    <style>
    /* 全局背景与文字 */
    [data-testid="stAppViewContainer"] { background: #0e1117; color: #ffffff !important; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    h1, h2, h3, p, span, label { color: #ffffff !important; }

    /* 关键修复：启动按钮样式 */
    div.stButton > button:first-child {
        background-color: #007AFF !important; /* Apple 经典蓝 */
        color: white !important;
        border: none;
        padding: 15px 30px;
        font-weight: bold;
        width: 100%;
        border-radius: 10px;
        font-size: 18px;
        box-shadow: 0 4px 15px rgba(0,122,255,0.3);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #0056b3 !important;
        transform: translateY(-2px);
    }

    /* 指标卡片样式 */
    [data-testid="stMetricValue"] { color: #ffffff !important; font-family: 'SF Pro Display', sans-serif; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #86868b !important; }
    div[data-testid="stMetric"] { background: #1c1c1e; border: 1px solid #3a3a3c; border-radius: 12px; padding: 20px; }
    
    /* 舆情卡片样式 */
    .sentiment-card { background: #2c2c2e; padding: 20px; border-radius: 12px; border-left: 5px solid #00d1ff; margin: 15px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心量化算法 (手写 ATR 避开 numba 兼容性) ---
def compute_indicators(df):
    # 计算 ATR (用于 $1M 风险头寸管理)
    high_low = df['High'] - df['Low']
    high_pc = np.abs(df['High'] - df['Close'].shift())
    low_pc = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    # 均线
    df['MA20'] = df['Close'].rolling(window=20).mean()
    return df

# --- 3. 实时 Feed：分钟级行情 + 深度舆情 ---
@st.cache_data(ttl=60)
def get_institutional_feed(ticker):
    try:
        # 获取 1 分钟颗粒度，确保量化准确性
        df = yf.download(ticker, period="1d", interval="1m")
        if not df.empty:
            df = compute_indicators(df)
            return df, float(df['Close'].iloc[-1]), float((df['Close'].iloc[-1] - df['Open'].iloc[0])/df['Open'].iloc[0]*100)
    except: pass
    return None, 0.0, 0.0

@st.cache_data(ttl=300)
def open_crawl_intelligence(ticker):
    # 真实抓取主流财经 RSS
    feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
    return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]

# --- 4. 侧边栏：$1,000,000 风控控制台 ---
with st.sidebar:
    st.title("🏛️ 机构管理")
    or_key = st.text_input("OpenRouter API Key", type="password")
    
    st.divider()
    ASSETS = {
        "黄金 (Gold)": "GC=F", "原油 (WTI)": "CL=F", "纳指100": "^NDX",
        "英伟达 (NVDA)": "NVDA", "ETH/USDT": "ETH-USD"
    }
    target = st.selectbox("监控标的", list(ASSETS.keys()))
    
    st.divider()
    capital = 1000000 
    st.write(f"💼 资产管理规模: **${capital:,.0f}**")
    risk_level = st.slider("单笔风险暴露 (%)", 0.5, 3.0, 1.5)

# --- 5. 主界面布局 ---
st.title(f"📊 {target} 实时量化监控终端")

df, price, change = get_institutional_feed(ASSETS[target])
news_data = open_crawl_intelligence(ASSETS[target])

# A. 顶层核心指标
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("实时现价", f"${price:,.2f}")
with c2: st.metric("当日波动", f"{change:+.2f}%")
with c3:
    atr_val = df['ATR'].iloc[-1] if df is not None else 0
    st.metric("ATR 波动率 (1m)", f"{atr_val:.2f}")
with c4:
    # 基于 $1M 的 ATR 仓位计算：$15,000 / (ATR * 2)
    risk_amt = capital * (risk_level / 100)
    pos_size = risk_amt / (atr_val * 2) if atr_val > 0 else 0
    st.metric("建议头寸 (Units)", f"{pos_size:,.0f}", f"风控额: ${risk_amt:,.0f}")

# B. 动态技术分析图表
if df is not None:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    # K 线
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
    # MA20 趋势线
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='#FF9500', width=1.5)), row=1, col=1)
    # 成交量
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='#48484a'), row=2, col=1)
    
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# C. Open Crawl 深度情报与 AI 决策
st.divider()
st.subheader("🌐 Open Crawl 实时情报网")

# 舆情情报解析
if news_data:
    st.markdown('<div class="sentiment-card">', unsafe_allow_html=True)
    st.write("📡 **实时全网监控结果：**")
    for item in news_data:
        st.write(f"- {item['title']} ([原文]({item['link']}))")
    st.markdown('</div>', unsafe_allow_html=True)

if st.button("🚀 启动全球策略共识分析 (Global Consensus)"):
    if not or_key:
        st.error("请先在左侧输入 API Key")
    else:
        with st.spinner("正在融合分钟级行情与实时情报流..."):
            try:
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_key)
                prompt = f"""
                你是麦肯锡资深策略顾问。针对 {target}，现价 {price}。
                实时情报摘要: {news_data[0]['title'] if news_data else 'None'}。
                请结合 100 万美金账户（1.5% 风险限额）给出决策报告：
                1. [情报分析] 针对该实时新闻，判断是对该品种的 Short-term 利好还是利空。
                2. [操作矩阵] 精确的入场位参考、止损位 (SL) 和 三级止盈目标 (TP)。
                3. [机构警告] 基于 ATR {atr_val:.2f} 评估当前流动性风险。
                """
                resp = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                st.info(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"分析异常: {e}")

st.caption(f"麦肯锡首席顾问模式 | Leo 狮子座 1986-08-21 逻辑加持 | 数据延迟: <60s")
