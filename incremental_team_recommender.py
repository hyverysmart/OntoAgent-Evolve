
from team_recommender import recommend_team


class IncrementalTeamRecommender:

    def __init__(self, ontology, tasks):
        self.ontology = ontology
        self.tasks = tasks

        # 保存每个任务上一次的推荐团队
        self.cache = {}

        # 记录本次重新计算的任务
        self.last_updated_tasks = []

    def initialize(self):
        """第一次运行：计算全部任务"""

        for task_name, required in self.tasks.items():
            self.cache[task_name] = recommend_team(
                self.ontology,
                required
            )

        print("团队推荐缓存初始化完成")

    def update_capability(
        self, agent_name, capability, action
    ):
        """更新能力并重新计算受影响的任务"""

        if action == "add":
            self.ontology.add_capability(
                agent_name, capability
            )

        elif action == "remove":
            self.ontology.remove_capability(
                agent_name, capability
            )

        else:
            raise ValueError("action 必须是 add 或 remove")

        # 找出需要这种能力的任务
        affected = [
            name
            for name, required in self.tasks.items()
            if capability in required
        ]

        self.last_updated_tasks = affected

        # 只更新受影响任务的推荐团队
        for task_name in affected:
            self.cache[task_name] = recommend_team(
                self.ontology,
                self.tasks[task_name]
            )

        return affected

    def full_recompute(self):
        """全量重算：用于对照实验"""

        results = {}

        for task_name, required in self.tasks.items():
            results[task_name] = recommend_team(
                self.ontology,
                required
            )

        return results

    def check_consistency(self):
        """检查增量结果是否和全量结果一致"""

        full_results = self.full_recompute()

        return self.cache == full_results
