
import csv
import random
import time
from pathlib import Path

from ontology.agent_ontology import AgentOntology
from incremental_team_recommender import (
    IncrementalTeamRecommender
)


# ========== 1. 实验配置 ==========

CAPABILITIES = [
    "search_paper",
    "read_pdf",
    "write_report",
    "explain_concept",
    "summarize_notes"
]

SCALES = [
    (12, 30),
    (20, 60),
    (30, 100)
]

CHANGE_COUNT = 10
SEED = 42


# ========== 2. 生成模拟数据 ==========

def create_experiment(agent_count, task_count):
    rng = random.Random(SEED)

    ontology = AgentOntology()

    # 先创建 5 个基础 Agent
    # 保证每种能力至少有一个 Agent 能执行
    for i, cap in enumerate(CAPABILITIES):
        ontology.add_agent(
            f"BaseAgent{i}",
            [cap]
        )

    # 创建其他 Agent
    for i in range(agent_count - len(CAPABILITIES)):
        caps = rng.sample(
            CAPABILITIES,
            rng.randint(1, 3)
        )

        ontology.add_agent(
            f"Agent{i}",
            caps
        )

    # 创建任务，每个任务需要 1 到 3 种能力
    tasks = {}

    for i in range(task_count):
        required = rng.sample(
            CAPABILITIES,
            rng.randint(1, 3)
        )

        tasks[f"Task{i}"] = required

    return ontology, tasks, rng


# ========== 3. 运行单组实验 ==========

def run_experiment(agent_count, task_count):
    ontology, tasks, rng = create_experiment(
        agent_count,
        task_count
    )

    recommender = IncrementalTeamRecommender(
        ontology,
        tasks
    )

    # 初始化推荐缓存（不计入更新耗时）
    recommender.initialize()

    incremental_times = []
    full_times = []
    affected_counts = []

    # 只修改普通 Agent，不修改保底基础 Agent
    editable_agents = [
        f"Agent{i}"
        for i in range(agent_count - len(CAPABILITIES))
    ]

    for change_id in range(1, CHANGE_COUNT + 1):

        agent = rng.choice(editable_agents)
        capability = rng.choice(CAPABILITIES)

        current = ontology.get_capabilities(agent)

        action = (
            "remove"
            if capability in current
            else "add"
        )

        # 1. 测量增量更新
        start = time.perf_counter_ns()

        affected = recommender.update_capability(
            agent,
            capability,
            action
        )

        incremental_ns = (
            time.perf_counter_ns() - start
        )

        # 2. 在相同的本体状态下测量全量重算
        start = time.perf_counter_ns()

        full_results = recommender.full_recompute()

        full_ns = time.perf_counter_ns() - start

        # 3. 正确性验证
        if recommender.cache != full_results:
            raise AssertionError(
                f"第 {change_id} 次能力变化结果不一致"
            )

        incremental_times.append(
            incremental_ns / 1_000_000
        )

        full_times.append(
            full_ns / 1_000_000
        )

        affected_counts.append(len(affected))

        print(
            f"变化 {change_id}: "
            f"{agent} {action} {capability}, "
            f"受影响任务 {len(affected)}, PASS"
        )

    # 4. 计算平均值
    avg_inc = sum(incremental_times) / CHANGE_COUNT
    avg_full = sum(full_times) / CHANGE_COUNT
    avg_affected = sum(affected_counts) / CHANGE_COUNT

    speedup = (
        avg_full / avg_inc
        if avg_inc > 0 else 0
    )

    return {
        "agents": agent_count,
        "tasks": task_count,
        "changes": CHANGE_COUNT,
        "avg_full_ms": round(avg_full, 4),
        "avg_incremental_ms": round(avg_inc, 4),
        "avg_affected_tasks": round(avg_affected, 2),
        "speedup": round(speedup, 2),
        "consistency": "PASS"
    }


# ========== 4. 运行所有规模 ==========

def main():
    results = []

    for agents, tasks in SCALES:
        print(
            f"\n=== 实验: {agents} Agents, "
            f"{tasks} Tasks ==="
        )

        result = run_experiment(agents, tasks)
        results.append(result)

        print("全量平均耗时:", result["avg_full_ms"], "ms")
        print(
            "增量平均耗时:",
            result["avg_incremental_ms"], "ms"
        )
        print("平均受影响任务:", result["avg_affected_tasks"])
        print("加速比:", result["speedup"], "x")

    # ========== 5. 保存实验结果 ==========

    output_dir = Path("experiments")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "team_benchmark.csv"

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(results[0].keys())
        )

        writer.writeheader()
        writer.writerows(results)

    print("\n=== 全部实验完成 ===")
    print("实验结果:", output_path)


if __name__ == "__main__":
    main()
