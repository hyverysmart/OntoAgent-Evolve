
from ontology.agent_ontology import AgentOntology
from ontology.sparql_queries import (
    query_agent_tools,
    query_all_tool_bindings,
    check_tool_provenance_consistency
)
from dynamic_agent_manager import DynamicAgentManager
from tools.pdf_reader import read_pdf


PDF_PATH = "data/papers/LLMs4OL 3.pdf"


# 1. 创建本体
ontology = AgentOntology()

ontology.add_agent(
    "ResearchAgent",
    ["search_paper"]
)

ontology.add_agent(
    "WriterAgent",
    ["write_report"]
)

ontology.add_agent(
    "ReaderAgent",
    []
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


def register(agent, tool_name):
    return manager.register_tool(
        agent,
        tool_name,
        "read_pdf",
        read_pdf,
        {
            "file_path": PDF_PATH,
            "max_pages": 1
        }
    )


# 2. 注册两个工具
assert register(
    "ReaderAgent",
    "PDFReaderTool"
)

assert register(
    "ResearchAgent",
    "PDFReaderTool"
)


# 3. 使用 SPARQL 查询 ResearchAgent
print("\n=== SPARQL 查询 ResearchAgent ===")

tools = query_agent_tools(
    ontology,
    "ResearchAgent"
)

print(tools)

assert tools == [
    {
        "tool": "PDFReaderTool",
        "capability": "read_pdf"
    }
]


# 4. 查询全部绑定关系
print("\n=== 全部 RDF 工具来源 ===")

bindings = query_all_tool_bindings(ontology)

for item in bindings:
    print(item)

assert len(bindings) == 2


# 5. 一致性测试
print("\n=== 一致性测试 ===")

assert check_tool_provenance_consistency(manager)
assert manager.check_consistency()

print("工具注册表与 RDF 一致: PASS")


# 6. 删除 ResearchAgent 的工具
assert manager.remove_tool(
    "ResearchAgent",
    "PDFReaderTool"
)

assert query_agent_tools(
    ontology,
    "ResearchAgent"
) == []

assert check_tool_provenance_consistency(manager)
assert manager.check_consistency()

print("工具删除后 RDF 一致: PASS")


# 7. 主动破坏 RDF，验证检测能力
print("\n=== 模拟 RDF 来源不一致 ===")

from ontology.tool_provenance import (
    add_tool_provenance
)

add_tool_provenance(
    ontology,
    "ResearchAgent",
    "FakeTool",
    "read_pdf"
)

assert not check_tool_provenance_consistency(
    manager
)

print("成功检测到工具来源不一致: PASS")


print("\n=== SPARQL 一致性测试全部通过 ===")
