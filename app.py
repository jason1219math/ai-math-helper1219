import os
import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
st.markdown("""
<style>
.stApp {
    background: radial-gradient(ellipse at bottom, #1b2735 0%, #090a0f 100%);
    overflow: hidden;
}
.stApp::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: transparent;
    box-shadow:
        1744px 122px #FFF, 134px 1321px #FFF, 1730px 1124px #FFF,
        1682px 1049px #FFF, 981px 1053px #FFF, 774px 1448px #FFF,
        927px 1442px #FFF, 906px 1333px #FFF, 1461px 1336px #FFF,
        1040px 1341px #FFF, 1947px 1085px #FFF, 1426px 1087px #FFF,
        1386px 685px #FFF, 1962px 704px #FFF, 1314px 1949px #FFF,
        1016px 1856px #FFF, 1886px 1825px #FFF, 1173px 1827px #FFF,
        1744px 122px #FFF, 134px 1321px #FFF, 1730px 1124px #FFF;
    animation: twinkle 3s infinite alternate;
}
@keyframes twinkle {
    0% { opacity: 0.3; }
    100% { opacity: 1; }
}
div[data-testid="stVerticalBlock"] > div {
    background: rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
h1, h2, h3, p, label {
    color: #e0e0e0 !important;
}
.stButton > button {
    background: rgba(255, 255, 255, 0.1);
    color: white;
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 10px;
}
.stButton > button:hover {
    background: rgba(255, 255, 255, 0.2);
}
</style>
""", unsafe_allow_html=True)
# ========== 1. 读密钥 ==========
load_dotenv()
simpletex_token = os.getenv("SIMPLETEX_TOKEN")
deepseek_key = os.getenv("DEEPSEEK_API_KEY")

# ========== 2. SimpleTex 识别 ==========
def ocr(image_file):
    url = "https://server.simpletex.cn/api/latex_ocr_turbo"
    headers = {"token": simpletex_token}
    files = {"file": image_file}
    result = requests.post(url, headers=headers, files=files).json()
    return result["res"]["latex"]
def translate_latex(latex):
    client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
    content = f"""请把下面这段 LaTeX 代码，翻译成普通人能看懂的中文数学题目。
不要用 LaTeX 符号，用 x1、x2、x^2 这种写法。
如果是方程组，分行写清楚。

LaTeX：
{latex}
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": content}]
    )
    return response.choices[0].message.content
# ========== 3. DeepSeek 解题 ==========
def solve(latex):
    client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com")
    content = f"""请完成以下任务：
1. 先把题目用标准的中文数学语言完整复述一遍。
2. 然后一步步详细解答，每一步都说明为什么这么做。
3. 最后给出答案。

要求：
- 不要用 LaTeX 代码。
- 数学符号用普通文字表示，比如 x1、x2、x^2、分数写成 1/2。
- 矩阵用中括号和文字描述，比如 [1, 2, 3; 4, 5, 6]。

题目：
{latex}
"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": content}]
    )
    return response.choices[0].message.content

# ========== 4. B站搜索 ==========
import random

def search_bilibili(keyword):
    url = "https://api.bilibili.com/x/web-interface/search/type"
    params = {"search_type": "video", "keyword": keyword, "page": random.randint(1, 5)}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.bilibili.com/"
    }
    try:
        res = requests.get(url, params=params, headers=headers)
        data = res.json()
    except:
        return []

    videos = []
    for item in data.get("data", {}).get("result", [])[:5]:
        title = item["title"].replace('<em class="keyword">', '').replace('</em>', '')
        videos.append({"title": title, "bvid": item["bvid"]})
    return videos
# ========== 5. 页面 ==========
st.title("AI 数学助手")

tab1, tab2 = st.tabs(["拍照解题", "搜知识点看视频"])

# ----- 拍照解题 -----
with tab1:
    st.write("**提示：请先把图片裁剪好，只保留题目部分，再上传。**")

    st.write("**方式一：拍照**")
    img_camera = st.camera_input("用摄像头拍一张数学题")

    st.write("**方式二：上传图片**")
    img_upload = st.file_uploader("或者上传一张数学题图片", type=["jpg", "jpeg", "png"])

    img_file = img_camera if img_camera is not None else img_upload

    if img_file is not None:
        st.image(img_file, caption="你的图片", use_container_width=True)

        if st.button("识别题目"):
            with st.spinner("正在识别..."):
                latex = ocr(img_file)
                readable = translate_latex(latex)
            st.session_state["question"] = readable

        if "question" in st.session_state:
            edited = st.text_area("识别结果（可修改）", st.session_state["question"], height=200)

            if st.button("开始解题"):
                with st.spinner("正在解题..."):
                    answer = solve(edited)
                st.markdown("**解答：**")
                st.markdown(answer)
# ----- 搜知识点 -----
with tab2:
    kw = st.text_input("输入知识点，比如：洛必达法则、矩阵特征值")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("搜索视频"):
            st.session_state["keyword"] = kw
    with col2:
        if st.button("换一批"):
            st.session_state["keyword"] = kw

    if "keyword" in st.session_state and st.session_state["keyword"]:
        with st.spinner("正在搜索B站视频..."):
            videos = search_bilibili(st.session_state["keyword"])
        if videos:
            for v in videos:
                st.write(f"**{v['title']}**")
                st.components.v1.iframe(
                    f"//player.bilibili.com/player.html?bvid={v['bvid']}",
                    height=400
                )
        else:
            st.warning("没找到相关视频，请稍后再试一次。")