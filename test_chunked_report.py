
from pathlib import Path

from tools.pdf_reader import read_pdf
from tools.text_chunker import split_text
from services.writer_client import generate_report


# 1. 读取论文
result = read_pdf(
    "data/papers/LLMs4OL 3.pdf",
    max_pages=5
)

text = result["content"]

# 2. 将文本分段
chunks = split_text(text, chunk_size=1800)

print("提取文本长度:", len(text))
print("分段数量:", len(chunks))


# 3. 先只分析前 3 段
# 避免第一次测试就产生大量 Dify API 调用
notes = []

for index, chunk in enumerate(chunks[:3], start=1):
    print(f"\n正在分析第 {index} 段...")

    report = generate_report(
        paper_title=f"LLMs4OL - 片段 {index}",
        paper_text=chunk
    )

    notes.append(
        f"=== 文本片段 {index} ===\n{report}"
    )

    print(f"第 {index} 段分析完成")


# 4. 保存每段分析结果
output = Path("data/chunked_report.txt")

output.write_text(
    "\n\n".join(notes),
    encoding="utf-8"
)

print("\n分段分析完成")
print("结果保存至:", output)
