from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

import numpy as np

from hephaestus.tool.perception import ObjectDetector, PoseEstimator
from hephaestus.tool.types import Detection, Observation, Pose


class ObjectPoseProvider(Protocol):
    def object_pose(self, object_name: str) -> Pose | None:
        ...


class DiagnosticsProvider(Protocol):
    def terminal_diagnostics(self, object_name: str) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class _PointCloudFallbackConfig:
    radius_xy: float = 0.02
    radius_z: float = 0.01


class PerceptionAtoms:
    def __init__(
        self,
        detector: ObjectDetector,
        pose_estimator: PoseEstimator,
        *,
        object_pose_provider: ObjectPoseProvider | None = None,
        diagnostics_provider: DiagnosticsProvider | None = None,
    ) -> None:
        self._detector = detector
        self._pose_estimator = pose_estimator
        self._object_pose_provider = object_pose_provider
        self._diagnostics_provider = diagnostics_provider
        self._point_cloud_fallback = _PointCloudFallbackConfig()

    def detect(self, image: object, object_name: str) -> list[Detection]:
        _require_name(object_name)
        return self._detector.detect(image, object_name)

    def segment(self, image: object, object_name: str) -> np.ndarray:
        _require_name(object_name)
        segmenter = getattr(self._detector, "segment", None)
        if callable(segmenter):
            return np.asarray(segmenter(image, object_name), dtype=bool)
        detections = self.detect(image, object_name)
        if not detections:
            raise LookupError(f"Object '{object_name}' was not detected for segmentation.")
        shape = _image_shape(image)
        if shape is None:
            raise ValueError("Segmentation fallback requires an image-like object with height and width.")
        height, width = shape
        mask = np.zeros((height, width), dtype=bool)
        x1, y1, x2, y2 = _clamp_bbox(detections[0].bbox_xyxy, width=width, height=height)
        mask[y1:y2, x1:x2] = True
        return mask

    def estimate_pose(self, point_cloud: object, object_name: str) -> Pose:
        _require_name(object_name)
        return self._pose_estimator.estimate_pose(point_cloud, object_name)

    def track(self, point_cloud: object, object_name: str) -> Pose:
        _require_name(object_name)
        tracker = getattr(self._pose_estimator, "track", None)
        if callable(tracker):
            return tracker(point_cloud, object_name)
        return self.estimate_pose(point_cloud, object_name)

    def get_point_cloud(self, observation: Observation, object_name: str) -> np.ndarray:
        _require_name(object_name)
        if not isinstance(observation, Observation):
            raise TypeError("get_point_cloud requires an Observation instance.")
        provider = self._object_pose_provider
        if provider is None:
            raise LookupError(f"Point cloud fallback for '{object_name}' requires an object pose provider.")
        pose = provider.object_pose(object_name)
        if pose is None:
            raise LookupError(f"Object '{object_name}' has no pose available for point-cloud fallback.")
        return _point_cloud_from_pose(pose, config=self._point_cloud_fallback)

    def check_grasp_state(self, object_name: str) -> float:
        _require_name(object_name)
        diagnostics = self._terminal_diagnostics(object_name)
        sim_flags = diagnostics.get("sim_flags")
        if isinstance(sim_flags, dict):
            is_grasped = sim_flags.get("is_grasped")
            if is_grasped is True:
                return 1.0
            if is_grasped is False:
                return 0.0
        gripper_state = diagnostics.get("gripper_state")
        if isinstance(gripper_state, (float, int)) and float(gripper_state) > 0.5:
            return 0.5
        return 0.0

    def check_stable(self, object_name: str) -> bool:
        _require_name(object_name)
        diagnostics = self._terminal_diagnostics(object_name)
        for key in ("object_stable", "is_object_stable"):
            is_stable = diagnostics.get(key)
            if isinstance(is_stable, bool):
                return is_stable
        velocity_norm = diagnostics.get("object_velocity_norm_mps")
        if isinstance(velocity_norm, (float, int)):
            return float(velocity_norm) <= 1e-3
        return False

    def _terminal_diagnostics(self, object_name: str) -> dict[str, Any]:
        if self._diagnostics_provider is None:
            return {}
        terminal_diagnostics = getattr(self._diagnostics_provider, "terminal_diagnostics", None)
        if not callable(terminal_diagnostics):
            return {}
        return dict(terminal_diagnostics(object_name))


def _require_name(object_name: str) -> None:
    if not object_name:
        raise ValueError("object_name must be non-empty.")


def _image_shape(image: object) -> tuple[int, int] | None:
    shape = getattr(image, "shape", None)
    if shape is None or len(shape) < 2:
        return None
    return int(shape[0]), int(shape[1])


def _clamp_bbox(
    bbox_xyxy: tuple[float, float, float, float],
    *,
    width: int,
    height: int,
) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox_xyxy
    left = max(0, min(width, int(round(x1))))
    top = max(0, min(height, int(round(y1))))
    right = max(left, min(width, int(round(x2))))
    bottom = max(top, min(height, int(round(y2))))
    return left, top, right, bottom


def _point_cloud_from_pose(pose: Pose, *, config: _PointCloudFallbackConfig) -> np.ndarray:
    x, y, z = pose.position
    return np.asarray(
        [
            (x, y, z),
            (x - config.radius_xy, y, z),
            (x + config.radius_xy, y, z),
            (x, y - config.radius_xy, z),
            (x, y + config.radius_xy, z),
            (x, y, z - config.radius_z),
            (x, y, z + config.radius_z),
        ],
        dtype=float,
    )
