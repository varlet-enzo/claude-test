import base64
import io
import zipfile
from types import SimpleNamespace

import pytest

from mon_ia.files import AttachmentError, extract_text, prepare_attachments


def attachment(name, data: bytes, kind=""):
    return SimpleNamespace(name=name, type=kind, data=base64.b64encode(data).decode())


def make_pdf(text: str) -> bytes:
    stream = f"BT /F1 24 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf, offsets = b"%PDF-1.4\n", []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(pdf)
    pdf += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    pdf += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    pdf += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return pdf


def make_docx(paragraphs: list[str]) -> bytes:
    body = "".join(f"<w:p><w:r><w:t>{text}</w:t></w:r></w:p>" for text in paragraphs)
    xml = f'<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{body}</w:body></w:document>'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", xml)
    return buffer.getvalue()


def test_text_files_in_any_common_encoding():
    assert extract_text("notes.txt", "Café crème".encode("utf-8")) == "Café crème"
    assert extract_text("vieux.txt", "Café crème".encode("cp1252")) == "Café crème"
    assert extract_text("bom.csv", "﻿a;b".encode("utf-8")) == "a;b"


def test_pdf_text_is_extracted():
    assert "Rapport annuel 2026" in extract_text("rapport.pdf", make_pdf("Rapport annuel 2026"))


def test_word_documents_are_read():
    assert extract_text("lettre.docx", make_docx(["Bonjour,", "A &amp; B"])) == "Bonjour,\nA & B"


def test_binary_files_are_refused():
    with pytest.raises(AttachmentError, match="format non pris en charge"):
        extract_text("programme.exe", b"MZ\x00\x00\x01")


def test_attachments_are_split_between_images_and_documents():
    images, documents = prepare_attachments(
        [attachment("photo.jpg", b"\xff\xd8image", "image/jpeg"), attachment("..\\..\\notes.txt", b"hello", "text/plain")]
    )

    assert images == [("photo.jpg", base64.b64encode(b"\xff\xd8image").decode())]
    assert documents == [("notes.txt", "hello")]


def test_invalid_attachments():
    with pytest.raises(AttachmentError, match="encodage invalide"):
        prepare_attachments([SimpleNamespace(name="a.txt", type="text/plain", data="pas du base64 !")])
    with pytest.raises(AttachmentError, match="format d'image"):
        prepare_attachments([attachment("dessin.svg", b"<svg/>", "image/svg+xml")])
    with pytest.raises(AttachmentError, match="trop gros"):
        prepare_attachments([attachment("gros.txt", b"a" * (20 * 1024 * 1024 + 1))])
