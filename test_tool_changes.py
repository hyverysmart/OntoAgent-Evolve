
from ontology.agent_ontology import AgentOntology
from incremental_recommender import IncrementalRecommender
from services.tool_registry import ToolRegistry
from services.capability_sync import CapabilitySync


# 1. 创建 RDF 本体
ontology = AgentOntology()

ontology.add_agent("SearchAgent", ["search_paper"])
ontology.add_agent("ReaderAgent", ["read_pdf"])

# 2. 创建三个任务
ontology.add_task("SearchTask", ["search_paper"])
ontology.add_task("ReadTask", ["read_pdf"])
ontology.add_task(
    "ResearchTask",
    ["search_paper", "read_pdf"]
)

tasks = ["SearchTask", "ReadTask", "ResearchTask"]

# 3. 初始化推荐器
recommender = IncrementalRecommender(ontology)
recommender.initialize(tasks)

# 4. 初始化工具注册表
registry = ToolRegistry()

registry.register_agent(
    "SearchAgent",
    ["WebSearchTool"]
)

# 5. 创建能力同步器
sync = CapabilitySync(registry, recommender)


def check_results():
    # 检查增量结果是否与全量结果一致
    for task in tasks:
        full = ontology.recommend_task(task)
        cached = recommender.cache[task]
        assert full == cached, f"{task} 推荐不一致"

    print("全部推荐结果一致: True")


print("\n=== 初始推荐 ===")
recommender.show_results()
check_results()

# 6. 模拟新增 PDF 工具
print("\n=== 事件1：新增 PDFParserTool ===")

sync.sync(
    "SearchAgent",
    ["WebSearchTool", "PDFParserTool"]
)

recommender.show_results()
check_results()

# 7. 模拟删除 Web Search 工具
print("\n=== 事件2：删除 WebSearchTool ===")

sync.sync(
    "SearchAgent",
    ["PDFParserTool"]
)

recommender.show_results()
check_results()

# 8. 再次同步相同配置
print("\n=== 事件3：工具没有变化 ===")

changes = sync.sync(
    "SearchAgent",
    ["PDFParserTool"]
)

assert changes == {"added": [], "removed": []}
check_results()

# 9. 保存最终本体
ontology.save("data/agents.ttl")

print("\n测试全部完成！")
