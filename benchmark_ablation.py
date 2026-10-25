
import csv
import random
import statistics
import time
from pathlib import Path

from ontology.agent_ontology import AgentOntology
from team_recommender import recommend_team
from optimized_team_recommender import recommend_team_optimized


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

ALGORITHMS = {
    "A": recommend_team,
    "B": recommend_team,
    "C": recommend_team_optimized,
    "D": recommend_team_optimized
}


# ========== 2. 创建模拟数据 ==========

def create_data(seed):
    rng = random.Random(seed)
    ontology = AgentOntology()

    for i, capability in enumerate(CAPABILITIES):
        ontology.add_agent(
            f"BaseAgent{i}",
            [capability]
        )

    editable_agents = []

    for i in range(AGENT_COUNT - len(CAPABILITIES)):
        name = f"Agent{i}"

        capabilities = rng.sample(
            CAPABILITIES,
            rng.randint(1, 3)
        )

        ontology.add_agent(name, capabilities)
        editable_agents.append(name)

    tasks = {}

    for i in range(TASK_COUNT):
        tasks[f"Task{i}"] = rng.sample(
            CAPABILITIES,
            rng.randint(1, 3)
        )

    return ontology, tasks, editable_agents, rng


# ========== 3. 全量重算 ==========

def full_recompute(ontology, tasks, algorithm):
    return {
        name: algorithm(ontology, required)
        for name, required in tasks.items()
    }


# ========== 4. 增量重算 ==========

def incremental_recompute(
    ontology,
    tasks,
    cache,
    capability,
    algorithm
):
    affected = [
        name
        for name, required in tasks.items()
        if capability in required
    ]

    for name in affected:
        cache[name] = algorithm(
            ontology,
            tasks[name]
        )

    return len(affected)


# ========== 5. 验证推荐结果 ==========

def validate(ontology, tasks, results):
    for task_name, required in tasks.items():
        team = results[task_name]

        if not team or len(team) > 3:
            raise AssertionError(
                f"{task_name}: 推荐团队无效"
            )

        covered = set()

        for agent in team:
            covered.update(
                ontology.get_capabilities(agent)
            )

        if not set(required).issubset(covered):
            raise AssertionError(
                f"{task_name}: 能力覆盖失败"
            )


# ========== 6. 单个随机种子实验 ==========

def run_once(seed):
    ontology, tasks, agents, rng = create_data(seed)

    # 初始化两个增量算法的缓存
    cache_b = full_recompute(
        ontology, tasks, recommend_team
    )

    cache_c = full_recompute(
        ontology, tasks, recommend_team_optimized
    )

    times = {
        "A": [],
        "B": [],
        "C": [],
        "D": []
    }

    affected_ratios = []

    for event in range(CHANGES_PER_RUN):
        agent = rng.choice(agents)
        capability = rng.choice(CAPABILITIES)

        current = ontology.get_capabilities(agent)

        # 同一份 RDF 只修改一次
        if capability in current:
            ontology.remove_capability(agent, capability)
        else:
            ontology.add_capability(agent, capability)

        # A：全量 + 原始枚举
        def run_a():
            return full_recompute(
                ontology, tasks, recommend_team
            )

        # B：增量 + 原始枚举
        def run_b():
            return incremental_recompute(
                ontology, tasks, cache_b,
                capability, recommend_team
            )

        # C：增量 + 位掩码
        def run_c():
            return incremental_recompute(
                ontology, tasks, cache_c,
                capability, recommend_team_optimized
            )

        # D：全量 + 位掩码
        def run_d():
            return full_recompute(
                ontology, tasks, recommend_team_optimized
            )

        methods = [
            ("A", run_a),
            ("B", run_b),
            ("C", run_c),
            ("D", run_d)
        ]

        # 每轮改变执行顺序
        shift = event % 4
        methods = methods[shift:] + methods[:shift]

        outputs = {}

        for name, method in methods:
            start = time.perf_counter_ns()

            result = method()

            elapsed_ms = (
                time.perf_counter_ns() - start
            ) / 1_000_000

            times[name].append(elapsed_ms)
            outputs[name] = result

        result_a = outputs["A"]
        result_d = outputs["D"]

        # 原始算法的增量和全量结果要完全一致
        assert cache_b == result_a

        # 优化算法的增量和全量结果要完全一致
        assert cache_c == result_d

        # 不同搜索实现可以选择不同的同人数最优团队
        for task_name in tasks:
            assert len(result_a[task_name]) == len(
                result_d[task_name]
            ), f"{task_name}: 最优人数不一致"

        # 所有团队必须正确覆盖所需能力
        for results in (
            result_a,
            cache_b,
            cache_c,
            result_d
        ):
            validate(ontology, tasks, results)

        # 记录受影响任务比例
        affected = sum(
            capability in required
            for required in tasks.values()
        )

        affected_ratios.append(
            affected / len(tasks) * 100
        )

        print(
            f"seed={seed}, event={event + 1}: "
            "A/B/C/D PASS"
        )

    return {
        name: statistics.mean(times[name])
        for name in times
    } | {
        "affected_pct": statistics.mean(
            affected_ratios
        )
    }


# ========== 7. 多随机种子汇总 ==========

def main():
    runs = []

    for seed in SEEDS:
        print(f"\n=== 随机种子 {seed} ===")
        runs.append(run_once(seed))

    mean_times = {
        name: statistics.mean(
            run[name] for run in runs
        )
        for name in ALGORITHMS
    }

    a = mean_times["A"]
    b = mean_times["B"]
    c = mean_times["C"]
    d = mean_times["D"]

    print("\n=== 四算法消融实验结果 ===")

    print(f"A 全量原始: {a:.4f} ms")
    print(f"B 增量原始: {b:.4f} ms")
    print(f"C 增量优化: {c:.4f} ms")
    print(f"D 全量优化: {d:.4f} ms")

    print("\n=== 加速比 ===")
    print(f"增量作用（原始算法）A/B: {a / b:.3f}x")
    print(f"增量作用（优化算法）D/C: {d / c:.3f}x")
    print(f"位掩码作用（全量）A/D: {a / d:.3f}x")
    print(f"位掩码作用（增量）B/C: {b / c:.3f}x")
    print(f"综合加速 A/C: {a / c:.3f}x")

    result = {
        "agents": AGENT_COUNT,
        "tasks": TASK_COUNT,
        "seeds": len(SEEDS),
        "changes_per_seed": CHANGES_PER_RUN,
        "A_full_baseline_ms": round(a, 4),
        "B_incremental_baseline_ms": round(b, 4),
        "C_incremental_optimized_ms": round(c, 4),
        "D_full_optimized_ms": round(d, 4),
        "speedup_A_B": round(a / b, 3),
        "speedup_D_C": round(d / c, 3),
        "speedup_A_D": round(a / d, 3),
        "speedup_B_C": round(b / c, 3),
        "speedup_A_C": round(a / c, 3),
        "affected_pct": round(
            statistics.mean(
                run["affected_pct"] for run in runs
            ), 2
        ),
        "consistency": "PASS"
    }

    output = Path("experiments/ablation_benchmark.csv")
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
            fieldnames=result.keys()
        )
        writer.writeheader()
        writer.writerow(result)

    print("\n正确性: PASS")
    print("结果保存至:", output)


if __name__ == "__main__":
    main()
