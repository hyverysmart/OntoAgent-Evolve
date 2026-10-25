
from ontology.agent_ontology import AgentOntology
from dynamic_agent_manager import DynamicAgentManager
from tools.pdf_reader import read_pdf


# 1. 创建测试用本体
ontology = AgentOntology()

ontology.add_agent(
    "ResearchAgent",
    ["search_paper"]
)

tasks = {
    "SearchReadTask": [
        "search_paper",
        "read_pdf"
    ]
}

manager = DynamicAgentManager(ontology, tasks)
manager.initialize()


# 2. 记录修改前状态
before = ontology.get_capabilities(
    "ResearchAgent"
)

# 3. 使用不存在的 PDF 验证工具
success = manager.register_tool(
    "ResearchAgent",
    "BrokenPDFTool",
    "read_pdf",
    read_pdf,
    {
        "file_path": "data/papers/not_exist.pdf",
        "max_pages": 1
    }
)

# 4. 记录修改后状态
after = ontology.get_capabilities(
    "ResearchAgent"
)

print("\n=== 工具验证失败测试 ===")

print("工具是否注册成功:", success)
print("修改前能力:", before)
print("修改后能力:", after)

# 工具注册应该失败
assert success is False

# 本体不能发生错误变化
assert before == after

# 工具注册表不能保存错误工具
assert "BrokenPDFTool" not in manager.tools.get(
    "ResearchAgent", {}
)

# 推荐缓存仍然与本体状态一致
assert manager.check_consistency()

print("\n异常验证结果: PASS")
