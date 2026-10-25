
from ontology.agent_ontology import AgentOntology
from incremental_recommender import IncrementalRecommender
from services.dify_client import extract_capabilities

# 1. 创建本体
ontology = AgentOntology()

ontology.add_agent("SearchAgent", ["search_paper"])
ontology.add_agent("ReaderAgent", ["read_pdf"])

ontology.add_task(
    "ResearchTask",
    ["search_paper", "read_pdf"]
)

# 2. 初始化推荐缓存
recommender = IncrementalRecommender(ontology)
recommender.initialize(["ResearchTask"])

print("=== 更新前 ===")
recommender.show_results()

# 3. 将工具描述发给 Dify
description = (
    "This agent can search academic papers "
    "and extract text from PDF files."
)

candidates = extract_capabilities(
    "SearchAgent",
    description
)

print("\nDify 识别的候选能力:", candidates)

# 4. 人工确认：仅同步新增能力
current = ontology.get_capabilities("SearchAgent")
new_capabilities = set(candidates) - current

for capability in sorted(new_capabilities):
    answer = input(
        f"确认 SearchAgent 已具备 {capability} 能力？(y/n): "
    )

    if answer.strip().lower() == "y":
        affected = recommender.update_capability(
            "SearchAgent",
            capability,
            "add"
        )
        print("已更新任务:", affected)

# 5. 对比全量重算与增量推荐
print("\n=== 更新后 ===")
recommender.show_results()

full_result = ontology.recommend_task("ResearchTask")
cached_result = recommender.cache["ResearchTask"]

print("推荐结果一致:", full_result == cached_result)

# 6. 保存本体
ontology.save("data/agents.ttl")
