
from ontology.agent_ontology import AgentOntology
from dynamic_agent_manager import DynamicAgentManager
from tools.pdf_reader import read_pdf


PDF_PATH = "data/papers/LLMs4OL 3.pdf"

ontology = AgentOntology()

ontology.add_agent(
    "SearchAgent", ["search_paper"]
)
ontology.add_agent(
    "ReaderAgent", ["read_pdf"]
)
ontology.add_agent(
    "WriterAgent", ["write_report"]
)
ontology.add_agent(
    "ResearchAgent", ["search_paper"]
)

tasks = {
    "ResearchTask": [
        "search_paper",
        "read_pdf",
        "write_report"
    ]
}

manager = DynamicAgentManager(ontology, tasks)
manager.initialize()


def show(title):
    print(f"\n=== {title} ===")

    print(
        "能力:",
        ontology.get_capabilities("ResearchAgent")
    )

    print(
        "来源:",
        manager.capability_sources(
            "ResearchAgent",
            "read_pdf"
        )
    )

    print(
        "推荐团队:",
        manager.cache["ResearchTask"]
    )

    assert manager.check_consistency()
    print("一致性: PASS")


# 1. 初始状态
show("初始状态")

assert len(manager.cache["ResearchTask"]) == 3


# 2. 注册第一个 PDF 工具
assert manager.register_tool(
    "ResearchAgent",
    "PDFReaderTool",
    "read_pdf",
    read_pdf,
    {"file_path": PDF_PATH, "max_pages": 1}
)

show("注册第一个工具")

assert len(manager.cache["ResearchTask"]) == 2


# 3. 注册备用 PDF 工具
assert manager.register_tool(
    "ResearchAgent",
    "BackupPDFReaderTool",
    "read_pdf",
    read_pdf,
    {"file_path": PDF_PATH, "max_pages": 1}
)

show("注册第二个工具")

assert len(manager.cache["ResearchTask"]) == 2


# 4. 移除第一个工具
assert manager.remove_tool(
    "ResearchAgent",
    "PDFReaderTool"
)

show("移除第一个工具")

# 备用工具仍然提供 read_pdf
assert "read_pdf" in ontology.get_capabilities(
    "ResearchAgent"
)

assert len(manager.cache["ResearchTask"]) == 2

# 备用工具仍然可以执行
assert manager.execute_pdf(
    manager.cache["ResearchTask"],
    PDF_PATH
)


# 5. 移除最后一个 PDF 工具
assert manager.remove_tool(
    "ResearchAgent",
    "BackupPDFReaderTool"
)

show("移除最后一个工具")

assert "read_pdf" not in ontology.get_capabilities(
    "ResearchAgent"
)

assert len(manager.cache["ResearchTask"]) == 3


print("\n=== 多来源能力测试全部通过 ===")
print("团队人数: 3 -> 2 -> 2 -> 2 -> 3")
