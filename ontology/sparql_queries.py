
from ontology.agent_ontology import EX


def query_agent_tools(ontology, agent_name):
    """使用 SPARQL 查询 Agent 的工具来源"""

    query = """
    PREFIX ex: <http://example.org/ontoagent#>

    SELECT ?tool ?capability
    WHERE {
        ?agent ex:hasToolBinding ?binding .
        ?binding ex:toolName ?tool .
        ?binding ex:providesCapability ?capability .
    }
    """

    results = ontology.graph.query(
        query,
        initBindings={
            "agent": EX[agent_name]
        }
    )

    tools = []

    for row in results:
        tools.append({
            "tool": str(row.tool),
            "capability": str(row.capability).replace(
                str(EX), "", 1
            )
        })

    return sorted(
        tools,
        key=lambda item: item["tool"]
    )


def query_all_tool_bindings(ontology):
    """查询本体中全部 Agent 的工具绑定"""

    query = """
    PREFIX ex: <http://example.org/ontoagent#>

    SELECT ?agent ?tool ?capability
    WHERE {
        ?agent ex:hasToolBinding ?binding .
        ?binding ex:toolName ?tool .
        ?binding ex:providesCapability ?capability .
    }
    ORDER BY ?agent ?tool
    """

    results = ontology.graph.query(query)

    bindings = []

    for row in results:
        bindings.append({
            "agent": str(row.agent).replace(
                str(EX), "", 1
            ),
            "tool": str(row.tool),
            "capability": str(row.capability).replace(
                str(EX), "", 1
            )
        })

    return bindings


def check_tool_provenance_consistency(manager):
    """比较 RDF 工具来源与 Python 注册表"""

    rdf_bindings = query_all_tool_bindings(
        manager.ontology
    )

    rdf_set = {
        (
            item["agent"],
            item["tool"],
            item["capability"]
        )
        for item in rdf_bindings
    }

    registry_set = set()

    for agent, tools in manager.tools.items():
        for tool_name, info in tools.items():
            registry_set.add((
                agent,
                tool_name,
                info["capability"]
            ))

    return rdf_set == registry_set
