# Blender Instructions

- Every stage reads the previous checkpoint and writes a new checkpoint; never overwrite an approved `.blend`.
- Put review cameras and lights in `REVIEW_ONLY` and exclude that collection from GLB exports.
- Run long Blender changes from tracked scripts in `blender/scripts`; MCP calls may only invoke those scripts.
- Export environment and character separately from the final checkpoint.
- Render fixed front, side, back, perspective, wireframe, day, and night evidence views.

