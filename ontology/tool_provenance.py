
from urllib.parse import quote

from rdflib import RDF, RDFS, Literal

from ontology.agent_ontology import EX


def binding_uri(agent, tool_name):
    """为 Agent 的每个工具绑定生成唯一 URI"""

    key = f"{agent}::{tool_name}"

    return EX[
        "binding_" + quote(key, safe="")
    ]


def add_tool_provenance(
    ontology,
    agent,
    tool_name,
    capability
):
    """向 RDF 写入工具来源"""

    graph = ontology.graph
    binding = binding_uri(agent, tool_name)

    graph.add((
        binding,
        RDF.type,
        EX.ToolBinding
    ))

    graph.add((
        EX[agent],
        EX.hasToolBinding,
        binding
    ))

    graph.add((
        binding,
        EX.toolName,
        Literal(tool_name)
    ))

    graph.add((
        binding,
        EX.providesCapability,
        EX[capability]
    ))

    graph.add((
        EX[capability],
        RDF.type,
        EX.Capability
    ))


def remove_tool_provenance(
    ontology,
    agent,
    tool_name
):
    """移除指定工具的 RDF 绑定记录"""

    graph = ontology.graph
    binding = binding_uri(agent, tool_name)

    graph.remove((
        EX[agent],
        EX.hasToolBinding,
        binding
    ))

    # 删除绑定节点的属性
    graph.remove((binding, None, None))


def get_tool_provenance(ontology, agent):
    """查询 Agent 的所有工具来源"""

    graph = ontology.graph
    results = []

    for binding in graph.objects(
        EX[agent],
        EX.hasToolBinding
    ):
        name = graph.value(
            binding,
            EX.toolName
        )

        capability = graph.value(
            binding,
            EX.providesCapability
        )

        if name is None or capability is None:
            continue

        results.append({
            "tool": str(name),
            "capability": str(capability).replace(
                str(EX), "", 1
            )
        })

    return sorted(
        results,
        key=lambda item: item["tool"]
    )
