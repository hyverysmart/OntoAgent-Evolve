
import sys
from pathlib import Path
from time import perf_counter_ns

# 让 Python 能找到项目根目录的模块
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ontology.agent_ontology import AgentOntology
from incremental_recommender import IncrementalRecommender


# 1. 创建本体
ontology = AgentOntology()

capabilities = [
    "search_paper",
    "read_pdf",
    "write_report",
    "translate",
    "analyze_data",
]

# 2. 创建 40 个 Agent
for i in range(40):
    name = f"Agent{i:02d}"
    capability = capabilities[i % len(capabilities)]
    ontology.add_agent(name, [capability])

# 3. 创建 100 个 Task
tasks = []

for i in range(100):
    name = f"Task{i:03d}"
    requirement = capabilities[i % len(capabilities)]

    ontology.add_task(name, [requirement])
    tasks.append(name)

# 4. 初始化增量推荐缓存
recommender = IncrementalRecommender(ontology)
recommender.initialize(tasks)

# 5. 设计 10 次能力变化
events = [
    ("Agent00", "read_pdf", "add"),
    ("Agent01", "write_report", "add"),
    ("Agent02", "translate", "add"),
    ("Agent03", "analyze_data", "add"),
    ("Agent04", "search_paper", "add"),
    ("Agent00", "read_pdf", "remove"),
    ("Agent01", "write_report", "remove"),
    ("Agent02", "translate", "remove"),
    ("Agent03", "analyze_data", "remove"),
    ("Agent04", "search_paper", "remove"),
]

print("=== OntoAgent-Evolve 性能实验 ===")
print("Agent 数量: 40")
print("Task 数量: 100")
print("能力变化次数: 10")

full_times = []
incremental_times = []
all_consistent = True

for i, (agent, capability, action) in enumerate(events, 1):

    # A. 先进行增量更新
    affected = recommender.update_capability(
        agent, capability, action
    )

    incremental_ms = recommender.last_recompute_ns / 1_000_000

    # B. 在同一个更新后的本体状态上全量重算
    start = perf_counter_ns()

    full_results = {
        task: ontology.recommend_task(task)
        for task in tasks
    }

    full_ms = (perf_counter_ns() - start) / 1_000_000

    # C. 比较全部任务的推荐结果
    consistent = full_results == recommender.cache

    full_times.append(full_ms)
    incremental_times.append(incremental_ms)
    all_consistent = all_consistent and consistent

    print(f"\n第 {i} 次能力变化")
    print(f"Agent: {agent}")
    print(f"操作: {action} {capability}")
    print(f"受影响任务数: {len(affected)}")
    print(f"全量重算: {full_ms:.4f} ms")
    print(f"增量重算: {incremental_ms:.4f} ms")
    print(f"推荐结果一致: {consistent}")

# 6. 计算平均时间
avg_full = sum(full_times) / len(full_times)
avg_incremental = sum(incremental_times) / len(incremental_times)

print("\n=== 实验总结 ===")
print(f"平均全量重算: {avg_full:.4f} ms")
print(f"平均增量重算: {avg_incremental:.4f} ms")

if avg_incremental > 0:
    speedup = avg_full / avg_incremental
    print(f"重算阶段加速比: {speedup:.2f}x")

print(f"全部推荐结果一致: {all_consistent}")
