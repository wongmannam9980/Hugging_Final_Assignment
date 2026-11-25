"""Read local attachments without executing their contents."""

import csv
import json
from pathlib import Path
from langchain_core.tools import tool

MAX_BYTES = 2_000_000
MAX_CHARS = 24_000
TEXT = {".txt", ".md", ".py", ".log", ".xml", ".html", ".htm"}


@tool
def inspect_file(path: str) -> str:
    """Extract readable text from a supported attachment for the file agent."""
    try:
        file = Path(path).expanduser().resolve(strict=True)
        if not file.is_file():
            return f"Not a file: {file}"
        # Limit file size and returned text so one attachment cannot fill the model context.
        if file.stat().st_size > MAX_BYTES:
            return f"File is larger than {MAX_BYTES} bytes: {file.name}"
        suffix = file.suffix.lower()
        if suffix in TEXT:
            content = file.read_text(encoding="utf-8-sig", errors="replace")
        elif suffix == ".json":
            content = json.dumps(json.loads(file.read_text(encoding="utf-8-sig")), ensure_ascii=False, indent=2)
        elif suffix in {".csv", ".tsv"}:
            with file.open(encoding="utf-8-sig", errors="replace", newline="") as handle:
                rows = list(csv.reader(handle, delimiter="\t" if suffix == ".tsv" else ","))
            content = "\n".join(" | ".join(row) for row in rows)
        elif suffix == ".pdf":
            from pypdf import PdfReader
            content = "\n".join(page.extract_text() or "" for page in PdfReader(file).pages)
        elif suffix == ".docx":
            from docx import Document
            content = "\n".join(p.text for p in Document(file).paragraphs)
        elif suffix == ".xlsx":
            from openpyxl import load_workbook
            book = load_workbook(file, read_only=True, data_only=True)
            content = "\n".join(
                f"Sheet: {sheet.title}\n" + "\n".join(
                    " | ".join("" if cell is None else str(cell) for cell in row)
                    for row in sheet.iter_rows(values_only=True))
                for sheet in book.worksheets)
            book.close()
        else:
            return f"Unsupported attachment type: {suffix or '(none)'} ({file.name})"
        if not content.strip():
            return f"No readable text found in {file.name}"
        return f"File: {file.name}\nContent:\n{content[:MAX_CHARS]}" + (
            "\n[Content truncated]" if len(content) > MAX_CHARS else "")
    except ImportError as exc:
        return f"Install the optional parser for {Path(path).suffix}: {exc}"
    except (OSError, ValueError, csv.Error) as exc:
        return f"Could not inspect file: {exc}"
