# Godot Instructions

- Use GDScript and the Compatibility renderer.
- Runtime code must not write files, open sockets, or start processes.
- Keep imported GLB files canonical; customize them through wrapper scenes and scripts.
- Movement is controller-driven. Character animation clips contain no root translation.
- Keep automated tests deterministic and runnable headlessly.

