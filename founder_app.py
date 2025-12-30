import streamlit as st
from tavily import TavilyClient
from openai import OpenAI  # <--- 核心变化：用 OpenAI 库连接 DeepSeek
import os
from dotenv import load_dotenv

# --- 1. 全局配置 ---
st.set_page_config(page_title="雄心荟·创业参谋", page_icon="🦁", layout="wide")
load_dotenv()

# 获取 Key
deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
tavily_key = os.environ.get("TAVILY_API_KEY")

# 检查 Key 是否存在
if not deepseek_key:
    st.error("❌ 未找到 DEEPSEEK_API_KEY，请检查 .env 文件")
    st.stop()

# 初始化 DeepSeek 客户端
client = OpenAI(
    api_key=deepseek_key, 
    base_url="https://api.deepseek.com"  # <--- 指向 DeepSeek 服务器
)

# --- 2. 界面设计 ---
st.title("🦁 雄心荟·超级轻创个体参谋")
st.markdown("### 🚀 专为雄心荟会员打造 | 深度商业评估系统")

# 侧边栏说明
with st.sidebar:
    st.info("💡 **使用指南**")
    st.markdown("""
    输入你想做的项目（如：*鲜花店、收纳师、车位投资*），AI 将为你：
    1. 🕵️‍♂️ **全网调研**：搜寻最新行情
    2. 🧠 **深度评估**：DeepSeek 拆解模式
    3. 💰 **算账避坑**：计算回本周期
    """)
    st.divider()
    st.caption("Powered by DeepSeek V3 & Tavily")

# --- 3. 核心逻辑 ---
topic = st.text_input("👇 请输入你想评估的创业项目:", placeholder="例如：在三线城市开一家自助洗车店")
start_btn = st.button("🚀 开始深度评估", type="primary")

if start_btn and topic:
    # 状态容器
    with st.status("⚙️ 参谋正在工作中...", expanded=True) as s:
        
        # 步骤 A: 联网搜索
        s.write("🕵️‍♂️ 正在全网搜集情报 (Tavily)...")
        tavily = TavilyClient(api_key=tavily_key)
        
        # 自动把用户的词扩展，搜得更细
        # 加上年份和“最新”关键词，强制搜索引擎找近期的
        import datetime
        current_year = datetime.datetime.now().year
        # 获取今天的具体日期，例如 "2025年12月30日"
        today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
        
        # 针对金融/时效性强的关键词，强制加上日期和“最新”
        # 搜索词变成： "白银 价格走势 2025年12月30日 最新行情 近一周涨跌原因"
        search_query = f"{topic} 价格走势 {today_str} 最新行情 近一周涨跌原因"
        
        s.write(f"🕵️‍♂️ 正在搜集 {today_str} 的最新情报...") # 提示语也改一下，看着更爽
        
        tavily = TavilyClient(api_key=tavily_key)
        search_res = tavily.search(query=search_query, search_depth="advanced", max_results=5)        
        # 整理搜索结果
        context = "\n".join([f"【来源：{r['title']}】{r['content']}" for r in search_res['results']])
        s.write("✅ 情报搜集完毕！")
        
        # 步骤 B: DeepSeek 思考
        s.write("🧠 DeepSeek V3 正在深度分析商业模式...")
        
        # 你的“毒舌导师” Prompt
        prompt = f"""
        【身份】你是一位拥有 20 年实战经验的资深创业导师，专为“雄心荟”个体创业者服务。你熟悉中国下沉市场、实体店逻辑和电商玩法。
        
        【用户想做】"{topic}"
        
        【全网情报】
        {context}
        
        【任务】请基于情报，撰写《项目可行性深度评测》。
        
        【要求】
        1. **拒绝废话**：用数据说话，犀利点评，不讲正确的废话。
        2. **必须包含以下模块**：
           - 📊 **市场红蓝海**：用数据判断饱和度。
           - 💰 **算笔账**：预估客单价、毛利、盈亏平衡点、回本周期（必须给出估算数字）。
           - 🚚 **进货实操**：给出具体的平台名称（如1688关键词）、批发市场名字或APP。
           - ⚠️ **劝退指南**：直击痛点，什么样的人千万别干这个。
        3. **结尾推荐**：给出 0-10 分的推荐指数，并一句话总结。
        4. **格式**：使用 Markdown，排版清晰，多用 Emoji。
        """
        
        # 发送给 DeepSeek
        response = client.chat.completions.create(
            model="deepseek-chat",  # 指定模型
            messages=[
                {"role": "system", "content": "你是一个专业、犀利、数据驱动的商业分析师。"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        
        # 获取结果
        article = response.choices[0].message.content
        s.update(label="✅ 评估报告已生成", state="complete", expanded=False)

# ... (前面的代码不变) ...
    
    # ... (前面的代码不变) ...
    
    # --- 4. 结果展示 ---
    st.divider()
    st.markdown(article)

    # === 🌟 升级版：生成 Word 文档 ===
    from docx import Document
    from io import BytesIO

    # 创建一个内存里的 Word 文档
    doc = Document()
    doc.add_heading(f'🦁 雄心荟·创业评测：{topic}', 0)
    
    # 把生成的报告写入 Word (注意：Word 不会自动渲染 Markdown 的加粗格式，但内容都在)
    doc.add_paragraph(article)
    doc.add_paragraph('\n\n(由 DeepSeek & 雄心荟 AI 参谋生成)')

    # 保存到内存
    binary_output = BytesIO()
    doc.save(binary_output)
    binary_output.seek(0)
    
    # 文件名
    file_name = f"创业评测_{topic}_{datetime.now().strftime('%Y%m%d')}.docx"
    
    st.download_button(
        label="📥 下载 Word 报告 (手机友好版)",
        data=binary_output,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    # ==============================
    
    # ... (底部版权不变) ...
    # ==============================

    # 底部版权
    st.divider()
    st.caption("🦁 雄心荟内部工具 | 数据仅供参考，投资需谨慎")
