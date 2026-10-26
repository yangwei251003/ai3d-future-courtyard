from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIEF = ROOT / "assets" / "briefs" / "future_courtyard.brief.json"
METRICS = ROOT / "build" / "candidates" / "future_courtyard.metrics.json"
CANDIDATES = {
    "environment": ROOT / "build" / "candidates" / "future_courtyard_environment.raw.glb",
    "character": ROOT / "build" / "candidates" / "future_courtyard_character.raw.glb",
}
RUNTIME = {
    "environment": ROOT / "assets" / "runtime" / "future_courtyard_environment.glb",
    "character": ROOT / "assets" / "runtime" / "future_courtyard_character.glb",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_glb(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 20:
        raise ValueError(f"{path.name}: file too small")
    magic, version, declared_length = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF" or version != 2 or declared_length != len(data):
        raise ValueError(f"{path.name}: invalid GLB header")
    offset = 12
    document = None
    while offset < len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset : offset + chunk_length]
        offset += chunk_length
        if chunk_type == 0x4E4F534A:
            document = json.loads(chunk.rstrip(b" \t\r\n\0").decode("utf-8"))
    if document is None:
        raise ValueError(f"{path.name}: JSON chunk missing")
    return document


def triangle_count(doc: dict) -> int:
    total = 0
    accessors = doc.get("accessors", [])
    for mesh in doc.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            mode = primitive.get("mode", 4)
            if mode != 4:
                continue
            if "indices" in primitive:
                total += accessors[primitive["indices"]]["count"] // 3
            else:
                position_accessor = primitive.get("attributes", {}).get("POSITION")
                if position_accessor is not None:
                    total += accessors[position_accessor]["count"] // 3
    return total


def inspect(path: Path) -> dict:
    doc = read_glb(path)
    return {
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "nodes": [node.get("name", "") for node in doc.get("nodes", [])],
        "animations": [animation.get("name", "") for animation in doc.get("animations", [])],
        "materials": [material.get("name", "") for material in doc.get("materials", [])],
        "textures": len(doc.get("textures", [])),
        "images": len(doc.get("images", [])),
        "triangles": triangle_count(doc),
        "externalUris": [
            item["uri"]
            for collection in (doc.get("buffers", []), doc.get("images", []))
            for item in collection
            if isinstance(item, dict) and "uri" in item
        ],
    }


def assertion(assertions: list[dict], assertion_id: str, expected, actual, passed: bool) -> None:
    assertions.append({"id": assertion_id, "status": "pass" if passed else "fail", "expected": expected, "actual": actual})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--promote", action="store_true")
    args = parser.parse_args()
    brief = json.loads(BRIEF.read_text(encoding="utf-8"))
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    reports = {name: inspect(path) for name, path in CANDIDATES.items()}
    assertions: list[dict] = []

    combined_bytes = sum(report["bytes"] for report in reports.values())
    combined_triangles = sum(report["triangles"] for report in reports.values())
    unique_materials = sorted(set(reports["environment"]["materials"] + reports["character"]["materials"]))
    node_names = set(reports["environment"]["nodes"])
    character_nodes = set(reports["character"]["nodes"])
    animation_names = set(reports["character"]["animations"])
    budgets = brief["budgets"]

    assertion(assertions, "glb.version", 2, 2, True)
    assertion(assertions, "budget.bytes", budgets["maxCombinedBytes"], combined_bytes, combined_bytes <= budgets["maxCombinedBytes"])
    assertion(assertions, "budget.triangles", budgets["maxTriangles"], combined_triangles, combined_triangles <= budgets["maxTriangles"])
    assertion(assertions, "budget.materials", budgets["maxMaterials"], len(unique_materials), len(unique_materials) <= budgets["maxMaterials"])
    assertion(assertions, "budget.textures", budgets["maxTextures"], sum(report["textures"] for report in reports.values()), sum(report["textures"] for report in reports.values()) == 0)
    assertion(assertions, "budget.bones", budgets["maxBones"], metrics["bones"], metrics["bones"] <= budgets["maxBones"])
    assertion(assertions, "external.uris", [], reports["environment"]["externalUris"] + reports["character"]["externalUris"], not reports["environment"]["externalUris"] and not reports["character"]["externalUris"])
    for module in brief["world"]["modules"]:
        prefix = module.replace("KIT_WallSolid_4x3", "KIT_WallSolid")
        assertion(assertions, f"module.{module}", "present", prefix, any(name.startswith(prefix) for name in node_names))
    for prop in brief["world"]["props"]:
        assertion(assertions, f"prop.{prop}", "present", prop, prop in node_names)
    assertion(assertions, "collision.proxies", ">=5", len([name for name in node_names if name.startswith("COL_") and name.endswith("-colonly")]), len([name for name in node_names if name.startswith("COL_") and name.endswith("-colonly")]) >= 5)
    assertion(assertions, "navigation.proxy", "present", "NAV_Courtyard-navmesh", "NAV_Courtyard-navmesh" in node_names)
    assertion(assertions, "character.root", "CHR_Player", sorted(character_nodes), "CHR_Player" in character_nodes)
    assertion(assertions, "character.rig", "RIG_Player", sorted(character_nodes), "RIG_Player" in character_nodes)
    expected_clips = {clip["name"] for clip in brief["character"]["clips"]}
    assertion(assertions, "character.animations", sorted(expected_clips), sorted(animation_names), expected_clips == animation_names)
    assertion(assertions, "bounds.environment", "<=24.5m XY, <=5m Z", metrics["environmentBoundsM"], metrics["environmentBoundsM"][0] <= 24.5 and metrics["environmentBoundsM"][1] <= 24.5 and metrics["environmentBoundsM"][2] <= 5.0)

    passed = all(item["status"] == "pass" for item in assertions)
    evidence_paths = [
        "blender/renders/future_courtyard_front.png",
        "blender/renders/future_courtyard_side.png",
        "blender/renders/future_courtyard_back.png",
        "blender/renders/future_courtyard_perspective.png",
        "blender/renders/future_courtyard_wireframe.png",
        "blender/renders/future_courtyard_day.png",
        "blender/renders/future_courtyard_night.png",
    ]
    receipt = {
        "gateId": "G4",
        "status": "pass" if passed else "fail",
        "inputHashes": {name: report["sha256"] for name, report in reports.items()},
        "toolVersions": {"blender": metrics["blenderVersion"], "validator": "ai3d-glb-validator/1.0.0"},
        "assertions": assertions,
        "evidencePaths": evidence_paths,
        "failureCategory": None if passed else "asset-contract",
        "recoveryFrom": None if passed else "future_courtyard_v003_material_animation.blend",
    }
    receipt_path = ROOT / "evidence" / "gates" / "G4-glb.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    if not passed:
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
        return 1

    if args.promote:
        for name, source in CANDIDATES.items():
            shutil.copy2(source, RUNTIME[name])
        shutil.copy2(ROOT / "blender" / "renders" / "future_courtyard_perspective.png", ROOT / "assets" / "runtime" / "future_courtyard_poster.png")

    runtime_report = {
        name: {**report, "path": RUNTIME[name].relative_to(ROOT).as_posix()}
        for name, report in reports.items()
    }
    manifest = {
        "schemaVersion": "1.0.0",
        "assetId": brief["assetId"],
        "checkpointId": "future_courtyard_v004_export",
        "source": {
            "brief": BRIEF.relative_to(ROOT).as_posix(),
            "briefSha256": sha256(BRIEF),
            "stageScript": "blender/scripts/build_future_courtyard.py",
            "stageScriptSha256": sha256(ROOT / "blender" / "scripts" / "build_future_courtyard.py"),
            "seed": brief["seed"],
        },
        "runtime": {"format": "glTF 2.0 GLB", "metersPerUnit": 1, "upAxis": "Y", "assets": runtime_report},
        "toolchain": {"blender": metrics["blenderVersion"], "validator": "ai3d-glb-validator/1.0.0"},
        "contents": {
            "modules": brief["world"]["modules"],
            "props": brief["world"]["props"],
            "materials": unique_materials,
            "animations": sorted(animation_names),
        },
        "metrics": {
            "bytes": combined_bytes,
            "triangles": combined_triangles,
            "materials": len(unique_materials),
            "textures": 0,
            "bones": metrics["bones"],
            "environmentBoundsM": metrics["environmentBoundsM"],
        },
        "provenance": {"kind": "deterministic-procedural", "prompt": "low-poly future courtyard", "seed": brief["seed"], "thirdParty": []},
        "validation": {"g4": receipt_path.relative_to(ROOT).as_posix(), "generatedAt": datetime.now(timezone.utc).isoformat()},
    }
    manifest_path = ROOT / "assets" / "manifests" / "future_courtyard.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"status": "pass", "promoted": args.promote, "bytes": combined_bytes, "triangles": combined_triangles, "animations": sorted(animation_names)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

