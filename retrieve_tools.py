"""Reusable retrieval of relevant English Wikipedia article chunks."""

import re
from functools import lru_cache

import requests
from bs4 import BeautifulSoup
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter


API_URL = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "FinalUnitWikipediaRAG/1.0 (educational project)"}
SKIP_SECTIONS = {"references", "external links", "notes", "further reading"}
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "between", "by", "did",
    "do", "for", "from", "how", "in", "is", "many", "of", "on", "or",
    "the", "to", "was", "were", "what", "when", "which", "who", "with",
}


def _api(params: dict) -> dict:
    """Send one request to Wikipedia and return its JSON response."""
    response = requests.get(API_URL, params={**params, "format": "json"}, headers=HEADERS, timeout=30)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise ValueError(data["error"].get("info", "Wikipedia API error"))
    return data


def _article_for_topic(topic: str) -> tuple[str, int, str]:
    """Search Wikipedia for a topic and select the first matching article."""
    search = _api({
        "action": "query", "list": "search", "srsearch": topic,
        "srnamespace": 0, "srlimit": 3,
    })["query"]["search"]
    if not search:
        raise ValueError(f"No English Wikipedia article found for {topic!r}.")
    title = search[0]["title"]
    return title, search[0]["pageid"], search[0]["snippet"]


def _requested_revision_year(question: str) -> int | None:
    """Find a year when the question asks for an older Wikipedia version."""
    match = re.search(r"\b(20\d{2})\s+(?:version|revision)\b", question, re.I)
    if match is None:
        match = re.search(r"\bas\s+of\s+(20\d{2})\b", question, re.I)
    return int(match.group(1)) if match else None


def _get_revision(page_id: int, question: str) -> tuple[int, str]:
    """Get the latest article version, or its version at the requested year."""
    params = {
        "action": "query", "prop": "revisions", "pageids": page_id,
        "rvlimit": 1, "rvprop": "ids|timestamp", "formatversion": 2,
    }
    as_of_year = _requested_revision_year(question)
    if as_of_year is not None:
        params.update({"rvstart": f"{as_of_year}-12-31T23:59:59Z", "rvdir": "older"})
    page = _api(params)["query"]["pages"][0]
    revisions = page.get("revisions")
    if not revisions:
        raise ValueError(f"No Wikipedia revision found for {page.get('title', page_id)}.")
    return revisions[0]["revid"], revisions[0]["timestamp"]

def extract_year(date_text: str) -> int | None:
    """Extract a four-digit year from a release-date string."""
    match = re.search(r"\b(?:19|20)\d{2}\b", date_text)
    return int(match.group()) if match else None

def extract_release_date(details: str) -> str | None:
    """Extract an album's release date from Wikipedia's Details text."""

    match = re.search(
        r"Released:\s*(.+?)(?=\s+Label:|\s+Formats:|\[|$)",
        details,
        re.I
    )

    return match.group(1).strip() if match else None

def extract_album(headers: list[str], values: list[str]) -> dict | None:
    """Convert a Wikipedia album table row into structured data."""

    title_index = next(
        (i for i, header in enumerate(headers)
         if header.lower() == "title"),
        None
    )

    details_index = next(
        (i for i, header in enumerate(headers)
         if header.lower() == "details"),
        None
    )

    if title_index is None or details_index is None:
        return None

    if max(title_index, details_index) >= len(values):
        return None

    title = values[title_index]
    details = values[details_index]

    release_date = extract_release_date(details)

    if release_date is None:
        return None

    return {
        "title": title,
        "release_date": release_date,
        "year": extract_year(release_date)
    }

@lru_cache(maxsize=16)
def _article_chunks(revision_id: int) -> list[Document]:
    """Turn article paragraphs and table rows into searchable documents."""
    parsed = _api({
        "action": "parse", "oldid": revision_id,
        "prop": "text", "formatversion": 2,
    })["parse"]
    soup = BeautifulSoup(parsed["text"], "html.parser")
    root = soup.select_one(".mw-parser-output") or soup
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    section = "Introduction"
    subsection = ""
    chunks: list[Document] = []

    # Keep table rows separate so counts can be checked item by item.
    for element in root.find_all(recursive=False):
        if "mw-heading" in element.get("class", []):
            heading = element.find(["h2", "h3", "h4"])
            if heading:
                label = heading.get_text(" ", strip=True)
                if heading.name == "h2":
                    section, subsection = label, ""
                else:
                    subsection = label
            continue
        if section.lower() in SKIP_SECTIONS:
            continue
        section_name = f"{section} > {subsection}" if subsection else section

        if element.name == "table" and "wikitable" in element.get("class", []):
            rows = element.find_all("tr")
            if not rows:
                continue
            headers = [cell.get_text(" ", strip=True) 
                       for cell in rows[0].find_all(["th", "td"], recursive=False)]
            release_index = next(
                (
                    i for i, header in enumerate(headers)
                    if "release" in header.lower() or header.lower() == "year"
                ),
                None
            )
            for row in rows[1:]:
                cells = row.find_all(["th", "td"], recursive=False)
                if len(cells) < 2:
                    continue
                values = [cell.get_text(" ", strip=True) for cell in cells]
                album = extract_album(headers, values)
                content = " | ".join(
                    f"{headers[i] if i < len(headers) else f'Column {i + 1}'}: {value}"
                    for i, value in enumerate(values)
                )
                year = None

                if release_index is not None and release_index < len(values):
                    year = extract_year(values[release_index])
                if album and album["year"] is not None:
                    year = album["year"]
                title_index = next((i for i, header in enumerate(headers)
                                    if header.lower() in {"title", "album", "album details"}), None)
                title = values[title_index] if title_index is not None and title_index < len(values) else ""
                chunks.append(Document(
                    page_content=f"{section_name}\n{content}",
                    metadata={
                    "section": section_name,
                    "kind": "table_row",
                    "year": year,
                    "album": album,
                    "title": album["title"] if album else re.split(r"\s+Label:", title, maxsplit=1, flags=re.I)[0],
                    }
                ))
        elif element.name in {"p", "ul", "ol"}:
            text = element.get_text(" ", strip=True)
            if len(text) < 40:
                continue
            for part in splitter.split_text(text):
                chunks.append(Document(
                    page_content=f"{section_name}\n{part}",
                    metadata={"section": section_name, "kind": "text", "year": None},
                ))
    if not chunks:
        raise ValueError("No readable text or tables found in the Wikipedia article.")
    return chunks


def _words(text: str) -> set[str]:
    """Extract useful lowercase words for matching question and section titles."""
    return set(re.findall(r"[a-z]+", text.lower())) - STOP_WORDS

def choose_retrieval_strategy(question: str) -> str:
    """Choose filtering, BM25, or a hybrid strategy using keywords."""
    filter_keywords = ["how many", "between", "released in", "list all"]
    bm25_keywords = ["describe", "influenced", "explain", "history"]

    question_lower = question.lower()

    has_filter = any(
        keyword in question_lower
        for keyword in filter_keywords
    )

    has_bm25 = any(
        keyword in question_lower
        for keyword in bm25_keywords
    )

    if has_filter and has_bm25:
        return "hybrid"  # Prefer structured filtering when both are present.
    if has_filter:
        return "filter"
    if has_bm25:
        return "bm25"

    return "bm25"

def filter_album_chunks(
    chunks: list[Document],
    start_year: int,
    end_year: int
) -> list[Document]:
    """Return album records released within an inclusive year range."""

    matching = []
    seen = set()

    for chunk in chunks:
        album = chunk.metadata.get("album") or {}
        year = chunk.metadata.get("year", album.get("year"))
        title = chunk.metadata.get("title") or album.get("title") or chunk.page_content
        key = (" ".join(title.casefold().split()), year)
        if chunk.metadata.get("kind") == "table_row" and isinstance(year, int) and start_year <= year <= end_year and key not in seen:
            matching.append(chunk)
            seen.add(key)
    return matching

def _relevant_chunks(question: str, chunks: list[Document]) -> list[Document]:
    """Select relevant chunks using structured filters or BM25."""

    question_words = _words(question)

    section_scores = {
        section: len(question_words & _words(section))
        for section in {str(chunk.metadata["section"]) for chunk in chunks}
    }
    best_score = max(section_scores.values(), default=0)
    if best_score:
        best_sections = {section for section, score in section_scores.items() if score == best_score}
        candidates = [chunk for chunk in chunks if chunk.metadata["section"] in best_sections]
    else:
        candidates = chunks

    years = re.search(
    r"\b(?:between|from)\s+(\d{4})\s+(?:and|to)\s+(\d{4})\b",
    question,
    re.I
)
    if years and "albums" in question_words:
        start, end = map(int, years.groups())
        album_rows = [chunk for chunk in chunks if "albums" in _words(chunk.metadata["section"])
                      and chunk.metadata["kind"] == "table_row"]
        if "studio" in question_words:
            album_rows = [chunk for chunk in album_rows if "studio" in _words(chunk.metadata["section"])]
        if album_rows:
            matching = filter_album_chunks(album_rows, start, end)
            unknown = [chunk for chunk in album_rows if chunk.metadata.get("year") is None]
            return matching + unknown
    if not candidates:
        return []
    return BM25Retriever.from_documents(candidates, k=min(8, len(candidates))).invoke(question)


@tool
def wikipedia_retrieve(topic: str, question: str) -> str:
    """Find a Wikipedia article and return chunks relevant to the user's question.

    Args:
        topic: A short subject or article title taken from the user's question, such as a person's name.
        question: The full user question, including any requested Wikipedia version year.
    """
    try:
        title, page_id, _ = _article_for_topic(topic)
        revision_id, revision_time = _get_revision(page_id, question)
        all_chunks = _article_chunks(revision_id)

        chunks = _relevant_chunks(question, all_chunks)
    except requests.Timeout:
        raise
    except (requests.RequestException, KeyError, ValueError) as exc:
        return f"Wikipedia retrieval failed for {topic!r}: {exc}. Try a shorter or different topic."

    source_url = f"https://en.wikipedia.org/w/index.php?oldid={revision_id}"
    evidence = "\n\n".join(
        f"[Chunk {index}] {chunk.page_content}"
        + ("\nRelease year unknown." if chunk.metadata.get("title") and chunk.metadata.get("year") is None else "")
        for index, chunk in enumerate(chunks, start=1)
    )
    return (
        f"Article: {title}\nRevision: {revision_time}\nSource: {source_url}\n"
        f"Relevant evidence:\n{evidence or 'No matching rows in the selected article and revision.'}"
    )
