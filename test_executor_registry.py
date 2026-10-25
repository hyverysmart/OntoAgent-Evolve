
from ontology.agent_ontology import AgentOntology
from services.executor_registry import ExecutorRegistry


# 1. 创建本体
ontology = AgentOntology()

ontology.add_agent(
    "ExplainAgent",
    ["explain_concept"]
)

ontology.add_agent(
    "SearchAgent",
    ["search_paper"]
)

# 2. 创建任务
ontology.add_task(
    "ExplainTask",
    ["explain_concept"]
)

# 3. 创建执行器注册表
registry = ExecutorRegistry()

# ExplainAgent 绑定 Dify Workflow
registry.register(
    "ExplainAgent",
    "DIFY_EXECUTOR_API_KEY"
)

# 4. 通过本体选择 Agent
recommendations = ontology.recommend_task(
    "ExplainTask"
)

required = ontology.get_task_requirements(
    "ExplainTask"
)

selected = None

for agent_name, score in recommendations:
    capabilities = ontology.get_capabilities(
        agent_name
    )

    if (
        required.issubset(capabilities)
        and registry.is_available(agent_name)
    ):
        selected = agent_name
        break

if selected is None:
    raise RuntimeError("没有符合要求的可执行 Agent")

print("推荐 Agent:", selected)

# 5. 调用注册表执行任务
task = "请简单解释动态本体是什么。"

answer = registry.execute(selected, task)

print("\n=== Dify 执行结果 ===")
print(answer)
