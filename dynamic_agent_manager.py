
from rdflib import RDF

from ontology.agent_ontology import EX
from team_recommender import recommend_team
from optimized_team_recommender import recommend_team_optimized

from ontology.tool_provenance import (
    add_tool_provenance,
    remove_tool_provenance
)

class DynamicAgentManager:

    def __init__(self, ontology, tasks):
        self.ontology = ontology
        self.tasks = tasks

        # 记录创建管理器之前已经存在的能力
        self.base_capabilities = {}

        for agent_uri in ontology.graph.subjects(
            RDF.type, EX.Agent
        ):
            agent = str(agent_uri).split("#")[-1]

            self.base_capabilities[agent] = set(
                ontology.get_capabilities(agent)
            )

        # Agent -> Tool -> 工具信息
        self.tools = {}

        # Task -> 推荐团队
        self.cache = {}

        # 能力变化记录
        self.history = []

    def initialize(self):
        """初始化推荐缓存"""

        self.cache = {
            name: recommend_team_optimized(
                self.ontology,
                required
            )
            for name, required in self.tasks.items()
        }

    def has_agent(self, agent):
        return (
            EX[agent], RDF.type, EX.Agent
        ) in self.ontology.graph

    def capability_sources(self, agent, capability):
        """查找某种能力来自哪些地方"""

        sources = []

        # 原本就声明的能力
        if capability in self.base_capabilities.get(
            agent, set()
        ):
            sources.append("base")

        # 由已注册工具提供的能力
        for tool_name, info in self.tools.get(
            agent, {}
        ).items():
            if info["capability"] == capability:
                sources.append(tool_name)

        return sources

    def sync_capability(self, agent, capability):
        """根据有效来源决定 RDF 是否保留能力"""

        sources = self.capability_sources(
            agent, capability
        )

        before = (
            capability in
            self.ontology.get_capabilities(agent)
        )

        after = bool(sources)

        if after and not before:
            self.ontology.add_capability(
                agent, capability
            )

        elif before and not after:
            self.ontology.remove_capability(
                agent, capability
            )

        # 只有有效能力状态改变时才重算
        if before != after:
            return self.update_recommendations(
                capability
            )

        return []

    def register_tool(
        self,
        agent,
        tool_name,
        capability,
        tool_function,
        test_input
    ):
        """验证并注册工具"""

        if not self.has_agent(agent):
            print("Agent 不存在:", agent)
            return False

        # 拒绝重复注册
        if tool_name in self.tools.get(agent, {}):
            print("工具已经注册:", tool_name)
            return False

        # 验证工具
        try:
            result = tool_function(**test_input)

            if not isinstance(result, dict):
                raise ValueError("工具结果不是字典")

            if not isinstance(
                result.get("content"),
                str
            ) or not result["content"].strip():
                raise ValueError("没有返回有效文本")

        except Exception as error:
            print("工具验证失败:", error)
            return False

        # 保存工具来源
        self.tools.setdefault(agent, {})

        self.tools[agent][tool_name] = {
            "capability": capability,
            "function": tool_function
        }
        add_tool_provenance(
        self.ontology,
        agent,
        tool_name,
        capability
)

        # 更新 RDF 与推荐
        affected = self.sync_capability(
            agent, capability
        )

        self.history.append({
            "agent": agent,
            "action": "add",
            "tool": tool_name,
            "capability": capability,
            "affected_tasks": affected
        })

        print("注册成功:", agent, tool_name)
        return True

    def remove_tool(self, agent, tool_name):
        """删除工具，但保留其他来源提供的能力"""

        agent_tools = self.tools.get(agent, {})

        if tool_name not in agent_tools:
            print("工具不存在:", tool_name)
            return False

        capability = agent_tools[tool_name]["capability"]

        del agent_tools[tool_name]
        remove_tool_provenance(
            self.ontology,
            agent,
            tool_name
        )

        affected = self.sync_capability(
            agent, capability
        )

        self.history.append({
            "agent": agent,
            "action": "remove",
            "tool": tool_name,
            "capability": capability,
            "affected_tasks": affected
        })

        print("工具已移除:", agent, tool_name)
        return True

    def update_recommendations(self, capability):
        """只更新受影响任务"""

        affected = [
            name
            for name, required in self.tasks.items()
            if capability in required
        ]

        for name in affected:
            self.cache[name] = recommend_team_optimized(
                self.ontology,
                self.tasks[name]
            )

        return affected

    def execute_pdf(self, team, pdf_path):
        """使用推荐团队实际绑定的 PDF 工具"""

        for agent in team:
            for tool_name, info in self.tools.get(
                agent, {}
            ).items():

                if info["capability"] != "read_pdf":
                    continue

                result = info["function"](
                    pdf_path,
                    max_pages=1
                )

                if not result["content"].strip():
                    raise RuntimeError("PDF 内容为空")

                print("实际执行 Agent:", agent)
                print("使用工具:", tool_name)
                print("PDF:", result["filename"])
                print(
                    "提取字符数:",
                    len(result["content"])
                )

                return True

        raise RuntimeError(
            "推荐团队没有绑定可用的 PDF 工具"
        )

    def check_consistency(self):
        """验证 RDF 来源、推荐人数和能力覆盖"""

        # 1. RDF 能力必须与记录的来源一致
        for agent in self.base_capabilities:
            actual = self.ontology.get_capabilities(agent)

            expected = set(
                self.base_capabilities[agent]
            )

            for info in self.tools.get(agent, {}).values():
                expected.add(info["capability"])

            if actual != expected:
                return False

        # 2. 检查团队推荐
        for name, required in self.tasks.items():
            full = recommend_team(
                self.ontology, required
            )

            incremental = self.cache.get(name)

            if incremental is None:
                return False

            if len(full) != len(incremental):
                return False

            covered = set()

            for agent in incremental:
                covered.update(
                    self.ontology.get_capabilities(agent)
                )

            if incremental and not set(required).issubset(
                covered
            ):
                return False

            if not incremental and full:
                return False

        return True
