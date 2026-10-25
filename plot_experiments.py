
import csv
from pathlib import Path

import matplotlib.pyplot as plt


DATA_DIR = Path("experiments")
OUTPUT_DIR = DATA_DIR / "figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_csv(filename):
    with (DATA_DIR / filename).open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        return list(csv.DictReader(file))


def plot_scaling():
    rows = load_csv("fair_benchmark.csv")

    for group in ["AgentScaling", "TaskScaling"]:
        subset = [
            row for row in rows
            if row["group"] == group
        ]

        if not subset:
            continue

        x_key = "agents" if group == "AgentScaling" else "tasks"

        subset.sort(key=lambda row: int(row[x_key]))

        x = [int(row[x_key]) for row in subset]
        full = [float(row["full_mean_ms"]) for row in subset]
        incremental = [
            float(row["incremental_mean_ms"])
            for row in subset
        ]

        full_std = [
            float(row["full_std_ms"]) for row in subset
        ]
        incremental_std = [
            float(row["incremental_std_ms"])
            for row in subset
        ]

        plt.figure(figsize=(8, 5))

        plt.errorbar(
            x, full, yerr=full_std,
            marker="o", capsize=4,
            label="Full Recalculation"
        )

        plt.errorbar(
            x, incremental, yerr=incremental_std,
            marker="s", capsize=4,
            label="Incremental Update"
        )

        plt.xlabel(
            "Number of Agents"
            if group == "AgentScaling"
            else "Number of Tasks"
        )
        plt.ylabel("Mean Update Time (ms)")
        plt.title(group)
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()

        filename = (
            "figure1_agent_scaling.png"
            if group == "AgentScaling"
            else "figure1_task_scaling.png"
        )

        plt.savefig(
            OUTPUT_DIR / filename, dpi=200
        )
        plt.close()

        print("已生成:", filename)


def plot_ablation():
    row = load_csv("ablation_benchmark.csv")[0]

    names = [
        "A: Full + Baseline",
        "B: Incremental + Baseline",
        "D: Full + Optimized",
        "C: Incremental + Optimized"
    ]

    values = [
        float(row["A_full_baseline_ms"]),
        float(row["B_incremental_baseline_ms"]),
        float(row["D_full_optimized_ms"]),
        float(row["C_incremental_optimized_ms"])
    ]

    plt.figure(figsize=(9, 5))
    bars = plt.bar(names, values)

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{value:.2f}",
            ha="center"
        )

    plt.ylabel("Mean Update Time (ms)")
    plt.title("Ablation Study")
    plt.xticks(rotation=15, ha="right")
    plt.ylim(0, max(values) * 1.2)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "figure2_ablation.png",
        dpi=200
    )
    plt.close()

    print("已生成: figure2_ablation.png")


def plot_bottleneck():
    row = load_csv("bottleneck_benchmark.csv")[0]

    names = [
        "Affected-task Lookup",
        "Recommendation Recalculation"
    ]

    values = [
        float(row["lookup_mean_ms"]),
        float(row["recommendation_mean_ms"])
    ]

    plt.figure(figsize=(8, 4))
    bars = plt.barh(names, values)

    for bar, value in zip(bars, values):
        plt.text(
            value + max(values) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{value:.4f} ms",
            va="center"
        )

    plt.xlabel("Mean Time (ms)")
    plt.title("Incremental Update Bottleneck")
    plt.xlim(0, max(values) * 1.2)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "figure3_bottleneck.png",
        dpi=200
    )
    plt.close()

    print("已生成: figure3_bottleneck.png")


if __name__ == "__main__":
    plot_scaling()
    plot_ablation()
    plot_bottleneck()

    print("\n全部实验图表生成完成")
