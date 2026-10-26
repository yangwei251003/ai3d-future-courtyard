# AI3D Repository Instructions

This repository is a deterministic Blender → glTF → Godot/Web production pipeline.

## Source of truth

- `assets/briefs/future_courtyard.brief.json` is the design input.
- Blender stage scripts are the only persistent scene mutation source.
- `assets/runtime/*.glb` are the only canonical runtime assets.
- `assets/manifests/*.manifest.json` and `evidence/gates/*.json` record promotion evidence.
- Never hand-edit generated GLB files or committed Blender checkpoints.

## Production invariants

- Blender is Z-up, one unit is one metre. Export glTF as Y-up; do not add consumer-side correction rotations.
- Visible object scale must be positive and applied. No external textures or third-party assets in v1.
- Use only `ENV_`, `KIT_`, `PROP_`, `CHR_`, `RIG_`, `COL_`, and `NAV_` object prefixes.
- Collision and navigation meshes use `-colonly` and `-navmesh` suffixes.
- Run `tools/verify-all.ps1` before promoting a candidate or claiming completion.

## Tool safety

- Blender MCP may execute only repository-tracked scripts or small reversible inspection snippets.
- Keep third-party Blender asset providers disabled and telemetry disabled.
- Godot MCP runs with strict mode. Do not add filesystem, shell, or network operations to runtime scripts.
- Do not expose tokens or copy user Codex configuration into the repository.

Use the project skill at `.agents/skills/3d-production-pipeline` for production or repair tasks.

