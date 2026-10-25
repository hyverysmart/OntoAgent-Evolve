
from ontology.agent_ontology import AgentOntology
from incremental_recommender import IncrementalRecommender

# 1. 创建本体
ontology = AgentOntology()

# 2. 注册 Agent
ontology.add_agent("SearchAgent", ["search_paper"])
ontology.add_agent("ReaderAgent", ["read_pdf"])
ontology.add_agent("WriterAgent", ["write_report"])

# 3. 创建任务
ontology.add_task("SearchTask", ["search_paper"])
ontology.add_task("ReadTask", ["read_pdf"])
ontology.add_task(
    "ResearchTask",
    ["search_paper", "read_pdf"]
)
ontology.add_task("WriteTask", ["write_report"])

tasks = [
    "SearchTask",
    "ReadTask",
    "ResearchTask",
    "WriteTask"
]

# 4. 初始化推荐缓存
recommender = IncrementalRecommender(ontology)
recommender.initialize(tasks)

print("=== 初始推荐 ===")
recommender.show_results()

# 5. 模拟 Agent 增加新能力
print("\n=== SearchAgent 新增 read_pdf ===")

affected = recommender.update_capability(
    "SearchAgent",
    "read_pdf",
    "add"
)

print("重新计算的任务:", affected)

# 6. 查看增量更新结果
print("\n=== 增量更新后的推荐 ===")
recommender.show_results()

# 7. 验证与全量重算是否一致
print("\n=== 正确性验证 ===")

all_correct = True

for task in tasks:
    full_result = ontology.recommend_task(task)
    incremental_result = recommender.cache[task]

    correct = full_result == incremental_result

    print(f"{task}: {'一致' if correct else '不一致'}")

    if not correct:
        all_correct = False

print("全部一致:", all_correct)

# 8. 保存本体
ontology.save("data/agents.ttl")
