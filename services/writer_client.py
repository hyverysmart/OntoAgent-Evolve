
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def generate_report(paper_title, paper_text):
    # 1. 读取 WriterAgent API Key
    api_key = os.getenv("DIFY_WRITER_API_KEY")

    if not api_key:
        raise ValueError("缺少 DIFY_WRITER_API_KEY")

    base_url = os.getenv(
        "DIFY_BASE_URL",
        "https://api.dify.ai/v1"
    ).rstrip("/")

    # 2. 构造 Dify 请求
    url = base_url + "/workflows/run"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {
            "paper_title": paper_title,
            "paper_text": paper_text[:8000]
        },
        "response_mode": "blocking",
        "user": "ontoagent-writer"
    }

    # 3. 发送请求
    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=120
    )

    if response.status_code != 200:
        print("\n=== Dify 返回的错误详情 ===")
        print("状态码:", response.status_code)
        print("错误内容:", response.text[:1000])
        response.raise_for_status()

    # 4. 检查工作流执行结果
    data = response.json().get("data", {})

    if data.get("status") != "succeeded":
        raise RuntimeError(
            f"WriterAgent 执行失败: {data.get('error')}"
        )

    report = data.get("outputs", {}).get("report")

    if not isinstance(report, str) or not report.strip():
        raise ValueError("Dify 未返回有效的 report")

    return report
