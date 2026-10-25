
from rdflib import RDF

from ontology.agent_ontology import (
    AgentOntology,
    EX
)
from ontology.tool_provenance import (
    get_tool_provenance
)
from dynamic_agent_manager import DynamicAgentManager
from tools.pdf_reader import read_pdf


PDF_PATH = "data/papers/LLMs4OL 3.pdf"

ontology = AgentOntology()

ontology.add_agent(
    "ResearchAgent",
    ["search_paper"]
)

manager = DynamicAgentManager(
    ontology,
    {
        "SearchReadTask": [
            "search_paper",
            "read_pdf"
        ]
    }
)

manager.initialize()


def register(name):
    return manager.register_tool(
        "ResearchAgent",
        name,
        "read_pdf",
        read_pdf,
        {
            "file_path": PDF_PATH,
            "max_pages": 1
        }
    )


# Test 1: 注册两个工具
assert register("PDFReaderTool")
assert register("BackupPDFReaderTool")

sources = get_tool_provenance(
    ontology,
    "ResearchAgent"
)

print("\n=== 两个工具注册后 ===")
print(sources)

assert len(sources) == 2
assert all(
    item["capability"] == "read_pdf"
    for item in sources
)

assert "read_pdf" in ontology.get_capabilities(
    "ResearchAgent"
)

assert manager.check_consistency()


# Test 2: 移除一个工具
assert manager.remove_tool(
    "ResearchAgent",
    "PDFReaderTool"
)

sources = get_tool_provenance(
    ontology,
    "ResearchAgent"
)

print("\n=== 移除第一个工具后 ===")
print(sources)

assert len(sources) == 1
assert sources[0]["tool"] == "BackupPDFReaderTool"

assert "read_pdf" in ontology.get_capabilities(
    "ResearchAgent"
)


# Test 3: 移除最后一个工具
assert manager.remove_tool(
    "ResearchAgent",
    "BackupPDFReaderTool"
)

sources = get_tool_provenance(
    ontology,
    "ResearchAgent"
)

print("\n=== 移除最后一个工具后 ===")
print(sources)

assert sources == []

assert "read_pdf" not in ontology.get_capabilities(
    "ResearchAgent"
)

assert manager.check_consistency()


# Test 4: 输出 RDF
print("\n=== 最终 RDF ===")

print(
    ontology.graph.serialize(
        format="turtle"
    )
)

print("\nRDF 工具来源测试: PASS")
