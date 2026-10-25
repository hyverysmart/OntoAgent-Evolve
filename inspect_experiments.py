
import csv
from pathlib import Path


FILES = [
    "fair_benchmark.csv",
    "bottleneck_benchmark.csv",
    "three_methods_benchmark.csv",
    "ablation_benchmark.csv",
]

DATA_DIR = Path("experiments")


def inspect_csv(filename):
    path = DATA_DIR / filename

    print(f"\n{'=' * 50}")
    print("文件:", filename)

    if not path.exists():
        print("状态: 文件不存在")
        return

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            print("状态: CSV 为空")
            return

        print("列名:", reader.fieldnames)

        rows = list(reader)

        print("数据行数:", len(rows))

        print("\n前 3 行:")

        for row in rows[:3]:
            print(row)

        print("\n最后 1 行:")

        if rows:
            print(rows[-1])


def main():
    print("OntoAgent-Evolve 实验数据检查")

    for filename in FILES:
        inspect_csv(filename)

    print("\n检查结束")


if __name__ == "__main__":
    main()
