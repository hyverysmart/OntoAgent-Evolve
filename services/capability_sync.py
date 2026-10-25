
# 第一版使用预先确认的工具能力映射
TOOL_CAPABILITIES = {
    "WebSearchTool": {"search_paper"},
    "PDFParserTool": {"read_pdf"},
    "ReportWriterTool": {"write_report"},
}


class CapabilitySync:
    def __init__(self, registry, recommender):
        self.registry = registry
        self.recommender = recommender

    def sync(self, agent_name, new_tools):
        # 1. 检测工具配置变化
        changes = self.registry.detect_changes(
            agent_name, new_tools
        )

        print("工具变化:", changes)

        # 不允许未知工具直接获得能力
        unknown = set(new_tools) - set(TOOL_CAPABILITIES)

        if unknown:
            raise ValueError(f"未知工具，需要先验证: {unknown}")

        # 2. 计算新工具配置对应的能力集合
        new_capabilities = set()

        for tool in new_tools:
            new_capabilities.update(TOOL_CAPABILITIES[tool])

        # 3. 获取本体中已经记录的能力
        ontology = self.recommender.ontology

        old_capabilities = ontology.get_capabilities(agent_name)

        to_add = new_capabilities - old_capabilities
        to_remove = old_capabilities - new_capabilities

        # 4. 更新本体并触发增量推荐
        for cap in sorted(to_add):
            affected = self.recommender.update_capability(
                agent_name, cap, "add"
            )
            print("能力增加:", cap, "受影响任务:", affected)

        for cap in sorted(to_remove):
            affected = self.recommender.update_capability(
                agent_name, cap, "remove"
            )
            print("能力删除:", cap, "受影响任务:", affected)

        # 5. 成功后保存新的工具配置快照
        self.registry.update_tools(agent_name, new_tools)

        return changes
