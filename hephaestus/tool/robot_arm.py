from __future__ import annotations

from abc import ABC, abstractmethod

from hephaestus.tool.types import CommandResult, MotionCommand, Observation, Pose, RobotState


class RobotArm(ABC):
    """Stable abstraction for simulation and future hardware robot arms."""

    @abstractmethod
    def move_to(self, command: MotionCommand) -> CommandResult:
        raise NotImplementedError

    @abstractmethod
    def move_joints(self, positions: tuple[float, ...], speed: float = 0.5, dry_run: bool = True) -> CommandResult:
        raise NotImplementedError

    @abstractmethod
    def gripper(self, state: str, dry_run: bool = True) -> CommandResult:
        raise NotImplementedError

    @abstractmethod
    def get_observation(self) -> Observation:
        raise NotImplementedError

    @abstractmethod
    def get_state(self) -> RobotState:
        raise NotImplementedError

    @abstractmethod
    def get_ik(self, target: Pose) -> tuple[float, ...] | None:
        raise NotImplementedError

    @abstractmethod
    def get_joint_limits(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        raise NotImplementedError
