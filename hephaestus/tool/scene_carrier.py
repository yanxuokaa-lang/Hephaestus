from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SceneXYBounds:
    min_xy: tuple[float, float]
    max_xy: tuple[float, float]

    def contains_point(self, position_xy: tuple[float, float]) -> bool:
        return (
            self.min_xy[0] <= position_xy[0] <= self.max_xy[0]
            and self.min_xy[1] <= position_xy[1] <= self.max_xy[1]
        )

    def overlaps(self, other: "SceneXYBounds") -> bool:
        overlap_x = min(self.max_xy[0], other.max_xy[0]) - max(self.min_xy[0], other.min_xy[0])
        overlap_y = min(self.max_xy[1], other.max_xy[1]) - max(self.min_xy[1], other.min_xy[1])
        return overlap_x > 0.0 and overlap_y > 0.0


@dataclass(frozen=True)
class SceneTargetRegion:
    logical_name: str
    bounds: SceneXYBounds
    blocks_pick_corridor: bool = False


@dataclass(frozen=True)
class ScenePreviewPlacement:
    logical_name: str
    asset_dir: str
    position_xy: tuple[float, float]
    model_id: int = 0
    orientation_wxyz: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    scale_override: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class SceneReviewCamera:
    name: str
    eye: tuple[float, float, float]
    target: tuple[float, float, float]
    width: int
    height: int
    fov: float
    near: float = 0.01
    far: float = 100.0


@dataclass(frozen=True)
class SceneCarrier:
    scenario_name: str
    preview_env: str
    layout_name: str
    workspace_profile: str
    work_area: SceneXYBounds
    target_regions: tuple[SceneTargetRegion, ...]
    no_obstruction_corridor: SceneXYBounds
    category_to_canonical_zone: dict[str, str]
    preview_asset_placements: tuple[ScenePreviewPlacement, ...]
    review_cameras: tuple[SceneReviewCamera, ...]
    execution_assumptions: tuple[str, ...]
    evaluation_assumptions: tuple[str, ...]

    def __post_init__(self) -> None:
        preview_names = {placement.logical_name for placement in self.preview_asset_placements}
        target_region_names = self.target_region_names
        if len(target_region_names) != len(set(target_region_names)):
            raise ValueError(f"scene carrier '{self.scenario_name}' defines duplicate target region names.")
        missing_preview_names = [name for name in target_region_names if name not in preview_names]
        if missing_preview_names:
            raise ValueError(
                f"scene carrier '{self.scenario_name}' target regions are missing preview placements: {missing_preview_names}"
            )
        missing_canonical_zones = sorted(set(self.category_to_canonical_zone.values()) - set(target_region_names))
        if missing_canonical_zones:
            raise ValueError(
                f"scene carrier '{self.scenario_name}' canonical zones are not declared target regions: "
                f"{missing_canonical_zones}"
            )
        if not self.no_obstruction_corridor.overlaps(self.work_area):
            raise ValueError(
                f"scene carrier '{self.scenario_name}' no_obstruction_corridor must enter the work_area."
            )
        for region in self.target_regions:
            if self.work_area.overlaps(region.bounds):
                raise ValueError(
                    f"scene carrier '{self.scenario_name}' defines overlapping work_area and target region "
                    f"'{region.logical_name}'."
                )
            if self.no_obstruction_corridor.overlaps(region.bounds):
                raise ValueError(
                    f"scene carrier '{self.scenario_name}' target region '{region.logical_name}' overlaps "
                    "the no_obstruction_corridor."
                )
        for placement in self.preview_asset_placements:
            if placement.logical_name in target_region_names:
                region = self.target_region(placement.logical_name)
                if not region.bounds.contains_point(placement.position_xy):
                    raise ValueError(
                        f"scene carrier '{self.scenario_name}' placement '{placement.logical_name}' is outside "
                        "its declared target region."
                    )
                continue
            if not self.work_area.contains_point(placement.position_xy):
                raise ValueError(
                    f"scene carrier '{self.scenario_name}' movable placement '{placement.logical_name}' is outside "
                    "the work_area."
                )

    @property
    def review_camera_names(self) -> tuple[str, ...]:
        return tuple(camera.name for camera in self.review_cameras)

    @property
    def preview_object_count(self) -> int:
        return len(self.preview_asset_placements)

    @property
    def target_region_names(self) -> tuple[str, ...]:
        return tuple(region.logical_name for region in self.target_regions)

    @property
    def static_keepout_region_names(self) -> tuple[str, ...]:
        return tuple(region.logical_name for region in self.target_regions if region.blocks_pick_corridor)

    def target_region(self, logical_name: str) -> SceneTargetRegion:
        for region in self.target_regions:
            if region.logical_name == logical_name:
                return region
        raise KeyError(f"scene carrier '{self.scenario_name}' does not define target region '{logical_name}'.")


_TABLETOP_ORGANIZATION_V1 = SceneCarrier(
    scenario_name="tabletop_organization_v1",
    preview_env="TableTopFreeDraw-v1",
    layout_name="tabletop_preview_v1",
    workspace_profile="tabletop_object_relocation",
    work_area=SceneXYBounds(min_xy=(-0.38, -0.22), max_xy=(0.40, 0.05)),
    target_regions=(
        SceneTargetRegion(
            logical_name="plate",
            bounds=SceneXYBounds(min_xy=(-0.34, 0.09), max_xy=(-0.16, 0.24)),
        ),
        SceneTargetRegion(
            logical_name="storage_box",
            bounds=SceneXYBounds(min_xy=(0.10, 0.08), max_xy=(0.34, 0.24)),
            blocks_pick_corridor=True,
        ),
        SceneTargetRegion(
            logical_name="trash_bin",
            bounds=SceneXYBounds(min_xy=(-0.12, 0.18), max_xy=(0.12, 0.38)),
            blocks_pick_corridor=True,
        ),
    ),
    no_obstruction_corridor=SceneXYBounds(min_xy=(-0.08, -0.24), max_xy=(0.08, 0.16)),
    category_to_canonical_zone={
        "fruit": "plate",
        "toy": "storage_box",
        "trash": "trash_bin",
    },
    preview_asset_placements=(
        ScenePreviewPlacement(
            "plate",
            "objects/003_plate",
            (-0.25, 0.15),
            orientation_wxyz=(0.5, 0.5, 0.5, 0.5),
        ),
        ScenePreviewPlacement(
            "storage_box",
            "objects/062_plasticbox",
            (0.22, 0.14),
            model_id=3,
            orientation_wxyz=(0.5, 0.5, 0.5, 0.5),
        ),
        ScenePreviewPlacement(
            "trash_bin",
            "objects/063_tabletrashbin",
            (0.00, 0.28),
            orientation_wxyz=(0.651892, 0.651428, 0.274378, 0.274584),
        ),
        ScenePreviewPlacement(
            "apple",
            "objects/035_apple",
            (-0.10, -0.02),
            orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
        ),
        ScenePreviewPlacement(
            "banana",
            "objects/103_fruit",
            (-0.18, -0.10),
            model_id=4,
            orientation_wxyz=(0.707, 0.707, 0.0, 0.0),
            scale_override=(0.05, 0.05, 0.05),
        ),
        ScenePreviewPlacement(
            "fruit_group",
            "objects/103_fruit",
            (-0.28, -0.04),
            model_id=1,
            orientation_wxyz=(0.707, 0.707, 0.0, 0.0),
            scale_override=(0.05, 0.05, 0.05),
        ),
        ScenePreviewPlacement(
            "toy_car",
            "objects/057_toycar",
            (0.16, -0.03),
            orientation_wxyz=(0.707, 0.707, 0.0, 0.0),
        ),
        ScenePreviewPlacement(
            "soda_can",
            "objects/071_can",
            (0.05, 0.00),
            orientation_wxyz=(0.707, 0.707, 0.0, 0.0),
        ),
        ScenePreviewPlacement(
            "fries",
            "objects/005_french-fries",
            (0.34, 0.02),
            orientation_wxyz=(1.0, 0.0, 0.0, 0.0),
        ),
        ScenePreviewPlacement(
            "vegetable",
            "objects/069_vagetable",
            (-0.04, -0.14),
            orientation_wxyz=(0.707, 0.707, 0.0, 0.0),
            scale_override=(0.05, 0.05, 0.05),
        ),
    ),
    review_cameras=(
        SceneReviewCamera(
            name="left_review_camera",
            eye=(0.62, -0.58, 0.92),
            target=(0.0, 0.08, 0.12),
            width=1280,
            height=960,
            fov=1.0,
        ),
        SceneReviewCamera(
            name="right_review_camera",
            eye=(0.46, 0.74, 0.88),
            target=(0.0, 0.08, 0.12),
            width=1280,
            height=960,
            fov=1.0,
        ),
    ),
    execution_assumptions=(
        "preview uses a tabletop-only dry-run scene and never enables live motion",
        "scene truth remains runtime-owned even when assets come from RobotWin",
    ),
    evaluation_assumptions=(
        "category-to-zone truth is enforced by runtime normalization before plan execution",
        "preview layout is workspace-bounded and seeded for replayable review",
    ),
)

_SCENE_CARRIERS = {
    _TABLETOP_ORGANIZATION_V1.scenario_name: _TABLETOP_ORGANIZATION_V1,
}


def get_scene_carrier(scenario_name: str) -> SceneCarrier:
    carrier = _SCENE_CARRIERS.get(scenario_name)
    if carrier is None:
        raise ValueError(f"scene carrier '{scenario_name}' is not registered by runtime.")
    return carrier
