# Production Contract

- Canonical inputs: `assets/briefs/*.brief.json`.
- Canonical runtime outputs: `assets/runtime/*.glb`.
- Blender checkpoints are append-only and named by stage.
- Review-only lights and cameras are never exported.
- Environment and character are separate GLBs.
- Allowed object prefixes: `ENV_`, `KIT_`, `PROP_`, `CHR_`, `RIG_`, `COL_`, `NAV_`.
- Collider suffix: `-colonly`; navigation suffix: `-navmesh`.
- Visible meshes must have positive applied scale and no missing materials.
- v1 permits Principled PBR scalar/color values but no image textures.
- Consumers may change lights and cloned material values, not geometry or asset orientation.

