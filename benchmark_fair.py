
import csv
import random
import statistics
import time
from pathlib import Path

from ontology.agent_ontology import AgentOntology
from incremental_team_recommender import IncrementalTeamRecommender
from team_recommender import recommend_team


# ========== 1. 实验配置 ==========

CAPABILITIES = [
    "search_paper",
    "read_pdf",
    "write_report",
    "explain_concept",
    "summarize_notes"
]

# 先测试一个规模
EXPERIMENTS = [
    ("TaskScaling", 20, 100)
]

SEEDS = [42, 123, 2026]
CHANGES_PER_RUN = 10


# ========== 2. 创建模拟数据 ==========

def create_data(agent_count, task_count, seed):
    rng = random.Random(seed)
    ontology = AgentOntology()

    # 创建基础 Agent
    for i, cap in enumerate(CAPABILITIES):
        ontology.add_agent(
            f"BaseAgent{i}",
            [cap]
        )

    editable_agents = []

    # 创建普通 Agent
    for i in range(agent_count - len(CAPABILITIES)):
        name = f"Agent{i}"

        caps = rng.sample(
            CAPABILITIES,
            rng.randint(1, 3)
        )

        ontology.add_agent(name, caps)
        editable_agents.append(name)

    # 创建任务
    tasks = {}

    for i in range(task_count):
        tasks[f"Task{i}"] = rng.sample(
            CAPABILITIES,
            rng.randint(1, 3)
        )

    return ontology, tasks, editable_agents, rng


# ========== 3. 增量团队推荐 ==========

def incremental_recompute(
    recommender, changed_capability
):
    # 第一步：测量受影响任务查询时间
    start = time.perf_counter_ns()

    affected = [
        name
        for name, required in recommender.tasks.items()
        if changed_capability in required
    ]

    lookup_ms = (
        time.perf_counter_ns() - start
    ) / 1_000_000

    # 第二步：测量团队重新推荐时间
    start = time.perf_counter_ns()

    for name in affected:
        recommender.cache[name] = recommend_team(
            recommender.ontology,
            recommender.tasks[name]
        )

    recommendation_ms = (
        time.perf_counter_ns() - start
    ) / 1_000_000

    return (
        len(affected),
        lookup_ms,
        recommendation_ms
    )


# ========== 4. 单次规模实验 ==========

def run_once(agent_count, task_count, seed):
    ontology, tasks, agents, rng = create_data(
        agent_count,
        task_count,
        seed
    )

    recommender = IncrementalTeamRecommender(
        ontology,
        tasks
    )

    # 初始化缓存，不计入更新耗时
    recommender.initialize()

    full_times = []
    incremental_times = []
    affected_ratios = []

    lookup_times = []
    recommendation_times = []

    # 模拟多次 Agent 能力变化
    for event in range(CHANGES_PER_RUN):

        agent = rng.choice(agents)
        capability = rng.choice(CAPABILITIES)

        current = ontology.get_capabilities(agent)

        # 更新 RDF 本体
        if capability in current:
            ontology.remove_capability(
                agent,
                capability
            )
        else:
            ontology.add_capability(
                agent,
                capability
            )

        # 测量增量推荐
        def measure_incremental():
            start = time.perf_counter_ns()

            count, lookup_ms, recommendation_ms = (
                incremental_recompute(
                    recommender,
                    capability
                )
            )

            elapsed = (
                time.perf_counter_ns() - start
            ) / 1_000_000

            lookup_times.append(lookup_ms)
            recommendation_times.append(
                recommendation_ms
            )

            return elapsed, count

        # 测量全量推荐
        def measure_full():
            start = time.perf_counter_ns()

            results = recommender.full_recompute()

            elapsed = (
                time.perf_counter_ns() - start
            ) / 1_000_000

            return elapsed, results

        # 交替测试执行顺序
        if event % 2 == 0:
            inc_ms, affected = measure_incremental()
            full_ms, full_result = measure_full()
        else:
            full_ms, full_result = measure_full()
            inc_ms, affected = measure_incremental()

        # 检查增量结果与全量结果一致
        assert recommender.cache == full_result, (
            f"一致性失败: seed={seed}, event={event}"
        )

        full_times.append(full_ms)
        incremental_times.append(inc_ms)

        affected_ratios.append(
            affected / task_count * 100
        )

    # 返回当前随机种子的平均结果
    return {
        "full_ms": statistics.mean(full_times),

        "incremental_ms": statistics.mean(
            incremental_times
        ),

        "affected_pct": statistics.mean(
            affected_ratios
        ),

        "lookup_ms": statistics.mean(
            lookup_times
        ),

        "recommendation_ms": statistics.mean(
            recommendation_times
        )
    }


# ========== 5. 多个随机种子重复实验 ==========

def run_scale(group, agents, tasks):
    runs = []

    for seed in SEEDS:
        print(
            f"\n运行 {group}: "
            f"{agents} Agents / {tasks} Tasks, "
            f"seed={seed}"
        )

        result = run_once(
            agents,
            tasks,
            seed
        )

        runs.append(result)

    full = [
        r["full_ms"]
        for r in runs
    ]

    incremental = [
        r["incremental_ms"]
        for r in runs
    ]

    full_mean = statistics.mean(full)
    inc_mean = statistics.mean(incremental)

    lookup_mean = statistics.mean(
        r["lookup_ms"] for r in runs
    )

    recommendation_mean = statistics.mean(
        r["recommendation_ms"] for r in runs
    )

    return {
        "group": group,
        "agents": agents,
        "tasks": tasks,

        "repetitions": len(SEEDS),
        "changes_per_run": CHANGES_PER_RUN,

        "full_mean_ms": round(
            full_mean, 4
        ),

        "incremental_mean_ms": round(
            inc_mean, 4
        ),

        "full_std_ms": round(
            statistics.stdev(full), 4
        ),

        "incremental_std_ms": round(
            statistics.stdev(incremental), 4
        ),

        "lookup_mean_ms": round(
            lookup_mean, 4
        ),

        "recommendation_mean_ms": round(
            recommendation_mean, 4
        ),

        "affected_pct": round(
            statistics.mean(
                r["affected_pct"] for r in runs
            ), 2
        ),

        "speedup": round(
            full_mean / inc_mean, 3
        ),

        "consistency": "PASS"
    }


# ========== 6. 运行实验并保存 CSV ==========

def main():
    results = []

    for group, agents, tasks in EXPERIMENTS:

        result = run_scale(
            group,
            agents,
            tasks
        )

        results.append(result)

        print("\n=== 当前实验结果 ===")

        print(
            "全量平均耗时:",
            result["full_mean_ms"],
            "ms"
        )

        print(
            "增量平均耗时:",
            result["incremental_mean_ms"],
            "ms"
        )

        print(
            "受影响任务查询:",
            result["lookup_mean_ms"],
            "ms"
        )

        print(
            "团队重新推荐:",
            result["recommendation_mean_ms"],
            "ms"
        )

        print(
            "加速比:",
            result["speedup"],
            "x"
        )

        print(
            "一致性:",
            result["consistency"]
        )

    # 保存新文件，不覆盖旧实验结果
    output = Path(
        "experiments/bottleneck_benchmark.csv"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output.open(
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
    print("文件:", output)


if __name__ == "__main__":
    main()
