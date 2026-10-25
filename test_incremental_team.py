
from ontology.agent_ontology import AgentOntology
from incremental_team_recommender import (
    IncrementalTeamRecommender
)


# 1. 创建本体
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

ontology.add_agent(
    "ExplainAgent", ["explain_concept"]
)


# 2. 定义四个任务
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
    ],

    "ExplainTask": [
        "explain_concept"
    ]
}


# 3. 创建增量推荐器
recommender = IncrementalTeamRecommender(
    ontology,
    tasks
)

recommender.initialize()


def show_results(title):
    print(f"\n=== {title} ===")

    for task, team in recommender.cache.items():
        print(task, "->", team)


# 4. 显示初始推荐
show_results("初始状态")


# 5. ResearchAgent 新增 PDF 阅读能力
print("\n=== 新增 read_pdf ===")

affected = recommender.update_capability(
    "ResearchAgent",
    "read_pdf",
    "add"
)

print("受影响任务:", affected)
print("增量重算任务数:", len(affected))
print("全量重算任务数:", len(tasks))

show_results("能力更新后")

assert len(recommender.cache["ResearchTask"]) == 2
assert len(recommender.cache["SearchReadTask"]) == 1

assert recommender.check_consistency()
print("一致性检查: PASS")


# 6. ResearchAgent 失去 PDF 阅读能力
print("\n=== 移除 read_pdf ===")

affected = recommender.update_capability(
    "ResearchAgent",
    "read_pdf",
    "remove"
)

print("受影响任务:", affected)

show_results("能力移除后")

assert len(recommender.cache["ResearchTask"]) == 3
assert len(recommender.cache["SearchReadTask"]) == 2

assert recommender.check_consistency()
print("一致性检查: PASS")

print("\n=== 实验完成 ===")
