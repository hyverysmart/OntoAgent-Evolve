
from ontology.agent_ontology import AgentOntology
from team_recommender import recommend_team
from tools.pdf_reader import read_pdf


# ========== 1. 创建本体 ==========

ontology = AgentOntology()

ontology.add_agent("SearchAgent", ["search_paper"])
ontology.add_agent("ReaderAgent", ["read_pdf"])
ontology.add_agent("WriterAgent", ["write_report"])
ontology.add_agent("ResearchAgent", ["search_paper"])

# 用户任务需要的能力
required = [
    "search_paper",
    "read_pdf",
    "write_report"
]

PDF_PATH = "data/papers/LLMs4OL 3.pdf"


# ========== 2. 定义工具配置 ==========

# 每个 Agent 实际绑定的 PDF 工具
# 目前只有 ReaderAgent 拥有它
pdf_tools = {
    "ReaderAgent": read_pdf
}


# ========== 3. 自动推荐团队 ==========

def show_team(title):
    print(f"\n=== {title} ===")

    team = recommend_team(ontology, required)

    print("推荐团队:", team)
    print("团队人数:", len(team))

    for agent in team:
        print(
            agent,
            "能力:",
            ontology.get_capabilities(agent)
        )

    return team


# ========== 4. 验证工具 ==========

def verify_pdf_tool(tool):
    try:
        result = tool(PDF_PATH, max_pages=1)

        if not result["content"].strip():
            return False

        return True

    except Exception as error:
        print("工具验证失败:", error)
        return False


# ========== 5. 注册工具并同步本体 ==========

def register_pdf_tool(agent_name, tool):
    print(f"\n正在为 {agent_name} 注册 PDF 工具")

    # 必须先验证工具是否正常
    if not verify_pdf_tool(tool):
        print("验证失败，本体保持不变")
        return False

    # 验证成功，绑定工具
    pdf_tools[agent_name] = tool

    # 更新 RDF 中的能力关系
    ontology.add_capability(
        agent_name,
        "read_pdf"
    )

    print("工具已绑定")
    print("RDF 本体已更新")
    return True


# ========== 6. 移除工具并同步本体 ==========

def remove_pdf_tool(agent_name):
    if agent_name not in pdf_tools:
        print("该 Agent 没有 PDF 工具")
        return False

    # 移除工具绑定
    del pdf_tools[agent_name]

    # 删除 RDF 能力关系
    ontology.remove_capability(
        agent_name,
        "read_pdf"
    )

    print(f"\n已移除 {agent_name} 的 PDF 工具")
    print("RDF 本体已更新")
    return True


# ========== 7. 执行真实 PDF 任务 ==========

def execute_pdf_task(team):
    print("\n=== 验证推荐团队的 PDF 执行能力 ===")

    for agent in team:
        if agent not in pdf_tools:
            continue

        if "read_pdf" not in ontology.get_capabilities(agent):
            continue

        print("执行 Agent:", agent)

        result = pdf_tools[agent](
            PDF_PATH,
            max_pages=1
        )

        print("PDF 文件:", result["filename"])
        print("提取页数:", result["pages_read"])
        print("提取字符数:", len(result["content"]))

        assert result["content"].strip(), "PDF 内容为空"

        print("PDF 执行成功")
        return

    raise RuntimeError("推荐团队没有可执行的 PDF 工具")


# ========== 8. 开始完整实验 ==========

print("OntoAgent-Evolve 动态工具实验")

# 状态 A：原始推荐
team_a = show_team("状态 A：工具更新前")
execute_pdf_task(team_a)

# 状态 B：ResearchAgent 获得 PDF 工具
success = register_pdf_tool(
    "ResearchAgent",
    read_pdf
)

assert success, "新增工具验证失败"

team_b = show_team("状态 B：新增工具后")
execute_pdf_task(team_b)

# 状态 C：ResearchAgent 失去 PDF 工具
remove_pdf_tool("ResearchAgent")

team_c = show_team("状态 C：移除工具后")
execute_pdf_task(team_c)

# ========== 9. 检查结果 ==========

assert len(team_a) == 3
assert len(team_b) == 2
assert len(team_c) == 3

assert "ResearchAgent" in team_b
assert "ResearchAgent" not in pdf_tools

print("\n=== 实验完成 ===")
print("团队人数变化: 3 -> 2 -> 3")
print("能力更新与工具执行验证通过")
