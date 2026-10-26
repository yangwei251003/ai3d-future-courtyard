# Web Instructions

- Load the canonical GLBs through Vite's external `publicDir`; do not commit copied Web-specific GLBs.
- Clone materials before palette changes so the GLTFLoader cache remains immutable.
- Preserve mobile DPR limits, reduced-motion behavior, and the static fallback.
- Production build and Playwright checks must pass with no console errors.

