from __future__ import annotations

from io import BytesIO

from docx import Document


def extract_text_from_pdf(file_bytes: bytes) -> str:
    # Prefer PyMuPDF when available, but fall back to pure-Python extraction
    # to keep local installs hackathon-friendly (some environments won't have
    # PyMuPDF wheels).
    try:
        import fitz  # type: ignore

        doc = fitz.open(stream=BytesIO(file_bytes), filetype="pdf")
        texts: list[str] = []
        for page in doc:
            texts.append(page.get_text("text"))
        return "\n".join(texts).strip()
    except Exception:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(file_bytes))
        texts: list[str] = []
        for page in reader.pages:
            try:
                texts.append(page.extract_text() or "")
            except Exception:
                texts.append("")
        return "\n".join(texts).strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(BytesIO(file_bytes))
    texts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    # Keep paragraph separation for better scoring keyword matches.
    return "\n".join(texts).strip()

