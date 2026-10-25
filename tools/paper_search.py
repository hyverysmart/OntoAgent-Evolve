
import requests


def search_papers(query):
    url = "https://api.crossref.org/works"

    # 告诉 Crossref 我们要搜索什么
    params = {
        "query": query,
        "rows": 3
    }

    # 发送 HTTP 请求
    response = requests.get(
        url,
        params=params,
        timeout=20
    )

    # 检查请求是否成功
    response.raise_for_status()

    data = response.json()

    # 从返回的数据中取出论文列表
    items = data["message"]["items"]

    papers = []

    for item in items:
        titles = item.get("title", [])
        title = titles[0] if titles else "Unknown"

        authors = []

        for author in item.get("author", []):
            name = (
                author.get("given", "") + " " +
                author.get("family", "")
            ).strip()

            if name:
                authors.append(name)

        paper = {
            "title": title,
            "authors": authors,
            "doi": item.get("DOI", ""),
            "url": item.get("URL", "")
        }

        papers.append(paper)

    return papers
