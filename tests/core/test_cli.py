import sys
from io import StringIO

from ag3tools.core.cli import main


def run_cli(args):
    old_argv = sys.argv
    old_stdout = sys.stdout
    try:
        sys.argv = ["ag3tools", *args]
        sys.stdout = StringIO()
        main()
        return sys.stdout.getvalue()
    finally:
        sys.argv = old_argv
        sys.stdout = old_stdout


def test_cli_list():
    out = run_cli(["list"])  # should print tool listing
    assert "web_search" in out and "find_docs" in out


def test_cli_docs_json():
    out = run_cli(["docs", "langgraph", "--json"])  # should print JSON
    assert out.strip().startswith("{")

