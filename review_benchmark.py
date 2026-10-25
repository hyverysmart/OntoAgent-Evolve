
import csv
from pathlib import Path

DATA_DIR = Path("experiments")


def load_csv(filename):
    path = DATA_DIR / filename

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:
        return list(csv.DictReader(file))


def check_speedup(reported, calculated, tolerance=0.02):
    """允许 CSV 四舍五入造成的小误差"""
    return abs(float(reported) - calculated) < tolerance


def review_scaling():
    print("\n=== 1. 规模实验检查 ===")

    rows = load_csv("fair_benchmark.csv")

    all_passed = True

    for row in rows:
        full = float(row["full_mean_ms"])
        incremental = float(row["incremental_mean_ms"])

        full_std = float(row["full_std_ms"])
        incremental_std = float(row["incremental_std_ms"])

        calculated = full / incremental

        speedup_ok = check_speedup(
            row["speedup"], calculated
        )

        consistency_ok = row["consistency"] == "PASS"

        all_passed = (
            all_passed
            and speedup_ok
            and consistency_ok
        )

        print(
            f"{row['group']} | "
            f"Agents={row['agents']} | "
            f"Tasks={row['tasks']} | "
            f"加速比={calculated:.3f}x | "
            f"检查={'PASS' if speedup_ok and consistency_ok else 'FAIL'}"
        )

        # 变异系数 = 标准差 / 均值
        full_cv = full_std / full
        incremental_cv = incremental_std / incremental

        if full_cv > 0.20 or incremental_cv > 0.20:
            print(
                "  注意：运行时间波动较大，"
                f"全量 CV={full_cv:.1%}，"
                f"增量 CV={incremental_cv:.1%}"
            )

    print("规模实验记录检查:", "PASS" if all_passed else "FAIL")
    return all_passed


def review_ablation():
    print("\n=== 2. 消融实验检查 ===")

    rows = load_csv("ablation_benchmark.csv")

    all_passed = True

    for row in rows:
        a = float(row["A_full_baseline_ms"])
        b = float(row["B_incremental_baseline_ms"])
        c = float(row["C_incremental_optimized_ms"])
        d = float(row["D_full_optimized_ms"])

        comparisons = {
            "speedup_A_B": a / b,
            "speedup_D_C": d / c,
            "speedup_A_D": a / d,
            "speedup_B_C": b / c,
            "speedup_A_C": a / c
        }

        for name, calculated in comparisons.items():
            passed = check_speedup(
                row[name], calculated
            )

            all_passed = all_passed and passed

            print(
                f"{name}: {calculated:.3f}x | "
                f"{'PASS' if passed else 'FAIL'}"
            )

        all_passed = (
            all_passed and row["consistency"] == "PASS"
        )

    print("消融实验记录检查:", "PASS" if all_passed else "FAIL")
    return all_passed


def main():
    scaling_ok = review_scaling()
    ablation_ok = review_ablation()

    print("\n=== 最终检查 ===")

    if scaling_ok and ablation_ok:
        print("实验数据复核: PASS")
    else:
        print("实验数据复核: FAIL")


if __name__ == "__main__":
    main()
