import pytest
from docx import Document

from products.humanizer.service.document_parser import (
    export_docx_revisions,
    parse_document,
)


def test_docx_keeps_styles_tables_and_complex_paragraphs(tmp_path):
    src = tmp_path / "original.docx"
    out = tmp_path / "revised.docx"
    document = Document()
    document.add_heading("Chapter One", 1)
    simple = document.add_paragraph()
    run = simple.add_run("The original wording is unclear.")
    run.bold = True

    complex_p = document.add_paragraph()
    complex_p.add_run("Mixed ")
    complex_p.add_run("formatting.").italic = True

    cell = document.add_table(rows=1, cols=1).cell(0, 0)
    cell.text = "Table content unchanged."
    document.save(src)

    parsed = parse_document(src)
    simple_block = next(x for x in parsed.blocks if x.text == "The original wording is unclear.")
    complex_block = next(x for x in parsed.blocks if x.text == "Mixed formatting.")
    table_block = next(x for x in parsed.blocks if x.text == "Table content unchanged.")

    assert simple_block.editable
    assert not complex_block.editable
    assert table_block.kind == "table_cell"

    export_docx_revisions(src, out, {simple_block.index: "The wording is now clearer."})
    original = Document(src)
    revised = Document(out)

    assert original.paragraphs[1].text == "The original wording is unclear."
    assert revised.paragraphs[0].style.name == "Heading 1"
    assert revised.paragraphs[1].runs[0].bold
    assert revised.paragraphs[1].text == "The wording is now clearer."
    assert revised.paragraphs[2].text == "Mixed formatting."
    assert revised.tables[0].cell(0, 0).text == "Table content unchanged."

    with pytest.raises(ValueError, match="complex formatting"):
        export_docx_revisions(src, tmp_path / "unsafe.docx", {complex_block.index: "Destructive edit"})
    with pytest.raises(ValueError, match="overwrite"):
        export_docx_revisions(src, src, {})
    with pytest.raises(FileExistsError):
        export_docx_revisions(src, out, {})
