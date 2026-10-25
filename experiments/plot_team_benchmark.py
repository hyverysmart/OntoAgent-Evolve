
import csv
from pathlib import Path
import matplotlib.pyplot as plt


# 1. 定位实验数据
DATA_DIR = Path(__file__).resolve().parent
csv_path = DATA_DIR / "team_benchmark.csv"

if not csv_path.exists():
    raise FileNotFoundError(
        "找不到 team_benchmark.csv，"
        "请先运行 benchmark_team.py"
    )


# 2. 读取 CSV
with csv_path.open(
    "r",
    encoding="utf-8-sig",
    newline=""
) as file:
    rows = list(csv.DictReader(file))

if not rows:
    raise ValueError("CSV 文件没有实验数据")


# 3. 转换数据类型
agent_counts = [int(r["agents"]) for r in rows]
task_counts = [int(r["tasks"]) for r in rows]

full_times = [
    float(r["avg_full_ms"]) for r in rows
]

incremental_times = [
    float(r["avg_incremental_ms"]) for r in rows
]

speedups = [
    full / inc if inc > 0 else 0
    for full, inc in zip(full_times, incremental_times)
]

affected_ratios = [
    float(r["avg_affected_tasks"]) / int(r["tasks"]) * 100
    for r in rows
]


# 4. 使用 Agent 和 Task 数量作为横轴标签
labels = [
    f"{a}A / {t}T"
    for a, t in zip(agent_counts, task_counts)
]


# 5. 图一：运行时间对比
plt.figure(figsize=(8, 5))

plt.plot(
    labels,
    full_times,
    marker="o",
    label="Full recomputation"
)

plt.plot(
    labels,
    incremental_times,
    marker="s",
    label="Incremental update"
)

plt.xlabel("Experiment Scale (Agents / Tasks)")
plt.ylabel("Average Time (ms)")
plt.title("Full vs Incremental Team Recommendation")

plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(
    DATA_DIR / "time_comparison.png",
    dpi=200
)

plt.close()


# 6. 图二：加速比
plt.figure(figsize=(8, 5))

plt.bar(labels, speedups)

plt.axhline(1, linestyle="--", label="No speedup")

plt.xlabel("Experiment Scale (Agents / Tasks)")
plt.ylabel("Speedup (x)")
plt.title("Incremental Recommendation Speedup")

plt.legend()
plt.tight_layout()

plt.savefig(
    DATA_DIR / "speedup.png",
    dpi=200
)

plt.close()


# 7. 图三：受影响任务比例
plt.figure(figsize=(8, 5))

plt.bar(labels, affected_ratios)

plt.xlabel("Experiment Scale (Agents / Tasks)")
plt.ylabel("Affected Tasks (%)")
plt.title("Percentage of Affected Tasks")
plt.ylim(0, 100)

plt.tight_layout()

plt.savefig(
    DATA_DIR / "affected_tasks.png",
    dpi=200
)

plt.close()


# 8. 输出实验数据
print("\n=== 实验结果汇总 ===")

for i in range(len(rows)):
    print(f"\n规模: {labels[i]}")
    print(f"全量耗时: {full_times[i]:.4f} ms")
    print(f"增量耗时: {incremental_times[i]:.4f} ms")
    print(f"加速比: {speedups[i]:.2f}x")
    print(f"受影响任务比例: {affected_ratios[i]:.2f}%")

    assert rows[i]["consistency"] == "PASS"

print("\n一致性检查: 全部 PASS")
print("已生成 3 张实验图表")
