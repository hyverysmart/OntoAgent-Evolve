
from ontology.agent_ontology import AgentOntology
from team_recommender import recommend_team


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

# 2. 任务需要三个能力
required = [
    "search_paper",
    "read_pdf",
    "write_report"
]

# 3. 第一次推荐
print("=== 更新前 ===")

team = recommend_team(ontology, required)

print("推荐团队:", team)


# 4. 新增 ResearchAgent
print("\n=== 新增 ResearchAgent ===")

ontology.add_agent(
    "ResearchAgent",
    ["search_paper", "read_pdf"]
)

team = recommend_team(ontology, required)

print("推荐团队:", team)


# 5. ResearchAgent 获得写报告能力
print("\n=== ResearchAgent 获得新能力 ===")

ontology.add_capability(
    "ResearchAgent",
    "write_report"
)

team = recommend_team(ontology, required)

print("推荐团队:", team)


# 6. ResearchAgent 失去 PDF 能力
print("\n=== ResearchAgent 失去 PDF 能力 ===")

ontology.remove_capability(
    "ResearchAgent",
    "read_pdf"
)

team = recommend_team(ontology, required)

print("推荐团队:", team)


print("\n=== 正确性检查 ===")

combined = set()

for agent in team:
    combined.update(
        ontology.get_capabilities(agent)
    )

correct = set(required).issubset(combined)

print("任务需要的能力:", sorted(required))
print("团队拥有的能力:", sorted(combined))
print("覆盖全部能力:", correct)
