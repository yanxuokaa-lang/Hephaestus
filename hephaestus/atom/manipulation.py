from __future__ import annotations

from typing import Any

from hephaestus.atom.motion import MotionAtoms
from hephaestus.atom.perception import PerceptionAtoms
from hephaestus.tool.robot_arm import RobotArm
from hephaestus.tool.types import CommandResult, Pose


class ManipulationAtoms:
    def __init__(
        self,
        arm: RobotArm,
        motion: MotionAtoms | None = None,
        perception: PerceptionAtoms | None = None,
    ) -> None:
        self._arm = arm
        self._motion = motion
        self._perception = perception

    def grasp(
        self,
        target: Pose | None = None,
        force: float = 0.5,
        width: float = 0.04,
        speed: float = 0.5,
        dry_run: bool = True,
    ) -> CommandResult:
        if force <= 0.0:
            raise ValueError("force must be positive.")
        if width < 0.0:
            raise ValueError("width must be non-negative.")
        if speed <= 0.0:
            raise ValueError("speed must be positive.")
        result = self._arm.gripper("close", dry_run=dry_run)
        data = dict(result.data)
        data.update(
            {
                "force": force,
                "width": width,
                "speed": speed,
                "target_pose": _pose_to_dict(target) if target is not None else None,
            }
        )
        return CommandResult(success=result.success, message=result.message, data=data)

    def release(self, dry_run: bool = True) -> CommandResult:
        return self._arm.gripper("open", dry_run=dry_run)

    def push(
        self,
        object_name: str,
        target: Pose,
        direction: str,
        distance: float,
        speed: float = 0.5,
        dry_run: bool = True,
    ) -> CommandResult:
        motion = self._require_motion()
        pre_contact = motion.approach(target, direction="top", distance=0.05, speed=speed, dry_run=dry_run)
        if not pre_contact.success:
            return _failed_contact_result("pre_contact", pre_contact)
        contact = motion.move_to(target, speed=speed, dry_run=dry_run)
        if not contact.success:
            return _failed_contact_result("contact", contact)
        pushed_pose = _offset_pose(target, direction=direction, distance=distance)
        push_result = motion.move_to(pushed_pose, speed=speed, dry_run=dry_run)
        if not push_result.success:
            return _failed_contact_result("push", push_result)
        retreat = motion.approach(pushed_pose, direction="top", distance=0.05, speed=speed, dry_run=dry_run)
        steps = [
            _step_dict("pre_contact", pre_contact),
            _step_dict("contact", contact),
            _step_dict("push", push_result),
            _step_dict("retreat", retreat),
        ]
        return CommandResult(
            success=retreat.success,
            message="push completed" if retreat.success else retreat.message,
            data={
                "object_name": object_name,
                "direction": direction,
                "distance": distance,
                "contact_mode": "brief",
                "steps": steps,
            },
        )

    def slide(
        self,
        object_name: str,
        target: Pose,
        direction: str,
        distance: float,
        speed: float = 0.5,
        dry_run: bool = True,
    ) -> CommandResult:
        motion = self._require_motion()
        pre_contact = motion.approach(target, direction="top", distance=0.05, speed=speed, dry_run=dry_run)
        if not pre_contact.success:
            return _failed_contact_result("pre_contact", pre_contact)
        contact = motion.move_to(target, speed=speed, dry_run=dry_run)
        if not contact.success:
            return _failed_contact_result("contact", contact)
        slide_target = _offset_pose(target, direction=direction, distance=distance)
        slide_result = motion.move_to(slide_target, speed=speed, dry_run=dry_run)
        if not slide_result.success:
            return _failed_contact_result("slide", slide_result)
        retreat = motion.approach(slide_target, direction="top", distance=0.05, speed=speed, dry_run=dry_run)
        steps = [
            _step_dict("pre_contact", pre_contact),
            _step_dict("contact", contact),
            _step_dict("slide", slide_result),
            _step_dict("retreat", retreat),
        ]
        return CommandResult(
            success=retreat.success,
            message="slide completed" if retreat.success else retreat.message,
            data={
                "object_name": object_name,
                "direction": direction,
                "distance": distance,
                "contact_mode": "maintained",
                "steps": steps,
            },
        )

    def pick(
        self,
        object_name: str,
        *,
        dry_run: bool = True,
        speed: float = 0.5,
        approach_distance: float = 0.06,
        lift_distance: float = 0.06,
    ) -> CommandResult:
        motion = self._require_motion()
        perception = self._require_perception()
        observation = self._arm.get_observation()
        try:
            detections = perception.detect(observation.rgb, object_name)
        except Exception as exc:
            return _failed_exception_result("detect", exc)
        if not detections:
            return CommandResult(success=False, message="object not detected", data={"steps": []})
        detect_step = {"name": "detect", "success": True, "message": "object detected", "data": {"count": len(detections)}}
        try:
            point_cloud = (
                perception.get_point_cloud(observation, object_name)
                if self._can_get_point_cloud(perception)
                else observation.depth
            )
        except Exception as exc:
            return _failed_exception_result("get_point_cloud", exc, steps=[detect_step])
        try:
            pose = perception.estimate_pose(point_cloud, object_name)
        except Exception as exc:
            return _failed_exception_result("estimate_pose", exc, steps=[detect_step])
        approach_result = motion.approach(pose, direction="top", distance=approach_distance, speed=speed, dry_run=dry_run)
        if not approach_result.success:
            return _failed_contact_result("approach", approach_result)
        grasp_pose_result = motion.move_to(pose, speed=speed, dry_run=dry_run)
        if not grasp_pose_result.success:
            return _failed_contact_result("grasp_pose", grasp_pose_result)
        grasp_result = self.grasp(target=pose, speed=speed, dry_run=dry_run)
        if not grasp_result.success:
            return _failed_contact_result("gripper_close", grasp_result)
        lift_result = motion.retreat(
            direction="top",
            distance=lift_distance,
            speed=speed,
            dry_run=dry_run,
            reference_pose=pose,
        )
        steps = [
            detect_step,
            {"name": "estimate_pose", "success": True, "message": "pose estimated", "data": {"pose": _pose_to_dict(pose)}},
            _step_dict("approach", approach_result),
            _step_dict("grasp_pose", grasp_pose_result),
            _step_dict("gripper_close", grasp_result),
            _step_dict("lift", lift_result),
        ]
        return CommandResult(
            success=lift_result.success,
            message="pick completed" if lift_result.success else lift_result.message,
            data={
                "object_name": object_name,
                "target_pose": _pose_to_dict(pose),
                "steps": steps,
            },
        )

    def _require_motion(self) -> MotionAtoms:
        if self._motion is None:
            raise RuntimeError("Manipulation atom requires MotionAtoms for composed contact primitives.")
        return self._motion

    def _require_perception(self) -> PerceptionAtoms:
        if self._perception is None:
            raise RuntimeError("Manipulation atom requires PerceptionAtoms for composed pick.")
        return self._perception

    def _can_get_point_cloud(self, perception: PerceptionAtoms) -> bool:
        return getattr(perception, "_object_pose_provider", None) is not None


def _failed_contact_result(name: str, result: CommandResult) -> CommandResult:
    return CommandResult(
        success=False,
        message=result.message,
        data={"failed_step": name, "step": _step_dict(name, result), "steps": [_step_dict(name, result)]},
    )


def _failed_exception_result(name: str, exc: Exception, *, steps: list[dict[str, Any]] | None = None) -> CommandResult:
    return CommandResult(
        success=False,
        message=f"{name} failed: {exc}",
        data={
            "failed_step": name,
            "error": {"type": type(exc).__name__, "message": str(exc)},
            "steps": list(steps or []),
        },
    )


def _offset_pose(target: Pose, *, direction: str, distance: float) -> Pose:
    axis = direction.strip().lower()
    x, y, z = target.position
    offsets = {
        "top": (0.0, 0.0, distance),
        "front": (distance, 0.0, 0.0),
        "back": (-distance, 0.0, 0.0),
        "side": (0.0, distance, 0.0),
        "left": (0.0, distance, 0.0),
        "right": (0.0, -distance, 0.0),
    }
    if axis not in offsets:
        raise ValueError(f"Unsupported contact direction '{direction}'.")
    dx, dy, dz = offsets[axis]
    return Pose(position=(x + dx, y + dy, z + dz), orientation=target.orientation, frame=target.frame)


def _step_dict(name: str, result: CommandResult) -> dict[str, Any]:
    return {
        "name": name,
        "success": result.success,
        "message": result.message,
        "data": dict(result.data),
    }


def _pose_to_dict(pose: Pose | None) -> dict[str, Any] | None:
    if pose is None:
        return None
    return {
        "position": pose.position,
        "orientation": pose.orientation,
        "frame": pose.frame,
    }
