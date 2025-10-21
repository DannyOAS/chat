"""Document extraction utilities for knowledge ingestion."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import requests
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


def extract_text_from_pdf(path: Path) -> str:
    try:
        from PyPDF2 import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency missing
        raise RuntimeError("PyPDF2 is required to process PDF files") from exc

    reader = PdfReader(path)
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:  # pragma: no cover - defensive
            logger.exception("Failed to extract text from PDF page")
    return "\n".join(texts)


def extract_text_from_docx(path: Path) -> str:
    try:
        import docx  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("python-docx is required to process DOCX files") from exc

    document = docx.Document(path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def extract_text_from_html(url: str) -> str:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("beautifulsoup4 is required to process HTML sources") from exc

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Unable to fetch URL {url}: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split())


def extract_text_from_file(upload) -> str:
    """Extract text from a Django file or uploaded file object."""

    name = getattr(upload, "name", "upload")
    suffix = Path(name).suffix.lower()

    # Ensure we have a local path to operate on
    if hasattr(upload, "path"):
        temp_path = Path(upload.path)
    else:
        temp_path = Path(default_storage.path(name))
        with default_storage.open(name, "wb+") as destination:
            for chunk in upload.chunks():
                destination.write(chunk)
    try:
        if suffix == ".pdf":
            return extract_text_from_pdf(temp_path)
        if suffix in {".docx"}:
            return extract_text_from_docx(temp_path)
        text = temp_path.read_text(encoding="utf-8", errors="ignore")
        return text
    finally:
        if not hasattr(upload, "path"):
            try:
                temp_path.unlink()
            except FileNotFoundError:  # pragma: no cover
                pass


def combine_segments(segments: Iterable[str]) -> str:
    return "\n".join(segment.strip() for segment in segments if segment.strip())
