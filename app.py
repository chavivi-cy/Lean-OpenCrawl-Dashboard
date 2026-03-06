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

# 终极 CSS 修复：侧边栏深色背景+纯白文字，按钮高亮，报告容器优化
st.markdown("""
    <style>
    /* 全局背景 */
    [data-testid="stAppViewContainer"] { background: #0e1117; color: #ffffff !important; }
    
    /* 侧边栏极致修复：深色背景 (#161b22) + 纯白文字 */
    [data-testid="stSidebar"] { background-color: #161b22 !important; }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] input { background-color: #2c2c2e !important; color: white !important; border: 1px solid #3a3a3c !important; }

    /* 蓝色高亮按钮修复 */
    div.stButton > button:first-child {
        background-color: #007AFF !important; color: white !important;
        border: none; padding: 18px 0; font-weight: 800; width: 100%; 
        border-radius: 12px; font-size: 20px; box-shadow: 0 4px 20px rgba(0,122,255,0.4);
    }
    
    /* 情报看板样式 */
    .summary-dashboard { background: linear-gradient(135deg, #1c1c1e 0%, #2c2c2e 100%); padding: 20px; border-radius: 12px; border: 1px solid #00d1ff; margin-bottom: 20px; }
    .news-box { background-color: #1c1c1e; padding: 12px; border-radius: 8px; border-left: 4px solid #3a3a3c; margin-bottom: 10px; color: #ffffff; }
    .report-card { background: #1c1c1e; padding: 25px; border-radius: 12px; border: 1px solid #3a3a3c; margin-top: 15px; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 核心量化算法与预警引擎 ---
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
def fetch_institutional_feed(ticker):
    try:
        df = yf.download(ticker, period="30d", interval="15m")
        if not df.empty:
            df = compute_metrics(df)
            return df, float(df['Close'].iloc[-1]), float((df['Close'].iloc[-1] - df['Open'].iloc[0])/df['Open'].iloc[0]*100)
    except: pass
    return None, 0.0, 0.0

@st.cache_data(ttl=300)
def fetch_open_crawl(ticker):
    feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
    return [{"title": e.title, "link": e.link} for e in feed.entries[:5]]

# --- 3. 侧边栏：$1M 决策控制中心 ---
with st.sidebar:
    st.title("🏛️ 策略控制中枢")
    or_key = st.text_input("OpenRouter Key", type="password")
    
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
    target = st.selectbox("监控标的", ["GC=F", "^NDX", "NVDA", "ETH-USD", "CL=F"])
    capital = 1000000 
    risk_limit = st.slider("单笔风险暴露 (%)", 0.5, 3.0, 1.5) * risk_multiplier

# --- 4. 主界面布局 ---
now = datetime.now()
st.title(f"📊 {target} 机构级量化终端")
st.caption(f"当前时间轴：{now.strftime('%Y-%m-%d %H:%M:%S')} (2026 量化实盘)")

df, price, change = fetch_institutional_feed(target)
news = fetch_open_crawl(target)

if df is not None:
    # A. 核心指标面板
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("实时现价", f"${price:,.2f}")
    c2.metric("当日波动", f"{change:+.2f}%")
    atr_val = df['ATR'].iloc[-1]
    c3.metric("ATR 波动率 (1m)", f"{atr_val:.2f}")
    
    risk_dollar = capital * (risk_limit / 100)
    pos_size = risk_dollar / (atr_val * 2) if atr_val > 0 else 0
    c4.metric("建议头寸", f"{pos_size:,.0f} Units", f"风控额: ${risk_dollar:,.0f}")

    # B. 分钟级动态技术图表
    fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20 趋势', line=dict(color='#FF9500', width=1.5)))
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

    # C. Open Crawl 实时情报网 (Summary Dashboard + Original Links)
    st.divider()
    st.subheader("🌐 Open Crawl 实时情报扫描系统")
    if news:
        # 1. 摘要看板
        st.markdown('<div class="summary-dashboard">📝 <b>2026 市场核心观点归纳：</b><br>' + 
                    "<br>".join([f"🔹 {n['title']}" for n in news[:3]]) + '</div>', unsafe_allow_html=True)
        # 2. 原文链接目录
        with st.expander("查看原文情报源列表"):
            for item in news:
                st.markdown(f'<div class="news-box"><b>{item["title"]}</b><br><small><a href="{item["link"]}" target="_blank" style="color:#00d1ff;">[阅读原文]</a></small></div>', unsafe_allow_html=True)
    else: st.info("📡 正在全网扫描 2026 最新财经情报...")

    # D. 双模型共识分析 (精准修复版)
    st.divider()
    if st.button("🚀 启动全球策略共识分析 (Cross-Model PK)"):
        if not or_key: st.error("请填入 OpenRouter Key")
        else:
            with st.spinner("正在进行深度交叉验证..."):
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1", 
                    api_key=or_key,
                    default_headers={
                        "HTTP-Referer": "https://lean-quantum-pro.streamlit.app",
                        "X-Title": "LEAN Quantum Terminal"
                    }
                )
                prompt = f"今天是 {now.strftime('%Y-%m-%d')}。你是麦肯锡顾问。针对 {target}现价 {price}。请结合实时情报简短给出入场、止损(SL)及 3 级止盈(TP)建议。基于 2026 环境。"
                
                col_left, col_right = st.columns(2)
                
                # Claude 3.5 调用
                with col_left:
                    st.markdown("### 🏛️ Claude 3.5 (稳健派)")
                    try:
                        r_c = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                        st.markdown(f'<div class="report-card">{r_c.choices[0].message.content}</div>', unsafe_allow_html=True)
                    except Exception as e: st.error(f"Claude 响应中断: {e}")

                # 修复核心：使用 OpenRouter 确切支持的 Gemini 标识符
                with col_right:
                    st.markdown("### ⚡ Gemini 进取派 (最新量化模型)")
                    try:
                        # 换用绝对稳定的 Gemini 2.0 Flash 最新接口
                        r_g = client.chat.completions.create(model="google/gemini-2.0-flash-001", messages=[{"role": "user", "content": prompt}])
                        st.markdown(f'<div class="report-card">{r_g.choices[0].message.content}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.warning("首选接口波动，正在降级至备用通道...")
                        try:
                            # 备用方案：使用规范的 1.5-pro 命名
                            r_g_alt = client.chat.completions.create(model="google/gemini-1.5-pro", messages=[{"role": "user", "content": prompt}])
                            st.markdown(f'<div class="report-card">{r_g_alt.choices[0].message.content}</div>', unsafe_allow_html=True)
                        except Exception as inner_e: 
                            # 如果全挂了，直接把 OpenRouter 的报错打印出来，拒绝盲猜
                            st.error(f"OpenRouter 拒绝了请求。详细错误码: {str(inner_e)}")
                
                # WhatsApp 推送
                if wa_num and wa_key:
                    push_whatsapp(wa_num, wa_key, f"LEAN 预警: {target} 触发共识分析。建议头寸: {pos_size:,.0f}。")
                    st.toast("✅ 预警已同步至 WhatsApp")

st.caption("麦肯锡顾问模式 | 狮子座 1986-08-21 风险逻辑 | 资产规模：$1,000,000")
