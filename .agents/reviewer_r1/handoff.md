# Adversarial Review Handoff Report: India Mule Corridors Map

> [!WARNING] **Skepticism Disclaimer**
> High confidence in code structure, mathematical vector geometry, and build integrity (977 pytest passed, 0 ruff errors, 0 ESLint warnings, successful production build); moderate confidence in visual tile fetching in environments with sandboxed/restricted DNS to external ArcGIS servers.

## 1. What the prior attempt got wrong
1. **Ineffective DOM Click Event Propagation Stopper on Hub Markers**:
   - **Input**: User clicks a city hub marker on the Leaflet map.
   - **Expected**: Native DOM click event stops propagating to parent DOM containers, preventing parent container clicks or slide-out drawer activations.
   - **Actual**: Native DOM `click` event bubbled up to parent containers unimpeded.
   - **Root Cause**: The prior attempt wrote `marker.on("click", (e) => { L.DomEvent.stopPropagation(e); })`. In Leaflet, `e` is an `L.LeafletEvent`, not a native DOM event. Leaflet's internal `stopPropagation` function checks `if (e.stopPropagation) { e.stopPropagation(); } else if (e.originalEvent) { e.originalEvent._stopped = true; }`. Because `e.stopPropagation` is undefined on `L.LeafletEvent`, Leaflet only set a custom property `e.originalEvent._stopped = true`, never invoking `e.originalEvent.stopPropagation()` or `cancelBubble`. The browser's native DOM event bubbling was never stopped.

2. **Unintercepted Click Events on Map Canvas and Corridor Polylines**:
   - **Input**: User clicks on the map canvas or polyline corridors.
   - **Expected**: Clicks within the map canvas do not propagate to parent page layout containers.
   - **Actual**: Clicks on the map canvas and polylines bubbled up to parent DOM containers.
   - **Root Cause**: No click event handlers were registered on `map` or `polyline` to stop `e.originalEvent` propagation.

3. **Leaflet Container ID Reuse Vulnerability on Component Remount**:
   - **Input**: Component remounts (e.g. fast navigation, React 18 StrictMode double-invocations).
   - **Expected**: `L.map` initializes without throwing fatal container collision errors.
   - **Actual**: If `containerRef.current._leaflet_id` persists on a reused DOM element, Leaflet throws `Error: Map container is already initialized.`
   - **Root Cause**: Did not delete `containerRef.current._leaflet_id` before instantiating `L.map`.

## 2. What I changed
- `frontend/src/components/overview/GeoMuleMap.jsx`:
  - Fixed click event propagation on city hub markers to inspect and pass `e.originalEvent` to `L.DomEvent.stopPropagation(e.originalEvent)`.
  - Added click event handler to `map.on("click")` and `line.on("click")` to intercept and stop `e.originalEvent` propagation.
  - Added container safeguard `if (containerRef.current._leaflet_id) delete containerRef.current._leaflet_id;` prior to `L.map` instantiation.
  - Rebuilt production assets via Vite.
- `tests/test_geomulemap_contract.py`:
  - Added assertion verifying that `stopPropagation(e.originalEvent)` is explicitly used to ensure native DOM click propagation is halted.
- `frontend/dist/*`:
  - Rebuilt fresh production assets.

## 3. Verification Record
- **Deep Verification (ran actual tests):**
  - `./.venv/bin/pytest tests/`: 977 passed, 6 warnings in 137.42s.
  - `./.venv/bin/pytest tests/test_geomulemap_contract.py`: 8 passed in 0.98s.
  - `./.venv/bin/ruff check app tests`: All checks passed.
  - `cd frontend && npm run lint`: ESLint passed with 0 warnings (`--max-warnings 0`).
  - `cd frontend && npm run build`: Vite production build passed cleanly in 14.55s (`dist/assets/index-BNlH00g8.js`, `dist/assets/index-DWCBC0gd.css`).
  - Python mathematical verification: Validated Mercator bearing angles across all 9 corridors (e.g., Mewat → Delhi: -81.4°, Jamtara → Delhi: -151.6°, Delhi → Mumbai: 111.8°, Kolkata → Mumbai: 166.4°), confirming orientation matches directional flow.
- **Shallow Verification (manual only):**
  - Node.js runtime verification of Leaflet's `stopPropagation` implementation proving that passing `e.originalEvent` invokes native `stopPropagation()` whereas passing `e` does not.
- **Unverified aspects:**
  - Live visual tile rendering in a real desktop/mobile browser window with an unrestricted internet connection (the sandbox environment has restricted DNS that prevents external HTTP resolution of ArcGIS tile servers).

## 4. Known Issues
- `Shallow Verification`: Live tile image rendering from `https://server.arcgisonline.com/...` cannot be visually confirmed via live screenshot inside this sandboxed container due to network DNS restriction, although the tile endpoint URL and Leaflet configuration are standard and valid.
- `Minor Robustness Risk`: In a completely air-gapped environment with zero internet access, external ArcGIS map tiles will not load, though vector polylines, SVG flow chevrons, hub markers, and interactive popups will still render without crashing.

## 5. Remaining risk & next step
- Task is complete. All three core requirements (R1 reliable initialization with direct Leaflet import and ResizeObserver size invalidation, R2 directional flow arrows oriented via Mercator bearings, R3 stable interaction with `autoPan: false` and DOM event isolation) are satisfied, and all 977 backend and frontend tests pass cleanly.
