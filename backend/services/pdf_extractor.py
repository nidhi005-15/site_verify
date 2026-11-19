import pymupdf


def extract_pdf_text(pdf_bytes: bytes):
    document = pymupdf.open(stream=pdf_bytes, filetype="pdf")

    pages = []
    for page_number, page in enumerate(document, start=1):
        extracted_text = page.get_text("text").strip()
        pages.append({
            "page_number": page_number,
            "content": extracted_text,
        })

    document.close()

    full_text = "\n".join(page["content"] for page in pages if page["content"])

    return {
        "total_pages": len(pages),
        "full_text": full_text,
        "pages": pages,
    }
