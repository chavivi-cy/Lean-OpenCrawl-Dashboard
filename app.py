import streamlit as st
from openai import OpenAI
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# --- 页面高级配置 ---
st.set_page_config(page_title="LEAN Pro | 数字化投研终端", layout="wide")

# --- 核心逻辑：稳健的实时行情抓取 ---
@st.cache_data(ttl=60)
def get_market_data(ticker_symbol):
    try:
        # 使用 Ticker 对象的 history 方法，稳定性更高
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="5d", interval="15m")
        if not data.empty and len(data) >= 2:
            current_price = data['Close'].iloc[-1]
            prev_close = data['Close'].iloc[-2]
            change = (current_price - prev_close) / prev_close * 100
            return data, float(current_price), float(change)
    except Exception as e:
        st.sidebar.error(f"数据抓取失败 ({ticker_symbol}): {e}")
    # 如果抓取失败，返回默认值，防止解包报错
    return None, 0.0, 0.0

# --- 全资产代码映射 (Yahoo Finance 格式) ---
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
    # 注意：请填入你新申请的那个正确的 sk-or-v1-... 钥匙
    or_api_key = st.text_input("OpenRouter API Key", type="password")
    asset_label = st.selectbox("选择交易标的", list(TICKERS.keys()))
    model_choice = st.selectbox("AI 首席分析师", ["anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-001"])
    st.divider()
    st.info("决策者：苏先生\n账户基数：$2500 (Prop Firm)")

# --- 逻辑执行：安全获取行情 ---
df, price, change = get_market_data(TICKERS[asset_label])

# --- 主界面布局 ---
st.title(f"📈 {asset_label} 深度决策矩阵")

# 1. 动态行情面板
c1, c2, c3, c4 = st.columns(4)
with c1: 
    st.metric("实时现价", f"${price:,.2f}" if price > 0 else "加载中...")
with c2: 
    st.metric("今日涨跌", f"{change:+.2f}%" if price > 0 else "--")
with c3: 
    st.metric("LEAN 趋势信号", "多头排列" if change > 0 else "高位震荡")
with m4: 
    # 针对你 $2500 挑战账户的实时风险提醒
    st.metric("单笔风控限额 (1.5%)", "$37.5")

# 2. 技术面可视化
if df is not None:
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Market'
    )])
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ 当前资产行情加载失败，请检查网络或代理是否通畅。")

# 3. AI 深度策略生成
st.divider()
if st.button("🚀 生成首席投研研报", use_container_width=True):
    if not or_api_key:
        st.error("请先填入 API Key")
    elif price == 0:
        st.error("行情数据不完整，无法进行 AI 分析")
    else:
        with st.spinner("正在整合实时行情进行决策建模..."):
            try:
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_api_key)
                prompt = f"""
                你是麦肯锡资深策略顾问。针对 {asset_label}，当前价格 {price}，涨跌幅 {change:.2f}%。
                请结合技术面走势，为苏先生（资深交易员）提供一份 200 字以内的专业研报：
                1. 现状评估：当前价格在均线系统中的位置。
                2. 操作矩阵：明确的入场参考位、止损位与止盈目标。
                3. 风控建议：针对 $2500 账户在 {asset_label} 上的特有仓位建议。
                语言风格：冷静、干练、结果导向。
                """
                resp = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": prompt}])
                st.markdown("### 📋 首席顾问报告")
                st.info(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"AI 调用异常: {e}")

st.caption("数据源：Yahoo Finance | 系统：LEAN + OpenRouter | 仅供演示")
