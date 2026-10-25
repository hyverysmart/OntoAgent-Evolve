
from itertools import combinations

from rdflib import RDF
from ontology.agent_ontology import EX


def recommend_team_optimized(
    ontology,
    required,
    max_team_size=3
):
    required = set(required)

    if not required:
        return []

    # 1. 从 RDF 中查询所有 Agent
    agents = sorted({
        str(agent).split("#")[-1]
        for agent in ontology.graph.subjects(
            RDF.type, EX.Agent
        )
    })

    # 2. 为每种所需能力分配一个二进制位
    capability_bits = {
        cap: 1 << i
        for i, cap in enumerate(sorted(required))
    }

    target = (1 << len(required)) - 1

    # 3. 每个 Agent 只读取一次 RDF 能力
    agent_masks = {}

    for agent in agents:
        capabilities = ontology.get_capabilities(agent)

        mask = 0

        for cap in capabilities:
            mask |= capability_bits.get(cap, 0)

        agent_masks[agent] = mask

    # 4. 按人数从少到多搜索
    for size in range(
        1,
        min(max_team_size, len(agents)) + 1
    ):
        for team in combinations(agents, size):

            # 5. 使用位运算计算团队能力覆盖
            covered = 0

            for agent in team:
                covered |= agent_masks[agent]

                # 所有能力都已经覆盖，提前结束
                if covered == target:
                    break

            if covered == target:
                return list(team)

    # 没有找到满足要求的团队
    return []
