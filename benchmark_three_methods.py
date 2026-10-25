
import csv
import random
import statistics
import time
from pathlib import Path

from ontology.agent_ontology import AgentOntology
from team_recommender import recommend_team
from optimized_team_recommender import (
    recommend_team_optimized
)


# ========== 1. 实验配置 ==========

CAPABILITIES = [
    "search_paper",
    "read_pdf",
    "write_report",
    "explain_concept",
    "summarize_notes"
]

AGENT_COUNT = 20
TASK_COUNT = 100

SEEDS = [42, 123, 2026]
CHANGES_PER_RUN = 10


# ========== 2. 生成实验数据 ==========

def create_data(seed):
    rng = random.Random(seed)
    ontology = AgentOntology()

    # 基础 Agent 保证每种能力都有提供者
    for i, cap in enumerate(CAPABILITIES):
        ontology.add_agent(
            f"BaseAgent{i}", [cap]
        )

    editable_agents = []

    for i in range(AGENT_COUNT - len(CAPABILITIES)):
        name = f"Agent{i}"

        caps = rng.sample(
            CAPABILITIES,
            rng.randint(1, 3)
        )

        ontology.add_agent(name, caps)
        editable_agents.append(name)

    tasks = {}

    for i in range(TASK_COUNT):
        tasks[f"Task{i}"] = rng.sample(
            CAPABILITIES,
            rng.randint(1, 3)
        )

    return ontology, tasks, editable_agents, rng


# ========== 3. 三种推荐算法 ==========

def full_baseline(ontology, tasks):
    """A：全量计算所有任务"""

    return {
        name: recommend_team(ontology, required)
        for name, required in tasks.items()
    }


def incremental_update(
    ontology, tasks, cache, changed_capability,
    algorithm
):
    """B/C：只更新受影响任务"""

    affected = [
        name
        for name, required in tasks.items()
        if changed_capability in required
    ]

    for name in affected:
        cache[name] = algorithm(
            ontology, tasks[name]
        )

    return len(affected)


# ========== 4. 检查推荐正确性 ==========

def validate_results(ontology, tasks, results):
    for task_name, required in tasks.items():
        team = results[task_name]

        if not team:
            raise AssertionError(
                f"{task_name}: 没有推荐团队"
            )

        if len(team) > 3:
            raise AssertionError(
                f"{task_name}: 团队人数超过限制"
            )

        covered = set()

        for agent in team:
            covered.update(
                ontology.get_capabilities(agent)
            )

        if not set(required).issubset(covered):
            raise AssertionError(
                f"{task_name}: 能力覆盖不完整"
            )


# ========== 5. 单次实验 ==========

def run_once(seed):
    ontology, tasks, agents, rng = create_data(seed)

    # 分别维护 B、C 的推荐缓存
    # 初始化不计入能力变化后的更新时间
    cache_b = full_baseline(ontology, tasks)

    cache_c = {
        name: recommend_team_optimized(
            ontology, required
        )
        for name, required in tasks.items()
    }

    # 检查初始结果
    validate_results(ontology, tasks, cache_b)
    validate_results(ontology, tasks, cache_c)

    times_a = []
    times_b = []
    times_c = []
    affected_ratios = []

    for event in range(CHANGES_PER_RUN):
        agent = rng.choice(agents)
        capability = rng.choice(CAPABILITIES)

        current = ontology.get_capabilities(agent)

        # 同一份 RDF：只更新一次
        if capability in current:
            ontology.remove_capability(
                agent, capability
            )
            action = "remove"
        else:
            ontology.add_capability(
                agent, capability
            )
            action = "add"

        # 三种方法都在同一个更新后的状态运行
        def measure_a():
            start = time.perf_counter_ns()
            result = full_baseline(ontology, tasks)
            elapsed = time.perf_counter_ns() - start
            return elapsed / 1_000_000, result

        def measure_b():
            start = time.perf_counter_ns()

            count = incremental_update(
                ontology, tasks, cache_b,
                capability, recommend_team
            )

            elapsed = time.perf_counter_ns() - start
            return elapsed / 1_000_000, count

        def measure_c():
            start = time.perf_counter_ns()

            count = incremental_update(
                ontology, tasks, cache_c,
                capability, recommend_team_optimized
            )

            elapsed = time.perf_counter_ns() - start
            return elapsed / 1_000_000, count

        # 轮换算法执行顺序，减少固定顺序影响
        methods = [("A", measure_a),
                   ("B", measure_b),
                   ("C", measure_c)]

        rotation = event % 3
        methods = methods[rotation:] + methods[:rotation]

        measurements = {}

        for label, method in methods:
            measurements[label] = method()

        a_ms, result_a = measurements["A"]
        b_ms, affected_b = measurements["B"]
        c_ms, affected_c = measurements["C"]

        assert affected_b == affected_c

        # A 与 B 使用同一推荐算法，要求完全一致
        assert cache_b == result_a, (
            f"A/B 不一致: seed={seed}, event={event}"
        )

        # C 允许不同的最优平局团队
        # 但要求团队人数与 A 相同
        for task_name in tasks:
            assert len(cache_c[task_name]) == len(
                result_a[task_name]
            ), (
                f"A/C 人数不一致: "
                f"seed={seed}, event={event}, "
                f"task={task_name}"
            )

        validate_results(ontology, tasks, cache_c)

        times_a.append(a_ms)
        times_b.append(b_ms)
        times_c.append(c_ms)

        affected_ratios.append(
            affected_b / len(tasks) * 100
        )

        print(
            f"Seed {seed}, event {event + 1}: "
            f"{agent} {action} {capability} | "
            f"A={a_ms:.2f}, "
            f"B={b_ms:.2f}, "
            f"C={c_ms:.2f} ms | PASS"
        )

    return {
        "a": statistics.mean(times_a),
        "b": statistics.mean(times_b),
        "c": statistics.mean(times_c),
        "affected": statistics.mean(affected_ratios)
    }


# ========== 6. 多随机种子实验 ==========

def main():
    runs = []

    for seed in SEEDS:
        runs.append(run_once(seed))

    a = statistics.mean(r["a"] for r in runs)
    b = statistics.mean(r["b"] for r in runs)
    c = statistics.mean(r["c"] for r in runs)

    print("\n=== 三种算法对比结果 ===")
    print(f"A 全量原始: {a:.4f} ms")
    print(f"B 增量原始: {b:.4f} ms")
    print(f"C 增量优化: {c:.4f} ms")

    print(f"\n增量加速 A/B: {a / b:.3f}x")
    print(f"算法优化 B/C: {b / c:.3f}x")
    print(f"综合加速 A/C: {a / c:.3f}x")

    print("正确性: PASS")

    result = {
        "agents": AGENT_COUNT,
        "tasks": TASK_COUNT,
        "seeds": len(SEEDS),
        "changes_per_seed": CHANGES_PER_RUN,
        "full_baseline_ms": round(a, 4),
        "incremental_baseline_ms": round(b, 4),
        "incremental_optimized_ms": round(c, 4),
        "incremental_speedup": round(a / b, 3),
        "optimization_speedup": round(b / c, 3),
        "combined_speedup": round(a / c, 3),
        "affected_pct": round(
            statistics.mean(r["affected"] for r in runs),
            2
        ),
        "consistency": "PASS"
    }

    output = Path(
        "experiments/three_methods_benchmark.csv"
    )
    output.parent.mkdir(
        parents=True, exist_ok=True
    )

    with output.open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=result.keys()
        )
        writer.writeheader()
        writer.writerow(result)

    print("\n结果保存至:", output)


if __name__ == "__main__":
    main()
