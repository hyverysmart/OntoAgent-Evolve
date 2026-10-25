
import os
import requests

from dotenv import load_dotenv

load_dotenv()


class AgentExecutor:
    def __init__(self, api_key_env):
        # 根据传入的环境变量名称读取 API Key
        self.api_key = os.getenv(api_key_env)

        self.base_url = os.getenv(
            "DIFY_BASE_URL",
            "https://api.dify.ai/v1"
        ).rstrip("/")

        if not self.api_key:
            raise ValueError(
                f"找不到环境变量: {api_key_env}"
            )

    def execute(self, task):
        url = self.base_url + "/workflows/run"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "inputs": {"task": task},
            "response_mode": "blocking",
            "user": "ontoagent-executor"
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json().get("data", {})

        if data.get("status") != "succeeded":
            raise RuntimeError(
                f"工作流执行失败: {data.get('error')}"
            )

        outputs = data.get("outputs", {})

        if "answer" not in outputs:
            raise ValueError("Dify 没有返回 answer")

        return outputs["answer"]
