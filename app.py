import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
from datetime import datetime

# --- 1. 机构级页面配置 ---
st.set_page_config(page_title="LEAN Executive | $1M 决策终端", layout="wide")
st.markdown("""
    <style>
    .stMetric { border: 1px solid #30363d; border-radius: 10px; padding: 15px; background: #161b22; }
    .news-card { background: #1a1c24; padding: 15px; border-radius: 8px; border-left: 4px solid #00d1ff; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心风控算法：ATR 计算 (手写版，避开 numba 报错) ---
def compute_atr(df, period=14):
    high_low = df['High'] - df['Low']
    high_cp = np.abs(df['High'] - df['Close'].shift())
    low_cp = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

# --- 3. 数据抓取：分钟级行情 + Open Crawl 情报 ---
@st.cache_data(ttl=60)
def get_institutional_data(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="1m")
        if not df.empty:
            df['ATR'] = compute_atr(df)
            price = df['Close'].iloc[-1]
            change = (price - df['Open'].iloc[0]) / df['Open'].iloc[0] * 100
            return df, float(price), float(change)
    except:
        pass
    return None, 0.0, 0.0

@st.cache_data(ttl=300)
def get_live_sentiment(ticker):
    # 真实抓取 Yahoo Finance 的新闻流
    feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
    return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]

# --- 4. 侧边栏：$1M 风控中控 ---
with st.sidebar:
    st.title("🏦 机构风控中心")
    api_key = st.text_input("OpenRouter Key (sk-or-v1-...)", type="password")
    
    st.divider()
    ASSETS = {
        "黄金 (Gold)": "GC=F", "原油 (WTI)": "CL=F", "纳指100": "^NDX",
        "恒指 (HSI)": "^HSI", "英伟达 (NVDA)": "NVDA", "ETH/USDT": "ETH-USD"
    }
    target = st.selectbox("核心分析标的", list(ASSETS.keys()))
    
    st.divider()
    capital = 1000000 
    risk_limit = st.slider("单笔风险暴露 (%)", 0.5, 3.0, 1.5)
    st.info(f"决策者：苏先生\n资产规模：${capital:,.0f}")

# --- 5. 主界面布局 ---
st.title(f"🏛️ {target} 分钟级量化决策系统")

df, price, change = get_institutional_data(ASSETS[target])
news_items = get_live_sentiment(ASSETS[target])

# A. 核心指标看板
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("实时现价", f"${price:,.2f}")
with c2: st.metric("当日波动", f"{change:+.2f}%")
with c3:
    atr_val = df['ATR'].iloc[-1] if df is not None else 0
    st.metric("ATR 波动率 (1m)", f"{atr_val:.2f}")
with c4:
    # $1M 风控：$15,000 / (ATR * 2)
    risk_dollar = capital * (risk_limit / 100)
    pos_size = risk_dollar / (atr_val * 2) if atr_val > 0 else 0
    st.metric("建议头寸 (Units)", f"{pos_size:,.0f}", f"风控额: ${risk_dollar:,.0f}")

# B. 动态 K 线图
if df is not None:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='#30363d'), row=2, col=1)
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# C. Open Crawl 情报展示
st.divider()
st.subheader("🌐 Open Crawl 实时情报分析")
col_news, col_ai = st.columns([1, 1])

with col_news:
    st.write("📡 **实时扫描结果：**")
    for item in news_items:
        st.markdown(f'<div class="news-card"><b>{item["title"]}</b><br><small><a href="{item["link"]}" target="_blank">查看原文</a></small></div>', unsafe_allow_html=True)

with col_ai:
    if st.button("🚀 生成麦肯锡首席策略报告", use_container_width=True):
        if not api_key: st.error("请填入 API Key")
        else:
            with st.spinner("整合分钟级行情与实时情报流..."):
                try:
                    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
                    prompt = f"你是资深量化顾问。{target}现价{price}，ATR为{atr_val:.2f}。实时新闻：{news_items[0]['title'] if news_items else '无'}。请基于100万美金账户给出入场、止损(SL)和3级止盈(TP)策略。"
                    resp = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                    st.info(resp.choices[0].message.content)
                except Exception as e: st.error(f"分析异常: {e}")

st.caption(f"麦肯锡首席顾问模式 | 狮子座 Leo 专属逻辑 | 更新：{datetime.now().strftime('%H:%M:%S')}")
