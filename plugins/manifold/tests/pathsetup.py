"""Test path setup for manifold MCP tests."""
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_ROOT = REPO_ROOT / "packages" / "manifold"
MCP_ROOT = REPO_ROOT / "plugins" / "manifold"

for p in (str(PKG_ROOT), str(MCP_ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

_spec = importlib.util.spec_from_file_location(
    "manifold_test_conftest", PKG_ROOT / "tests" / "conftest.py"
)
_conftest = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_conftest)
fresh_db = _conftest.fresh_db
seed_project = _conftest.seed_project
seed_portfolio_fixture = _conftest.seed_portfolio_fixture
