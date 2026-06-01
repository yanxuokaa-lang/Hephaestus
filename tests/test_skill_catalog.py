from hephaestus.skill import STAGED_GRASP_POLICY, resolve_place_policy
from hephaestus.tool.types import Pose


def test_public_skill_policy_surface_is_stable() -> None:
    assert STAGED_GRASP_POLICY == ("pregrasp", "descend_contact", "close_hold", "lift", "settle")

    decision = resolve_place_policy(
        strategy_candidate_id="place_release_height_pos_0_01",
        release_goal_pose=Pose(
            position=(0.1, 0.2, 0.3),
            orientation=(0.0, 0.0, 0.0, 1.0),
            frame="world",
        ),
    )

    assert decision.strategy_stage == "place"
    assert decision.release_goal_pose.position == (0.1, 0.2, 0.31)
