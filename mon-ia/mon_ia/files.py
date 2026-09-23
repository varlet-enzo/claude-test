"""Lecture des fichiers joints : images, PDF, documents Word et fichiers texte."""

from __future__ import annotations

import base64
import binascii
import html
import io
import re
import zipfile
from pathlib import PurePath
from typing import Iterable, Protocol

MAX_FILE_BYTES = 20 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


class AttachmentError(ValueError):
    """Fichier joint impossible à lire (message destiné à l'utilisateur)."""


class Attachment(Protocol):
    name: str
    type: str
    data: str


def _decode(name: str, data: str) -> bytes:
    if data.startswith("data:") and "," in data:
        data = data.split(",", 1)[1]
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        raise AttachmentError(f"« {name} » est illisible (encodage invalide).") from None
    if len(raw) > MAX_FILE_BYTES:
        raise AttachmentError(f"« {name} » est trop gros (20 Mo maximum).")
    return raw


def _pdf_text(name: str, raw: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise AttachmentError("La lecture des PDF n'est pas installée (commande : pip install pypdf).") from None
    try:
        reader = PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:
            reader.decrypt("")
        pages = [(page.extract_text() or "").strip() for page in reader.pages]
    except Exception as exc:
        raise AttachmentError(f"« {name} » : PDF illisible ou protégé ({exc}).") from None
    text = "\n\n".join(f"[Page {number}]\n{page}" for number, page in enumerate(pages, start=1) if page)
    if not text:
        raise AttachmentError(f"« {name} » ne contient pas de texte lisible (c'est peut-être un document scanné).")
    return text


def _docx_text(name: str, raw: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8")
    except (zipfile.BadZipFile, KeyError, UnicodeDecodeError):
        raise AttachmentError(f"« {name} » : document Word illisible.") from None
    xml = re.sub(r"<w:tab/>", "\t", xml)
    xml = re.sub(r"<w:br[^>]*/>|</w:p>", "\n", xml)
    text = html.unescape(re.sub(r"<[^>]+>", "", xml))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_text(name: str, raw: bytes) -> str:
    lowered = name.lower()
    if lowered.endswith(".pdf") or raw.startswith(b"%PDF"):
        return _pdf_text(name, raw)
    if lowered.endswith(".docx"):
        return _docx_text(name, raw)
    if b"\x00" in raw[:8192]:
        raise AttachmentError(
            f"« {name} » : format non pris en charge. Je sais lire les images, les PDF, les documents Word (.docx) "
            "et les fichiers texte."
        )
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def prepare_attachments(files: Iterable[Attachment]) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Sépare les images (gardées en base64) des documents (convertis en texte)."""
    images: list[tuple[str, str]] = []
    documents: list[tuple[str, str]] = []
    for file in files:
        name = PurePath(file.name.replace("\\", "/")).name or "fichier"
        raw = _decode(name, file.data)
        if file.type.startswith("image/"):
            if file.type not in IMAGE_TYPES:
                raise AttachmentError(f"« {name} » : format d'image non pris en charge (JPEG, PNG ou WebP).")
            images.append((name, base64.b64encode(raw).decode("ascii")))
        else:
            documents.append((name, extract_text(name, raw)))
    return images, documents
