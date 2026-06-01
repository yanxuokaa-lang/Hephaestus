from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hephaestus.tool.perception import ObjectDetector, PoseEstimator
from hephaestus.tool.types import Detection, Pose


@dataclass(frozen=True)
class StaticSceneObject:
    name: str
    pose: Pose
    confidence: float = 1.0
    bbox_xyxy: tuple[float, float, float, float] = (0.0, 0.0, 1.0, 1.0)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Static scene object name must be non-empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Static scene object confidence must be in [0, 1].")
        if len(self.bbox_xyxy) != 4:
            raise ValueError("Static scene object bbox_xyxy must contain four values.")


class StaticSceneObjectDetector(ObjectDetector):
    def __init__(self, objects: dict[str, StaticSceneObject]) -> None:
        self._objects = dict(objects)

    def detect(self, image: Any, object_name: str) -> list[Detection]:
        scene_object = self._objects.get(object_name)
        if scene_object is None:
            return []
        return [
            Detection(
                object_name=scene_object.name,
                confidence=scene_object.confidence,
                bbox_xyxy=scene_object.bbox_xyxy,
                frame="image",
            )
        ]


class StaticScenePoseEstimator(PoseEstimator):
    def __init__(self, objects: dict[str, StaticSceneObject]) -> None:
        self._objects = dict(objects)

    def estimate_pose(self, point_cloud: Any, object_name: str) -> Pose:
        try:
            return self._objects[object_name].pose
        except KeyError as exc:
            raise LookupError(f"Static scene object '{object_name}' has no pose.") from exc
