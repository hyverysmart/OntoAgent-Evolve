
from ontology.agent_ontology import AgentOntology
from dynamic_agent_manager import DynamicAgentManager
from tools.pdf_reader import read_pdf


PDF_PATH = "data/papers/LLMs4OL 3.pdf"


# 1. 创建本体与 Agent
ontology = AgentOntology()

ontology.add_agent(
    "SearchAgent", ["search_paper"]
)
ontology.add_agent(
    "ReaderAgent", []
)
ontology.add_agent(
    "WriterAgent", ["write_report"]
)
ontology.add_agent(
    "ResearchAgent", ["search_paper"]
)

# 2. 定义任务
tasks = {
    "ResearchTask": [
        "search_paper",
        "read_pdf",
        "write_report"
    ],
    "SearchReadTask": [
        "search_paper",
        "read_pdf"
    ],
    "WritingTask": [
        "write_report"
    ]
}

# 3. 初始化动态管理器
manager = DynamicAgentManager(ontology, tasks)

# ReaderAgent 注册原有 PDF 工具
success = manager.register_tool(
    "ReaderAgent",
    "PDFReaderTool",
    "read_pdf",
    read_pdf,
    {
        "file_path": PDF_PATH,
        "max_pages": 1
    }
)

assert success, "ReaderAgent 工具初始化失败"

manager.initialize()


def show_status(title):
    print(f"\n=== {title} ===")

    for task, team in manager.cache.items():
        print(task, "->", team)

    assert manager.check_consistency()
    print("一致性: PASS")

    team = manager.cache["ResearchTask"]

    manager.execute_pdf(team, PDF_PATH)

    return team


# 状态 A
team_a = show_status("状态 A：初始团队")


# 4. 为 ResearchAgent 注册 PDF 工具
success = manager.register_tool(
    "ResearchAgent",
    "PDFReaderTool",
    "read_pdf",
    read_pdf,
    {
        "file_path": PDF_PATH,
        "max_pages": 1
    }
)

assert success, "ResearchAgent 工具注册失败"

# 状态 B
team_b = show_status("状态 B：新增 PDF 工具")


# 5. 移除 ResearchAgent 的工具
success = manager.remove_tool(
    "ResearchAgent",
    "PDFReaderTool"
)

assert success, "移除工具失败"

# 状态 C
team_c = show_status("状态 C：移除 PDF 工具")


# 6. 验证预期变化
assert len(team_a) == 3
assert len(team_b) == 2
assert len(team_c) == 3

assert "ResearchAgent" in team_b

assert "read_pdf" not in ontology.get_capabilities(
    "ResearchAgent"
)

print("\n=== 动态集成实验成功 ===")
print("团队人数: 3 -> 2 -> 3")

print("\n=== 能力变化记录 ===")
for event in manager.history:
    print(event)
