from __future__ import annotations

import json
from pathlib import Path

import bpy


def run() -> dict:
    root = Path(__file__).resolve().parents[2]
    output = root / "evidence" / "tmp"
    output.mkdir(parents=True, exist_ok=True)
    before = len(bpy.context.scene.objects)
    bpy.ops.mesh.primitive_cube_add(size=0.25, location=(0, 0, 6))
    obj = bpy.context.object
    obj.name = "MCP_SMOKE_TEMP"
    bpy.data.libraries.write(str(output / "blender-mcp-smoke.blend"), {obj, obj.data})
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(
        filepath=str(output / "blender-mcp-smoke.glb"),
        export_format="GLB",
        use_selection=True,
        export_animations=False,
        export_cameras=False,
        export_lights=False,
    )
    bpy.data.objects.remove(obj, do_unlink=True)
    result = {
        "created": "MCP_SMOKE_TEMP",
        "sceneCountBefore": before,
        "sceneCountAfter": len(bpy.context.scene.objects),
        "blendBytes": (output / "blender-mcp-smoke.blend").stat().st_size,
        "glbBytes": (output / "blender-mcp-smoke.glb").stat().st_size,
        "reversible": before == len(bpy.context.scene.objects),
    }
    print("AI3D_MCP_SMOKE", json.dumps(result))
    return result


if __name__ == "__main__":
    run()

