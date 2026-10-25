
from services.dify_client import extract_capabilities
from services.capability_sync import (
    CapabilitySync,
    TOOL_CAPABILITIES,
)


# 测试用的工具注册信息
# 后期由真实 Dify 工具配置替代
TOOL_DESCRIPTIONS = {
    "WebSearchTool": (
        "Search academic papers using a web search API."
    ),
    "PDFParserTool": (
        "Extract and read text from PDF documents."
    ),
    "ReportWriterTool": (
        "Generate structured research reports."
    ),
}


class AutoCapabilitySync:
    def __init__(self, registry, recommender):
        self.registry = registry
        self.recommender = recommender

        self.sync_service = CapabilitySync(
            registry, recommender
        )

    def sync_agent(self, agent_name, new_tools):
        # 1. 检测工具变化
        changes = self.registry.detect_changes(
            agent_name, new_tools
        )

        print("检测到工具变化:", changes)

        # 工具不变时无需再次调用 Dify
        if not changes["added"] and not changes["removed"]:
            print("配置没有变化，无需更新")
            return changes

        # 2. 检查工具是否已注册
        for tool in new_tools:
            if tool not in TOOL_DESCRIPTIONS:
                raise ValueError(f"未知工具: {tool}")

        # 3. 让 Dify 识别新增工具的能力
        for tool in changes["added"]:
            description = TOOL_DESCRIPTIONS[tool]

            candidates = set(
                extract_capabilities(
                    agent_name,
                    description
                )
            )

            # 4. 使用可信工具映射验证候选能力
            expected = TOOL_CAPABILITIES[tool]

            print(f"{tool} 候选能力: {sorted(candidates)}")

            if candidates != expected:
                raise ValueError(
                    f"{tool} 能力验证不通过: "
                    f"候选={candidates}, 预期={expected}"
                )

        # 5. 验证通过后同步 RDF 本体
        return self.sync_service.sync(
            agent_name, new_tools
        )
