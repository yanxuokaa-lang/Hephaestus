from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hephaestus.tool.types import Pose


@dataclass(frozen=True)
class PlacePolicyDecision:
    strategy_stage: str | None
    release_goal_pose: Pose
    metadata: dict[str, Any]


def resolve_place_policy(
    *,
    strategy_candidate_id: str | None,
    release_goal_pose: Pose,
) -> PlacePolicyDecision:
    if strategy_candidate_id != "place_release_height_pos_0_01":
        return PlacePolicyDecision(
            strategy_stage=None,
            release_goal_pose=release_goal_pose,
            metadata={},
        )
    x, y, z = release_goal_pose.position
    return PlacePolicyDecision(
        strategy_stage="place",
        release_goal_pose=Pose(
            position=(x, y, z + 0.01),
            orientation=release_goal_pose.orientation,
            frame=release_goal_pose.frame,
        ),
        metadata={"release_height_offset_m": 0.01},
    )
