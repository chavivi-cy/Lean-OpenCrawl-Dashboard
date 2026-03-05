import streamlit as st
from openai import OpenAI
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# --- 页面高级配置 ---
st.set_page_config(page_title="LEAN Pro | 金融决策终端", layout="wide")

# --- 核心逻辑：实时行情抓取 ---
@st.cache_data(ttl=60) # 缓存 60 秒，避免频繁请求被封 IP
def get_market_data(ticker):
    try:
        data = yf.download(ticker, period="5d", interval="15m")
        if not data.empty:
            current_price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2]
            change = (current_price - prev_close) / prev_close * 100
            return data, current_price, change
    except:
        return None, 0, 0

# --- 资产代码映射 ---
TICKERS = {
    "纳指100 (NAS100)": "^IXIC",
    "黄金 (Gold)": "GC=F",
    "原油 (WTI)": "CL=F",
    "ETH/USDT": "ETH-USD",
    "恒生指数 (HSI)": "^HSI",
    "NVDA (英伟达)": "NVDA",
    "腾讯控股 (0700)": "0700.HK"
}

# --- 侧边栏 ---
with st.sidebar:
    st.title("🛡️ 终端授权")
    or_api_key = st.text_input("OpenRouter API Key", type="password")
    asset_label = st.selectbox("选择交易标的", list(TICKERS.keys()))
    model_choice = st.selectbox("AI 首席分析师", ["anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-001"])
    st.divider()
    st.info(f"决策者：苏先生 (Leo)\n账户基数：$2500 (Prop Firm)") #

# --- 获取实时行情 ---
df, price, change = get_market_data(TICKERS[asset_label])

# --- 主界面 ---
st.title(f"📈 {asset_label} 实时决策矩阵")

# 1. 动态行情面板
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("实时现价", f"${price:,.2f}", f"{change:+.2f}%")
with c2: st.metric("24h 波动率", "1.8%", "低波动")
with c3: st.metric("LEAN 趋势得分", "82/100", "+5")
with c4: st.metric("风控限额 ($2500)", "$37.5", "1.5% Risk") #

# 2. 交互式 K 线 (Plotly)
if df is not None:
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# 3. AI 深度研报逻辑
st.divider()
if st.button("🚀 生成首席投研研报", use_container_width=True):
    if not or_api_key:
        st.error("请输入 API Key")
    else:
        with st.spinner("正在整合实时行情数据与全球舆情..."):
            client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_api_key)
            prompt = f"""
            你是麦肯锡资深策略顾问。针对 {asset_label}，当前实时价格为 {price}，今日涨跌幅 {change:.2f}%。
            请结合当前量化指标，为苏先生（1986年生，资深交易员）提供一份 200 字以内的专业研报：
            1. 技术结论：基于当前 K 线走势的短期预测。
            2. 关键点位：给出支撑位与阻力位。
            3. 执行建议：针对 $2500 挑战账户的具体仓位与风控建议。
            要求：逻辑硬核，拒绝废话。
            """
            #
            resp = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": prompt}])
            st.markdown("### 📋 首席顾问报告")
            st.info(resp.choices[0].message.content)

st.caption("数据源：Yahoo Finance | 系统：LEAN + OpenRouter")
