
from ontology.agent_ontology import AgentOntology
from team_recommender import recommend_team
from workflow_runner import execute_team


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

required = [
    "search_paper",
    "read_pdf",
    "write_report"
]

task = "ontology-based multi-agent systems"


def run_test(title):
    print(f"\n========== {title} ==========")

    team = recommend_team(ontology, required)

    print("推荐团队:", team)

    if not team:
        print("没有能够完成任务的团队")
        return

    result = execute_team(ontology, team, task)

    print("\n最终结果:")
    print(result)


# 2. 初始团队
run_test("初始状态")


# 3. 新 Agent 加入
ontology.add_agent(
    "ResearchAgent",
    ["search_paper", "read_pdf"]
)

run_test("ResearchAgent 加入")


# 4. Agent 获得新能力
ontology.add_capability(
    "ResearchAgent",
    "write_report"
)

run_test("ResearchAgent 获得报告能力")


# 5. Agent 失去能力
ontology.remove_capability(
    "ResearchAgent",
    "read_pdf"
)

run_test("ResearchAgent 失去 PDF 能力")
