
from pathlib import Path

from ontology.agent_ontology import AgentOntology
from team_recommender import recommend_team
from tools.paper_search import search_papers
from tools.pdf_reader import read_pdf
from services.writer_client import generate_report


# 1. 创建 Agent 本体
ontology = AgentOntology()

ontology.add_agent("SearchAgent", ["search_paper"])
ontology.add_agent("ReaderAgent", ["read_pdf"])
ontology.add_agent("WriterAgent", ["write_report"])

# 2. 定义任务需要的能力
required = [
    "search_paper",
    "read_pdf",
    "write_report"
]

# 3. 推荐团队
team = recommend_team(ontology, required)
print("推荐团队:", team)


def find_agent(capability):
    for agent in team:
        abilities = ontology.get_capabilities(agent)

        if capability in abilities:
            return agent

    raise RuntimeError(f"缺少能力: {capability}")


# 4. SearchAgent 检索论文
print("\n=== 第一步：搜索论文 ===")
print("执行 Agent:", find_agent("search_paper"))

query = "ontology learning large language models"

try:
    papers = search_papers(query)
    print("检索论文数量:", len(papers))

    for paper in papers:
        print("论文:", paper["title"])

except Exception as error:
    print("论文检索失败:", error)
    papers = []


# 5. ReaderAgent 阅读本地 PDF
print("\n=== 第二步：读取 PDF ===")
print("执行 Agent:", find_agent("read_pdf"))

pdf_path = "data/papers/LLMs4OL 3.pdf"

result = read_pdf(pdf_path, max_pages=15)

print("文件:", result["filename"])
print("总页数:", result["total_pages"])
print("已读取:", result["pages_read"])

content = result["content"]

if not content.strip():
    raise RuntimeError("PDF 没有提取到文字")



# 6. WriterAgent 分析真实论文文本
print("\n=== 第三步：WriterAgent 生成报告 ===")

print("执行 Agent:", find_agent("write_report"))

paper_title = result["filename"]

# 将 ReaderAgent 的输出交给 WriterAgent
report = generate_report(
    paper_title=paper_title,
    paper_text=content
)

# 7. 添加阅读范围说明
report = (
    f"文件：{paper_title}\n"
    f"PDF 总页数：{result['total_pages']}\n"
    f"提取页数：{result['pages_read']}\n"
    "AI 实际分析范围：提取文本的前 8000 字符\n"
    "注意：以下报告只基于部分文本生成。\n\n"
    + report
)

# 8. 保存报告
output_path = Path("data/research_report.txt")

output_path.write_text(
    report,
    encoding="utf-8"
)

print("\n=== WriterAgent 执行成功 ===")
print(report[:1000])

print("\n完整报告已保存至:", output_path)
