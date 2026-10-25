
from fastapi import FastAPI, HTTPException

from ontology.agent_ontology import AgentOntology
from dynamic_agent_manager import DynamicAgentManager
from tools.pdf_reader import read_pdf

from services.tool_persistence import (
    PDF_FILE,
    STATE_FILE,
    save_tools,
    restore_tools
)

from ontology.sparql_queries import (
    query_all_tool_bindings,
    check_tool_provenance_consistency
)


# ========== 1. 创建 FastAPI ==========

app = FastAPI(
    title="OntoAgent-Evolve Dynamic API"
)


# ========== 2. 创建 RDF 本体 ==========

ontology = AgentOntology()

ontology.add_agent("SearchAgent", ["search_paper"])
ontology.add_agent("ReaderAgent", [])
ontology.add_agent("WriterAgent", ["write_report"])
ontology.add_agent("ResearchAgent", ["search_paper"])


# ========== 3. 定义任务 ==========

tasks = {
    "ResearchTask": [
        "search_paper",
        "read_pdf",
        "write_report"
    ],
    "SearchReadTask": [
        "search_paper",
        "read_pdf"
    ],
    "WritingTask": [
        "write_report"
    ]
}


# ========== 4. 初始化管理器 ==========

manager = DynamicAgentManager(ontology, tasks)
manager.initialize()


# 如果已有状态文件，就自动恢复
restored = restore_tools(manager)

# 第一次运行时，注册 ReaderAgent 的基础工具
if not restored:
    success = manager.register_tool(
        "ReaderAgent",
        "PDFReaderTool",
        "read_pdf",
        read_pdf,
        {
            "file_path": str(PDF_FILE),
            "max_pages": 1
        }
    )

    if not success:
        raise RuntimeError("ReaderAgent 初始化失败")

    save_tools(manager)


# ========== 5. 查询当前状态 ==========

@app.get("/dynamic/status")
def get_status():
    agents = [
        "SearchAgent",
        "ReaderAgent",
        "WriterAgent",
        "ResearchAgent"
    ]

    return {
        "agents": {
            name: {
                "capabilities": sorted(
                    ontology.get_capabilities(name)
                ),
                "registered_tools": sorted(
                    manager.tools.get(name, {}).keys()
                )
            }
            for name in agents
        },
        "recommendations": manager.cache,
        "consistency": manager.check_consistency(),
        "state_file": str(STATE_FILE),
        "events": manager.history
    }


# ========== 6. 新增 PDF 工具 ==========

@app.post("/dynamic/research-agent/pdf-tool")
def add_pdf_tool():
    existing = manager.tools.get(
        "ResearchAgent", {}
    )

    if "PDFReaderTool" in existing:
        raise HTTPException(
            status_code=409,
            detail="ResearchAgent 已注册 PDFReaderTool"
        )

    success = manager.register_tool(
        "ResearchAgent",
        "PDFReaderTool",
        "read_pdf",
        read_pdf,
        {
            "file_path": str(PDF_FILE),
            "max_pages": 1
        }
    )

    if not success:
        raise HTTPException(
            status_code=400,
            detail="工具验证失败"
        )

    try:
        save_tools(manager)
    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail=f"工具已注册，但保存失败: {error}"
        )

    return {
        "message": "PDF 工具注册并保存成功",
        "team": manager.cache["ResearchTask"],
        "consistency": manager.check_consistency()
    }


# ========== 7. 删除 PDF 工具 ==========

@app.delete("/dynamic/research-agent/pdf-tool")
def remove_pdf_tool():
    success = manager.remove_tool(
        "ResearchAgent",
        "PDFReaderTool"
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="ResearchAgent 没有该工具"
        )

    try:
        save_tools(manager)
    except OSError as error:
        raise HTTPException(
            status_code=500,
            detail=f"工具已删除，但保存失败: {error}"
        )

    return {
        "message": "PDF 工具移除并保存成功",
        "team": manager.cache["ResearchTask"],
        "consistency": manager.check_consistency()
    }


# ========== 8. 使用推荐团队执行 PDF ==========

@app.post("/dynamic/execute-pdf")
def execute_pdf():
    team = manager.cache["ResearchTask"]

    try:
        manager.execute_pdf(
            team,
            str(PDF_FILE)
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    return {
        "message": "PDF 阅读成功",
        "team": team
    }
    
@app.get("/dynamic/ontology/tool-bindings")
def get_ontology_tool_bindings():
    return {
        "bindings": query_all_tool_bindings(ontology),
        "provenance_consistency": check_tool_provenance_consistency(manager),
        "recommendation_consistency": manager.check_consistency()
    }
