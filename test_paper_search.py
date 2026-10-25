
from tools.paper_search import search_papers


query = "ontology-based multi-agent systems"

print("正在检索论文:", query)

try:
    papers = search_papers(query)

    for i, paper in enumerate(papers, 1):
        print(f"\n=== 论文 {i} ===")
        print("标题:", paper["title"])
        print("作者:", ", ".join(paper["authors"]))
        print("DOI:", paper["doi"])
        print("链接:", paper["url"])

except Exception as error:
    print("搜索失败:", error)
