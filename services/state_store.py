
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_FILE = ROOT / "data" / "agent_registry.json"
ONTOLOGY_FILE = ROOT / "data" / "agents.ttl"


# 第一次启动时使用的默认 Agent 配置
DEFAULT_AGENTS = {
    "SearchAgent": ["WebSearchTool"],
    "ReaderAgent": ["PDFParserTool"],
    "WriterAgent": ["ReportWriterTool"],
}


def load_agents():
    if not STATE_FILE.exists():
        return {
            name: tools.copy()
            for name, tools in DEFAULT_AGENTS.items()
        }

    with STATE_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        raise ValueError("Agent 注册表格式错误")

    return data


def save_agents(agent_tools):
    STATE_FILE.parent.mkdir(
        parents=True, exist_ok=True
    )

    data = {
        name: sorted(tools)
        for name, tools in agent_tools.items()
    }

    # 先写临时文件，再替换旧文件
    temp_file = STATE_FILE.with_suffix(".tmp")

    temp_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    temp_file.replace(STATE_FILE)
