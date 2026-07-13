"""Testes de exportação Markdown/PDF."""

import pytest

from traveling_salesman_problem.llm.export import (
    PdfUnavailableError,
    export_markdown,
    export_pdf,
)


def test_export_markdown_returns_bytes():
    content = "# Título\n\nTexto."
    data, media_type, filename = export_markdown(content, "relatorio.md")
    assert data == content.encode("utf-8")
    assert media_type.startswith("text/markdown")
    assert filename == "relatorio.md"


def test_export_pdf_without_weasyprint_raises():
    with pytest.raises(PdfUnavailableError):
        export_pdf("# Teste")
