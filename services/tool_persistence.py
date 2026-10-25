
import json
import os
from pathlib import Path

from tools.pdf_reader import read_pdf


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STATE_FILE = PROJECT_ROOT / "data" / "dynamic_tools.json"
PDF_FILE = PROJECT_ROOT / "data" / "papers" / "LLMs4OL 3.pdf"


# 允许恢复的工具白名单
# 不从 JSON 动态导入任意 Python 函数
TOOL_CATALOG = {
    "PDFReaderTool": {
        "capability": "read_pdf",
        "function": read_pdf
    },
    "BackupPDFReaderTool": {
        "capability": "read_pdf",
        "function": read_pdf
    }
}

ALLOWED_AGENTS = {"ReaderAgent", "ResearchAgent"}


def save_tools(manager):
    """把工具绑定保存到 JSON"""

    state = {}

    for agent, tools in manager.tools.items():
        state[agent] = sorted(tools.keys())

    STATE_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # 先写临时文件，再替换正式文件
    temp_file = STATE_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=2
        )
        file.flush()
        os.fsync(file.fileno())

    os.replace(temp_file, STATE_FILE)

    print("工具状态已保存:", STATE_FILE)


def restore_tools(manager):
    """启动时读取 JSON 并恢复工具"""

    if not STATE_FILE.exists():
        print("未找到历史状态，使用初始配置")
        return False

    state = json.loads(
        STATE_FILE.read_text(encoding="utf-8")
    )

    if not isinstance(state, dict):
        raise ValueError("工具状态文件格式错误")

    # 先检查保存的内容是否符合白名单
    for agent, tool_names in state.items():
        if agent not in ALLOWED_AGENTS:
            raise ValueError(f"不允许的 Agent: {agent}")

        if not manager.has_agent(agent):
            raise ValueError(f"本体中不存在 Agent: {agent}")

        if not isinstance(tool_names, list):
            raise ValueError("工具列表格式错误")

        if len(tool_names) != len(set(tool_names)):
            raise ValueError("存在重复工具名称")

        for tool_name in tool_names:
            if tool_name not in TOOL_CATALOG:
                raise ValueError(
                    f"未知工具: {tool_name}"
                )

    # 验证并恢复工具绑定
    for agent, tool_names in state.items():
        for tool_name in tool_names:
            info = TOOL_CATALOG[tool_name]

            success = manager.register_tool(
                agent,
                tool_name,
                info["capability"],
                info["function"],
                {
                    "file_path": str(PDF_FILE),
                    "max_pages": 1
                }
            )

            if not success:
                raise RuntimeError(
                    f"恢复失败: {agent}/{tool_name}"
                )

    print("工具状态恢复成功")
    return True
