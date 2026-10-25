
from time import perf_counter_ns


class IncrementalRecommender:
    def __init__(self, ontology):
        self.ontology = ontology
        self.cache = {}
        self.last_recompute_ns = 0

    def initialize(self, task_names):
        for task in task_names:
            self.cache[task] = self.ontology.recommend_task(task)

    def update_capability(self, agent_name, capability, action):
        # 1. 修改本体中的能力关系
        if action == "add":
            self.ontology.add_capability(agent_name, capability)
        elif action == "remove":
            self.ontology.remove_capability(agent_name, capability)
        else:
            raise ValueError("不支持的操作")

        # 2. 找到需要重新推荐的任务
        affected = self.ontology.get_affected_tasks(capability)

        # 3. 测量重新计算推荐所需的时间
        start = perf_counter_ns()

        updated = []

        for task in affected:
            if task in self.cache:
                self.cache[task] = self.ontology.recommend_task(task)
                updated.append(task)

        self.last_recompute_ns = perf_counter_ns() - start

        return updated

    def show_results(self):
        for task, results in sorted(self.cache.items()):
            print(f"{task}: {results}")
