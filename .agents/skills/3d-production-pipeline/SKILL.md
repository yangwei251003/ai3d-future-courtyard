---
name: 3d-production-pipeline
description: Build, validate, or repair deterministic Blender-to-glTF pipelines whose canonical assets must run consistently in Godot and Three.js. Use for staged 3D production, asset promotion, cross-runtime verification, or pipeline troubleshooting; do not use for unrelated CAD/CAM work.
---

# 3D Production Pipeline

Treat the brief as intent, Blender scripts as reproducible authoring, and canonical GLBs as the runtime contract.

## Workflow

1. Run `tools/doctor.ps1`. Stop if required paths, versions, MCP bridges, or the Unicode workspace gate fail.
2. Read the asset brief and [production contract](references/production-contract.md).
3. Build one stage at a time with `tools/build-asset.ps1`; inspect the prior checkpoint before mutation.
4. Review fixed renders and metrics. Failed candidates remain under `build/candidates` and never replace runtime assets.
5. Promote only after `tools/verify-all.ps1` passes Blender, glTF, Godot, Web, and cross-hash gates.
6. Record failures and recovery checkpoints in gate receipts rather than hiding them.

## Non-obvious constraints

- Invoke tracked Blender scripts instead of pasting long Python through MCP.
- One Blender unit is one metre. Model characters facing Blender `-Y`; the exporter maps this to glTF `+Z` front.
- Do not add Draco, Meshopt, texture, or consumer-specific asset variants in v1.
- Keep provider integrations and network-dependent generation disabled unless a later task explicitly authorizes them.
- Godot and Web must consume the exact same canonical asset bytes; compare SHA-256, not filenames.

For gate definitions, failure categories, and recovery rules, read [gates-and-recovery](references/gates-and-recovery.md). Read it whenever a build fails or an asset is about to be promoted.
