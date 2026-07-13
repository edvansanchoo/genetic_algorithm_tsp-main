"""Exportação de relatórios Markdown e PDF."""

from __future__ import annotations

import markdown


class PdfUnavailableError(Exception):
    pass


def export_markdown(
    content: str,
    filename: str = "relatorio-vrp.md",
) -> tuple[bytes, str, str]:
    return content.encode("utf-8"), "text/markdown; charset=utf-8", filename


def export_pdf(
    content: str,
    filename: str = "relatorio-vrp.pdf",
) -> tuple[bytes, str, str]:
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise PdfUnavailableError(
            "WeasyPrint não instalado. Use requirements-llm.txt ou exporte MD."
        ) from exc

    html_body = markdown.markdown(content, extensions=["tables", "fenced_code"])
    wrapped = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        f"<body>{html_body}</body></html>"
    )
    pdf_bytes = HTML(string=wrapped).write_pdf()
    return pdf_bytes, "application/pdf", filename
