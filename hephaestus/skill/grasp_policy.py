from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from hephaestus.tool.types import Pose, Quaternion, Vector3


STAGED_GRASP_POLICY = ("pregrasp", "descend_contact", "close_hold", "lift", "settle")


class GraspPlanner(Protocol):
    def plan(self, object_pose: Pose) -> "GraspPlan":
        ...


@dataclass(frozen=True)
class GraspPlan:
    object_pose: Pose
    approach_pose: Pose
    grasp_pose: Pose
    retreat_pose: Pose

    def motion_poses(self) -> tuple[Pose, Pose, Pose]:
        return self.approach_pose, self.grasp_pose, self.retreat_pose


@dataclass(frozen=True)
class TopDownGraspPlanner:
    grasp_clearance: float = 0.16
    approach_clearance: float = 0.20
    retreat_clearance: float = 0.20
    x_offset: float = 0.0
    y_offset: float = 0.0
    grasp_orientation: Quaternion = (0.0, 0.0, 0.0, 1.0)
    approach_orientation: Quaternion | None = None
    retreat_orientation: Quaternion | None = None
    approach_direction: Vector3 | None = None

    def __post_init__(self) -> None:
        if self.grasp_clearance < 0.0:
            raise ValueError("grasp_clearance must be non-negative.")
        if self.approach_clearance <= 0.0:
            raise ValueError("approach_clearance must be positive.")
        if self.retreat_clearance <= 0.0:
            raise ValueError("retreat_clearance must be positive.")
        object.__setattr__(
            self,
            "approach_orientation",
            self.grasp_orientation if self.approach_orientation is None else self.approach_orientation,
        )
        object.__setattr__(
            self,
            "retreat_orientation",
            self.grasp_orientation if self.retreat_orientation is None else self.retreat_orientation,
        )
        _validate_orientation(self.grasp_orientation, field_name="grasp_orientation")
        _validate_orientation(self.approach_orientation, field_name="approach_orientation")
        _validate_orientation(self.retreat_orientation, field_name="retreat_orientation")
        _validate_direction(self.approach_direction, field_name="approach_direction")

    def plan(self, object_pose: Pose) -> GraspPlan:
        object_x, object_y, z = object_pose.position
        x = _offset_xy(object_x, self.x_offset)
        y = _offset_xy(object_y, self.y_offset)
        grasp_z = _offset_z(z, self.grasp_clearance)
        grasp_position = (x, y, grasp_z)
        approach_pose = Pose(
            position=_offset_position(
                grasp_position,
                direction=(0.0, 0.0, 1.0) if self.approach_direction is None else self.approach_direction,
                distance=self.approach_clearance,
            ),
            orientation=self.grasp_orientation if self.approach_orientation is None else self.approach_orientation,
            frame=object_pose.frame,
        )
        grasp_pose = Pose(
            position=grasp_position,
            orientation=self.grasp_orientation,
            frame=object_pose.frame,
        )
        retreat_pose = Pose(
            position=(x, y, _offset_z(grasp_z, self.retreat_clearance)),
            orientation=self.grasp_orientation if self.retreat_orientation is None else self.retreat_orientation,
            frame=object_pose.frame,
        )
        return GraspPlan(
            object_pose=object_pose,
            approach_pose=approach_pose,
            grasp_pose=grasp_pose,
            retreat_pose=retreat_pose,
        )


def default_pick_grasp_plan(object_pose: Pose, *, approach_offset: float) -> GraspPlan:
    approach_pose = Pose(
        position=(object_pose.position[0], object_pose.position[1], _offset_z(object_pose.position[2], approach_offset)),
        orientation=object_pose.orientation,
        frame=object_pose.frame,
    )
    return GraspPlan(
        object_pose=object_pose,
        approach_pose=approach_pose,
        grasp_pose=object_pose,
        retreat_pose=approach_pose,
    )


def _offset_z(z: float, clearance: float) -> float:
    return round(z + clearance, 12)


def _offset_xy(value: float, offset: float) -> float:
    return round(value + offset, 12)


def _validate_orientation(orientation: Quaternion | None, *, field_name: str) -> None:
    if orientation is None or len(orientation) != 4:
        raise ValueError(f"{field_name} must contain exactly 4 values.")


def _validate_direction(direction: Vector3 | None, *, field_name: str) -> None:
    if direction is None:
        return
    if len(direction) != 3:
        raise ValueError(f"{field_name} must contain exactly 3 values.")
    if sum(float(component) * float(component) for component in direction) == 0.0:
        raise ValueError(f"{field_name} must be non-zero.")


def _offset_position(position: Vector3, *, direction: Vector3, distance: float) -> Vector3:
    normalized = _normalized_direction(direction)
    return tuple(round(position[index] + normalized[index] * distance, 12) for index in range(3))


def _normalized_direction(direction: Vector3) -> Vector3:
    norm = sum(float(component) * float(component) for component in direction) ** 0.5
    if norm == 0.0:
        raise ValueError("direction must be non-zero.")
    return tuple(float(component) / norm for component in direction)
