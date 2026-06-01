from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
import json
from typing import Any

from hephaestus import PUBLIC_CORE_SOURCE_FILES
from hephaestus.skill import STAGED_GRASP_POLICY
from hephaestus.task import get_proof_case, proof_case_names
from hephaestus.tool import get_scene_carrier


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hephaestus")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_core = subparsers.add_parser("list-core-files", help="List the public core source files.")
    list_core.add_argument("--json", action="store_true")

    list_cases = subparsers.add_parser("list-proof-cases", help="List the public proof-case names.")
    list_cases.add_argument("--json", action="store_true")

    show_scene = subparsers.add_parser("show-scene-carrier", help="Show a public scene-carrier contract.")
    show_scene.add_argument("scenario_name")
    show_scene.add_argument("--json", action="store_true")

    show_policy = subparsers.add_parser("show-grasp-policy", help="Show the staged public grasp policy.")
    show_policy.add_argument("--json", action="store_true")

    show_case = subparsers.add_parser("show-proof-case", help="Show a public proof-case contract.")
    show_case.add_argument("case_name")
    show_case.add_argument("--json", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command

    if command == "list-core-files":
        return _emit({"core_files": list(PUBLIC_CORE_SOURCE_FILES)}, as_json=args.json)
    if command == "list-proof-cases":
        return _emit({"proof_cases": list(proof_case_names())}, as_json=args.json)
    if command == "show-scene-carrier":
        return _emit(get_scene_carrier(args.scenario_name), as_json=args.json)
    if command == "show-grasp-policy":
        return _emit({"stages": list(STAGED_GRASP_POLICY)}, as_json=args.json)
    if command == "show-proof-case":
        return _emit(get_proof_case(args.case_name), as_json=args.json)

    raise ValueError(f"Unsupported command: {command}")


def entrypoint() -> None:
    raise SystemExit(main())


def _emit(payload: Any, *, as_json: bool) -> int:
    normalized = _normalize(payload)
    if as_json:
        print(json.dumps(normalized, indent=2, sort_keys=True))
    else:
        print(normalized)
    return 0


def _normalize(value: Any) -> Any:
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, dict):
        return {key: _normalize(inner) for key, inner in value.items()}
    if isinstance(value, tuple):
        return [_normalize(inner) for inner in value]
    if isinstance(value, list):
        return [_normalize(inner) for inner in value]
    return value
