import streamlit as st
from openai import OpenAI
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# --- 页面高级配置 ---
st.set_page_config(page_title="LEAN Pro | 金融决策终端", layout="wide")

# --- 核心逻辑：稳健的实时行情抓取 ---
@st.cache_data(ttl=60)
def get_market_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        # 获取最近5天的数据，间隔15分钟
        data = ticker.history(period="5d", interval="15m")
        if not data.empty and len(data) >= 2:
            current_price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2]
            change = (current_price - prev_close) / prev_close * 100
            return data, float(current_price), float(change)
    except Exception as e:
        st.sidebar.error(f"数据抓取失败 ({ticker_symbol}): {e}")
    return None, 0.0, 0.0

# --- 全资产代码映射 (Yahoo Finance 标准格式) ---
TICKERS = {
    "黄金 (Gold)": "GC=F",
    "原油 (WTI)": "CL=F",
    "纳指100 (NAS100)": "^NDX",
    "标普500 (SPX)": "^GSPC",
    "恒生指数 (HSI)": "^HSI",
    "英伟达 (NVDA)": "NVDA",
    "特斯拉 (TSLA)": "TSLA",
    "腾讯控股 (0700.HK)": "0700.HK",
    "阿里巴巴 (9988.HK)": "9988.HK",
    "ETH/USDT": "ETH-USD"
}

# --- 侧边栏：核心配置 ---
with st.sidebar:
    st.title("🛡️ 终端授权")
    # 填入你新复制的那串 sk-or-v1-... 钥匙
    or_api_key = st.text_input("OpenRouter API Key", type="password")
    asset_label = st.selectbox("选择分析标的", list(TICKERS.keys()))
    model_choice = st.selectbox("AI 首席分析师", ["anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-001"])
    st.divider()
    st.info("决策者：苏先生\n账户基数：$2500 (Prop Firm)")

# --- 执行数据抓取 ---
df, price, change = get_market_data(TICKERS[asset_label])

# --- 主界面布局 ---
st.title(f"📊 {asset_label} 深度决策矩阵")

# 1. 动态行情面板 (修复了 c4 变量名报错)
c1, c2, c3, c4 = st.columns(4)
with c1: 
    st.metric("实时现价", f"${price:,.2f}" if price > 0 else "加载中...")
with c2: 
    st.metric("今日涨跌", f"{change:+.2f}%" if price > 0 else "--")
with c3: 
    st.metric("LEAN 趋势信号", "多头排列" if change > 0 else "震荡修正")
with c4: 
    # 针对你 $2500 挑战账户的 1.5% 风险限额提醒
    st.metric("单笔风控上限", "$37.5")

# 2. 技术面可视化
if df is not None:
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Market'
    )])
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ 正在尝试连接行情源，请确保代理通畅...")

# 3. AI 深度策略生成
st.divider()
if st.button("🚀 启动全球共识引擎 (McKinsey Analysis Mode)", use_container_width=True):
    if not or_api_key:
        st.error("请在左侧填入 OpenRouter API Key")
    elif price == 0:
        st.error("无法获取行情，请检查网络后再试")
    else:
        with st.spinner(f"正在调动 {model_choice} 进行深度建模..."):
            try:
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_api_key)
                prompt = f"""
                你是麦肯锡资深策略顾问。针对 {asset_label}，当前实时价格 {price}，今日涨跌 {change:.2f}%。
                请结合 1986 年生 Leo（狮子座资深交易员）的职业风格，提供 200 字以内的研报：
                1. 现状评估：目前该资产在多周期均线系统中的位置。
                2. 交易矩阵：给出明确的入场位参考、止损(SL)以及三级止盈(TP)目标。
                3. 顾问提示：基于 $2500 挑战账户的杠杆管理建议。
                语言：极其专业、冷静、去散户化。
                """
                resp = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": prompt}])
                st.markdown("### 📋 首席顾问决策报告")
                st.info(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"AI 分析中断：{e}")

st.caption("数据源：Yahoo Finance | 系统：LEAN + OpenRouter | 仅供演示")
