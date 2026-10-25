
from ontology.agent_ontology import AgentOntology
from team_recommender import recommend_team
from optimized_team_recommender import (
    recommend_team_optimized
)


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

required = [
    "search_paper",
    "read_pdf",
    "write_report"
]


def compare(title):
    print(f"\n=== {title} ===")

    old_team = recommend_team(ontology, required)

    new_team = recommend_team_optimized(
        ontology, required
    )

    print("原始算法:", old_team)
    print("优化算法:", new_team)

    # 两种算法选出的团队人数必须一致
    assert len(old_team) == len(new_team)

    # 优化团队必须覆盖所有任务能力
    covered = set()

    for agent in new_team:
        covered.update(
            ontology.get_capabilities(agent)
        )

    assert set(required).issubset(covered)

    print("检查结果: PASS")

    return new_team


# 1. 初始状态
team_a = compare("初始状态")

# 2. ResearchAgent 新增 PDF 阅读能力
ontology.add_capability(
    "ResearchAgent", "read_pdf"
)

team_b = compare("新增 read_pdf")

# 3. ResearchAgent 失去 PDF 阅读能力
ontology.remove_capability(
    "ResearchAgent", "read_pdf"
)

team_c = compare("移除 read_pdf")


# 4. 验证团队人数变化
assert len(team_a) == 3
assert len(team_b) == 2
assert len(team_c) == 3

print("\n=== 全部测试通过 ===")
print("团队人数变化: 3 -> 2 -> 3")
