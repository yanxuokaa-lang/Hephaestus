from __future__ import annotations

import time

from hephaestus.tool.robot_arm import RobotArm
from hephaestus.tool.types import CommandResult, Pose


class UtilityAtoms:
    def __init__(self, arm: RobotArm) -> None:
        self._arm = arm

    def wait(self, seconds: float, dry_run: bool = True) -> CommandResult:
        if seconds < 0.0:
            raise ValueError("seconds must be non-negative.")
        if not dry_run:
            time.sleep(seconds)
        return CommandResult(
            success=True,
            message="wait completed" if not dry_run else "dry-run wait recorded",
            data={"seconds": seconds, "dry_run": dry_run},
        )

    def check_collision(self) -> bool:
        return bool(self._arm.get_state().in_collision)

    def get_joint_limits(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        return self._arm.get_joint_limits()

    def get_ik(self, target: Pose) -> tuple[float, ...] | None:
        if not isinstance(target, Pose):
            raise TypeError("target must be a Pose.")
        return self._arm.get_ik(target)
