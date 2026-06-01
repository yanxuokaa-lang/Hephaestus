from __future__ import annotations

from dataclasses import dataclass
from typing import Any


Vector3 = tuple[float, float, float]
Quaternion = tuple[float, float, float, float]


@dataclass(frozen=True)
class Pose:
    position: Vector3
    orientation: Quaternion
    frame: str = "world"

    def __post_init__(self) -> None:
        if len(self.position) != 3:
            raise ValueError("Pose.position must contain exactly 3 values.")
        if len(self.orientation) != 4:
            raise ValueError("Pose.orientation must contain exactly 4 values.")
        if not self.frame:
            raise ValueError("Pose.frame must be non-empty.")


@dataclass(frozen=True)
class BoundingBox:
    frame: str
    min: Vector3
    max: Vector3

    def __post_init__(self) -> None:
        if len(self.min) != 3 or len(self.max) != 3:
            raise ValueError("BoundingBox min/max must contain exactly 3 values.")
        if not self.frame:
            raise ValueError("BoundingBox.frame must be non-empty.")
        if any(low > high for low, high in zip(self.min, self.max, strict=True)):
            raise ValueError("BoundingBox min values must be <= max values.")

    def contains(self, pose: Pose) -> bool:
        return all(
            low <= value <= high
            for value, low, high in zip(pose.position, self.min, self.max, strict=True)
        )


@dataclass(frozen=True)
class CameraInfo:
    name: str
    frame: str
    intrinsics: tuple[tuple[float, float, float], tuple[float, float, float], tuple[float, float, float]]
    extrinsics: Pose
    resolution: tuple[int, int]


@dataclass(frozen=True)
class Detection:
    object_name: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]
    frame: str = "image"


@dataclass(frozen=True)
class Observation:
    rgb: Any | None
    depth: Any | None
    camera_info: CameraInfo
    joint_pos: tuple[float, ...]
    joint_vel: tuple[float, ...]
    ee_pose: Pose
    gripper_state: float
    timestamp: float


@dataclass(frozen=True)
class RobotState:
    joint_pos: tuple[float, ...]
    joint_vel: tuple[float, ...]
    ee_pose: Pose
    gripper_state: float
    in_collision: bool
    workspace_bounds: BoundingBox
    joint_torques: tuple[float, ...] | None = None


@dataclass(frozen=True)
class MotionCommand:
    command_type: str
    target: Pose
    speed: float = 0.5
    dry_run: bool | None = None


@dataclass(frozen=True)
class SafetyRecord:
    accepted: bool
    command_type: str
    frame: str
    dry_run: bool
    reason: str


@dataclass(frozen=True)
class CommandResult:
    success: bool
    message: str
    data: dict[str, Any]
