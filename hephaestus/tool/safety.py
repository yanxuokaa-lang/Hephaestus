from __future__ import annotations

from dataclasses import dataclass

from hephaestus.tool.types import BoundingBox, MotionCommand, SafetyRecord


class SafetyViolation(ValueError):
    """Raised when a robotics command fails pre-execution validation."""


@dataclass(frozen=True)
class SafetyKeepoutZone:
    name: str
    bounds: BoundingBox


@dataclass(frozen=True)
class SafetyValidator:
    workspace: BoundingBox
    dry_run_default: bool = True
    live_run_enabled: bool = False
    keepout_zones: tuple[SafetyKeepoutZone, ...] = ()
    path_overflight_clearance_m: float = 0.02

    def __post_init__(self) -> None:
        if self.path_overflight_clearance_m < 0.0:
            raise ValueError("path_overflight_clearance_m must be non-negative.")
        for zone in self.keepout_zones:
            if zone.bounds.frame != self.workspace.frame:
                raise ValueError(
                    f"Keepout zone '{zone.name}' frame '{zone.bounds.frame}' does not match workspace frame "
                    f"'{self.workspace.frame}'."
                )

    def validate_motion(self, command: MotionCommand, *, reference_pose=None) -> SafetyRecord:
        if not command.command_type:
            raise SafetyViolation("Command type must be non-empty.")
        if command.speed <= 0.0:
            raise SafetyViolation("Motion speed must be positive.")
        if command.target.frame != self.workspace.frame:
            raise SafetyViolation(
                f"Target frame '{command.target.frame}' does not match workspace frame '{self.workspace.frame}'."
            )
        if not self.workspace.contains(command.target):
            raise SafetyViolation(f"Motion target {command.target.position} is outside workspace bounds.")
        if reference_pose is not None and reference_pose.frame != self.workspace.frame:
            raise SafetyViolation(
                f"Reference frame '{reference_pose.frame}' does not match workspace frame '{self.workspace.frame}'."
            )

        self._validate_keepout_zones(command, reference_pose=reference_pose)

        dry_run = self.dry_run_default if command.dry_run is None else command.dry_run
        if not dry_run and not self.live_run_enabled:
            raise SafetyViolation("Live execution is disabled; use dry_run or explicitly enable live_run.")

        return SafetyRecord(
            accepted=True,
            command_type=command.command_type,
            frame=command.target.frame,
            dry_run=dry_run,
            reason="validated",
        )

    def _validate_keepout_zones(self, command: MotionCommand, *, reference_pose) -> None:
        for zone in self.keepout_zones:
            if zone.bounds.contains(command.target):
                raise SafetyViolation(
                    f"Motion target {command.target.position} enters keepout zone '{zone.name}'."
                )
            if reference_pose is None:
                continue
            if _path_intersects_keepout_zone(
                start=reference_pose.position,
                target=command.target.position,
                bounds=zone.bounds,
                overflight_clearance_m=self.path_overflight_clearance_m,
            ):
                raise SafetyViolation(
                    f"Motion path from {reference_pose.position} to {command.target.position} intersects keepout "
                    f"zone '{zone.name}'."
                )


def _path_intersects_keepout_zone(
    *,
    start: tuple[float, float, float],
    target: tuple[float, float, float],
    bounds: BoundingBox,
    overflight_clearance_m: float,
) -> bool:
    if not _xy_segment_intersects_bounds(start=start, target=target, bounds=bounds):
        return False
    max_safe_z = float(bounds.max[2]) + overflight_clearance_m
    return min(float(start[2]), float(target[2])) < max_safe_z


def _xy_segment_intersects_bounds(
    *,
    start: tuple[float, float, float],
    target: tuple[float, float, float],
    bounds: BoundingBox,
) -> bool:
    x0, y0 = float(start[0]), float(start[1])
    x1, y1 = float(target[0]), float(target[1])
    min_x, min_y = float(bounds.min[0]), float(bounds.min[1])
    max_x, max_y = float(bounds.max[0]), float(bounds.max[1])

    dx = x1 - x0
    dy = y1 - y0
    t_min = 0.0
    t_max = 1.0

    for p, q in (
        (-dx, x0 - min_x),
        (dx, max_x - x0),
        (-dy, y0 - min_y),
        (dy, max_y - y0),
    ):
        if abs(p) <= 1e-12:
            if q < 0.0:
                return False
            continue
        ratio = q / p
        if p < 0.0:
            t_min = max(t_min, ratio)
        else:
            t_max = min(t_max, ratio)
        if t_min > t_max:
            return False
    return True
