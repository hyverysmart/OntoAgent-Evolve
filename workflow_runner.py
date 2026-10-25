
# 三种能力对应的模拟执行函数


def search_paper(data):
    from tools.paper_search import search_papers

    print("正在 Crossref 检索真实论文...")

    papers = search_papers(data)

    if not papers:
        return "未检索到相关论文"

    result = []

    for paper in papers:
        result.append(
            f"标题: {paper['title']}\n"
            f"DOI: {paper['doi']}\n"
            f"链接: {paper['url']}"
        )

    return "\n\n".join(result)



def read_pdf(data):
    print("PDF 阅读尚未实现，当前仅传递论文元数据。")
    return f"尚未阅读 PDF。以下是检索到的论文元数据：\n{data}"


def write_report(data):
    print("正在生成模拟报告...")
    return (
        "初步论文检索记录（未阅读全文）\n\n"
        + data
        + "\n\n备注：以上信息不能作为论文内容总结。"
    )


# 能力与执行函数的映射
ACTIONS = {
    "search_paper": search_paper,
    "read_pdf": read_pdf,
    "write_report": write_report,
}


def execute_team(ontology, team, task):
    # 固定执行顺序：搜索 → 阅读 → 报告
    steps = ["search_paper", "read_pdf", "write_report"]

    data = task

    for capability in steps:
        # 找到团队中能执行当前步骤的 Agent
        selected = None

        for agent in team:
            abilities = ontology.get_capabilities(agent)

            if capability in abilities:
                selected = agent
                break

        if selected is None:
            raise RuntimeError(
                f"团队缺少能力: {capability}"
            )

        print(f"\n{selected} 执行 {capability}")

        # 调用对应的模拟函数
        data = ACTIONS[capability](data)

    return data
