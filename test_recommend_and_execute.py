
from ontology.agent_ontology import AgentOntology
from services.agent_executor import AgentExecutor

# 1. 创建演示本体
ontology = AgentOntology()

ontology.add_agent(
    "ResearchAgent",
    ["explain_concept"]
)

ontology.add_agent(
    "SearchAgent",
    ["search_paper"]
)

ontology.add_task(
    "ExplainTask",
    ["explain_concept"]
)

# 2. 推荐 Agent
recommendations = ontology.recommend_task(
    "ExplainTask"
)

print("推荐结果:", recommendations)

# 3. 选择满足全部能力要求的 Agent
required = ontology.get_task_requirements(
    "ExplainTask"
)

selected = None

for agent_name, score in recommendations:
    capabilities = ontology.get_capabilities(
        agent_name
    )

    if required.issubset(capabilities):
        selected = agent_name
        break

if selected is None:
    raise RuntimeError("没有满足任务能力要求的 Agent")

print("选择 Agent:", selected)

# 4. 映射到 Dify 执行器
if selected != "ResearchAgent":
    raise RuntimeError("尚未配置该 Agent 的执行器")

executor = AgentExecutor()

# 5. 真正执行任务
result = executor.execute(
    "请解释动态本体与传统静态本体的区别。"
)

print("\n=== 执行结果 ===")
print(result)
