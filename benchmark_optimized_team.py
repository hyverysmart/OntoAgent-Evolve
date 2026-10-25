
import random
import statistics
import time

from ontology.agent_ontology import AgentOntology
from team_recommender import recommend_team
from optimized_team_recommender import (
    recommend_team_optimized
)


CAPABILITIES = [
    "search_paper",
    "read_pdf",
    "write_report",
    "explain_concept",
    "summarize_notes"
]

AGENT_COUNT = 20
TASK_COUNT = 100
REPEATS = 5

rng = random.Random(42)

ontology = AgentOntology()

# 创建模拟 Agent
for i in range(AGENT_COUNT):
    caps = rng.sample(
        CAPABILITIES,
        rng.randint(1, 3)
    )

    ontology.add_agent(f"Agent{i}", caps)

# 创建模拟任务
tasks = [
    rng.sample(
        CAPABILITIES,
        rng.randint(1, 3)
    )
    for _ in range(TASK_COUNT)
]


def run_algorithm(algorithm):
    start = time.perf_counter_ns()

    results = [
        algorithm(ontology, required)
        for required in tasks
    ]

    elapsed = (
        time.perf_counter_ns() - start
    ) / 1_000_000

    return elapsed, results


# 预热，减少首次执行偏差
run_algorithm(recommend_team)
run_algorithm(recommend_team_optimized)

old_times = []
new_times = []

for i in range(REPEATS):

    if i % 2 == 0:
        old_ms, old_results = run_algorithm(recommend_team)
        new_ms, new_results = run_algorithm(
            recommend_team_optimized
        )
    else:
        new_ms, new_results = run_algorithm(
            recommend_team_optimized
        )
        old_ms, old_results = run_algorithm(recommend_team)

    # 检查最少人数是否一致
    for required, old, new in zip(
        tasks, old_results, new_results
    ):
        assert len(old) == len(new)

        if new:
            covered = set()

            for agent in new:
                covered.update(
                    ontology.get_capabilities(agent)
                )

            assert set(required).issubset(covered)

    old_times.append(old_ms)
    new_times.append(new_ms)

    print(
        f"第 {i + 1} 轮: "
        f"原始 {old_ms:.3f} ms, "
        f"优化 {new_ms:.3f} ms"
    )


old_mean = statistics.mean(old_times)
new_mean = statistics.mean(new_times)

print("\n=== 性能测试结果 ===")
print(f"原始算法平均耗时: {old_mean:.4f} ms")
print(f"优化算法平均耗时: {new_mean:.4f} ms")
print(f"加速比: {old_mean / new_mean:.3f}x")
print("正确性: PASS")
