import streamlit as st
from openai import OpenAI
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
import requests
from datetime import datetime

# --- 1. 机构级页面配置 (Apple 极致视觉 + 2026 逻辑) ---
st.set_page_config(page_title="LEAN Quantum Pro | $1M Terminal", layout="wide")

# 终极 CSS 修复：强制侧边栏深色背景+纯白文字，其他部分保持原有的机构黑金风格
st.markdown("""
    <style>
    /* 1. 全局背景与主文字 */
    [data-testid="stAppViewContainer"] { background: #0e1117; color: #ffffff !important; }
    
    /* 2. 侧边栏极致修复：深色背景 (#161b22) + 纯白文字 */
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
    }
    /* 强制侧边栏内所有文字元素为白色 */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] small {
        color: #ffffff !important;
    }
    /* 侧边栏输入框背景与文字颜色 */
    [data-testid="stSidebar"] input {
        background-color: #2c2c2e !important;
        color: #ffffff !important;
        border: 1px solid #3a3a3c !important;
    }

    /* 3. 核心决策按钮：苹果蓝 (#007AFF) */
    div.stButton > button:first-child {
        background-color: #007AFF !important;
        color: #ffffff !important;
        border: none;
        padding: 18px 0;
        font-weight: 800;
        width: 100%;
        border-radius: 12px;
        font-size: 20px;
        box-shadow: 0 4px 20px rgba(0,122,255,0.4);
        margin-top: 20px;
    }
    
    /* 4. 情报卡片与报告样式 */
    .news-box { 
        background-color: #1c1c1e; padding: 15px; border-radius: 10px; 
        border-left: 5px solid #00d1ff; margin-bottom: 15px;
    }
    .report-card { 
        background: #1c1c1e; padding: 25px; border-radius: 12px; 
        border: 1px solid #3a3a3c; margin-top: 15px; color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心量化算法引擎 ---
def compute_metrics(df):
    high_low = df['High'] - df['Low']
    high_pc = np.abs(df['High'] - df['Close'].shift())
    low_pc = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    return df

@st.cache_data(ttl=60)
def fetch_institutional_feed(ticker):
    try:
        # 强制获取分钟级采样数据，模拟量化实盘准确度
        df = yf.download(ticker, period="30d", interval="15m")
        if not df.empty:
            df = compute_metrics(df)
            return df, float(df['Close'].iloc[-1]), float((df['Close'].iloc[-1] - df['Open'].iloc[0])/df['Open'].iloc[0]*100)
    except: pass
    return None, 0.0, 0.0

@st.cache_data(ttl=300)
def fetch_open_crawl(ticker):
    # 模拟 Open Crawl：实时抓取全球财经情报 RSS
    feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
    return [{"title": e.title, "link": e.link} for e in feed.entries[:3]]

# --- 3. 侧边栏决策控制中心 ---
with st.sidebar:
    st.title("🏛️ 策略控制中枢")
    or_key = st.text_input("OpenRouter Key", type="password")
    
    st.divider()
    st.subheader("🧘 心理博弈日志")
    mood = st.select_slider("当前心理状态", options=["焦虑", "压力", "冷静", "自信", "亢奋"])
    # 情绪熔断机制：极端情绪自动降权
    risk_multiplier = 0.5 if mood in ["焦虑", "亢奋"] else 1.0
    if risk_multiplier < 1.0: 
        st.error("⚠️ 狮子座风控协议：情绪异常，风险额度已强制削减 50%。")

    st.divider()
    target = st.selectbox("监控标的", ["GC=F", "^NDX", "NVDA", "ETH-USD", "CL=F"])
    capital = 1000000 
    risk_limit = st.slider("单笔风险暴露 (%)", 0.5, 3.0, 1.5) * risk_multiplier

# --- 4. 主界面：$1,000,000 实时监控矩阵 ---
now = datetime.now()
st.title(f"📊 {target} 机构级量化终端")
st.caption(f"当前时间轴：{now.strftime('%Y-%m-%d %H:%M:%S')} (2026 实盘驱动)")

df, price, change = fetch_institutional_feed(target)
news = fetch_open_crawl(target)

if df is not None:
    # A. 顶层核心指标面板
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("实时价", f"${price:,.2f}")
    c2.metric("当日波动", f"{change:+.2f}%")
    atr_val = df['ATR'].iloc[-1]
    c3.metric("ATR 波动率 (1m)", f"{atr_val:.2f}")
    
    # 基于 $1M 的 ATR 仓位计算逻辑
    risk_dollar = capital * (risk_limit / 100)
    pos_size = risk_dollar / (atr_val * 2) if atr_val > 0 else 0
    c4.metric("建议头寸 (Units)", f"{pos_size:,.0f}", f"风控额: ${risk_dollar:,.0f}")

    # B. 分钟级动态技术图表
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20 趋势线', line=dict(color='#FF9500', width=1.5)))
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # C. Open Crawl 实时情报流
    st.divider()
    st.subheader("🌐 Open Crawl 实时情报流")
    if news:
        for item in news:
            st.markdown(f'<div class="news-box"><b>{item["title"]}</b><br><small><a href="{item["link"]}" target="_blank" style="color:#00d1ff;">[来源详情]</a></small></div>', unsafe_allow_html=True)
    else: 
        st.info("📡 正在全网扫描 2026 最新财经情报...")

    # D. 双模型共识分析 (Cross-Model PK)
    st.divider()
    if st.button("🚀 启动全球策略共识分析 (Global Consensus Analytics)"):
        if not or_key: 
            st.error("请填入 OpenRouter API Key")
        else:
            with st.spinner("Claude 3.5 与 Gemini 2.0 正在进行逻辑交叉对比..."):
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_key)
                prompt = f"今天是 {now.strftime('%Y-%m-%d')}。你是麦肯锡量化顾问。针对 {target}，现价 {price}。请参考实时新闻 {news[0]['title'] if news else ''} 给出 150 字内的入场、止损(SL)及 3 级止盈(TP)策略。必须基于 2026 年宏观背景。"
                
                # 并发生成两个模型的研报
                r_c = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                r_g = client.chat.completions.create(model="google/gemini-2.0-flash-001", messages=[{"role": "user", "content": prompt}])
                
                col_left, col_right = st.columns(2)
                with col_left:
                    st.markdown("### 🏛️ Claude 3.5 (稳健派)")
                    st.markdown(f'<div class="report-card">{r_c.choices[0].message.content}</div>', unsafe_allow_html=True)
                with col_right:
                    st.markdown("### ⚡ Gemini 2.0 (进取派)")
                    st.markdown(f'<div class="report-card">{r_g.choices[0].message.content}</div>', unsafe_allow_html=True)

st.caption("麦肯锡顾问模式 | 狮子座 1986-08-21 逻辑加持 | 资产管理规模：$1,000,000")
