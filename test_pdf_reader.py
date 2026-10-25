
from tools.pdf_reader import read_pdf


pdf_path = "data/papers/LLMs4OL 3.pdf"

try:
    print("=== ReaderAgent 开始阅读 PDF ===")

    result = read_pdf(
        pdf_path,
        max_pages=5
    )

    print("文件名:", result["filename"])
    print("总页数:", result["total_pages"])
    print("已读取页数:", result["pages_read"])

    print("\n=== 提取到的论文内容 ===")

    # 终端只显示前 2000 个字符
    print(result["content"][:2000])

    # 将实际提取的文字保存到文件
    from pathlib import Path

    output = Path("data/pdf_extracted.txt")

    output.write_text(
        result["content"],
        encoding="utf-8"
    )

    print("\n阅读成功！")
    print("提取结果已保存到:", output)

except Exception as error:
    print("阅读失败:", error)
