import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
from datetime import datetime

# --- 1. 机构级页面配置 (Apple 极致视觉 + 2026 时间锚点) ---
st.set_page_config(page_title="LEAN Executive | $1M Institutional", layout="wide")

# 核心视觉修复：强制高对比度
st.markdown("""
    <style>
    /* 全局深邃背景与纯白文字 */
    [data-testid="stAppViewContainer"] { background: #0e1117; color: #ffffff !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #ffffff !important; }

    /* 终极修复：高亮蓝色按钮 */
    div.stButton > button:first-child {
        background-color: #007AFF !important; /* Apple Blue */
        color: #ffffff !important;
        border: none;
        padding: 18px 30px;
        font-weight: 800;
        width: 100%;
        border-radius: 12px;
        font-size: 20px;
        box-shadow: 0 10px 20px rgba(0,122,255,0.4);
        margin-top: 20px;
    }
    div.stButton > button:hover { background-color: #005DCB !important; transform: scale(1.01); }

    /* 策略报告专用高对比度容器 */
    .report-box { 
        background-color: #1c1c1e; 
        color: #ffffff !important; 
        padding: 25px; 
        border-radius: 12px; 
        border: 1px solid #00d1ff; 
        line-height: 1.6;
        margin-top: 20px;
    }
    
    /* 指标卡片优化 */
    [data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 800; }
    div[data-testid="stMetric"] { background: #1c1c1e; border: 1px solid #3a3a3c; border-radius: 12px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心量化算法 ---
def compute_indicators(df):
    high_low = df['High'] - df['Low']
    high_pc = np.abs(df['High'] - df['Close'].shift())
    low_pc = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    return df

# --- 3. 数据与情报抓取 (2026 实拍) ---
@st.cache_data(ttl=60)
def get_institutional_feed(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="1m")
        if not df.empty:
            df = compute_indicators(df)
            return df, float(df['Close'].iloc[-1]), float((df['Close'].iloc[-1] - df['Open'].iloc[0])/df['Open'].iloc[0]*100)
    except: pass
    return None, 0.0, 0.0

@st.cache_data(ttl=300)
def open_crawl_intelligence(ticker):
    feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
    return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]

# --- 4. 侧边栏：$1M 决策中枢 ---
with st.sidebar:
    st.title("🏛️ 策略控制台")
    or_key = st.text_input("OpenRouter Key", type="password")
    ASSETS = {"黄金 (Gold)": "GC=F", "原油 (WTI)": "CL=F", "纳指100": "^NDX", "英伟达 (NVDA)": "NVDA", "ETH/USDT": "ETH-USD"}
    target = st.selectbox("监控标的", list(ASSETS.keys()))
    st.divider()
    capital = 1000000 
    risk_level = st.slider("单笔风险暴露 (%)", 0.5, 3.0, 1.5)

# --- 5. 主界面布局 ---
st.title(f"📊 {target} 实时量化监控终端")

df, price, change = get_institutional_feed(ASSETS[target])
news_data = open_crawl_intelligence(ASSETS[target])
current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# A. 顶层核心指标
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("实时现价", f"${price:,.2f}")
with c2: st.metric("当日波动", f"{change:+.2f}%")
with c3:
    atr_val = df['ATR'].iloc[-1] if df is not None and not df.empty else 0
    st.metric("ATR 波动率 (1m)", f"{atr_val:.2f}")
with c4:
    risk_amt = capital * (risk_level / 100)
    pos_size = risk_amt / (atr_val * 2) if atr_val > 0 else 0
    st.metric("建议头寸 (Units)", f"{pos_size:,.0f}", f"风控额: ${risk_amt:,.0f}")

# B. 动态技术分析图表
if df is not None and not df.empty:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='#FF9500', width=1.5)), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='#48484a'), row=2, col=1)
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ 正在校准 2026 实时数据流...")

# C. Open Crawl 情报与 AI 深度决策
st.divider()
st.subheader("🌐 Open Crawl 实时情报网")

if news_data:
    cols = st.columns(len(news_data))
    for i, item in enumerate(news_data):
        cols[i].markdown(f"**情报 {i+1}**\n{item['title']}\n[查看原文]({item['link']})")

# 启动按钮
if st.button("🚀 启动全球策略共识分析 (Global Consensus)"):
    if not or_key:
        st.error("请填入 API Key")
    else:
        with st.spinner("正在校准 2026 时间锚点并融合情报流..."):
            try:
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_key)
                # 关键修复：在 Prompt 中明确今天的日期
                prompt = f"""
                今天是 {current_time_str}。请严格基于当前时间进行分析。
                你是麦肯锡资深策略顾问。针对 {target}，现价 {price}，ATR {atr_val:.2f}。
                实时情报: {news_data[0]['title'] if news_data else 'None'}。
                
                请为苏先生（资深交易员，$1M 账户规模）生成报告：
                1. [报告头部] 标题必须包含正确的当前日期：{current_time_str[:7]}。
                2. [情报对冲] 该新闻在 2026 年的市场背景下是支撑还是压制？
                3. [操作矩阵] 精确的入场、SL（止损）和 三级 TP（止盈）。
                4. [风控警告] 在 1.5% 风险系数下，当前的仓位安全性。
                """
                resp = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                
                # 结果展示：使用自定义白字黑底容器
                st.markdown(f'<div class="report-box">{resp.choices[0].message.content.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"分析异常: {e}")

st.caption(f"麦肯锡首席顾问模式 | Leo 狮子座 1986-08-21 逻辑加持 | 账户基数: $1,000,000")
