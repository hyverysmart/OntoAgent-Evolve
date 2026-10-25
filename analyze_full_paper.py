
from pathlib import Path
import json

from tools.pdf_reader import read_pdf
from tools.text_chunker import split_text
from services.writer_client import generate_report


# ===== 1. 实验配置 =====

PDF_PATH = "data/papers/LLMs4OL 3.pdf"

# 先测试 3 段，成功后改为 None
MAX_CHUNKS = None

# 每段文字数量
CHUNK_SIZE = 1500

# 论文总页数为 27，允许读取全部
MAX_PAGES = 100


# ===== 2. 读取 PDF =====

print("=== 开始读取论文 ===")

result = read_pdf(
    PDF_PATH,
    max_pages=MAX_PAGES
)

text = result["content"]

print("文件:", result["filename"])
print("总页数:", result["total_pages"])
print("实际读取页数:", result["pages_read"])
print("提取字符数:", len(text))


# ===== 3. 自动分段 =====

chunks = split_text(
    text,
    chunk_size=CHUNK_SIZE
)

print("\n总片段数量:", len(chunks))

if MAX_CHUNKS is None:
    selected_chunks = chunks
else:
    selected_chunks = chunks[:MAX_CHUNKS]

print("本次计划分析:", len(selected_chunks), "段")


# ===== 4. 创建输出文件夹 =====

output_dir = Path("data/paper_analysis")
output_dir.mkdir(
    parents=True,
    exist_ok=True
)


# ===== 5. 逐段调用 WriterAgent =====

for index, chunk in enumerate(
    selected_chunks,
    start=1
):

    output_file = output_dir / f"chunk_{index:03d}.txt"

    # 已经成功分析的片段不重复调用 Dify
    if output_file.exists():
        print(f"片段 {index} 已完成，跳过")
        continue

    print(f"\n正在分析片段 {index}/{len(selected_chunks)}")

    try:
        report = generate_report(
            paper_title=(
                f"LLMs4OL - 文本片段 {index}"
                f"（共 {len(chunks)} 段）"
            ),
            paper_text=chunk
        )

        # 保存单段分析结果
        output_file.write_text(
            report,
            encoding="utf-8"
        )

        print(f"片段 {index} 分析成功")

    except Exception as error:
        print("分析失败:", error)
        print("已完成的片段不会丢失")
        break


# ===== 6. 汇总已完成片段 =====

reports = []

for index in range(1, len(selected_chunks) + 1):
    output_file = output_dir / f"chunk_{index:03d}.txt"

    if not output_file.exists():
        continue

    report = output_file.read_text(
        encoding="utf-8"
    )

    reports.append(
        f"=== 第 {index} 段分析 ===\n\n{report}"
    )


# ===== 7. 保存合并阅读记录 =====

final_path = output_dir / "combined_report.txt"

header = (
    f"论文文件：{result['filename']}\n"
    f"PDF 总页数：{result['total_pages']}\n"
    f"已提取页数：{result['pages_read']}\n"
    f"全部片段数：{len(chunks)}\n"
    f"已分析片段数：{len(reports)}\n\n"
    "注意：以下是分段阅读记录，"
    "不是综合全文后的最终结论。\n\n"
)

final_path.write_text(
    header + "\n\n".join(reports),
    encoding="utf-8"
)


# ===== 8. 保存实验信息 =====

metadata = {
    "filename": result["filename"],
    "total_pages": result["total_pages"],
    "pages_read": result["pages_read"],
    "total_chunks": len(chunks),
    "completed_chunks": len(reports),
    "chunk_size": CHUNK_SIZE
}

(output_dir / "metadata.json").write_text(
    json.dumps(
        metadata,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("\n=== 实验结束 ===")
print("完成:", len(reports), "/", len(chunks))
print("阅读记录:", final_path)
