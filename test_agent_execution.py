
from services.agent_executor import AgentExecutor

executor = AgentExecutor()

task = "请简单解释什么是动态本体。"

try:
    print("=== 开始执行任务 ===")
    print("任务:", task)

    result = executor.execute(task)

    print("\n=== Agent 执行结果 ===")
    print(result)

except Exception as error:
    print("执行失败:", error)
