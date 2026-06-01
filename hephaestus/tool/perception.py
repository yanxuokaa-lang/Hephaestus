from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from hephaestus.tool.types import Detection, Pose


class ObjectDetector(ABC):
    @abstractmethod
    def detect(self, image: Any, object_name: str) -> list[Detection]:
        raise NotImplementedError


class DepthEstimator(ABC):
    @abstractmethod
    def estimate(self, image: Any) -> Any:
        raise NotImplementedError


class PoseEstimator(ABC):
    @abstractmethod
    def estimate_pose(self, point_cloud: Any, object_name: str) -> Pose:
        raise NotImplementedError
