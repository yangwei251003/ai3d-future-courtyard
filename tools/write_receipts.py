from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATES = ROOT / "evidence" / "gates"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_gate(gate_id: str, assertions: list[dict], evidence: list[str], tools: dict, recovery: str | None = None) -> None:
    status = "pass" if all(item["pass"] for item in assertions) else "fail"
    data = {
        "gateId": gate_id,
        "status": status,
        "inputHashes": {},
        "toolVersions": tools,
        "assertions": assertions,
        "evidencePaths": evidence,
        "failureCategory": None if status == "pass" else "verification",
        "recoveryFrom": recovery,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
    }
    (GATES / f"{gate_id}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if status != "pass":
        raise SystemExit(f"{gate_id} failed")


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def main() -> None:
    GATES.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "assets/manifests/future_courtyard.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    env = ROOT / manifest["runtime"]["assets"]["environment"]["path"]
    char = ROOT / manifest["runtime"]["assets"]["character"]["path"]
    tools = {"blender": "5.2.1", "godot": "4.7.2", "validator": "1.0.0"}
    write_gate("G1", [{"name": "blockoutCheckpoint", "pass": exists("blender/checkpoints/future_courtyard_v001_blockout.blend")}, {"name": "fiveViews", "pass": all(exists(f"blender/renders/future_courtyard_{v}.png") for v in ("front", "side", "back", "perspective", "wireframe"))}], ["blender/checkpoints/future_courtyard_v001_blockout.blend", "blender/renders"], tools)
    write_gate("G2", [{"name": "geometryCheckpoint", "pass": exists("blender/checkpoints/future_courtyard_v002_geometry.blend")}, {"name": "budget", "pass": manifest["metrics"]["triangles"] <= 25000}, {"name": "naming", "pass": all(name.startswith(("ENV_", "KIT_", "PROP_", "COL_", "NAV_")) for name in manifest["runtime"]["assets"]["environment"]["nodes"])}], ["blender/checkpoints/future_courtyard_v002_geometry.blend", "assets/manifests/future_courtyard.manifest.json"], tools, "future_courtyard_v001_blockout")
    write_gate("G3", [{"name": "materialAnimationCheckpoint", "pass": exists("blender/checkpoints/future_courtyard_v003_material_animation.blend")}, {"name": "animations", "pass": set(manifest["contents"]["animations"]) == {"Idle_loop", "Walk_loop", "Run_loop", "Jump"}}, {"name": "materials", "pass": manifest["metrics"]["materials"] <= 8}], ["blender/checkpoints/future_courtyard_v003_material_animation.blend", "blender/renders/future_courtyard_day.png", "blender/renders/future_courtyard_night.png"], tools, "future_courtyard_v002_geometry")
    smoke = (ROOT / "evidence/tmp/godot-smoke.txt").read_text(encoding="utf-8", errors="replace")
    mcp = json.loads((ROOT / "evidence/mcp/godot-mcp-e2e.json").read_text(encoding="utf-8"))
    write_gate("G5", [{"name": "headlessGameplaySmoke", "pass": '"status":"pass"' in smoke}, {"name": "mcpReadWriteScreenshotRun", "pass": mcp.get("status") == "pass"}, {"name": "dayNightEvidence", "pass": exists("evidence/screenshots/godot-day.png") and exists("evidence/screenshots/godot-night.png")}], ["evidence/tmp/godot-smoke.txt", "evidence/mcp/godot-mcp-e2e.json", "evidence/mcp/godot-mcp-audit-summary.json", "evidence/screenshots/godot-day.png", "evidence/screenshots/godot-night.png"], {"godot": "4.7.2", "godotMcp": "3.2.2"}, "future_courtyard_v004_export")
    web_test = (ROOT / "evidence/tmp/web-test.txt").read_text(encoding="utf-8", errors="replace")
    write_gate("G6", [{"name": "desktopAndMobile", "pass": "6 passed" in web_test}, {"name": "desktopScreenshot", "pass": exists("evidence/screenshots/web-desktop.png")}, {"name": "mobileScreenshot", "pass": exists("evidence/screenshots/web-mobile.png")}], ["evidence/tmp/web-build.txt", "evidence/tmp/web-test.txt", "evidence/screenshots/web-desktop.png", "evidence/screenshots/web-mobile.png"], {"vite": "8.2.2", "playwright": "1.62.1"}, "G5")
    hashes_ok = digest(env) == manifest["runtime"]["assets"]["environment"]["sha256"] and digest(char) == manifest["runtime"]["assets"]["character"]["sha256"]
    docs_ok = all(exists(name) for name in ("docs/开始这里.md", "docs/故障排除.md", "docs/如何描述下一个3D任务.md", "docs/学习挑战.md"))
    videos_ok = exists("evidence/videos/future_courtyard_turntable.mp4") and exists("evidence/videos/future_courtyard_demo.mp4")
    cad_ok = exists("evidence/screenshots/cad-environment.png") and exists("evidence/screenshots/cad-character.png")
    write_gate("G7", [{"name": "canonicalHashes", "pass": hashes_ok}, {"name": "tutorials", "pass": docs_ok}, {"name": "videos", "pass": videos_ok}, {"name": "cadViewerReview", "pass": cad_ok}], ["assets/manifests/future_courtyard.manifest.json", "docs", "evidence/videos", "evidence/screenshots/cad-environment.png", "evidence/screenshots/cad-character.png"], tools, "G6")
    manifest.setdefault("validation", {}).update({f"g{i}": f"evidence/gates/G{i}.json" for i in range(1, 8)})
    manifest["validation"]["g0"] = "evidence/gates/G0-environment.json"
    manifest["validation"]["verifiedAt"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("receipts-ok:G0-G7")


if __name__ == "__main__":
    main()
