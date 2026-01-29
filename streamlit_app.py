import streamlit as st
import yfinance as yf
import json
import os
import requests
import base64

# --- 1. 彻底绕过 st.secrets，直接读取环境变量 ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = os.environ.get("REPO_NAME")
FILE_PATH = os.environ.get("FILE_PATH")

# 检查环境变量是否注入成功
if not GITHUB_TOKEN or not REPO_NAME:
    st.error("❌ 密钥读取失败！")
    st.info("请在 Hugging Face 的 Settings -> Variables and secrets 中添加 GITHUB_TOKEN 和 REPO_NAME。")
    st.stop()

API_URL = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"

# --- 2. GitHub 远程同步逻辑 ---
def load_config():
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(API_URL, headers=headers)
    if r.status_code == 200:
        data = r.json()
        decoded = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(decoded), data["sha"]
    else:
        st.error(f"GitHub 读取失败 (Code: {r.status_code})。请确认文件已在 Git 根目录。")
        return None, None

def save_config(new_data, sha):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    content_json = json.dumps(new_data, indent=4, ensure_ascii=False)
    content_base64 = base64.b64encode(content_json.encode("utf-8")).decode("utf-8")
    payload = {
        "message": "Update via HarmonyOS",
        "content": content_base64,
        "sha": sha
    }
    r = requests.put(API_URL, headers=headers, json=payload)
    return r.status_code == 200

# --- 3. UI 界面 ---
st.set_page_config(page_title="指挥部-HF版", layout="wide")

if 'config_data' not in st.session_state:
    conf, sha = load_config()
    if conf:
        st.session_state.config_data = conf
        st.session_state.sha = sha

if 'config_data' in st.session_state:
    config = st.session_state.config_data
    st.title("🚀 三位一体指挥部 (Hugging Face + GitHub)")

    with st.sidebar:
        st.header("⚙️ 实操同步")
        new_cash = st.number_input("可用现金 ¥", value=float(config["cash"]), step=100.0)
        
        updated_stocks = {}
        for sym, info in config["stocks"].items():
            st.markdown(f"**{info['name']}**")
            s = st.number_input(f"股数", value=float(info['shares']), key=f"s_{sym}")
            c = st.number_input(f"成本", value=float(info['cost']), key=f"c_{sym}")
            updated_stocks[sym] = {**info, "shares": s, "cost": c}
        
        if st.button("💾 永久同步至 GitHub"):
            final_conf = {"cash": new_cash, "stocks": updated_stocks}
            if save_config(final_conf, st.session_state.sha):
                st.success("✅ GitHub 已更新！")
                new_c, new_s = load_config()
                st.session_state.config_data = new_c
                st.session_state.sha = new_s
                st.rerun()

    # 显示行情
    cols = st.columns(len(config["stocks"]))
    total_mv = 0
    for i, (sym, info) in enumerate(config["stocks"].items()):
        with cols[i]:
            try:
                p = yf.Ticker(sym).history(period="1d")['Close'].iloc[-1]
                total_mv += (p * info['shares'])
                diff = (p - info['cost']) / info['cost'] if info['shares'] > 0 else 0
                st.metric(info['name'], f"¥{p:.2f}", f"{diff*100:+.2f}%")
            except:
                st.write(f"{info['name']} 获取中...")

    st.divider()
    st.header(f"💰 总资产: ¥{total_mv + config['cash']:,.2f}")
