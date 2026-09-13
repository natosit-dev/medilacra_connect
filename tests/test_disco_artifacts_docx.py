from __future__ import annotations

from io import BytesIO
import zipfile

from experiments.disco_inferno.disco.artifacts import extract_document_text


def _docx_bytes() -> bytes:
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>First paragraph.</w:t></w:r></w:p>
    <w:p>
      <w:r><w:t>Second</w:t></w:r>
      <w:r><w:tab/></w:r>
      <w:r><w:t>paragraph.</w:t></w:r>
    </w:p>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>Table cell</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("word/document.xml", document_xml)
    return stream.getvalue()


def test_docx_text_extraction_uses_ooxml_directly() -> None:
    text = extract_document_text(_docx_bytes(), "sample.docx")
    assert text == "First paragraph.\nSecond\tparagraph.\nTable cell"
