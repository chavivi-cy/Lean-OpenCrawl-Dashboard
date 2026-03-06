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

# --- 1. 机构级页面配置 (2026 极致视觉) ---
st.set_page_config(page_title="LEAN Quantum Pro | $1M Terminal", layout="wide")

# CSS 锁死：侧边栏深色白字，按钮苹果蓝
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #0e1117; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #161b22 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] input { background-color: #2c2c2e !important; color: white !important; }
    div.stButton > button:first-child {
        background-color: #007AFF !important; color: white !important;
        border: none; padding: 18px 0; font-weight: 800; width: 100%; 
        border-radius: 12px; font-size: 20px; box-shadow: 0 4px 20px rgba(0,122,255,0.4);
    }
    .summary-dashboard { background: linear-gradient(135deg, #1c1c1e 0%, #2c2c2e 100%); padding: 20px; border-radius: 12px; border: 1px solid #00d1ff; margin-bottom: 20px; }
    .report-card { background: #1c1c1e; padding: 25px; border-radius: 12px; border: 1px solid #3a3a3c; margin-top: 15px; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心量化引擎 ---
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
        df = yf.download(ticker, period="30d", interval="15m")
        if not df.empty:
            return compute_metrics(df), float(df['Close'].iloc[-1]), float((df['Close'].iloc[-1] - df['Open'].iloc[0])/df['Open'].iloc[0]*100)
    except: pass
    return None, 0.0, 0.0

@st.cache_data(ttl=300)
def fetch_open_crawl(ticker):
    feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
    return [{"title": e.title, "link": e.link} for e in feed.entries[:5]]

# --- 3. 侧边栏：$1M 决策控制 ---
with st.sidebar:
    st.title("🏛️ 策略控制中枢")
    or_key = st.text_input("OpenRouter Key", type="password")
    st.divider()
    mood = st.select_slider("当前心理状态", options=["焦虑", "压力", "冷静", "自信", "亢奋"])
    risk_multiplier = 0.5 if mood in ["焦虑", "亢奋"] else 1.0
    st.divider()
    target = st.selectbox("监控标的", ["GC=F", "^NDX", "NVDA", "ETH-USD", "CL=F"])
    capital = 1000000 
    risk_limit = st.slider("单笔风险暴露 (%)", 0.5, 3.0, 1.5) * risk_multiplier

# --- 4. 主界面布局 ---
now = datetime.now()
st.title(f"📊 {target} 机构级量化终端")
st.caption(f"2026-03-06 实盘引擎 | 决策者：苏先生 (Leo)")

df, price, change = fetch_institutional_feed(target)
news = fetch_open_crawl(target)

if df is not None:
    # A. 核心指标看板
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("实时现价", f"${price:,.2f}")
    c2.metric("当日波动", f"{change:+.2f}%")
    atr_val = df['ATR'].iloc[-1]
    c3.metric("ATR 波动率 (1m)", f"{atr_val:.2f}")
    risk_dollar = capital * (risk_limit / 100)
    pos_size = risk_dollar / (atr_val * 2) if atr_val > 0 else 0
    c4.metric("建议头寸", f"{pos_size:,.0f} Units", f"风控额: ${risk_dollar:,.0f}")

    # B. 动态 K 线图
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='趋势 MA20', line=dict(color='#FF9500')))
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # C. Open Crawl 情报摘要
    st.divider()
    if news:
        st.markdown('<div class="summary-dashboard">📝 <b>2026 市场核心观点归纳：</b><br>' + 
                    "<br>".join([f"🔹 {n['title']}" for n in news[:3]]) + '</div>', unsafe_allow_html=True)

    # D. 双模型共识 PK (异常加固版)
    st.divider()
    if st.button("🚀 启动全球策略共识分析 (Gemini 3.0 x Claude 3.5)"):
        if not or_key: st.error("请填入 OpenRouter Key")
        else:
            with st.spinner("正在进行多模型交叉验证..."):
                # 统一客户端配置，增加 OpenRouter 所需请求头
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1", 
                    api_key=or_key,
                    default_headers={
                        "HTTP-Referer": "https://lean-quantum-pro.streamlit.app",
                        "X-Title": "LEAN Quantum Terminal"
                    }
                )
                prompt = f"今天是 {now.strftime('%Y-%m-%d')}。你是麦肯锡顾问。针对 {target}，现价 {price}。请给出入场、止损(SL)及 3 级止盈(TP)建议。必须基于 2026 年环境。"
                
                col_left, col_right = st.columns(2)
                
                # --- Claude 3.5 Sonnet 调用 ---
                with col_left:
                    st.markdown("### 🏛️ Claude 3.5 (稳健派)")
                    try:
                        r_c = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                        st.markdown(f'<div class="report-card">{r_c.choices[0].message.content}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Claude 调用失败: {str(e)[:100]}...")

                # --- Gemini 3.0 Flash 调用 (修复 BadRequest) ---
                with col_right:
                    st.markdown("### ⚡ Gemini 3.0 (进取派)")
                    try:
                        # 尝试使用 OpenRouter 最稳健的 Gemini 3 标识符
                        r_g = client.chat.completions.create(model="google/gemini-3-flash", messages=[{"role": "user", "content": prompt}])
                        st.markdown(f'<div class="report-card">{r_g.choices[0].message.content}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        # 如果报错，尝试自动回退到 1.5 Pro 确保演示不中断
                        st.warning("Gemini 3.0 接口波动，正在尝试备选路径...")
                        try:
                            r_g_alt = client.chat.completions.create(model="google/gemini-pro-1.5", messages=[{"role": "user", "content": prompt}])
                            st.markdown(f'<div class="report-card">{r_g_alt.choices[0].message.content}</div>', unsafe_allow_html=True)
                        except:
                            st.error("AI 决策引擎暂时过载，请检查 OpenRouter 余额或 Key 有效性。")

st.caption("麦肯锡投研模式 | 狮子座 1986-08-21 风险逻辑 | 资产规模：$1,000,000")
