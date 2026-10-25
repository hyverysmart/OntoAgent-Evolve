
from rdflib import Graph, Namespace, RDF, OWL

# 为本体定义一个命名空间
EX = Namespace("http://example.org/ontoagent#")


class AgentOntology:
    def __init__(self):
        # 创建 RDF 知识图谱
        self.graph = Graph()
        self.graph.bind("ex", EX)

        # 定义本体中的两种类
        self.graph.add((EX.Agent, RDF.type, OWL.Class))
        self.graph.add((EX.Capability, RDF.type, OWL.Class))
        self.graph.add((EX.Capability, RDF.type, OWL.Class))

        # 定义 Agent 与 Capability 之间的关系
        self.graph.add(
            (EX.hasCapability, RDF.type, OWL.ObjectProperty)
        )
        self.graph.add((EX.Task, RDF.type, OWL.Class))
        self.graph.add((EX.requiresCapability, RDF.type, OWL.ObjectProperty))

    def add_agent(self, name, capabilities):
        agent = EX[name]

        # 声明这是一个 Agent
        self.graph.add((agent, RDF.type, EX.Agent))

        # 为 Agent 添加能力
        for capability in capabilities:
            cap = EX[capability]

            self.graph.add((cap, RDF.type, EX.Capability))
            self.graph.add((agent, EX.hasCapability, cap))

    def get_capabilities(self, name):
        agent = EX[name]

        return {
            str(cap).split("#")[-1]
            for cap in self.graph.objects(
                agent, EX.hasCapability
            )
        }

    def recommend(self, required_capabilities):
        required = set(required_capabilities)
        results = []

        # 找出本体里的全部 Agent
        for agent in self.graph.subjects(RDF.type, EX.Agent):
            name = str(agent).split("#")[-1]
            capabilities = self.get_capabilities(name)

            matched = required & capabilities
            score = len(matched)

            if score > 0:
                results.append((name, score))

        # 按匹配能力数量降序排列
        results.sort(key=lambda x: (-x[1], x[0]))
        return results

    def save(self, filename):
        self.graph.serialize(
            destination=filename,
            format="turtle"
        )
    
    def add_capability(self, agent_name, capability):
        agent = EX[agent_name]
        cap = EX[capability]

        # 检查 Agent 是否存在
        if (agent, RDF.type, EX.Agent) not in self.graph:
            raise ValueError(f"Agent 不存在: {agent_name}")

        # 将能力加入本体
        self.graph.add((cap, RDF.type, EX.Capability))
        self.graph.add((agent, EX.hasCapability, cap))

        print(f"{agent_name} 新增能力: {capability}")

    def remove_capability(self, agent_name, capability):
        agent = EX[agent_name]
        cap = EX[capability]

        # 移除 Agent 与能力之间的关系
        self.graph.remove((agent, EX.hasCapability, cap))

        print(f"{agent_name} 移除能力: {capability}")
    
    def add_task(self, task_name, required_capabilities):
        task = EX[task_name]

        self.graph.add((task, RDF.type, EX.Task))

        for capability in required_capabilities:
            cap = EX[capability]
            self.graph.add((cap, RDF.type, EX.Capability))
            self.graph.add((task, EX.requiresCapability, cap))

    def get_task_requirements(self, task_name):
        task = EX[task_name]

        return {
            str(cap).split("#")[-1]
            for cap in self.graph.objects(
                task, EX.requiresCapability
            )
        }

    def recommend_task(self, task_name):
        required = self.get_task_requirements(task_name)

        # 使用之前写好的推荐算法
        return self.recommend(required)

    def get_affected_tasks(self, changed_capability):
        cap = EX[changed_capability]
        affected = []

        # 查找所有需要这个能力的 Task
        for task in self.graph.subjects(
            EX.requiresCapability, cap
        ):
            task_name = str(task).split("#")[-1]
            affected.append(task_name)

        return sorted(affected)
