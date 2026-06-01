import json
from contextlib import redirect_stdout
from io import StringIO

from hephaestus.cli.main import main


def test_cli_lists_core_files_as_json() -> None:
    stdout = StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["list-core-files", "--json"])

    payload = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert "hephaestus/tool/types.py" in payload["core_files"]


def test_cli_lists_proof_cases_as_json() -> None:
    stdout = StringIO()
    with redirect_stdout(stdout):
        exit_code = main(["list-proof-cases", "--json"])

    payload = json.loads(stdout.getvalue())
    assert exit_code == 0
    assert "tabletop_two_category_ordered_proof_v1" in payload["proof_cases"]
