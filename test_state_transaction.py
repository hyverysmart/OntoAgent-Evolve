
from ontology.agent_ontology import AgentOntology
from dynamic_agent_manager import DynamicAgentManager
from tools.pdf_reader import read_pdf
from services.state_transaction import (
    apply_and_save,
    take_snapshot
)


PDF_PATH = "data/papers/LLMs4OL 3.pdf"


# 1. 创建测试环境
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


# 2. 模拟磁盘保存失败
def fake_save_failure(manager):
    raise OSError("模拟磁盘写入失败")


# 3. 定义新增工具操作
def add_pdf_tool():
    return manager.register_tool(
        "ResearchAgent",
        "PDFReaderTool",
        "read_pdf",
        read_pdf,
        {
            "file_path": PDF_PATH,
            "max_pages": 1
        }
    )


# 4. 记录原始状态
before = take_snapshot(manager)

print("=== 操作前 ===")

print(
    "ResearchAgent 能力:",
    ontology.get_capabilities("ResearchAgent")
)

print(
    "推荐团队:",
    manager.cache["ResearchTask"]
)


# 5. 执行操作，但让保存失败
print("\n=== 模拟 JSON 保存失败 ===")

try:
    apply_and_save(
        manager,
        add_pdf_tool,
        fake_save_failure
    )

except OSError as error:
    print("捕获到预期错误:", error)


# 6. 检查是否回滚
after = take_snapshot(manager)

assert set(before["triples"]) == set(after["triples"])
assert before["tools"] == after["tools"]
assert before["cache"] == after["cache"]
assert before["history"] == after["history"]

assert "read_pdf" not in ontology.get_capabilities(
    "ResearchAgent"
)

assert len(manager.cache["ResearchTask"]) == 3
assert manager.check_consistency()

print("\n=== 回滚后的状态 ===")

print(
    "ResearchAgent 能力:",
    ontology.get_capabilities("ResearchAgent")
)

print(
    "推荐团队:",
    manager.cache["ResearchTask"]
)

print("\n事务回滚测试: PASS")
