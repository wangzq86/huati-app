import streamlit as st
import yfinance as yf
import json
import os
import requests
import base64

# --- 获取 Secrets (在 Streamlit Cloud 后台设置) ---
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_NAME = st.secrets["REPO_NAME"]  # 格式: wzq6386/huati-app
FILE_PATH = st.secrets["FILE_PATH"]   # 格式: trading_config.json

API_URL = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"

# --- GitHub 读写逻辑 ---
def load_config_from_github():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(API_URL, headers=headers)
    if r.status_code == 200:
        content_data = r.json()
        decoded_bytes = base64.b64decode(content_data["content"])
        return json.loads(decoded_bytes.decode("utf-8")), content_data["sha"]
    else:
        st.error(f"无法读取 GitHub 文件。状态码: {r.status_code}")
        return None, None

def save_config_to_github(new_data, current_sha):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    json_str = json.dumps(new_data, indent=4, ensure_ascii=False)
    encoded_content = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    payload = {
        "message": "Update from HarmonyOS Mobile",
        "content": encoded_content,
        "sha": current_sha
    }
    r = requests.put(API_URL, headers=headers, json=payload)
    return r.status_code == 200

# --- 核心 UI 逻辑 ---
st.set_page_config(page_title="指挥部-专业版", layout="wide")

if 'config' not in st.session_state:
    config, sha = load_config_from_github()
    if config:
        st.session_state.config = config
        st.session_state.sha = sha

if 'config' in st.session_state:
    conf = st.session_state.config
    st.title("🚀 三位一体 - 全局资金指挥部")

    with st.sidebar:
        st.header("⚙️ 数据同步")
        new_cash = st.number_input("可用现金 ¥", value=float(conf["cash"]))
        
        updated_stocks = {}
        for sym, info in conf["stocks"].items():
            st.markdown(f"---")
            st.subheader(info['name'])
            n_s = st.number_input(f"股数", value=float(info['shares']), key=f"s_{sym}")
            n_c = st.number_input(f"成本", value=float(info['cost']), key=f"c_{sym}")
            updated_stocks[sym] = {**info, "shares": n_s, "cost": n_c}
        
        if st.button("💾 永久同步至 GitHub"):
            final_data = {"cash": new_cash, "stocks": updated_stocks}
            if save_config_to_github(final_data, st.session_state.sha):
                st.success("✅ GitHub 已更新！")
                new_c, new_s = load_config_from_github()
                st.session_state.config = new_c
                st.session_state.sha = new_s
                st.rerun()

    # 行情显示
    cols = st.columns(len(conf["stocks"]))
    total_val = 0
    for i, (sym, info) in enumerate(conf["stocks"].items()):
        with cols[i]:
            try:
                p = yf.Ticker(sym).history(period="1d")['Close'].iloc[-1]
                total_val += (p * info['shares'])
                diff = (p - info['cost']) / info['cost'] if info['shares'] > 0 else 0
                st.metric(info['name'], f"¥{p:.2f}", f"{diff*100:+.2f}%")
            except:
                st.write(f"{info['name']} 加载中...")

    st.divider()
    st.header(f"💰 总资产: ¥{total_val + conf['cash']:,.2f}")
