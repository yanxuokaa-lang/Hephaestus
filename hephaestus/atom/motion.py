from __future__ import annotations

import math
from typing import Any

from hephaestus.tool.robot_arm import RobotArm
from hephaestus.tool.safety import SafetyValidator, SafetyViolation
from hephaestus.tool.types import CommandResult, MotionCommand, Pose, Quaternion, SafetyRecord


class MotionAtoms:
    def __init__(self, arm: RobotArm, safety: SafetyValidator) -> None:
        self._arm = arm
        self._safety = safety

    def move_to(self, target: Pose, speed: float = 0.5, dry_run: bool | None = None) -> CommandResult:
        command = MotionCommand(command_type="move_to", target=target, speed=speed, dry_run=dry_run)
        record = self.validate(target, speed=speed, dry_run=dry_run)
        result = self._arm.move_to(command)
        return _with_safety(result, record)

    def move_joints(
        self,
        positions: tuple[float, ...],
        speed: float = 0.5,
        dry_run: bool | None = None,
    ) -> CommandResult:
        if not positions:
            raise SafetyViolation("Joint target must be non-empty.")
        dry_run_value = self._safety.dry_run_default if dry_run is None else dry_run
        return self._arm.move_joints(positions=positions, speed=speed, dry_run=dry_run_value)

    def approach(
        self,
        target: Pose,
        direction: str,
        distance: float,
        speed: float,
        dry_run: bool | None = None,
    ) -> CommandResult:
        offset_target = _offset_pose(target, direction=direction, distance=distance)
        result = self.move_to(offset_target, speed=speed, dry_run=dry_run)
        data = dict(result.data)
        data.update({"direction": direction, "distance": distance, "reference_pose": _pose_to_dict(target)})
        return CommandResult(success=result.success, message=result.message, data=data)

    def retreat(
        self,
        direction: str,
        distance: float,
        speed: float,
        dry_run: bool | None = None,
        reference_pose: Pose | None = None,
    ) -> CommandResult:
        base_pose = reference_pose or self._arm.get_state().ee_pose
        offset_target = _offset_pose(base_pose, direction=direction, distance=distance)
        result = self.move_to(offset_target, speed=speed, dry_run=dry_run)
        data = dict(result.data)
        data.update({"direction": direction, "distance": distance, "reference_pose": _pose_to_dict(base_pose)})
        return CommandResult(success=result.success, message=result.message, data=data)

    def rotate_gripper(
        self,
        axis: str,
        angle: float,
        speed: float,
        dry_run: bool | None = None,
        reference_pose: Pose | None = None,
    ) -> CommandResult:
        if not math.isfinite(angle):
            raise SafetyViolation("Rotation angle must be finite.")
        base_pose = reference_pose or self._arm.get_state().ee_pose
        target = Pose(
            position=base_pose.position,
            orientation=_rotate_orientation(base_pose.orientation, axis=axis, angle=angle),
            frame=base_pose.frame,
        )
        result = self.move_to(target, speed=speed, dry_run=dry_run)
        data = dict(result.data)
        data.update({"axis": axis, "angle": angle, "reference_pose": _pose_to_dict(base_pose)})
        return CommandResult(success=result.success, message=result.message, data=data)

    def adjust_height(
        self,
        delta: float,
        speed: float,
        dry_run: bool | None = None,
        reference_pose: Pose | None = None,
    ) -> CommandResult:
        if not math.isfinite(delta):
            raise SafetyViolation("Height delta must be finite.")
        base_pose = reference_pose or self._arm.get_state().ee_pose
        x, y, z = base_pose.position
        target = Pose(position=(x, y, z + delta), orientation=base_pose.orientation, frame=base_pose.frame)
        result = self.move_to(target, speed=speed, dry_run=dry_run)
        data = dict(result.data)
        data.update({"delta": delta, "reference_pose": _pose_to_dict(base_pose)})
        return CommandResult(success=result.success, message=result.message, data=data)

    def move_cartesian_path(
        self,
        waypoints: list[Pose],
        speed: float,
        dry_run: bool | None = None,
    ) -> CommandResult:
        if not waypoints:
            raise SafetyViolation("Cartesian path must contain at least one waypoint.")
        executed = 0
        for index, waypoint in enumerate(waypoints, start=1):
            try:
                result = self.move_to(waypoint, speed=speed, dry_run=dry_run)
            except SafetyViolation as exc:
                return CommandResult(
                    success=False,
                    message=str(exc),
                    data={
                        "failed_waypoint_index": index,
                        "executed_waypoints": executed,
                        "waypoint": _pose_to_dict(waypoint),
                    },
                )
            executed += 1
            if not result.success:
                data = dict(result.data)
                data.update({"failed_waypoint_index": index, "executed_waypoints": executed})
                return CommandResult(success=False, message=result.message, data=data)
        return CommandResult(
            success=True,
            message="cartesian path completed",
            data={
                "executed_waypoints": executed,
                "waypoint_count": len(waypoints),
                "path": [_pose_to_dict(waypoint) for waypoint in waypoints],
            },
        )

    def validate(self, target: Pose, speed: float = 0.5, dry_run: bool | None = None) -> SafetyRecord:
        command = MotionCommand(command_type="move_to", target=target, speed=speed, dry_run=dry_run)
        reference_pose = self._arm.get_state().ee_pose
        return self._safety.validate_motion(command, reference_pose=reference_pose)


def _with_safety(result: CommandResult, record: SafetyRecord) -> CommandResult:
    data = dict(result.data)
    data["safety"] = {
        "frame": record.frame,
        "dry_run": record.dry_run,
        "reason": record.reason,
    }
    return CommandResult(success=result.success, message=result.message, data=data)


def _offset_pose(target: Pose, *, direction: str, distance: float) -> Pose:
    if distance <= 0.0:
        raise SafetyViolation("Motion distance must be positive.")
    axis = direction.strip().lower()
    x, y, z = target.position
    offsets: dict[str, tuple[float, float, float]] = {
        "top": (0.0, 0.0, distance),
        "bottom": (0.0, 0.0, -distance),
        "front": (distance, 0.0, 0.0),
        "back": (-distance, 0.0, 0.0),
        "side": (0.0, distance, 0.0),
        "left": (0.0, distance, 0.0),
        "right": (0.0, -distance, 0.0),
    }
    if axis not in offsets:
        raise SafetyViolation(f"Unsupported motion direction '{direction}'.")
    dx, dy, dz = offsets[axis]
    return Pose(
        position=(round(x + dx, 12), round(y + dy, 12), round(z + dz, 12)),
        orientation=target.orientation,
        frame=target.frame,
    )


def _rotate_orientation(orientation: Quaternion, *, axis: str, angle: float) -> Quaternion:
    normalized_axis = axis.strip().lower()
    half_angle = angle / 2.0
    sin_half = math.sin(half_angle)
    cos_half = math.cos(half_angle)
    rotations: dict[str, Quaternion] = {
        "x": (sin_half, 0.0, 0.0, cos_half),
        "y": (0.0, sin_half, 0.0, cos_half),
        "z": (0.0, 0.0, sin_half, cos_half),
    }
    if normalized_axis not in rotations:
        raise SafetyViolation(f"Unsupported rotation axis '{axis}'.")
    return _normalize_quaternion(_quaternion_multiply(orientation, rotations[normalized_axis]))


def _quaternion_multiply(lhs: Quaternion, rhs: Quaternion) -> Quaternion:
    x1, y1, z1, w1 = lhs
    x2, y2, z2, w2 = rhs
    return (
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    )


def _normalize_quaternion(quaternion: Quaternion) -> Quaternion:
    norm = math.sqrt(sum(component * component for component in quaternion))
    if norm == 0.0:
        raise SafetyViolation("Quaternion norm must be non-zero.")
    return tuple(component / norm for component in quaternion)  # type: ignore[return-value]


def _pose_to_dict(pose: Pose) -> dict[str, Any]:
    return {
        "position": pose.position,
        "orientation": pose.orientation,
        "frame": pose.frame,
    }
