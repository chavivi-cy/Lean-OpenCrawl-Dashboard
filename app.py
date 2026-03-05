import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
from datetime import datetime

# --- 1. 机构级页面配置 (Apple 风格) ---
st.set_page_config(page_title="LEAN Quantum Core | $1M Institutional", layout="wide")
st.markdown("""
    <style>
    .stMetric { border: 1px solid #30363d; border-radius: 10px; padding: 15px; background: #161b22; }
    .breaker-active { background-color: #441111; padding: 25px; border-radius: 12px; border: 2px solid #ff4b4b; text-align: center; margin-bottom: 20px; }
    .news-card { background: #1a1c24; padding: 15px; border-radius: 8px; border-left: 4px solid #00d1ff; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心算法：手动计算 ATR (避开 numba/3.14 报错) ---
def compute_technical_indicators(df, atr_period=14):
    # 计算 ATR
    high_low = df['High'] - df['Low']
    high_pc = np.abs(df['High'] - df['Close'].shift())
    low_pc = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=atr_period).mean()
    # 均线
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA60'] = df['Close'].rolling(window=60).mean()
    return df

# --- 3. 实时数据抓取 (分钟级) ---
@st.cache_data(ttl=60)
def get_institutional_feed(ticker):
    try:
        # 获取 1 分钟颗粒度数据
        df = yf.download(ticker, period="1d", interval="1m")
        if not df.empty and len(df) > 20:
            df = compute_technical_indicators(df)
            price = df['Close'].iloc[-1]
            change = (price - df['Open'].iloc[0]) / df['Open'].iloc[0] * 100
            return df, float(price), float(change)
    except Exception as e:
        st.sidebar.error(f"Feed Error: {e}")
    return None, 0.0, 0.0

@st.cache_data(ttl=300)
def open_crawl_sentiment(ticker):
    # 真实扫描 Yahoo Finance RSS 新闻流
    feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
    return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]

# --- 4. 侧边栏：$1,000,000 风控控制台 ---
with st.sidebar:
    st.title("🏦 决策控制中心")
    # 填入你新申请的 sk-or-v1-... 钥匙
    or_api_key = st.text_input("OpenRouter API Key", type="password")
    
    st.divider()
    ASSETS = {
        "黄金 (Gold)": "GC=F",
        "原油 (WTI)": "CL=F",
        "纳指100 (NAS100)": "^NDX",
        "恒生指数 (HSI)": "^HSI",
        "英伟达 (NVDA)": "NVDA",
        "ETH/USDT": "ETH-USD"
    }
    target_label = st.selectbox("核心监控标的", list(ASSETS.keys()))
    
    st.divider()
    capital = 1000000 # 设定账户基数为 100 万美金
    risk_rate = st.slider("单笔风险暴露 (Risk %)", 0.5, 3.0, 1.5)
    drawdown_circuit = st.slider("最大允许回撤 (%)", 1.0, 10.0, 5.0)
    st.info(f"决策者：苏先生 | Leo\n资金规模：${capital:,.0f}")

# --- 5. 熔断判定逻辑 ---
simulated_drawdown = 0.4 # 实际应从账户余额 API 获取
is_locked = simulated_drawdown >= drawdown_circuit

# --- 6. 主界面 ---
st.title(f"🏛️ {target_label} 分钟级量化监控终端")

if is_locked:
    st.markdown(f'<div class="breaker-active"><h2>🚨 熔断系统已激活 (Circuit Breaker)</h2><p>当前回撤 {simulated_drawdown}% 超过阈值。1986-08-21 狮子座风控协议已锁定所有执行权限。</p></div>', unsafe_allow_html=True)
else:
    df, price, change = get_institutional_feed(ASSETS[target_label])
    news_items = open_crawl_sentiment(ASSETS[target_label])

    # A. 顶层机构指标看板
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("实时现价", f"${price:,.2f}")
    with c2: st.metric("当日波动", f"{change:+.2f}%")
    with c3:
        atr_val = df['ATR'].iloc[-1] if df is not None else 0
        st.metric("ATR 波动率 (1m)", f"{atr_val:.2f}")
    with c4:
        # 100 万美金风险计算：$15,000 / (ATR * 2)
        risk_dollar = capital * (risk_rate / 100)
        pos_size = risk_dollar / (atr_val * 2) if atr_val > 0 else 0
        st.metric("建议头寸 (Units)", f"{pos_size:,.0f}", f"风控额: ${risk_dollar:,.0f}")

    # B. 动态 K 线图 (15分钟视角/分钟采样)
    if df is not None:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Market'), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color='#30363d'), row=2, col=1)
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

    # C. Open Crawl 实时舆情研报
    st.divider()
    st.subheader("🌐 Open Crawl 实时情报网")
    
    col_news, col_ai = st.columns([1, 1])
    with col_news:
        st.write("📡 **全网实时扫描分析：**")
        for item in news_items:
            st.markdown(f'<div class="news-card"><b>{item["title"]}</b><br><small><a href="{item["link"]}" target="_blank">查看原文链接</a></small></div>', unsafe_allow_html=True)

    with col_ai:
        if st.button("🚀 生成麦肯锡首席策略报告", use_container_width=True):
            if not or_api_key:
                st.error("请填入 OpenRouter API Key")
            else:
                with st.spinner("整合分钟级行情数据与情报矩阵..."):
                    try:
                        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_api_key)
                        prompt = f"""
                        你是麦肯锡资深量化顾问。针对 {target_label}，当前现价 {price}。
                        ATR 波动率为 {atr_val:.2f}。实时新闻关键词: {news_items[0]['title'] if news_items else 'None'}。
                        请基于 100 万美金账户规模（1.5% 风险系数）提供决策建议：
                        1. 走势研判：分钟级趋势与舆情共振分析。
                        2. 操作建议：精确的入场参考、止损位 (SL) 和 3 级止盈位 (TP)。
                        3. 机构警示：在此波动率下，针对 $1M 账户的流动性风险提示。
                        """
                        resp = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                        st.info(resp.choices[0].message.content)
                    except Exception as e:
                        st.error(f"AI 调用异常: {e}")

st.caption(f"麦肯锡首席顾问模式 | $1M 风险管理引擎已激活 | 数据频率：1分钟 | {datetime.now().strftime('%H:%M:%S')}")
