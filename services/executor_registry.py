
from services.agent_executor import AgentExecutor


class ExecutorRegistry:
    def __init__(self):
        # 保存 Agent 与执行器之间的对应关系
        self.executors = {}

    def register(self, agent_name, api_key_env):
        # 注册执行器信息，不保存真实 API Key
        self.executors[agent_name] = api_key_env

    def is_available(self, agent_name):
        # 检查是否已经注册执行器
        return agent_name in self.executors

    def execute(self, agent_name, task):
        # 没有执行器就不能执行
        if not self.is_available(agent_name):
            raise ValueError(
                f"{agent_name} 尚未注册执行器"
            )

        # 找到该 Agent 对应的 API Key 环境变量
        api_key_env = self.executors[agent_name]

        # 创建执行器
        executor = AgentExecutor(api_key_env)

        # 调用 Dify 完成任务
        return executor.execute(task)
