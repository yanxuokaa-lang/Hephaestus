from __future__ import annotations

from dataclasses import dataclass

from hephaestus.tool.scene_carrier import get_scene_carrier


@dataclass(frozen=True)
class ProofComparisonTarget:
    decision_change_target_category: str
    stable_builtin_category: str
    expected_baseline_selection_source: str
    expected_conditioned_selection_source: str
    expected_outcome_improvement_mode: str


@dataclass(frozen=True)
class ProofCaseSpec:
    case_name: str
    case_version: str
    scenario_profile: str
    scene_layout_name: str
    task_instruction: str
    ordered_categories: tuple[str, ...]
    expected_category_to_zone: dict[str, str]
    comparison_target: ProofComparisonTarget


def _tabletop_two_category_case() -> ProofCaseSpec:
    carrier = get_scene_carrier("tabletop_organization_v1")
    return ProofCaseSpec(
        case_name="tabletop_two_category_ordered_proof_v1",
        case_version="v1",
        scenario_profile=carrier.scenario_name,
        scene_layout_name=carrier.layout_name,
        task_instruction="put the toy car into the storage box, then put the fruit onto the plate",
        ordered_categories=("toy", "fruit"),
        expected_category_to_zone={
            "toy": carrier.category_to_canonical_zone["toy"],
            "fruit": carrier.category_to_canonical_zone["fruit"],
        },
        comparison_target=ProofComparisonTarget(
            decision_change_target_category="fruit",
            stable_builtin_category="toy",
            expected_baseline_selection_source="builtin_fallback",
            expected_conditioned_selection_source="promoted",
            expected_outcome_improvement_mode="success_gain",
        ),
    )


def _tabletop_single_fruit_case() -> ProofCaseSpec:
    carrier = get_scene_carrier("tabletop_organization_v1")
    return ProofCaseSpec(
        case_name="tabletop_single_fruit_promoted_proof_v1",
        case_version="v1",
        scenario_profile=carrier.scenario_name,
        scene_layout_name=carrier.layout_name,
        task_instruction="put the fruit onto the plate",
        ordered_categories=("fruit",),
        expected_category_to_zone={
            "fruit": carrier.category_to_canonical_zone["fruit"],
        },
        comparison_target=ProofComparisonTarget(
            decision_change_target_category="fruit",
            stable_builtin_category="",
            expected_baseline_selection_source="builtin_fallback",
            expected_conditioned_selection_source="promoted",
            expected_outcome_improvement_mode="success_gain",
        ),
    )


_PROOF_CASES = {
    "tabletop_two_category_ordered_proof_v1": _tabletop_two_category_case(),
    "tabletop_single_fruit_promoted_proof_v1": _tabletop_single_fruit_case(),
}


def proof_case_names() -> tuple[str, ...]:
    return tuple(_PROOF_CASES.keys())


def get_proof_case(case_name: str) -> ProofCaseSpec:
    case = _PROOF_CASES.get(case_name)
    if case is None:
        raise ValueError(f"proof case '{case_name}' is not registered by runtime.")
    return case
