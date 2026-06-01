from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Protocol

from hephaestus.tool.types import BoundingBox, CameraInfo, CommandResult, MotionCommand, Observation, Pose, RobotState


class SimulationBackend(Protocol):
    def move_to(self, command: MotionCommand) -> CommandResult:
        ...

    def move_joints(self, positions: tuple[float, ...], speed: float, dry_run: bool) -> CommandResult:
        ...

    def set_gripper(self, state: str, dry_run: bool) -> CommandResult:
        ...

    def stabilize_grasp(self, close_steps: int, hold_steps: int, dry_run: bool) -> CommandResult:
        ...

    def settle(self, steps: int, dry_run: bool) -> CommandResult:
        ...

    def observation(self) -> Observation:
        ...

    def state(self) -> RobotState:
        ...

    def solve_ik(self, target: Pose) -> tuple[float, ...] | None:
        ...

    def joint_limits(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        ...

    def terminal_diagnostics(self, object_name: str) -> dict[str, Any]:
        ...

    def phase_diagnostics(
        self,
        object_name: str,
        *,
        phase: str,
        planned_tcp_pose: Pose | None = None,
    ) -> dict[str, Any]:
        ...

    def set_grasp_reference_source(self, object_name: str, source: str) -> None:
        ...


@dataclass
class DeterministicSimBackend:
    workspace: BoundingBox
    dof: int = 7
    ee_pose: Pose | None = None
    joint_pos: tuple[float, ...] | None = None
    gripper_state: float = 0.0
    command_history: list[dict[str, object]] = field(default_factory=list)
    _timestamp: float = 0.0
    _last_ik_seed: tuple[float, ...] | None = None
    _last_ik_target: Pose | None = None
    _last_ik_joints: tuple[float, ...] | None = None
    _grasp_reference_sources: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.dof <= 0:
            raise ValueError("dof must be positive.")
        if self.ee_pose is None:
            self.ee_pose = Pose(position=(0.0, 0.0, 0.2), orientation=(0.0, 0.0, 0.0, 1.0), frame=self.workspace.frame)
        if self.joint_pos is None:
            self.joint_pos = tuple(0.0 for _ in range(self.dof))
        if len(self.joint_pos) != self.dof:
            raise ValueError("joint_pos length must match dof.")

    def move_to(self, command: MotionCommand) -> CommandResult:
        self.ee_pose = command.target
        self._tick()
        self.command_history.append(
            {
                "command_type": command.command_type,
                "target": command.target.position,
                "speed": command.speed,
                "dry_run": command.dry_run,
            }
        )
        return CommandResult(
            success=True,
            message="deterministic simulation move_to accepted",
            data={"target": command.target.position, "dry_run": bool(command.dry_run)},
        )

    def move_joints(self, positions: tuple[float, ...], speed: float, dry_run: bool) -> CommandResult:
        self.joint_pos = positions
        self._tick()
        self.command_history.append(
            {
                "command_type": "move_joints",
                "positions": positions,
                "speed": speed,
                "dry_run": dry_run,
            }
        )
        return CommandResult(
            success=True,
            message="deterministic simulation joints accepted",
            data={"positions": positions, "dry_run": dry_run},
        )

    def set_gripper(self, state: str, dry_run: bool) -> CommandResult:
        self.gripper_state = 1.0 if state == "close" else 0.0
        self._tick()
        self.command_history.append({"command_type": "gripper", "state": state, "dry_run": dry_run})
        return CommandResult(
            success=True,
            message=f"deterministic simulation gripper {state}",
            data={"state": state, "dry_run": dry_run},
        )

    def stabilize_grasp(self, close_steps: int, hold_steps: int, dry_run: bool) -> CommandResult:
        if close_steps < 1:
            return CommandResult(success=False, message="close_steps must be positive.", data={})
        if hold_steps < 0:
            return CommandResult(success=False, message="hold_steps must be non-negative.", data={})
        self.gripper_state = 1.0
        self._tick()
        self.command_history.append(
            {
                "command_type": "stabilize_grasp",
                "close_steps": close_steps,
                "hold_steps": hold_steps,
                "dry_run": dry_run,
            }
        )
        return CommandResult(
            success=True,
            message="deterministic simulation grasp stabilized",
            data={
                "command_type": "stabilize_grasp",
                "close_steps": close_steps,
                "hold_steps": hold_steps,
                "dry_run": dry_run,
            },
        )

    def settle(self, steps: int, dry_run: bool) -> CommandResult:
        if steps < 1:
            return CommandResult(success=False, message="steps must be positive.", data={})
        self._tick()
        self.command_history.append(
            {
                "command_type": "settle",
                "steps": steps,
                "dry_run": dry_run,
            }
        )
        return CommandResult(
            success=True,
            message="deterministic simulation settled",
            data={
                "command_type": "settle",
                "steps": steps,
                "completed_steps": steps,
                "dry_run": dry_run,
            },
        )

    def observation(self) -> Observation:
        return Observation(
            rgb=None,
            depth=None,
            camera_info=CameraInfo(
                name="deterministic_camera",
                frame="camera",
                intrinsics=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                extrinsics=Pose(position=(0.0, 0.0, 0.0), orientation=(0.0, 0.0, 0.0, 1.0), frame=self.workspace.frame),
                resolution=(0, 0),
            ),
            joint_pos=self.joint_pos or (),
            joint_vel=tuple(0.0 for _ in range(self.dof)),
            ee_pose=self.ee_pose or Pose(
                position=(0.0, 0.0, 0.2),
                orientation=(0.0, 0.0, 0.0, 1.0),
                frame=self.workspace.frame,
            ),
            gripper_state=self.gripper_state,
            timestamp=self._timestamp,
        )

    def state(self) -> RobotState:
        observation = self.observation()
        return RobotState(
            joint_pos=observation.joint_pos,
            joint_vel=observation.joint_vel,
            ee_pose=observation.ee_pose,
            gripper_state=observation.gripper_state,
            in_collision=False,
            workspace_bounds=self.workspace,
        )

    def solve_ik(self, target: Pose) -> tuple[float, ...] | None:
        self._last_ik_seed = self.joint_pos
        self._last_ik_target = target
        if target.frame != self.workspace.frame or not self.workspace.contains(target):
            self._last_ik_joints = None
            return None
        lower, upper = self.joint_limits()
        seed = (
            target.position[0],
            target.position[1],
            target.position[2],
            target.orientation[0],
            target.orientation[1],
            target.orientation[2],
            target.orientation[3],
        )
        values = tuple(seed[index % len(seed)] for index in range(self.dof))
        self._last_ik_joints = tuple(
            max(low, min(high, value)) for value, low, high in zip(values, lower, upper, strict=True)
        )
        return self._last_ik_joints

    def joint_limits(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        return tuple(-2.9 for _ in range(self.dof)), tuple(2.9 for _ in range(self.dof))

    def terminal_diagnostics(self, object_name: str) -> dict[str, Any]:
        state = self.state()
        return {
            "backend": "deterministic",
            "frame": self.workspace.frame,
            "tcp_pose": _pose_to_dict(state.ee_pose),
            "tcp_pose_source": "deterministic_state",
            "tcp_pose_available": True,
            "object_pose": None,
            "gripper_state": state.gripper_state,
            "gripper_target": state.gripper_state,
            "gripper_width_m": None,
            "grasp_reference_source": self._grasp_reference_sources.get(object_name),
            "sim_flags": {
                "sim_success": None,
                "is_grasped": None,
                "is_obj_placed": None,
                "is_robot_static": None,
            },
        }

    def phase_diagnostics(
        self,
        object_name: str,
        *,
        phase: str,
        planned_tcp_pose: Pose | None = None,
    ) -> dict[str, Any]:
        state = self.state()
        diagnostics = self.terminal_diagnostics(object_name)
        diagnostics.update(
            {
                "diagnostic_scope": "phase",
                "phase": phase,
                "planned_tcp_pose": _pose_to_dict(planned_tcp_pose) if planned_tcp_pose is not None else None,
                "actual_tcp_pose": _pose_to_dict(state.ee_pose),
                "tcp_error_m": _pose_distance(planned_tcp_pose, state.ee_pose),
                "joint_qpos": state.joint_pos,
                "joint_qvel": state.joint_vel,
                "ik": self._ik_diagnostics(),
            }
        )
        return diagnostics

    def set_grasp_reference_source(self, object_name: str, source: str) -> None:
        if object_name and source:
            self._grasp_reference_sources[str(object_name)] = str(source)

    def _tick(self) -> None:
        self._timestamp += 1.0

    def _ik_diagnostics(self) -> dict[str, Any] | None:
        if self._last_ik_target is None:
            return None
        return {
            "target_pose": _pose_to_dict(self._last_ik_target),
            "seed": self._last_ik_seed,
            "success": self._last_ik_joints is not None,
            "solver": "deterministic",
            "message": (
                "deterministic IK solved"
                if self._last_ik_joints is not None
                else "deterministic IK rejected target"
            ),
            "iterations": 0,
            "error_norm": 0.0 if self._last_ik_joints is not None else None,
            "joint_count": len(self._last_ik_joints) if self._last_ik_joints is not None else 0,
        }


def _pose_to_dict(pose: Pose) -> dict[str, Any]:
    return {
        "position": pose.position,
        "orientation": pose.orientation,
        "frame": pose.frame,
    }


def _pose_distance(planned: Pose | None, actual: Pose | None) -> float | None:
    if planned is None or actual is None or planned.frame != actual.frame:
        return None
    return math.dist(planned.position, actual.position)
