import pytest

from hephaestus.tool.safety import SafetyKeepoutZone, SafetyValidator, SafetyViolation
from hephaestus.tool.types import BoundingBox, MotionCommand, Pose


def test_keepout_zone_blocks_motion_path() -> None:
    workspace = BoundingBox(frame="world", min=(-1.0, -1.0, 0.0), max=(1.0, 1.0, 1.0))
    keepout = SafetyKeepoutZone(
        name="center_box",
        bounds=BoundingBox(frame="world", min=(-0.1, -0.1, 0.0), max=(0.1, 0.1, 0.3)),
    )
    validator = SafetyValidator(
        workspace=workspace,
        keepout_zones=(keepout,),
        dry_run_default=True,
        live_run_enabled=False,
    )
    command = MotionCommand(
        command_type="move_to",
        target=Pose(position=(0.4, 0.0, 0.1), orientation=(0.0, 0.0, 0.0, 1.0), frame="world"),
        speed=0.2,
        dry_run=True,
    )
    reference_pose = Pose(position=(-0.4, 0.0, 0.1), orientation=(0.0, 0.0, 0.0, 1.0), frame="world")

    with pytest.raises(SafetyViolation, match="intersects keepout zone"):
        validator.validate_motion(command, reference_pose=reference_pose)
