from langchain_core.documents import Document
from retrieve_tools import _relevant_chunks
import retrieve_tools

def test_range_retrieval_preserves_matching_rows():
    chunks = [Document(page_content=f"Albums\nYear: {year} | Album: Test {year}",
                       metadata={"section": "Albums", "kind": "table_row", "year": year})
              for year in range(1960, 1966)]
    result = _relevant_chunks("How many albums between 1961 and 1963?", chunks)
    assert [r.metadata["year"] for r in result] == [1961, 1962, 1963]


def test_year_column_scopes_studio_count_and_preserves_unknowns(monkeypatch):
    html = """
    <h2 class="mw-heading"><h2>Discography</h2></h2>
    <div class="mw-heading"><h3>Studio albums</h3></div>
    <table class="wikitable">
      <tr><th>Year</th><th>Album details</th></tr>
      <tr><td>1999</td><td>Before</td></tr>
      <tr><td>2000</td><td>First Label: A</td></tr>
      <tr><td>2000</td><td>first Label: B</td></tr>
      <tr><td>2009</td><td>Last</td></tr>
      <tr><td>2010</td><td>After</td></tr>
      <tr><td>Unknown</td><td>Undated</td></tr>
    </table>
    <div class="mw-heading"><h3>Live albums</h3></div>
    <table class="wikitable">
      <tr><th>Year</th><th>Title</th></tr>
      <tr><td>2004</td><td>Live record</td></tr>
    </table>
    """
    monkeypatch.setattr(retrieve_tools, "_api", lambda _: {"parse": {"text": html}})
    chunks = retrieve_tools._article_chunks.__wrapped__(42)
    result = _relevant_chunks("How many studio albums between 2000 and 2009?", chunks)
    assert [(row.metadata["title"], row.metadata["year"]) for row in result] == [
        ("First", 2000), ("Last", 2009), ("Undated", None),
    ]
