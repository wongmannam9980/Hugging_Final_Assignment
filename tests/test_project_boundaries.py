"""Static architecture boundary tests; no model calls or network."""
import ast
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_app_owns_graph_but_not_specialist_construction():
    tree = ast.parse((ROOT / 'app.py').read_text(encoding='utf-8'))
    names = {getattr(n, 'name', None) for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    assert {'AgentState', 'manager', 'final_answer', 'answer_question'} <= names
    assert '_specialist' not in names
    assert (ROOT / 'agents' / 'factory.py').exists()

def test_dry_run_has_no_submit_call():
    text = (ROOT / 'evals' / 'run_gaia_dry_run.py').read_text(encoding='utf-8')
    assert 'submit_url' not in text and 'requests.post' not in text
