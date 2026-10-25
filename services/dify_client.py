
import os
import json
import requests

from dotenv import load_dotenv

load_dotenv()


ALLOWED_CAPABILITIES = {
    "search_paper",
    "read_pdf",
    "write_report",
    "translate",
    "analyze_data",
}


def extract_capabilities(agent_name, tool_description):
    api_key = os.getenv("DIFY_API_KEY")
    base_url = os.getenv("DIFY_BASE_URL")

    if not api_key or not base_url:
        raise ValueError("请检查 .env 中的 Dify 配置")

    url = base_url.rstrip("/") + "/workflows/run"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "inputs": {
            "agent_name": agent_name,
            "tool_description": tool_description,
        },
        "response_mode": "blocking",
        "user": "ontoagent-local-test",
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=90,
    )

    response.raise_for_status()
    result = response.json()

    data = result.get("data", {})

    if data.get("status") != "succeeded":
        raise RuntimeError(
            f"Dify 工作流失败: {data.get('error')}"
        )

    # 对应 Dify Output 节点中定义的 result
    output = data.get("outputs", {}).get("result")

    if isinstance(output, str):
        output = output.strip()

        # 兼容 LLM 返回 ```json ... ``` 的情况
        if output.startswith("```"):
            lines = output.splitlines()
            if lines[-1].strip() == "```":
                output = "\n".join(lines[1:-1])

        output = json.loads(output)

    if not isinstance(output, dict):
        raise ValueError("Dify 输出不是 JSON 对象")

    capabilities = output.get("capabilities")

    if not isinstance(capabilities, list):
        raise ValueError("缺少 capabilities 数组")

    if not all(
        isinstance(cap, str) and cap in ALLOWED_CAPABILITIES
        for cap in capabilities
    ):
        raise ValueError("存在未知或非法能力")

    return sorted(set(capabilities))
