from services.executor_registry import ExecutorRegistry
from threading import Lock
from pathlib import Path
import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ontology.agent_ontology import AgentOntology
from incremental_recommender import IncrementalRecommender
from services.tool_registry import ToolRegistry
from services.auto_capability_sync import AutoCapabilitySync
from services.capability_sync import TOOL_CAPABILITIES
from services.state_store import (
    load_agents,
    save_agents,
    ONTOLOGY_FILE,
)


app = FastAPI(title="OntoAgent-Evolve API")
update_lock = Lock()

TASKS = {
    "SearchTask": ["search_paper"],
    "ReadTask": ["read_pdf"],
    "ResearchTask": ["search_paper", "read_pdf"],
    "ExplainTask": ["explain_concept"],
}

NAME_PATTERN = r"^[A-Za-z][A-Za-z0-9_]{0,49}$"


class ToolUpdateRequest(BaseModel):
    tools: list[str] = Field(max_length=20)


class AgentCreateRequest(ToolUpdateRequest):
    name: str = Field(
        min_length=1,
        max_length=50,
        pattern=NAME_PATTERN
    )


def build_system(saved_agents):
    """从工具配置恢复本体与推荐缓存。"""

    ontology = AgentOntology()
    registry = ToolRegistry()

    for name, tools in saved_agents.items():
        if not re.fullmatch(NAME_PATTERN, name):
            raise ValueError(f"非法 Agent 名称: {name}")

        if not isinstance(tools, list):
            raise ValueError(f"{name} 的工具配置无效")

        if len(tools) != len(set(tools)):
            raise ValueError(f"{name} 的工具重复")

        capabilities = set()

        for tool in tools:
            if tool not in TOOL_CAPABILITIES:
                raise ValueError(f"未知工具: {tool}")

            capabilities.update(TOOL_CAPABILITIES[tool])

        ontology.add_agent(name, sorted(capabilities))
        registry.register_agent(name, tools)

    for task_name, required in TASKS.items():
        ontology.add_task(task_name, required)

    recommender = IncrementalRecommender(ontology)
    recommender.initialize(list(TASKS))

    auto_sync = AutoCapabilitySync(
        registry, recommender
    )

    return ontology, registry, recommender, auto_sync


def restore():
    """重新读取已保存的数据。"""
    global ontology, registry, recommender, auto_sync

    ontology, registry, recommender, auto_sync = (
        build_system(load_agents())
    )


def persist():
    """保存配置，并导出本体快照。"""
    save_agents(registry.agent_tools)
    ontology.save(str(ONTOLOGY_FILE))


restore()
ontology.add_agent(
    "ExplainAgent",
    ["explain_concept"]
)

# 更新 ExplainTask 的推荐缓存
recommender.cache["ExplainTask"] = (
    ontology.recommend_task("ExplainTask")
)
executor_registry = ExecutorRegistry()

executor_registry.register(
    "ExplainAgent",
    "DIFY_EXECUTOR_API_KEY"
)

@app.get("/")
def home():
    return {
        "system": "OntoAgent-Evolve",
        "status": "running"
    }


@app.get("/agents")
def list_agents():
    with update_lock:
        return {
            "agents": sorted(registry.agent_tools)
        }


@app.get("/agents/{agent_name}")
def get_agent(agent_name: str):
    with update_lock:
        if agent_name not in registry.agent_tools:
            raise HTTPException(404, "Agent 不存在")

        return {
            "agent": agent_name,
            "tools": sorted(
                registry.agent_tools[agent_name]
            ),
            "capabilities": sorted(
                ontology.get_capabilities(agent_name)
            )
        }


@app.post("/agents", status_code=201)
def create_agent(request: AgentCreateRequest):
    with update_lock:
        if request.name in registry.agent_tools:
            raise HTTPException(409, "Agent 已经存在")

        if len(request.tools) != len(set(request.tools)):
            raise HTTPException(400, "工具名称不能重复")

        if any(
            tool not in TOOL_CAPABILITIES
            for tool in request.tools
        ):
            raise HTTPException(400, "包含未知工具")

        try:
            # 先创建没有能力的 Agent
            ontology.add_agent(request.name, [])
            registry.register_agent(request.name, [])

            # 使用 Dify 分析和验证工具变化
            changes = auto_sync.sync_agent(
                request.name,
                request.tools
            )

            persist()

        except Exception:
            # 从上一次保存的配置恢复内存状态
            restore()
            raise HTTPException(
                500, "注册失败，已尝试恢复之前的状态"
            )

        return {
            "agent": request.name,
            "changes": changes,
            "tools": sorted(request.tools),
            "capabilities": sorted(
                ontology.get_capabilities(request.name)
            )
        }


@app.post("/agents/{agent_name}/tools")
def update_agent_tools(
    agent_name: str,
    request: ToolUpdateRequest
):
    with update_lock:
        if agent_name not in registry.agent_tools:
            raise HTTPException(404, "Agent 不存在")

        if len(request.tools) != len(set(request.tools)):
            raise HTTPException(400, "工具名称不能重复")

        if any(
            tool not in TOOL_CAPABILITIES
            for tool in request.tools
        ):
            raise HTTPException(400, "包含未知工具")

        try:
            changes = auto_sync.sync_agent(
                agent_name,
                request.tools
            )

            persist()

        except Exception:
            restore()
            raise HTTPException(
                500, "同步失败，已尝试恢复之前的状态"
            )

        return {
            "agent": agent_name,
            "changes": changes,
            "tools": sorted(
                registry.agent_tools[agent_name]
            ),
            "capabilities": sorted(
                ontology.get_capabilities(agent_name)
            )
        }


@app.get("/recommend/{task_name}")
def get_recommendation(task_name: str):
    with update_lock:
        if task_name not in TASKS:
            raise HTTPException(404, "Task 不存在")

        return {
            "task": task_name,
            "required_capabilities": sorted(
                ontology.get_task_requirements(task_name)
            ),
            "recommendations": [
                {"agent": name, "score": score}
                for name, score in recommender.cache[task_name]
            ]
        }

class TaskExecuteRequest(BaseModel):
    task: str = Field(min_length=1, max_length=2000)
    task_type: str = "ExplainTask"


@app.post("/tasks/execute")
def execute_task(request: TaskExecuteRequest):

    # 1. 查询任务需要的能力，并推荐 Agent
    with update_lock:
        required = ontology.get_task_requirements(
            request.task_type
        )

        if not required:
            raise HTTPException(
                404, "任务类型不存在或没有能力需求"
            )

        recommendations = ontology.recommend_task(
            request.task_type
        )

        selected = None

        # 2. 选择满足全部能力要求的可执行 Agent
        for agent_name, score in recommendations:

            capabilities = ontology.get_capabilities(
                agent_name
            )

            if (
                required.issubset(capabilities)
                and executor_registry.is_available(agent_name)
            ):
                selected = agent_name
                break

    if selected is None:
        raise HTTPException(
            404, "没有合适的可执行 Agent"
        )

    # 3. 调用对应的 Dify Workflow
    try:
        answer = executor_registry.execute(
            selected,
            request.task
        )

    except Exception as error:
        print("执行失败:", type(error).__name__)

        raise HTTPException(
            502, "Agent 执行失败"
        )

    # 4. 返回结果
    return {
        "task": request.task,
        "selected_agent": selected,
        "capabilities": sorted(required),
        "answer": answer,
        "status": "completed"
    }

# 第十四阶段：模拟 Agent 能力变化

class CapabilityChangeRequest(BaseModel):
    action: str


@app.post("/demo/explain-agent/capability")
def change_explain_capability(
    request: CapabilityChangeRequest
):
    with update_lock:

        if request.action not in ["add", "remove"]:
            raise HTTPException(
                400, "action 只能是 add 或 remove"
            )

        agent = "ExplainAgent"
        capability = "explain_concept"

        # 查询修改前的能力
        before = ontology.get_capabilities(agent)

        # 避免重复修改
        if request.action == "add":
            if capability not in before:
                affected = recommender.update_capability(
                    agent, capability, "add"
                )
            else:
                affected = []

        else:
            if capability in before:
                affected = recommender.update_capability(
                    agent, capability, "remove"
                )
            else:
                affected = []

        # 查询修改后的能力
        after = ontology.get_capabilities(agent)

        # 与全量推荐结果比较
        consistent = all(
            recommender.cache[task]
            == ontology.recommend_task(task)
            for task in TASKS
        )

        return {
            "agent": agent,
            "action": request.action,
            "capabilities_before": sorted(before),
            "capabilities_after": sorted(after),
            "affected_tasks": affected,
            "recommendation_consistent": consistent
        }
