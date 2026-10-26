from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
BRIEF_PATH = ROOT / "assets" / "briefs" / "future_courtyard.brief.json"
CHECKPOINTS = ROOT / "blender" / "checkpoints"
RENDERS = ROOT / "blender" / "renders"
CANDIDATES = ROOT / "build" / "candidates"
RUNTIME = ROOT / "assets" / "runtime"


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="all", choices=["all"])
    parser.add_argument("--turntable", action="store_true")
    return parser.parse_args(argv)


def ensure_dirs() -> None:
    for path in (CHECKPOINTS, RENDERS, CANDIDATES, RUNTIME):
        path.mkdir(parents=True, exist_ok=True)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.armatures):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)
    for collection in list(bpy.data.collections):
        if collection.name != "Collection":
            bpy.data.collections.remove(collection)
    base = bpy.data.collections.get("Collection")
    if base:
        base.name = "SCENE_ROOT"


def rgba(hex_value: str) -> tuple[float, float, float, float]:
    value = hex_value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255.0 for i in (0, 2, 4)) + (1.0,)


def make_material(name: str, color: str, metallic: float = 0.0, roughness: float = 0.65, emission: float = 0.0) -> bpy.types.Material:
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = rgba(color)
    material.node_tree.nodes.clear()
    principled = material.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
    output = material.node_tree.nodes.new("ShaderNodeOutputMaterial")
    output.is_active_output = True
    material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    principled.inputs["Base Color"].default_value = rgba(color)
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    emission_input = principled.inputs.get("Emission Color") or principled.inputs.get("Emission")
    if emission_input:
        emission_input.default_value = rgba(color)
    strength_input = principled.inputs.get("Emission Strength")
    if strength_input:
        strength_input.default_value = emission
    return material


def get_collection(name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    collection.objects.link(obj)


def add_empty(name: str, location=(0.0, 0.0, 0.0), parent=None, collection=None) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.35
    obj.location = location
    (collection or bpy.context.scene.collection).objects.link(obj)
    if parent:
        world = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = world
    return obj


def add_box(name: str, location, dimensions, material=None, parent=None, collection=None, bevel=0.0) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        modifier = obj.modifiers.new("SoftEdges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    if material:
        obj.data.materials.append(material)
    if collection:
        move_to_collection(obj, collection)
    if parent:
        world = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = world
    return obj


def add_cylinder(name: str, location, radius, depth, material=None, parent=None, collection=None, vertices=12) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    if collection:
        move_to_collection(obj, collection)
    if parent:
        world = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = world
    return obj


def add_ico(name: str, location, radius, material=None, parent=None, collection=None, subdivisions=1) -> bpy.types.Object:
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    if material:
        obj.data.materials.append(material)
    if collection:
        move_to_collection(obj, collection)
    if parent:
        world = obj.matrix_world.copy()
        obj.parent = parent
        obj.matrix_world = world
    return obj


def create_environment(materials: dict[str, bpy.types.Material]) -> tuple[bpy.types.Object, bpy.types.Collection]:
    env_collection = get_collection("ENVIRONMENT")
    root = add_empty("ENV_FutureCourtyard", collection=env_collection)
    add_box("ENV_Ground", (0, 0, -0.1), (24, 24, 0.2), materials["ground"], root, env_collection, 0.04)
    add_box("ENV_CentralWalkway", (0, 0, 0.015), (3.0, 20.0, 0.03), materials["accent"], root, env_collection)

    def solid(name, loc, dims=(4, 0.25, 3)):
        return add_box(name, loc, dims, materials["wall"], root, env_collection, 0.05)

    for x in (-8, -4, 4, 8):
        solid(f"KIT_WallSolid_S_{x:+d}", (x, -10, 1.5))
    door = add_empty("KIT_WallDoor_4x3", (0, -10, 0), root, env_collection)
    add_box("KIT_WallDoor_Left", (-1.35, -10, 1.5), (1.3, 0.25, 3), materials["wall"], door, env_collection, 0.04)
    add_box("KIT_WallDoor_Right", (1.35, -10, 1.5), (1.3, 0.25, 3), materials["wall"], door, env_collection, 0.04)
    add_box("KIT_WallDoor_Lintel", (0, -10, 2.7), (1.4, 0.25, 0.6), materials["wall"], door, env_collection, 0.04)

    for x in (-8, -4, 4, 8):
        solid(f"KIT_WallSolid_N_{x:+d}", (x, 10, 1.5))
    window = add_empty("KIT_WallWindow_4x3", (0, 10, 0), root, env_collection)
    add_box("KIT_WallWindow_Left", (-1.45, 10, 1.5), (1.1, 0.25, 3), materials["wall"], window, env_collection, 0.04)
    add_box("KIT_WallWindow_Right", (1.45, 10, 1.5), (1.1, 0.25, 3), materials["wall"], window, env_collection, 0.04)
    add_box("KIT_WallWindow_Sill", (0, 10, 0.55), (1.8, 0.25, 0.9), materials["wall"], window, env_collection, 0.04)
    add_box("KIT_WallWindow_Lintel", (0, 10, 2.35), (1.8, 0.25, 1.3), materials["wall"], window, env_collection, 0.04)
    add_box("KIT_WindowGlass", (0, 9.93, 1.45), (1.72, 0.04, 1.05), materials["accent"], window, env_collection)

    for y in (-8, -4, 0, 4, 8):
        solid(f"KIT_WallSolid_E_{y:+d}", (10, y, 1.5), (0.25, 4, 3))
        solid(f"KIT_WallSolid_W_{y:+d}", (-10, y, 1.5), (0.25, 4, 3))
    for x in (-10, 10):
        for y in (-10, 10):
            add_box(f"KIT_Pillar_0p5x3_{x:+d}_{y:+d}", (x, y, 1.5), (0.5, 0.5, 3), materials["metal"], root, env_collection, 0.04)
    canopy = add_empty("KIT_Canopy_4x4", (0, 6, 0), root, env_collection)
    add_box("KIT_Canopy_Roof", (0, 6, 3.1), (4, 4, 0.2), materials["wall"], canopy, env_collection, 0.08)
    for x in (-1.75, 1.75):
        add_box(f"KIT_Canopy_Support_{x:+.2f}", (x, 6, 1.5), (0.18, 0.18, 3), materials["metal"], canopy, env_collection, 0.02)

    bench = add_empty("PROP_Bench", (-4, 4, 0), root, env_collection)
    add_box("PROP_Bench_Seat", (-4, 4, 0.55), (2.2, 0.65, 0.16), materials["wall"], bench, env_collection, 0.07)
    add_box("PROP_Bench_Back", (-4, 4.28, 1.0), (2.2, 0.12, 0.8), materials["wall"], bench, env_collection, 0.05)
    for x in (-4.8, -3.2):
        add_box(f"PROP_Bench_Leg_{x:+.1f}", (x, 4, 0.27), (0.12, 0.5, 0.55), materials["metal"], bench, env_collection)

    planter = add_empty("PROP_Planter", (-7, 7, 0), root, env_collection)
    add_box("PROP_Planter_Box", (-7, 7, 0.35), (2.0, 2.0, 0.7), materials["metal"], planter, env_collection, 0.1)
    add_box("PROP_Planter_Soil", (-7, 7, 0.72), (1.65, 1.65, 0.08), materials["ground"], planter, env_collection)
    tree = add_empty("PROP_Tree", (-7, 7, 0), root, env_collection)
    add_cylinder("PROP_Tree_Trunk", (-7, 7, 1.6), 0.22, 2.0, materials["metal"], tree, env_collection, 8)
    add_ico("PROP_Tree_CrownLow", (-7, 7, 2.8), 1.15, materials["foliage"], tree, env_collection, 2)
    add_ico("PROP_Tree_CrownHigh", (-7.2, 7.1, 3.55), 0.8, materials["foliage"], tree, env_collection, 1)

    bollard = add_empty("PROP_BollardLight", (4, -4, 0), root, env_collection)
    add_cylinder("PROP_Bollard_Body", (4, -4, 0.45), 0.18, 0.9, materials["metal"], bollard, env_collection, 10)
    add_cylinder("PROP_Bollard_Glow", (4, -4, 0.92), 0.22, 0.12, materials["emission"], bollard, env_collection, 10)

    lamp = add_empty("PROP_StreetLamp", (8, 0, 0), root, env_collection)
    add_cylinder("PROP_StreetLamp_Pole", (8, 0, 1.8), 0.1, 3.6, materials["metal"], lamp, env_collection, 10)
    add_box("PROP_StreetLamp_Head", (8, -0.25, 3.55), (0.7, 0.45, 0.18), materials["emission"], lamp, env_collection, 0.08)

    terminal = add_empty("PROP_HoloTerminal", (0, 7, 0), root, env_collection)
    add_box("PROP_HoloTerminal_Base", (0, 7, 0.5), (0.8, 0.6, 1.0), materials["metal"], terminal, env_collection, 0.08)
    screen = add_box("PROP_HoloTerminal_Screen", (0, 6.65, 1.45), (1.1, 0.08, 1.0), materials["accent"], terminal, env_collection, 0.06)
    screen.rotation_euler.x = math.radians(-8)

    crate = add_empty("PROP_Crate", (-8, -5, 0), root, env_collection)
    add_box("PROP_Crate_Box", (-8, -5, 0.55), (1.2, 1.2, 1.1), materials["metal"], crate, env_collection, 0.07)
    add_box("PROP_Crate_BandX", (-8, -5, 0.55), (1.24, 0.14, 1.14), materials["accent"], crate, env_collection)
    add_box("PROP_Crate_BandY", (-8, -5, 0.55), (0.14, 1.24, 1.14), materials["accent"], crate, env_collection)

    barrier = add_empty("PROP_Barrier", (0, -6, 0), root, env_collection)
    for x in (-1.1, 1.1):
        add_cylinder(f"PROP_Barrier_Post_{x:+.1f}", (x, -6, 0.6), 0.12, 1.2, materials["metal"], barrier, env_collection, 10)
    add_box("PROP_Barrier_Beam", (0, -6, 0.85), (2.3, 0.15, 0.2), materials["emission"], barrier, env_collection, 0.04)

    fountain = add_empty("PROP_Fountain", (0, 0, 0), root, env_collection)
    add_cylinder("PROP_Fountain_Base", (0, 0, 0.25), 2.0, 0.5, materials["wall"], fountain, env_collection, 20)
    add_cylinder("PROP_Fountain_Water", (0, 0, 0.53), 1.65, 0.08, materials["accent"], fountain, env_collection, 20)
    add_cylinder("PROP_Fountain_Core", (0, 0, 1.05), 0.28, 1.1, materials["emission"], fountain, env_collection, 10)

    pad = add_empty("PROP_DronePad", (6, 6, 0), root, env_collection)
    add_cylinder("PROP_DronePad_Base", (6, 6, 0.12), 1.45, 0.24, materials["metal"], pad, env_collection, 16)
    add_cylinder("PROP_DronePad_Ring", (6, 6, 0.25), 1.05, 0.05, materials["emission"], pad, env_collection, 16)
    add_box("PROP_DronePad_H", (6, 6, 0.3), (1.2, 0.18, 0.05), materials["wall"], pad, env_collection)
    add_box("PROP_DronePad_H2", (6, 6, 0.3), (0.18, 0.8, 0.05), materials["wall"], pad, env_collection)
    return root, env_collection


def create_collision_and_navigation(root: bpy.types.Object, collection: bpy.types.Collection) -> None:
    proxies = [
        ("COL_WallNorth-colonly", (0, 10, 1.5), (20, 0.25, 3)),
        ("COL_WallSouthLeft-colonly", (-6, -10, 1.5), (8, 0.25, 3)),
        ("COL_WallSouthRight-colonly", (6, -10, 1.5), (8, 0.25, 3)),
        ("COL_WallEast-colonly", (10, 0, 1.5), (0.25, 20, 3)),
        ("COL_WallWest-colonly", (-10, 0, 1.5), (0.25, 20, 3)),
        ("COL_Fountain-colonly", (0, 0, 0.65), (4.0, 4.0, 1.3)),
    ]
    for name, loc, dims in proxies:
        obj = add_box(name, loc, dims, None, root, collection)
        obj.hide_render = True
        obj.display_type = "WIRE"
    nav = add_box("NAV_Courtyard-navmesh", (0, 0, 0.025), (19.2, 19.2, 0.05), None, root, collection)
    nav.hide_render = True
    nav.display_type = "WIRE"


def bone_parent_keep_world(obj: bpy.types.Object, armature: bpy.types.Object, bone: str) -> None:
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world


def create_character(materials: dict[str, bpy.types.Material]) -> tuple[bpy.types.Object, bpy.types.Object, bpy.types.Collection]:
    char_collection = get_collection("CHARACTER")
    root = add_empty("CHR_Player", (0, 0, 0), collection=char_collection)
    arm_data = bpy.data.armatures.new("RIG_PlayerData")
    arm = bpy.data.objects.new("RIG_Player", arm_data)
    char_collection.objects.link(arm)
    arm.parent = root
    arm.location = (0, 0, 0)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    specs = {
        "Root": ((0, 0, 0), (0, 0, 0.2), None),
        "Spine": ((0, 0, 0.2), (0, 0, 1.35), "Root"),
        "Head": ((0, 0, 1.35), (0, 0, 1.75), "Spine"),
        "UpperArm.L": ((-0.24, 0, 1.25), (-0.62, 0, 1.12), "Spine"),
        "Forearm.L": ((-0.62, 0, 1.12), (-0.93, 0, 0.95), "UpperArm.L"),
        "UpperArm.R": ((0.24, 0, 1.25), (0.62, 0, 1.12), "Spine"),
        "Forearm.R": ((0.62, 0, 1.12), (0.93, 0, 0.95), "UpperArm.R"),
        "Leg.L": ((-0.16, 0, 0.72), (-0.16, 0, 0.16), "Root"),
        "Foot.L": ((-0.16, 0, 0.16), (-0.16, -0.28, 0.08), "Leg.L"),
        "Leg.R": ((0.16, 0, 0.72), (0.16, 0, 0.16), "Root"),
        "Foot.R": ((0.16, 0, 0.16), (0.16, -0.28, 0.08), "Leg.R"),
    }
    for name, (head, tail, parent_name) in specs.items():
        bone = arm_data.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        if parent_name:
            bone.parent = arm_data.edit_bones[parent_name]
    bpy.ops.object.mode_set(mode="POSE")
    for pose_bone in arm.pose.bones:
        pose_bone.rotation_mode = "XYZ"
    bpy.ops.object.mode_set(mode="OBJECT")

    parts = [
        ("CHR_Torso", (0, 0, 1.03), (0.62, 0.38, 0.72), "Spine", "player"),
        ("CHR_ChestAccent", (0, -0.205, 1.13), (0.3, 0.04, 0.24), "Spine", "accent"),
        ("CHR_Head", (0, 0, 1.58), (0.46, 0.42, 0.4), "Head", "player"),
        ("CHR_Visor", (0, -0.225, 1.6), (0.3, 0.04, 0.12), "Head", "emission"),
        ("CHR_UpperArmL", (-0.43, 0, 1.18), (0.28, 0.28, 0.48), "UpperArm.L", "metal"),
        ("CHR_ForearmL", (-0.78, 0, 1.01), (0.23, 0.23, 0.42), "Forearm.L", "player"),
        ("CHR_UpperArmR", (0.43, 0, 1.18), (0.28, 0.28, 0.48), "UpperArm.R", "metal"),
        ("CHR_ForearmR", (0.78, 0, 1.01), (0.23, 0.23, 0.42), "Forearm.R", "player"),
        ("CHR_LegL", (-0.16, 0, 0.45), (0.28, 0.32, 0.58), "Leg.L", "metal"),
        ("CHR_FootL", (-0.16, -0.13, 0.1), (0.3, 0.48, 0.18), "Foot.L", "player"),
        ("CHR_LegR", (0.16, 0, 0.45), (0.28, 0.32, 0.58), "Leg.R", "metal"),
        ("CHR_FootR", (0.16, -0.13, 0.1), (0.3, 0.48, 0.18), "Foot.R", "player"),
    ]
    for name, loc, dims, bone, mat in parts:
        obj = add_box(name, loc, dims, materials[mat], collection=char_collection, bevel=0.04)
        bone_parent_keep_world(obj, arm, bone)
    root.location = (0, -2, 0)
    return root, arm, char_collection


def reset_pose(arm: bpy.types.Object) -> None:
    for bone in arm.pose.bones:
        bone.rotation_euler = (0, 0, 0)
        bone.scale = (1, 1, 1)
        bone.location = (0, 0, 0)


def make_action(arm: bpy.types.Object, name: str, keyframes: list[tuple[int, dict[str, tuple[float, float, float]]]], loop: bool) -> bpy.types.Action:
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    arm.animation_data_create()
    arm.animation_data.action = action
    for frame, rotations in keyframes:
        reset_pose(arm)
        for bone_name, degrees in rotations.items():
            arm.pose.bones[bone_name].rotation_euler = tuple(math.radians(v) for v in degrees)
        for bone in arm.pose.bones:
            bone.keyframe_insert("rotation_euler", frame=frame, group=bone.name)
    if hasattr(action, "fcurves"):
        for curve in action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation = "LINEAR"
            if loop:
                curve.modifiers.new("CYCLES")
    return action


def create_actions(arm: bpy.types.Object) -> list[bpy.types.Action]:
    actions = []
    actions.append(make_action(arm, "Idle_loop", [
        (1, {"Spine": (0, 0, -2), "Head": (0, 0, 3)}),
        (31, {"Spine": (0, 0, 2), "Head": (0, 0, -3)}),
        (61, {"Spine": (0, 0, -2), "Head": (0, 0, 3)}),
    ], True))
    actions.append(make_action(arm, "Walk_loop", [
        (1, {"UpperArm.L": (28, 0, 0), "UpperArm.R": (-28, 0, 0), "Leg.L": (-28, 0, 0), "Leg.R": (28, 0, 0)}),
        (16, {"UpperArm.L": (-28, 0, 0), "UpperArm.R": (28, 0, 0), "Leg.L": (28, 0, 0), "Leg.R": (-28, 0, 0)}),
        (31, {"UpperArm.L": (28, 0, 0), "UpperArm.R": (-28, 0, 0), "Leg.L": (-28, 0, 0), "Leg.R": (28, 0, 0)}),
    ], True))
    actions.append(make_action(arm, "Run_loop", [
        (1, {"Spine": (12, 0, 0), "UpperArm.L": (55, 0, 0), "UpperArm.R": (-55, 0, 0), "Leg.L": (-48, 0, 0), "Leg.R": (48, 0, 0)}),
        (11, {"Spine": (12, 0, 0), "UpperArm.L": (-55, 0, 0), "UpperArm.R": (55, 0, 0), "Leg.L": (48, 0, 0), "Leg.R": (-48, 0, 0)}),
        (21, {"Spine": (12, 0, 0), "UpperArm.L": (55, 0, 0), "UpperArm.R": (-55, 0, 0), "Leg.L": (-48, 0, 0), "Leg.R": (48, 0, 0)}),
    ], True))
    actions.append(make_action(arm, "Jump", [
        (1, {}),
        (16, {"UpperArm.L": (-75, 0, 0), "UpperArm.R": (-75, 0, 0), "Leg.L": (30, 0, 0), "Leg.R": (30, 0, 0), "Foot.L": (-25, 0, 0), "Foot.R": (-25, 0, 0)}),
        (31, {}),
    ], False))
    arm.animation_data.action = actions[0]
    bpy.context.scene.frame_set(1)
    return actions


def create_review_rig() -> tuple[bpy.types.Collection, dict[str, bpy.types.Object], dict[str, bpy.types.Object]]:
    review = get_collection("REVIEW_ONLY")
    cameras = {}
    for name, location in {
        "perspective": (16, -18, 13),
        "front": (0, -25, 6),
        "side": (25, 0, 6),
        "back": (0, 25, 6),
    }.items():
        data = bpy.data.cameras.new(f"REVIEW_Camera_{name}")
        data.lens = 48 if name == "perspective" else 58
        camera = bpy.data.objects.new(f"REVIEW_Camera_{name}", data)
        review.objects.link(camera)
        camera.location = location
        target = Vector((0, 0, 1.2))
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        cameras[name] = camera
    sun_data = bpy.data.lights.new("REVIEW_Sun", "SUN")
    sun_data.energy = 2.0
    sun = bpy.data.objects.new("REVIEW_Sun", sun_data)
    review.objects.link(sun)
    sun.rotation_euler = (math.radians(35), 0, math.radians(-35))
    area_data = bpy.data.lights.new("REVIEW_Area", "AREA")
    area_data.energy = 1300
    area_data.shape = "DISK"
    area_data.size = 8
    area = bpy.data.objects.new("REVIEW_Area", area_data)
    review.objects.link(area)
    area.location = (0, -4, 10)
    area.rotation_euler = (0, 0, 0)
    lights = {"sun": sun, "area": area}
    return review, cameras, lights


def configure_scene() -> None:
    scene = bpy.context.scene
    # Blender 5.2 exposes Eevee Next through the historical BLENDER_EEVEE enum.
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.fps = 30
    scene.world.color = (0.04, 0.055, 0.08)
    if scene.world.use_nodes:
        background = scene.world.node_tree.nodes.get("Background")
        background.inputs["Color"].default_value = (0.04, 0.055, 0.08, 1)
        background.inputs["Strength"].default_value = 0.35


def render_views(cameras: dict[str, bpy.types.Object], lights: dict[str, bpy.types.Object]) -> None:
    scene = bpy.context.scene
    for view in ("front", "side", "back", "perspective"):
        scene.camera = cameras[view]
        scene.render.filepath = str(RENDERS / f"future_courtyard_{view}.png")
        bpy.ops.render.render(write_still=True)
    scene.camera = cameras["perspective"]
    scene.render.filepath = str(RENDERS / "future_courtyard_day.png")
    bpy.ops.render.render(write_still=True)
    lights["sun"].data.energy = 0.12
    lights["area"].data.energy = 420
    background = scene.world.node_tree.nodes.get("Background") if scene.world.use_nodes else None
    if background:
        background.inputs["Color"].default_value = (0.005, 0.01, 0.04, 1)
        background.inputs["Strength"].default_value = 0.08
    scene.render.filepath = str(RENDERS / "future_courtyard_night.png")
    bpy.ops.render.render(write_still=True)
    lights["sun"].data.energy = 2.0
    lights["area"].data.energy = 1300
    if background:
        background.inputs["Color"].default_value = (0.04, 0.055, 0.08, 1)
        background.inputs["Strength"].default_value = 0.35
    wire_material = make_material("MAT_WireReview", "#12D6C5", 0.1, 0.3, 1.5)
    wire_modifiers = []
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and not obj.hide_render and not obj.name.startswith(("COL_", "NAV_")):
            modifier = obj.modifiers.new("AI3D_WireReview", "WIREFRAME")
            modifier.thickness = 0.014
            modifier.use_replace = True
            wire_modifiers.append((obj, modifier))
    scene.view_layers[0].material_override = wire_material
    scene.render.filepath = str(RENDERS / "future_courtyard_wireframe.png")
    bpy.ops.render.render(write_still=True)
    scene.view_layers[0].material_override = None
    for obj, modifier in wire_modifiers:
        obj.modifiers.remove(modifier)


def descendants(root: bpy.types.Object) -> list[bpy.types.Object]:
    result = [root]
    for child in root.children:
        result.extend(descendants(child))
    return result


def select_tree(root: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in descendants(root):
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root


def export_glb(root: bpy.types.Object, path: Path, animations: bool) -> None:
    select_tree(root)
    supported = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
    options = {
        "filepath": str(path),
        "export_format": "GLB",
        "use_selection": True,
        "export_yup": True,
        "export_apply": True,
        "export_materials": "EXPORT",
        "export_cameras": False,
        "export_lights": False,
        "export_extras": True,
        "export_animations": animations,
        "export_force_sampling": True,
        "export_frame_range": False,
        "export_all_actions": animations,
        "export_animation_mode": "ACTIONS",
        "export_nla_strips": False,
    }
    filtered = {key: value for key, value in options.items() if key in supported}
    bpy.ops.export_scene.gltf(**filtered)


def triangle_count(objects: list[bpy.types.Object]) -> int:
    total = 0
    for obj in objects:
        if obj.type != "MESH":
            continue
        obj.data.calc_loop_triangles()
        total += len(obj.data.loop_triangles)
    return total


def scene_bounds(objects: list[bpy.types.Object]) -> list[float]:
    points = []
    for obj in objects:
        if obj.type == "MESH" and not obj.name.startswith(("COL_", "NAV_")):
            points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    mins = [min(point[i] for point in points) for i in range(3)]
    maxs = [max(point[i] for point in points) for i in range(3)]
    return [round(maxs[i] - mins[i], 3) for i in range(3)]


def save_checkpoint(name: str) -> None:
    bpy.ops.wm.save_as_mainfile(filepath=str(CHECKPOINTS / name), check_existing=False)


def render_turntable(camera: bpy.types.Object) -> None:
    scene = bpy.context.scene
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.camera = camera
    frames = RENDERS / "turntable"
    frames.mkdir(parents=True, exist_ok=True)
    for frame in range(48):
        angle = (2 * math.pi * frame) / 48.0
        camera.location = (22 * math.sin(angle), -22 * math.cos(angle), 12)
        camera.rotation_euler = (Vector((0, 0, 1.2)) - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(frames / f"frame_{frame:04d}.png")
        bpy.ops.render.render(write_still=True)


def main() -> None:
    args = parse_args()
    ensure_dirs()
    brief = json.loads(BRIEF_PATH.read_text(encoding="utf-8"))
    random.seed(brief["seed"])
    clear_scene()
    configure_scene()
    palette = brief["palette"]
    materials = {
        "ground": make_material("MAT_Ground", palette["ground"], 0.15, 0.8),
        "wall": make_material("MAT_Wall", palette["wall"], 0.0, 0.72),
        "accent": make_material("MAT_Accent", palette["accent"], 0.15, 0.35, 0.4),
        "metal": make_material("MAT_Metal", palette["metal"], 0.72, 0.32),
        "emission": make_material("MAT_Emission", palette["emission"], 0.1, 0.28, 5.0),
        "foliage": make_material("MAT_Foliage", palette["foliage"], 0.0, 0.78),
        "player": make_material("MAT_Player", palette["player"], 0.25, 0.42),
    }
    env_root, env_collection = create_environment(materials)
    char_root, armature, char_collection = create_character(materials)
    save_checkpoint("future_courtyard_v001_blockout.blend")
    create_collision_and_navigation(env_root, env_collection)
    save_checkpoint("future_courtyard_v002_geometry.blend")
    actions = create_actions(armature)
    save_checkpoint("future_courtyard_v003_material_animation.blend")
    _, cameras, lights = create_review_rig()
    render_views(cameras, lights)
    export_glb(env_root, CANDIDATES / "future_courtyard_environment.raw.glb", False)
    char_root.location = (0, 0, 0)
    export_glb(char_root, CANDIDATES / "future_courtyard_character.raw.glb", True)
    char_root.location = (0, -2, 0)
    save_checkpoint("future_courtyard_v004_export.blend")
    if args.turntable:
        render_turntable(cameras["perspective"])
    env_objects = descendants(env_root)
    char_objects = descendants(char_root)
    metrics = {
        "assetId": brief["assetId"],
        "seed": brief["seed"],
        "blenderVersion": bpy.app.version_string,
        "environmentTriangles": triangle_count(env_objects),
        "characterTriangles": triangle_count(char_objects),
        "materials": len(materials),
        "textures": 0,
        "bones": len(armature.data.bones),
        "environmentBoundsM": scene_bounds(env_objects),
        "actions": [{"name": action.name, "frameRange": [round(v, 3) for v in action.frame_range]} for action in actions],
        "candidateFiles": {
            "environment": str(CANDIDATES / "future_courtyard_environment.raw.glb"),
            "character": str(CANDIDATES / "future_courtyard_character.raw.glb"),
        },
    }
    (CANDIDATES / "future_courtyard.metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print("AI3D_BUILD_COMPLETE", json.dumps(metrics, ensure_ascii=False))


if __name__ == "__main__":
    main()
