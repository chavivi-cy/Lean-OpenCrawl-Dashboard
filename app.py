import streamlit as st
from openai import OpenAI  # 使用通用 OpenAI 协议连接 OpenRouter
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# 页面基础设置
st.set_page_config(page_title="LEAN + OPEN CRAWL | 智能投研系统", layout="wide")
st.title("📈 智能投资演示看板 (OpenRouter 版)")

# 侧边栏：这里填入你的新钥匙
with st.sidebar:
    st.header("🔑 系统授权")
    # 这里就是填你那串 sk-or-v1-...301 的地方
    or_api_key = st.text_input("输入 OpenRouter API Key", type="password")
    
    st.divider()
    model_option = st.selectbox("核心 AI 引擎", [
        "google/gemini-2.0-flash-001", 
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4o-mini"
    ])
    asset = st.selectbox("分析目标", ["ETH/USDT", "纳指100", "Prop Firm 账户"])

# 数据展示区 (LEAN & Open Crawl)
col1, col2 = st.columns(2)
with col1:
    st.metric("LEAN 策略得分", "92/100", "+3")
    st.write("✅ 技术面：均线多头，RSI 62")
with col2:
    st.metric("Open Crawl 情绪", "🔥 极高", "78%")

# AI 策略生成逻辑
if st.button("🚀 生成深度研报", use_container_width=True):
    if not or_api_key:
        st.warning("请在左侧填入你的 OpenRouter Key (sk-or-v1-...)")
    else:
        with st.spinner(f"正在通过 OpenRouter 调用 {model_option}..."):
            try:
                # 关键步骤：指向 OpenRouter 的服务器地址
                client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=or_api_key,
                )
                
                completion = client.chat.completions.create(
                    extra_headers={
                        "HTTP-Referer": "http://localhost:8501", 
                        "X-Title": "Lean Dashboard",
                    },
                    model=model_option,
                    messages=[
                        {"role": "user", "content": f"请以资深交易员身份，结合RSI 62和看涨情绪，为 {asset} 提供150字策略建议。"}
                    ],
                )
                st.success("✅ 分析完成！")
                st.markdown("#### AI 建议全文：")
                st.write(completion.choices[0].message.content)
            except Exception as e:
                st.error(f"调用失败，请检查 Key 或网络: {e}")

st.caption("Powered by OpenRouter | 麦肯锡顾问模式")
