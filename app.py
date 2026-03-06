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
    .report-card { background: #1c1c1e; padding: 25px; border-radius: 12px; border: 1px solid #3a3a3c; margin-top: 15px; color: #ffffff; }
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

# 核心升级：Twelve Data 机构级 REST API 接入
@st.cache_data(ttl=60)
def fetch_twelvedata_feed(symbol, api_key):
    if not api_key:
        return None, 0.0, 0.0
    # 获取 15分钟 级别的最新 100 根 K 线
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=15min&outputsize=100&apikey={api_key}"
    try:
        res = requests.get(url).json()
        if 'values' in res:
            df = pd.DataFrame(res['values'])
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            df = df.astype(float)
            
            # Twelve Data 默认是倒序（最新在最上面），需要翻转回时间正序以计算技术指标
            df = df.iloc[::-1]
            
            # 格式化列名以适配绘图逻辑
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
            df = compute_metrics(df)
            
            price = df['Close'].iloc[-1]
            change = (price - df['Open'].iloc[0]) / df['Open'].iloc[0] * 100
            return df, float(price), float(change)
    except Exception as e:
        print(f"Data Fetch Error: {e}")
    return None, 0.0, 0.0

@st.cache_data(ttl=300)
def fetch_open_crawl(yf_symbol):
    feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={yf_symbol}")
    return [{"title": e.title, "link": e.link} for e in feed.entries[:5]]

# --- 3. 侧边栏：$1M 决策控制中心 ---
with st.sidebar:
    st.title("🏛️ 策略控制中枢")
    or_key = st.text_input("OpenRouter Key (AI 引擎)", type="password")
    
    # 新增：Twelve Data 密钥输入口
    st.divider()
    st.subheader("🔌 机构数据流接入")
    td_key = st.text_input("Twelve Data API Key", type="password", placeholder="输入刚才获取的密钥")
    
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
    
    # 架构升级：底层资产映射表 (Prop Firm 标准命名)
    ASSETS = {
        "黄金 (XAU/USD)": {"td": "XAU/USD", "yf": "GC=F"},
        "纳指100 (NDX)": {"td": "NDX", "yf": "^NDX"},
        "原油 (WTI)": {"td": "WTI/USD", "yf": "CL=F"},
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
    # 使用新接口拉取数据
    df, price, change = fetch_twelvedata_feed(td_symbol, td_key)
    news = fetch_open_crawl(yf_symbol)

    if df is not None:
        # A. 核心指标面板
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("实时现价", f"${price:,.2f}")
        c2.metric("当日波动", f"{change:+.2f}%")
        atr_val = df['ATR'].iloc[-1] if not np.isnan(df['ATR'].iloc[-1]) else 0
        c3.metric("ATR 波动率 (15m)", f"{atr_val:.2f}")
        
        risk_dollar = capital * (risk_limit / 100)
        pos_size = risk_dollar / (atr_val * 2) if atr_val > 0 else 0
        c4.metric("建议头寸", f"{pos_size:,.0f} Units", f"风控额: ${risk_dollar:,.0f}")

        # B. 动态技术图表 (基于极速数据)
        fig = go.Figure(data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'])])
        fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], name='MA20 趋势', line=dict(color='#FF9500', width=1.5)))
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=0, r=0, t=0, b=0), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        # C. Open Crawl 实时情报网
        st.divider()
        st.subheader("🌐 Open Crawl 实时情报扫描系统")
        if news:
            st.markdown('<div class="summary-dashboard">📝 <b>2026 市场核心观点归纳：</b><br>' + 
                        "<br>".join([f"🔹 {n['title']}" for n in news[:3]]) + '</div>', unsafe_allow_html=True)
            with st.expander("查看原文情报源列表"):
                for item in news:
                    st.markdown(f'<div class="news-box"><b>{item["title"]}</b><br><small><a href="{item["link"]}" target="_blank" style="color:#00d1ff;">[阅读原文]</a></small></div>', unsafe_allow_html=True)
        else: st.info("📡 正在全网扫描 2026 最新财经情报...")

        # D. 双模型共识分析
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
                    prompt = f"今天是 {now.strftime('%Y-%m-%d')}。你是麦肯锡顾问。针对 {td_symbol}现价 {price}。请结合实时情报简短给出入场、止损(SL)及 3 级止盈(TP)建议。基于 2026 环境。"
                    
                    col_left, col_right = st.columns(2)
                    
                    # Claude 3.5 调用
                    with col_left:
                        st.markdown("### 🏛️ Claude 3.5 (稳健派)")
                        try:
                            r_c = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                            st.markdown(f'<div class="report-card">{r_c.choices[0].message.content}</div>', unsafe_allow_html=True)
                        except Exception as e: st.error(f"Claude 响应中断: {e}")

                    # Gemini 2.0 Flash 调用
                    with col_right:
                        st.markdown("### ⚡ Gemini 进取派 (最新模型)")
                        try:
                            r_g = client.chat.completions.create(model="google/gemini-2.0-flash-001", messages=[{"role": "user", "content": prompt}])
                            st.markdown(f'<div class="report-card">{r_g.choices[0].message.content}</div>', unsafe_allow_html=True)
                        except Exception as e:
                            st.warning("首选接口波动，正在降级至备用通道...")
                            try:
                                r_g_alt = client.chat.completions.create(model="google/gemini-1.5-pro", messages=[{"role": "user", "content": prompt}])
                                st.markdown(f'<div class="report-card">{r_g_alt.choices[0].message.content}</div>', unsafe_allow_html=True)
                            except Exception as inner_e: 
                                st.error(f"OpenRouter 拒绝请求。详细错误码: {str(inner_e)}")
                    
                    # WhatsApp 推送
                    if wa_num and wa_key:
                        push_whatsapp(wa_num, wa_key, f"LEAN 预警: {td_symbol} 触发共识分析。建议头寸: {pos_size:,.0f}。")
                        st.toast("✅ 预警已同步至 WhatsApp")
    else:
        st.error("❌ 数据提取失败。请确认 Twelve Data API Key 是否正确，或稍后重试。")
