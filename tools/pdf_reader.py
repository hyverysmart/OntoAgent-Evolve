
from pathlib import Path
import pymupdf


def read_pdf(file_path, max_pages=5):
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"找不到文件: {file_path}")

    with pymupdf.open(path) as document:
        total_pages = document.page_count
        texts = []

        for i in range(min(total_pages, max_pages)):
            page = document[i]
            text = page.get_text("text")
            texts.append(text)

    content = "\n".join(texts)

    return {
        "filename": path.name,
        "total_pages": total_pages,
        "pages_read": min(total_pages, max_pages),
        "content": content
    }
