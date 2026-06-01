from hephaestus import PUBLIC_CORE_SOURCE_FILES


def test_public_core_source_manifest_lists_owner_files() -> None:
    expected = {
        "hephaestus/tool/types.py",
        "hephaestus/tool/safety.py",
        "hephaestus/tool/simulation.py",
        "hephaestus/tool/scene_carrier.py",
        "hephaestus/atom/motion.py",
        "hephaestus/atom/manipulation.py",
        "hephaestus/skill/grasp_policy.py",
        "hephaestus/task/registry.py",
    }

    assert expected.issubset(set(PUBLIC_CORE_SOURCE_FILES))
