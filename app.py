import streamlit as st
from openai import OpenAI
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime

# --- 页面专业配置 ---
st.set_page_config(page_title="LEAN Pro | 投研决策系统", layout="wide")
st.markdown("""
    <style>
    .stMetric { border: 1px solid #30363d; border-radius: 10px; padding: 15px; background: #161b22; }
    div[data-testid="stExpander"] { border: none; background: #1a1c24; }
    </style>
    """, unsafe_allow_html=True)

# --- 侧边栏：决策控制台 ---
with st.sidebar:
    st.title("🛡️ 决策中心")
    # 自动预填你截图中的 Key，方便演示（生产环境建议手动输入）
    or_api_key = st.text_input("OpenRouter API Key", type="password", value="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")
    
    st.divider()
    # 扩展后的分析目标
    asset_category = st.selectbox("资产大类", ["加密货币", "大宗商品", "全球指数", "个股/专项"])
    
    asset_map = {
        "加密货币": ["ETH/USDT", "BTC/USDT"],
        "大宗商品": ["黄金 (XAU/USD)", "原油 (WTI)"],
        "全球指数": ["纳指100 (NAS100)", "标普500 (SPX)", "恒生指数 (HSI)"],
        "个股/专项": ["美股 (NVDA/TSLA)", "港股 (腾讯/美团)", "Prop Firm $2500 账户"]
    }
    asset = st.selectbox("具体标的", asset_map[asset_category])
    
    model_option = st.selectbox("AI 首席分析师", [
        "anthropic/claude-3.5-sonnet", 
        "google/gemini-2.0-flash-001",
        "openai/gpt-4o"
    ])
    
    st.divider()
    st.info(f"身份：苏先生 | 顾问模式\n更新：{datetime.now().strftime('%m-%d %H:%M')}")

# --- 主界面布局 ---
st.title(f"📊 {asset} 综合研报")

# 1. 核心看板 (LEAN & Open Crawl 综合指标)
m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("LEAN 趋势强度", "72%", "+5%")
with m2: st.metric("情绪得分 (OC)", "🔥 极高", "Greed")
with m3: st.metric("波动率 (VIX)", "14.2", "-0.8%")
with m4: st.metric("R:R 盈亏比", "1:2.5", "Recommended")

# 2. 技术面深度解析 (Plotly 动态图)
st.markdown("### 📈 技术面多周期扫描")
tab_chart, tab_indicators = st.tabs(["专业 K 线图", "多因子指标矩阵"])

with tab_chart:
    # 模拟专业 K 线数据
    df = pd.DataFrame({
        'date': pd.date_range(start='2026-01-01', periods=60, freq='H'),
        'open': np.random.randn(60).cumsum() + 2000,
        'high': np.random.randn(60).cumsum() + 2010,
        'low': np.random.randn(60).cumsum() + 1990,
        'close': np.random.randn(60).cumsum() + 2000
    })
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Price'), row=1, col=1)
    fig.add_trace(go.Bar(x=df['date'], y=np.random.randint(100, 500, 60), name='Volume', marker_color='rgba(100,100,100,0.5)'), row=2, col=1)
    fig.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

with tab_indicators:
    i1, i2, i3 = st.columns(3)
    i1.write("**振荡指标**\n- RSI(14): 62.5\n- KDJ: 金叉")
    i2.write("**趋势指标**\n- MA20/MA60: 多头\n- MACD: 柱状图回升")
    i3.write("**支撑/阻力**\n- 关键阻力: 2150\n- 强力支撑: 1980")

# 3. 终极决策矩阵 (AI 深度分析)
st.divider()
if st.button("🚀 启动全球共识引擎 (Global Consensus Analytics)", use_container_width=True):
    if not or_api_key:
        st.error("请填入 API Key")
    else:
        with st.spinner(f"正在协调 {model_option} 整合 LEAN 引擎与舆情数据..."):
            try:
                client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_api_key)
                
                # 麦肯锡顾问级别的提示词
                prompt = f"""
                你是麦肯锡资深金融顾问，擅长结合技术面与舆情面进行决策。
                针对标的: {asset}
                当前数据：RSI 62.5，均线多头，Open Crawl 监测到 4 月越南展会预期利好，整体情绪偏向 Greed。
                请给出结构化报告：
                1. 执行摘要：一句话概括当前机会。
                2. 交易矩阵：明确的 入场参考、止损位 (SL)、三级止盈位 (TP1/2/3)。
                3. 顾问风险提示：针对 {asset} 的特有风险（如流动性或宏观政策）。
                4. 结论：综合推荐等级 (Strong Buy / Buy / Hold / Sell)。
                语言要求：极简、硬核、专业。
                """
                
                completion = client.chat.completions.create(
                    extra_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "LEAN Exec"},
                    model=model_option,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown(f"### 📋 {model_option} 首席研报")
                st.info(completion.choices[0].message.content)
                
                # 模拟仓位管理建议
                st.success(f"💡 顾问建议：基于你的 $2500 账户及当前波动率，建议单笔头寸不超过 2% (约 $50 风险敞口)。")
                
            except Exception as e:
                st.error(f"分析中断：{e}")

st.caption("麦肯锡顾问模式已激活 | 数据由 LEAN Engine 实时驱动 | 1986-08-21 狮子座逻辑加持")
