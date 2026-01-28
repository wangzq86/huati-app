import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="华体指挥部", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 核心策略参数 ---
PARAMS = {
    "buy_th_1": 0.06, "buy_th_2": 0.12, "stop_loss": 0.25,
    "sell_trigger": 0.09, "pullback": 0.025, "cash_redline": 0.10
}

# --- 侧边栏：资产输入 (手机端在左侧菜单) ---
st.sidebar.header("💰 资产配置")
shares = st.sidebar.number_input("当前持仓", value=2600)
avg_cost = st.sidebar.number_input("成本均价", value=16.384, format="%.3f")
cash = st.sidebar.number_input("可用现金", value=40000.0)

# --- 获取实时行情 ---
@st.cache_data(ttl=30) # 每30秒缓存失效，强制刷新
def get_price(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1d")
    return round(data['Close'].iloc[-1], 3) if not data.empty else None

price = get_price("603679.SS")

if price:
    # --- 计算逻辑 ---
    profit_ratio = (price - avg_cost) / avg_cost
    pl_amount = (price - avg_cost) * shares
    total_assets = cash + (price * shares)
    reserve_line = total_assets * PARAMS['cash_redline']

    # --- UI 顶部：实时核心指标 ---
    st.title("🚀 华体科技指挥部")
    
    col1, col2 = st.columns(2)
    col1.metric("实时现价", f"¥{price}")
    col2.metric("浮盈/浮亏", f"{pl_amount:,.2f}", f"{profit_ratio*100:.2f}%")

    st.divider()

    # --- UI 中部：资产看板 ---
    st.subheader("📊 账户全景")
    c1, c2 = st.columns(2)
    c1.write(f"**总资产:** ¥{total_assets:,.2f}")
    c2.write(f"**可用现金:** ¥{cash:,.2f}")
    st.progress(min(max(shares * price / total_assets, 0.0), 1.0), text=f"当前仓位: {(shares * price / total_assets)*100:.1f}%")

    # --- UI 下部：策略决策 (手机端最核心) ---
    st.subheader("🎯 实时决策建议")
    
    advice = "✅ 区间波动：目前波动正常，持股待机。"
    color = "blue"

    if profit_ratio <= -PARAMS['stop_loss']:
        advice = "🚫 [终极熔断] 跌幅过大，请立即清仓保护本金！"
        st.error(advice)
    elif profit_ratio <= -PARAMS['buy_th_1']:
        if cash > reserve_line:
            advice = f"🚨 [补仓信号] 跌幅达 {profit_ratio*100:.1f}%, 建议补仓。"
            st.success(advice)
        else:
            advice = "⚠️ [红线警告] 已达补仓位但现金不足，严禁加仓！"
            st.warning(advice)
    elif profit_ratio >= PARAMS['sell_trigger']:
        # 简化版止盈逻辑展示
        advice = f"📈 [追踪止盈激活] 目标价 ¥{avg_cost*(1+PARAMS['sell_trigger']):.2f} 已达。"
        st.info(advice)
    else:
        st.info(advice)

    # --- UI 底部：参考点位表格 ---
    with st.expander("🔍 查看策略参考点位"):
        st.write(f"● **终极熔断价:** ¥{avg_cost*(1-PARAMS['stop_loss']):.2f}")
        st.write(f"● **一级补仓价:** ¥{avg_cost*(1-PARAMS['buy_th_1']):.2f}")
        st.write(f"● **止盈激活价:** ¥{avg_cost*(1+PARAMS['sell_trigger']):.2f}")
        st.write(f"● **现金保护线:** ¥{reserve_line:.2f}")

    st.caption(f"最后同步时间: {datetime.now().strftime('%H:%M:%S')}")

else:
    st.error("无法获取行情，请检查网络或股票代码。")

# --- 自动刷新 ---
# time.sleep(30)
# st.rerun()