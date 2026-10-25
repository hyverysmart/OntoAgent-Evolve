
class ToolRegistry:
    def __init__(self):
        # 保存每个 Agent 当前的工具
        self.agent_tools = {}

    def register_agent(self, agent_name, tools):
        # 记录 Agent 的初始工具配置
        self.agent_tools[agent_name] = set(tools)

    def detect_changes(self, agent_name, new_tools):
        # 获取之前记录的工具配置
        old_tools = self.agent_tools.get(agent_name, set())
        new_tools = set(new_tools)

        # 找出新增和删除的工具
        added = new_tools - old_tools
        removed = old_tools - new_tools

        return {
            "added": sorted(added),
            "removed": sorted(removed),
        }

    def update_tools(self, agent_name, new_tools):
        # 更新保存的工具配置
        self.agent_tools[agent_name] = set(new_tools)
