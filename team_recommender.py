
from itertools import combinations
from rdflib import RDF

from ontology.agent_ontology import EX


def recommend_team(ontology, required, max_team_size=3):
    required = set(required)

    # 1. 从本体获取 Agent
    agents = sorted({
        str(agent).split("#")[-1]
        for agent in ontology.graph.subjects(
            RDF.type, EX.Agent
        )
    })

    # 2. 从一个 Agent 开始寻找
    for size in range(1, max_team_size + 1):

        valid_teams = []

        # 尝试不同的 Agent 组合
        for team in combinations(agents, size):

            combined = set()

            for agent in team:
                combined.update(
                    ontology.get_capabilities(agent)
                )

            # 3. 判断团队能否覆盖全部任务能力
            if required.issubset(combined):
                valid_teams.append(team)

        # 找到人数最少的可行团队
        if valid_teams:
            return list(valid_teams[0])

    return []
