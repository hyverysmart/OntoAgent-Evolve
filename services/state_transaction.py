
from copy import deepcopy


def take_snapshot(manager):
    """保存修改前的内存状态"""

    return {
        "triples": list(manager.ontology.graph),
        "tools": deepcopy(manager.tools),
        "cache": deepcopy(manager.cache),
        "history": deepcopy(manager.history)
    }


def restore_snapshot(manager, snapshot):
    """将内存状态恢复到修改之前"""

    # 1. 恢复 RDF 三元组
    graph = manager.ontology.graph

    graph.remove((None, None, None))

    for triple in snapshot["triples"]:
        graph.add(triple)

    # 2. 恢复工具绑定
    manager.tools = snapshot["tools"]

    # 3. 恢复推荐缓存
    manager.cache = snapshot["cache"]

    # 4. 恢复事件记录
    manager.history = snapshot["history"]


def apply_and_save(manager, operation, save_function):
    """
    执行操作并保存。
    保存失败时撤销内存变更。
    """

    snapshot = take_snapshot(manager)

    try:
        success = operation()

        if not success:
            restore_snapshot(manager, snapshot)
            return False

        # 持久化到 JSON
        save_function(manager)

        return True

    except Exception:
        restore_snapshot(manager, snapshot)
        raise
