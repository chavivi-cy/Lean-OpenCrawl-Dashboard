import streamlit as st
from openai import OpenAI
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import feedparser
import requests
from datetime import datetime

# --- 1. 机构级页面配置 (Apple 极致视觉 + 2026 逻辑) ---
st.set_page_config(page_title="LEAN Quantum Pro | $1M Terminal", layout="wide")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #0e1117; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #161b22 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] input { background-color: #2c2c2e !important; color: white !important; border: 1px solid #3a3a3c !important; }
    div.stButton > button:first-child {
        background-color: #007AFF !important; color: white !important;
        border: none; padding: 18px 0; font-weight: 800; width: 100%; 
        border-radius: 12px; font-size: 20px; box-shadow: 0 4px 20px rgba(0,122,255,0.4);
    }
    .summary-dashboard { background: linear-gradient(135deg, #1c1c1e 0%, #2c2c2e 100%); padding: 20px; border-radius: 12px; border: 1px solid #00d1ff; margin-bottom: 20px; }
    .news-box { background-color: #1c1c1e; padding: 12px; border-radius: 8px; border-left: 4px solid #3a3a3c; margin-bottom: 10px; color: #ffffff; }
    .report-card { background: #1c1c1e; padding: 25px; border-radius: 12px; border: 1px solid #3a3a3c; margin-top: 15px; color: #ffffff; line-height: 1.6; }
    /* 高亮置信度与时间标签 */
    .quant-badge { background-color: #00d1ff; color: #000; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; margin-right: 5px;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心量化算法与数据引擎 ---
def compute_metrics(df):
    high_low = df['High'] - df['Low']
    high_pc = np.abs(df['High'] - df['Close'].shift())
    low_pc = np.abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_pc, low_pc], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    return df

def push_whatsapp(phone, apikey, text):
    if phone and apikey:
        url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={text}&apikey={apikey}"
        try: requests.get(url, timeout=5)
        except: pass

@st.cache_data(ttl=60)
def fetch_twelvedata_feed(symbol, api_key):
    if not api_key: return None, 0.0, 0.0
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=15min&outputsize=100&apikey={api_key}"
    try:
        res = requests.get(url).json()
        if 'values' in res:
            df = pd.DataFrame(res['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            df = df.astype(float).iloc[::-1] # 正序排列
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
            df = compute_metrics(df)
            price = df['Close'].iloc[-1]
            change = (price - df['Open'].iloc[0]) / df['Open'].iloc[0] * 100
            return df, float(price), float(change)
    except: pass
    return None, 0.0, 0.0

@st.cache_data(ttl=300)
def fetch_open_crawl(yf_symbol):
    feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={yf_symbol}")
    return [{"title": e.title, "link": e.link} for e in feed.entries[:5]]

# --- 3. 侧边栏：$1M 决策控制中心 ---
with st.sidebar:
    st.title("🏛️ 策略控制中枢")
    or_key = st.text_input("OpenRouter Key (AI 引擎)", type="password")
    
    st.divider()
    st.subheader("🔌 机构数据流接入")
    td_key = st.text_input("Twelve Data API Key", type="password")
    
    st.divider()
    st.subheader("📱 移动预警绑定")
    wa_num = st.text_input("WhatsApp 号码", placeholder="86138...")
    wa_key = st.text_input("CallMeBot API Key", type="password")
    
    st.divider()
    st.subheader("🧘 心理博弈日志")
    mood = st.select_slider("当前心理状态", options=["焦虑", "压力", "冷静", "自信", "亢奋"])
    risk_multiplier = 0.5 if mood in ["焦虑", "亢奋"] else 1.0
    if risk_multiplier < 1.0: st.error("⚠️ 狮子座协议：风险减半保护已开启。")

    st.divider()
    ASSETS = {
        "黄金 (XAU/USD)": {"td": "XAU/USD", "yf": "GC=F"},
        "纳指100 (NDX)": {"td": "QQQ", "yf": "^NDX"},
        "原油 (WTI)": {"td": "USO", "yf": "CL=F"},
        "英伟达 (NVDA)": {"td": "NVDA", "yf": "NVDA"},
        "以太坊 (ETH/USD)": {"td": "ETH/USD", "yf": "ETH-USD"}
    }
    target_name = st.selectbox("核心监控标的", list(ASSETS.keys()))
    td_symbol = ASSETS[target_name]["td"]
    yf_symbol = ASSETS[target_name]["yf"]
    
    capital = 1000000 
    risk_limit = st.slider("单笔风险暴露 (%)", 0.5, 3.0, 1.5) * risk_multiplier

# --- 4. 主界面布局 ---
now = datetime.now()
st.title(f"📊 {target_name} 机构级量化终端")
st.caption(f"当前时间轴：{now.strftime('%Y-%m-%d %H:%M:%S')} (2026 实盘驱动 | 数据源: Twelve Data REST API)")

if not td_key:
    st.warning("⚠️ 终端处于待机状态：请在左侧边栏输入 Twelve Data API Key 以激活实盘数据流。")
else:
    df, price, change = fetch_twelvedata_feed(td_symbol, td_key)
    news = fetch_open_crawl(yf_symbol)

    if df is not None:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("实时现价", f"${price:,.2f}")
        c2.metric("当日波动", f"{change:+.2f}%")
        
        # 提取关键量化指标供 AI 使用
        atr_val = df['ATR'].iloc[-1] if not np.isnan(df['ATR'].iloc[-1]) else 0
        ma20_val = df['MA20'].iloc[-1] if not np.isnan(df['MA20'].iloc[-1]) else price
        
        c3.metric("ATR 波动率 (15m)", f"{atr_val:.2f}")
        risk_dollar = capital * (risk_limit / 100)
        pos_size = risk_dollar / (atr_val * 2) if atr_val > 0 else 0
        c4.metric("建议头寸", f"{pos_size:,.0f} Units", f"风控额: ${risk_dollar:,.0f}")

        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20 趋势', line=dict(color='#FF9500', width=1.5)))
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.subheader("🌐 Open Crawl 实时情报扫描系统")
        if news:
            st.markdown('<div class="summary-dashboard">📝 <b>2026 市场核心观点归纳：</b><br>' + 
                        "<br>".join([f"🔹 {n['title']}" for n in news[:3]]) + '</div>', unsafe_allow_html=True)
            with st.expander("查看原文情报源列表"):
                for item in news:
                    st.markdown(f'<div class="news-box"><b>{item["title"]}</b><br><small><a href="{item["link"]}" target="_blank" style="color:#00d1ff;">[阅读原文]</a></small></div>', unsafe_allow_html=True)
        else: st.info("📡 正在全网扫描 2026 最新财经情报...")

        st.divider()
        if st.button("🚀 启动全球策略共识分析 (Cross-Model PK)"):
            if not or_key: st.error("请填入 OpenRouter Key")
            else:
                with st.spinner("正在提取 ATR 与 MA20 测算置信度与持仓时间..."):
                    client = OpenAI(
                        base_url="https://openrouter.ai/api/v1", 
                        api_key=or_key,
                        default_headers={"HTTP-Referer": "https://lean-quantum-pro.streamlit.app", "X-Title": "LEAN Quantum Terminal"}
                    )
                    
                    # 核心指令重构：强迫 AI 具备量化思维
                    news_str = ' | '.join([n['title'] for n in news[:2]]) if news else '暂无重磅新闻'
                    prompt = f"""
                    今天是 {now.strftime('%Y-%m-%d')}。你是麦肯锡量化策略顾问。针对 {td_symbol}，现价 {price:.2f}。
                    [系统数据注入] 当前15分钟级别 MA20为 {ma20_val:.2f}，ATR波动率为 {atr_val:.2f}。实时新闻情绪：{news_str}。
                    
                    请严格按照以下结构输出 150 字内的实战简报（基于 2026 环境）：
                    
                    **[量化风控评估]**
                    - 🎯 **策略置信度**：结合技术面(价格与MA20关系)与基本面，给出一个具体胜率预估(如 65%, 85%)。
                    - ⏳ **预期持仓时段**：基于当前 ATR 算出的到达 TP1 所需的大致时间(如 4-8小时, 1-2天)。
                    
                    **[执行矩阵]**
                    - 入场建议：...
                    - 止损(SL)：...
                    - 止盈(TP1/TP2/TP3)：...
                    """
                    
                    col_left, col_right = st.columns(2)
                    
                    with col_left:
                        st.markdown("### 🏛️ Claude 3.5 (稳健量化)")
                        try:
                            r_c = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                            st.markdown(f'<div class="report-card">{r_c.choices[0].message.content}</div>', unsafe_allow_html=True)
                        except Exception as e: st.error(f"Claude 响应中断: {e}")

                    with col_right:
                        st.markdown("### ⚡ Gemini (敏捷量化)")
                        try:
                            r_g = client.chat.completions.create(model="google/gemini-2.0-flash-001", messages=[{"role": "user", "content": prompt}])
                            st.markdown(f'<div class="report-card">{r_g.choices[0].message.content}</div>', unsafe_allow_html=True)
                        except Exception as e:
                            try:
                                r_g_alt = client.chat.completions.create(model="google/gemini-1.5-pro", messages=[{"role": "user", "content": prompt}])
                                st.markdown(f'<div class="report-card">{r_g_alt.choices[0].message.content}</div>', unsafe_allow_html=True)
                            except Exception as inner_e: 
                                st.error(f"OpenRouter 拒绝请求。详细错误码: {str(inner_e)}")
                    
                    if wa_num and wa_key:
                        push_whatsapp(wa_num, wa_key, f"LEAN 预警: {td_symbol} 触发共识分析。建议头寸: {pos_size:,.0f}。请回终端查看策略置信度与持仓时段。")
                        st.toast("✅ 预警已同步至 WhatsApp")
    else:
        st.error("❌ 数据提取失败。请确认 Twelve Data API Key 是否正确，或网络是否通畅。")
