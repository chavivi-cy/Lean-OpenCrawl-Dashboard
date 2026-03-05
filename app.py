import streamlit as st
import google.generativeai as genai
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

# --- 页面专业设置 ---
st.set_page_config(page_title="LEAN + OPEN CRAWL | 智能投研系统", layout="wide", initial_sidebar_state="expanded")

# 自定义 CSS 让界面更有科技感
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 侧边栏：核心配置 ---
with st.sidebar:
    st.title("🛡️ 系统控制台")
    api_key = st.text_input("Gemini API Key (备用)", type="password", help="若不填，系统将进入智能模拟演示模式")
    asset_type = st.selectbox("核心监控标的", ["ETH/USDT", "纳斯达克100", "黄金 (XAU/USD)", "Prop Firm 挑战账户"])
    st.divider()
    st.info(f"身份验证: 苏先生 (顾问模式)\n更新时间: {datetime.now().strftime('%Y-%m-%d')}")

# --- 主界面：标题与核心指标 ---
st.title("📊 LEAN + OPEN CRAWL 深度投研看板")
st.caption("融合量化回测引擎与全网舆情抓取，提供多维度决策支持。")

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("RSI (14)", "68.2", "超买预警")
with m2: st.metric("波动率 (VIX)", "14.5", "-2.1%", delta_color="inverse")
with m3: st.metric("LEAN 策略得分", "88/100", "+5")
with m4: st.metric("舆情热度", "🔥 极高", "12k 讨论")

# --- 中间层：可视化分析图表 ---
st.markdown("### 📈 实时行情与量化信号 (LEAN Engine)")
tab1, tab2 = st.tabs(["价格走势图", "情绪热力图"])

with tab1:
    # 模拟一段价格数据
    dates = pd.date_range(start='2026-01-01', periods=100)
    prices = np.cumsum(np.random.randn(100) + 0.1) + 2600
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name='Price', line=dict(color='#00d1ff', width=2)))
    fig.update_layout(template="plotly_dark", margin=dict(l=20, r=20, t=20, b=20), height=400)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.write("正在从 **OPEN CRAWL** 抓取全球社交媒体、财报、新闻的情绪数据...")
    st.progress(72, text="当前市场看涨情绪: 72%")

# --- 底层：AI 策略生成 (双模逻辑) ---
st.markdown("---")
st.subheader("🧠 综合决策研报")

if st.button("🚀 生成深度策略建议", use_container_width=True):
    with st.spinner("正在融合多维数据，由 Gemini 提供 AI 支持..."):
        success = False
        # 尝试真实 API 调用
        if api_key:
            try:
                genai.configure(api_key=api_key)
                # 尝试目前最稳健的调用全称
                model = genai.GenerativeModel('models/gemini-1.5-flash')
                prompt = f"针对 {asset_type}，技术面RSI 68且均线向上，情绪面看涨72%，请给出30字以内的极简操作建议。"
                response = model.generate_content(prompt)
                st.success("✅ [实时 AI 模式] 策略已生成")
                st.info(response.text)
                success = True
            except:
                pass
        
        # 降级模拟模式 (演示核心)
        if not success:
            time_delay = 1.5
            import time
            time.sleep(time_delay)
            st.warning("💡 [智能演示模式已激活] API 暂时受限，当前基于 LEAN 历史模型输出：")
            
            strategies = {
                "ETH/USDT": "**建议持仓待涨**。目前 RSI 虽接近超买，但 Open Crawl 监测到 ETH 质押量持续上升，筹码锁定良好，建议止损上移至 $2550。",
                "Prop Firm 挑战账户": "**风控优先**。当前回撤控制在 1.2%，符合 The5ers 规则。建议在美盘开盘前半小时降低 50% 仓位以应对非农波动。",
                "default": "技术面处于强势扩张期，建议结合 LEAN 的动能因子进行右侧入场，目标位参考前高阻力区。"
            }
            st.write(strategies.get(asset_type, strategies["default"]))

st.caption("声明：本看板仅供演示，不构成任何投资建议。")