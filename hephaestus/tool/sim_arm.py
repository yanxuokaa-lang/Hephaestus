from __future__ import annotations

from hephaestus.tool.robot_arm import RobotArm
from hephaestus.tool.safety import SafetyValidator, SafetyViolation
from hephaestus.tool.simulation import SimulationBackend
from hephaestus.tool.types import CommandResult, MotionCommand, Observation, Pose, RobotState, SafetyRecord


class SimArm(RobotArm):
    """RobotArm adapter for deterministic simulation."""

    def __init__(self, backend: SimulationBackend, safety: SafetyValidator, adapter_name: str = "sim") -> None:
        self._backend = backend
        self._safety = safety
        self._adapter_name = adapter_name

    def move_to(self, command: MotionCommand) -> CommandResult:
        record = self._safety.validate_motion(command, reference_pose=self.get_state().ee_pose)
        normalized = MotionCommand(
            command_type=command.command_type,
            target=command.target,
            speed=command.speed,
            dry_run=record.dry_run,
        )
        result = self._backend.move_to(normalized)
        return self._with_adapter_data(result, record)

    def move_joints(self, positions: tuple[float, ...], speed: float = 0.5, dry_run: bool = True) -> CommandResult:
        record = self._validate_joint_motion(positions=positions, speed=speed, dry_run=dry_run)
        result = self._backend.move_joints(positions=positions, speed=speed, dry_run=dry_run)
        return self._with_adapter_data(result, record)

    def gripper(self, state: str, dry_run: bool = True) -> CommandResult:
        if state not in {"open", "close"}:
            raise SafetyViolation("Gripper state must be 'open' or 'close'.")
        if not dry_run and not self._safety.live_run_enabled:
            raise SafetyViolation("Live execution is disabled; use dry_run or explicitly enable live_run.")
        result = self._backend.set_gripper(state=state, dry_run=dry_run)
        record = SafetyRecord(
            accepted=True,
            command_type="gripper",
            frame=self._safety.workspace.frame,
            dry_run=dry_run,
            reason="validated",
        )
        return self._with_adapter_data(result, record)

    def stabilize_grasp(self, *, close_steps: int, hold_steps: int, dry_run: bool = True) -> CommandResult:
        if close_steps < 1:
            raise SafetyViolation("close_steps must be positive.")
        if hold_steps < 0:
            raise SafetyViolation("hold_steps must be non-negative.")
        if not dry_run and not self._safety.live_run_enabled:
            raise SafetyViolation("Live execution is disabled; use dry_run or explicitly enable live_run.")
        result = self._backend.stabilize_grasp(close_steps=close_steps, hold_steps=hold_steps, dry_run=dry_run)
        record = SafetyRecord(
            accepted=True,
            command_type="stabilize_grasp",
            frame=self._safety.workspace.frame,
            dry_run=dry_run,
            reason="validated",
        )
        return self._with_adapter_data(result, record)

    def settle(self, *, steps: int, dry_run: bool = True) -> CommandResult:
        if steps < 1:
            raise SafetyViolation("steps must be positive.")
        if not dry_run and not self._safety.live_run_enabled:
            raise SafetyViolation("Live execution is disabled; use dry_run or explicitly enable live_run.")
        result = self._backend.settle(steps=steps, dry_run=dry_run)
        record = SafetyRecord(
            accepted=True,
            command_type="settle",
            frame=self._safety.workspace.frame,
            dry_run=dry_run,
            reason="validated",
        )
        return self._with_adapter_data(result, record)

    def get_observation(self) -> Observation:
        return self._backend.observation()

    def get_state(self) -> RobotState:
        return self._backend.state()

    def get_ik(self, target: Pose) -> tuple[float, ...] | None:
        return self._backend.solve_ik(target)

    def get_joint_limits(self) -> tuple[tuple[float, ...], tuple[float, ...]]:
        return self._backend.joint_limits()

    def terminal_diagnostics(self, object_name: str) -> dict[str, object]:
        diagnostics = dict(self._backend.terminal_diagnostics(object_name))
        diagnostics["adapter"] = self._adapter_name
        diagnostics["safety"] = {
            "frame": self._safety.workspace.frame,
            "dry_run": True,
            "reason": "diagnostic_read_only",
        }
        return diagnostics

    def phase_diagnostics(
        self,
        object_name: str,
        *,
        phase: str,
        planned_tcp_pose: Pose | None = None,
    ) -> dict[str, object]:
        diagnostics = dict(self._backend.phase_diagnostics(object_name, phase=phase, planned_tcp_pose=planned_tcp_pose))
        diagnostics["adapter"] = self._adapter_name
        diagnostics["safety"] = {
            "frame": self._safety.workspace.frame,
            "dry_run": True,
            "reason": "diagnostic_read_only",
        }
        return diagnostics

    def _validate_joint_motion(self, positions: tuple[float, ...], speed: float, dry_run: bool) -> SafetyRecord:
        if speed <= 0.0:
            raise SafetyViolation("Motion speed must be positive.")
        if not dry_run and not self._safety.live_run_enabled:
            raise SafetyViolation("Live execution is disabled; use dry_run or explicitly enable live_run.")
        lower, upper = self._backend.joint_limits()
        if len(positions) != len(lower):
            raise SafetyViolation("Joint target length must match joint limits.")
        escaped = [
            index
            for index, (value, low, high) in enumerate(zip(positions, lower, upper, strict=True))
            if value < low or value > high
        ]
        if escaped:
            raise SafetyViolation(f"Joint targets outside limits at indexes: {escaped}.")
        return SafetyRecord(
            accepted=True,
            command_type="move_joints",
            frame=self._safety.workspace.frame,
            dry_run=dry_run,
            reason="validated",
        )

    def _with_adapter_data(self, result: CommandResult, record: SafetyRecord) -> CommandResult:
        data = dict(result.data)
        data["adapter"] = self._adapter_name
        data["safety"] = {
            "frame": record.frame,
            "dry_run": record.dry_run,
            "reason": record.reason,
        }
        return CommandResult(success=result.success, message=result.message, data=data)
