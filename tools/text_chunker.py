
def split_text(text, chunk_size=1800):
    chunks = []

    for start in range(0, len(text), chunk_size):
        end = start + chunk_size

        chunk = text[start:end]
        chunks.append(chunk)

    return chunks
