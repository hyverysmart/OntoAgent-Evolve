
from ontology.agent_ontology import AgentOntology
from incremental_recommender import IncrementalRecommender
from services.tool_registry import ToolRegistry
from services.auto_capability_sync import AutoCapabilitySync


# 1. 创建本体
ontology = AgentOntology()

ontology.add_agent(
    "SearchAgent",
    ["search_paper"]
)

ontology.add_agent(
    "ReaderAgent",
    ["read_pdf"]
)

# 2. 创建任务
tasks = ["SearchTask", "ReadTask", "ResearchTask"]

ontology.add_task("SearchTask", ["search_paper"])
ontology.add_task("ReadTask", ["read_pdf"])
ontology.add_task(
    "ResearchTask",
    ["search_paper", "read_pdf"]
)

# 3. 初始化增量推荐
recommender = IncrementalRecommender(ontology)
recommender.initialize(tasks)

# 4. 初始化工具注册表
registry = ToolRegistry()

registry.register_agent(
    "SearchAgent",
    ["WebSearchTool"]
)

auto_sync = AutoCapabilitySync(
    registry,
    recommender
)


def check_results():
    for task in tasks:
        full = ontology.recommend_task(task)
        cached = recommender.cache[task]
        assert full == cached, f"{task} 结果不一致"

    print("全量与增量推荐一致: True")


print("\n=== 初始推荐 ===")
recommender.show_results()

# 事件 1：新增 PDF 工具
print("\n=== 事件1：新增 PDFParserTool ===")

auto_sync.sync_agent(
    "SearchAgent",
    ["WebSearchTool", "PDFParserTool"]
)

recommender.show_results()
check_results()

# 事件 2：删除 Web Search 工具
print("\n=== 事件2：删除 WebSearchTool ===")

auto_sync.sync_agent(
    "SearchAgent",
    ["PDFParserTool"]
)

recommender.show_results()
check_results()

# 事件 3：没有变化
print("\n=== 事件3：没有变化 ===")

auto_sync.sync_agent(
    "SearchAgent",
    ["PDFParserTool"]
)

check_results()

# 保存最新本体
ontology.save("data/agents.ttl")

print("\n自动能力识别与同步测试完成！")
