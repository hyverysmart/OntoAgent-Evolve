
import subprocess
import sys
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run_script(filename):
    """使用当前 Python 环境运行脚本"""
    subprocess.run(
        [sys.executable, str(ROOT / filename)],
        cwd=ROOT,
        check=True
    )


def main():
    print("\n=== OntoAgent-Evolve ===")
    print("1. Run Performance Experiment")
    print("2. Run System Demo")
    print("3. Run E2E Test")
    print("0. Exit")

    choice = input("\nSelect an option: ").strip()

    if choice == "1":
        run_script("benchmark_ablation.py")

    elif choice == "2":
        print("Starting FastAPI...")
        print("Open http://127.0.0.1:8001/docs")

        webbrowser.open(
            "http://127.0.0.1:8001/docs"
        )

        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "services.dynamic_api:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8001"
            ],
            cwd=ROOT
        )

    elif choice == "3":
        run_script("test_system_e2e.py")

    elif choice == "0":
        print("Exiting...")

    else:
        print("Invalid option")


if __name__ == "__main__":
    main()
