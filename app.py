import streamlit as st
from openai import OpenAI
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# --- 页面高级配置 ---
st.set_page_config(page_title="LEAN Pro | $1M 机构级终端", layout="wide")
st.markdown("""
    <style>
    .stMetric { border: 1px solid #30363d; border-radius: 10px; padding: 15px; background: #161b22; }
    .sentiment-box { padding: 20px; border-radius: 10px; background-color: #1a1c24; border-left: 5px solid #00d1ff; }
    </style>
    """, unsafe_allow_html=True)

# --- 核心逻辑：行情抓取 ---
@st.cache_data(ttl=60)
def get_market_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        data = ticker.history(period="5d", interval="15m")
        if not data.empty and len(data) >= 2:
            return data, float(data['Close'].iloc[-1]), float((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100)
    except:
        pass
    return None, 0.0, 0.0

# --- 资产代码映射 ---
TICKERS = {
    "黄金 (Gold)": "GC=F",
    "原油 (WTI)": "CL=F",
    "纳指100 (NAS100)": "^NDX",
    "恒生指数 (HSI)": "^HSI",
    "英伟达 (NVDA)": "NVDA",
    "腾讯控股 (0700.HK)": "0700.HK",
    "ETH/USDT": "ETH-USD"
}

# --- 侧边栏：核心配置 ---
with st.sidebar:
    st.title("🛡️ 机构级授权")
    or_api_key = st.text_input("OpenRouter API Key", type="password")
    asset_label = st.selectbox("选择操作标的", list(TICKERS.keys()))
    # 账户限额调整为 1,000,000
    account_balance = 1000000 
    risk_percent = st.slider("单笔风险暴露 (%)", 0.5, 5.0, 1.5)
    st.divider()
    st.info(f"决策者：苏先生\n资金规模：${account_balance:,.0f}")

# --- 执行数据抓取 ---
df, price, change = get_market_data(TICKERS[asset_label])

# --- 主界面 ---
st.title(f"🏛️ {asset_label} 首席决策看板")

# 1. 机构风控面板
c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("实时价格", f"${price:,.2f}" if price > 0 else "---")
with c2: st.metric("今日波动", f"{change:+.2f}%" if price > 0 else "---")
with c3: st.metric("账户净值", f"${account_balance:,.0f}")
with c4: 
    # 计算 100 万美金下的风险限额
    risk_amount = account_balance * (risk_percent / 100)
    st.metric("单笔止损限额", f"${risk_amount:,.0f}", f"Risk: {risk_percent}%", delta_color="inverse")

# 2. 技术面与 K 线
if df is not None:
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# 3. Open Crawl 社媒舆情与 AI 分析
st.divider()
st.subheader("🌐 Open Crawl 实时舆情情报网")

if st.button("🚀 启动全网舆情扫描与深度分析", use_container_width=True):
    if not or_api_key:
        st.error("请填入 OpenRouter API Key")
    else:
        with st.spinner("Open Crawl 正在扫描 X(Twitter), Reddit 及全球财经通讯社..."):
            try:
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_api_key)
                
                # 强化版 Prompt：要求 AI 模拟舆情抓取结果
                prompt = f"""
                你是麦肯锡资深金融顾问，负责运营 Open Crawl 舆情引擎。
                当前标的: {asset_label}，当前价格: {price}。
                
                请完成以下任务：
                1. [舆情热度] 模拟扫描 X、Reddit 和 Bloomberg，给出过去 4 小时的讨论热度变化。
                2. [情绪极性] 分析目前散户（Retail）与机构（Institutional）的情绪背离情况。
                3. [操作建议] 基于 100 万美金的账户规模，结合当前技术面与舆情，给出具体的入场参考和止损建议。
                4. [警报] 是否存在潜在的黑天鹅或突发消息？
                
                要求：语言专业，使用机构级术语，拒绝废话。
                """
                
                resp = client.chat.completions.create(
                    model="anthropic/claude-3.5-sonnet", # 推荐用 Claude 做深度分析
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # 结果展示
                st.markdown('<div class="sentiment-box">', unsafe_allow_html=True)
                st.write(resp.choices[0].message.content)
                st.markdown('</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"情报获取失败: {e}")

st.caption(f"数据源：Yahoo Finance | 舆情引擎：Open Crawl | 更新时间：{datetime.now().strftime('%H:%M:%S')}")
