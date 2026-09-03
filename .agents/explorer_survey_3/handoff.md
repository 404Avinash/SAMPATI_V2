# Handoff Report: Survey R3 — Reactive UI Toast Notifications & Frontend Quality

- **Surveyor**: Surveyor 3 (`teamwork_preview_explorer`)
- **Working Directory**: `/home/avi/Downloads/Sampati_v2/.agents/explorer_survey_3`
- **Focus Area**: Requirement R3 — Reactive UI Toast Notifications, Frontend Quality, and Zero-Warning Architecture
- **Date**: 2026-09-03T06:54:00Z

---

## 1. Observation

### 1.1 Existing Frontend Dependencies (`frontend/package.json`)
Direct examination of `frontend/package.json` (lines 12–31) revealed:
```json
  "dependencies": {
    "framer-motion": "^11.11.17",
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "react-markdown": "9.1.0",
    "react-router-dom": "^6.28.0",
    "recharts": "2.15.4"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "4.7.0",
    "autoprefixer": "10.5.4",
    "eslint": "^8.57.0",
    "eslint-plugin-react": "^7.34.1",
    "eslint-plugin-react-hooks": "^4.6.2",
    "eslint-plugin-react-refresh": "^0.4.6",
    "postcss": "8.5.26",
    "tailwindcss": "3.4.19",
    "vite": "5.4.21"
  }
```
- **No external toast library** is currently installed (`react-toastify`, `react-hot-toast`, `sonner` are absent).
- **`framer-motion` (v11.11.17)** is already installed as a first-class production dependency and actively used in `OverviewPage.jsx` and `Modal.jsx`.
- **`tailwindcss` (v3.4.19)** is installed with custom design tokens in `tailwind.config.js`:
  - Palette: `ink.900` (`#0b1f3a`), `saffron` (`#c8641e`), `surface-muted` (`#f4f6fa`), `hairline` (`#e1e6ee`), `verdict-allow` (`#0f7a3d`), `verdict-hold` (`#a8660a`), `verdict-block` (`#b3261e`), fonts `serif`, `sans`, `mono`.

### 1.2 Frontend ESLint Rules & Build Baseline
Direct examination of `frontend/.eslintrc.cjs` and `frontend/package.json`:
- Lint script: `eslint src --ext js,jsx --report-unused-disable-directives --max-warnings 0`.
- Extends: `eslint:recommended`, `plugin:react/recommended`, `plugin:react/jsx-runtime`, `plugin:react-hooks/recommended`.
- Current execution result:
  - `npm run lint` exited with **code 0** (0 errors, 0 warnings).
  - `npm run build` completed cleanly in **14.69s** (exit code 0).
- Special Hook rule in `AGENTS.md`: In React cleanup functions (e.g. `useEffect`), mutable refs like `stateRef.current` must be copied to a local variable outside the return block to satisfy exhaustive-deps and avoid ESLint warnings.

### 1.3 Root Provider Hierarchy (`App.jsx` & `MainLayout.jsx`)
In `frontend/src/App.jsx` (lines 11–36):
```jsx
export default function App() {
  return (
    <AppStateProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
            <Route path="/" element={<Navigate to="/overview" replace />} />
            <Route path="/overview" element={<OverviewPage />} />
            ...
```
- `AppStateProvider` wraps the entire route tree.
- Currently, only `AppStateContext.jsx` exists in `frontend/src/context/`.
- In `frontend/src/layouts/MainLayout.jsx`, `<CaseDrawer />` is rendered alongside `<Outlet />` and `<Navbar />`.
- In `frontend/src/pages/OverviewPage.jsx` (lines 27–80), an ad-hoc local Honeypot notification is rendered via `AnimatePresence` and `motion.div` at `fixed top-20 right-6 z-50`.

### 1.4 Complete Inventory of Operational Dashboard Buttons Lacking Toast Feedback
Across 7 primary component and page files, 24 operational actions were audited:

| # | File Path & Line | Action Element | Current Behavior | Required Reactive Toast Notification |
|---|---|---|---|---|
| 1 | `components/ControlBar.jsx:100` | Button: "⚡ Start Live Feed" / "Stop Live Feed" | Calls `toggleAutoFeed()`. Toggles state silently without toast. | **Success**: `toast.success("Live Feed Started", "Streaming autonomous transactions at 10 tx/s")`<br>**Info**: `toast.info("Live Feed Paused", "Autonomous traffic stream halted")` |
| 2 | `components/ControlBar.jsx:152` | Button: "▶ Run batch simulation" | Calls `onSimulate(count, fraud/100)`. Updates charts but gives no toast. | **Success**: `toast.success("Batch Simulation Complete", "Processed ${count} txns (${fraud}% fraud ratio)")` |
| 3 | `components/ControlBar.jsx:160` | Button: "⟲ Federation round" | Calls `onFederate()`. Triggers backend silently. | **Success/Info**: `toast.info("Federation Mesh Synced", "Participating PSP nodes agreed on active ring clusters")` |
| 4 | `components/common/Navbar.jsx:133` | Button: "Refresh Data" | Calls `refreshStats()` & `refreshCases()`. | **Info**: `toast.info("Telemetry Synced", "Latest transaction stats and active cases refreshed")` |
| 5 | `components/CaseDrawer.jsx:305` | Button: "Copy" Case ID | Local state `copied` only. | **Info**: `toast.info("Case ID Copied", "Copied ${caseId} to clipboard")` |
| 6 | `components/CaseDrawer.jsx:318, 565` | Button: "Export SAR" (PDF) | Calls `downloadSarPdf()`. Sets local `downloadingPdf`. | **Info**: `toast.info("Generating Dossier", "Compiling Suspicious Activity Report PDF...")`<br>**Success**: `toast.success("SAR Export Complete", "Downloaded SAR PDF for case ${caseId}")`<br>**Error**: `toast.error("Export Failed", err.message)` |
| 7 | `components/CaseDrawer.jsx:552` | Button: "Confirm Fraud" | Calls `onFeedback(caseId, true)`. Silent. | **Warning**: `toast.warning("Fraud Confirmed", "Case ${caseId} confirmed as mule activity")` |
| 8 | `components/CaseDrawer.jsx:558` | Button: "Dismiss" | Calls `onFeedback(caseId, false)`. Silent. | **Info**: `toast.info("Case Dismissed", "Case ${caseId} marked as legitimate")` |
| 9 | `components/investigations/StatusTransitionActions.jsx:74` | Button: "Mark as Reviewed" | Sets inline text; uses `alert(...)` on error! | **Success**: `toast.success("Status Updated", "Case ${caseId} marked as REVIEWED")` |
| 10 | `components/investigations/StatusTransitionActions.jsx:84` | Button: "Escalate to DPIP" | Sets inline text; uses `alert(...)` on error! | **Warning**: `toast.warning("Escalated to DPIP", "Case ${caseId} broadcast to RBI DPIP mesh")` |
| 11 | `components/investigations/StatusTransitionActions.jsx:94` | Button: "Confirm Fraud / Mule" | Sets inline text; uses `alert(...)` on error! | **Warning**: `toast.warning("Mule Ring Recorded", "Case ${caseId} updated to RESOLVED mule ring")` |
| 12 | `components/investigations/StatusTransitionActions.jsx:104` | Button: "Dismiss False Pos" | Sets inline text; uses `alert(...)` on error! | **Info**: `toast.info("Case Dismissed", "Case ${caseId} marked false positive")` |
| 13 | `components/investigations/CaseDetailModal.jsx:19` | Button: "Copy" Case ID | **Uses raw browser `alert(...)`!** | **Info**: `toast.info("Case ID Copied", "Copied ${caseId} to clipboard")` |
| 14 | `pages/InvestigationsPage.jsx:120` | Button: "▶ Generate Fraud Stream" | Calls `runSimulation(250, 0.20)` silently. | **Success**: `toast.success("Fraud Stream Injected", "250 synthetic transactions processed")` |
| 15 | `pages/InvestigationsPage.jsx:105` | Button: "Reset Filters" | Resets filters silently. | **Info**: `toast.info("Filters Reset", "Showing all cases and verdicts")` |
| 16 | `pages/AnalyticsPage.jsx:268` | Button: "Refresh analytics data" | Loads analytics silently. | **Info**: `toast.info("Analytics Refreshed", "Time-series & threat fabric synchronized")` |
| 17 | `pages/AnalyticsPage.jsx:289` | Button: "▶ Inject Telemetry" | Calls `runSimulation(200, 0.18)` silently. | **Success**: `toast.success("Telemetry Injected", "200 synthetic transactions loaded into analytics")` |
| 18 | `pages/SystemHealthPage.jsx:152` | Button: "Manual refresh" | Fetches health silently. | **Info**: `toast.info("Health Telemetry Polled", "Database, Redis, and Latency stats refreshed")` |
| 19 | `pages/SettingsPage.jsx:37` | Button: "Save Sensitivity" | Sets local `sensitivitySavedMsg`. | **Success**: `toast.success("Sensitivity Updated", "Detection threshold set to ${sensitivity}")` |
| 20 | `pages/SettingsPage.jsx:53` | Buttons: Preset Sensitivity | Sets local `sensitivitySavedMsg`. | **Success**: `toast.success("Regime Applied", "Sensitivity preset applied successfully")` |
| 21 | `pages/SettingsPage.jsx:67` | Button: "Run Workload Simulation" | Sets local `simResultMsg`. | **Success**: `toast.success("Workload Executed", "Generated ${txnCount} transactions (${fraudRatio}% fraud)")` |
| 22 | `pages/SettingsPage.jsx:79` | Button: "Trigger Ring Sync" | Sets local `simResultMsg`. | **Info**: `toast.info("Federation Consensus", "Federated ring sync complete. Blacklist updated.")` |
| 23 | `pages/SettingsPage.jsx:89` | Button: "Check CI/CD Status" | Refreshes deploy status silently. | **Info**: `toast.info("CI/CD Checked", "Latest commit sha & deployment verified")` |
| 24 | `pages/SettingsPage.jsx:98` | Button: "Simulate Staging Deployment" | Sets local timeout. | **Success**: `toast.success("Staging Rollout Simulated", "Container image deployed to staging cluster")` |

---

## 2. Logic Chain

1. **Evaluation of Library Options (Zero-Dependency vs. External)**:
   - *Option A: External package (`sonner`, `react-hot-toast`, `react-toastify`)*:
     - Adding another npm package requires network installation, updates to `package-lock.json`, and introduces potential version pinning issues or styling disconnects from the existing Tailwind palette (`ink-900`, `saffron`, `verdict-allow`, etc.).
   - *Option B: Zero-Dependency Custom React Context with Framer Motion (`framer-motion` + Tailwind)*:
     - `framer-motion` (v11.11.17) is ALREADY a required production dependency in `frontend/package.json`.
     - Tailwind CSS is already configured with all brand tokens.
     - `OverviewPage.jsx` already implemented a raw prototype of an animated notification with `framer-motion` for honeypots.
     - A custom `<ToastProvider>` and `useToast()` hook adds **0 bytes of external bundle overhead**, requires **0 npm install commands**, and provides 100% control over layout, auto-dismiss countdown animation, and custom SAMPATI styling.
   - *Deduction*: Option B (Zero-dependency custom Framer Motion Toast System) is strictly superior and safest for the repository.

2. **Placement in Component Tree**:
   - `App.jsx` renders `<AppStateProvider><BrowserRouter><Routes>...`.
   - If `<ToastProvider>` is placed at the very top of `App.jsx` (wrapping `<AppStateProvider>`), then:
     1. Both `AppStateContext` AND all page/view components can call `useToast()`.
     2. Core async lifecycle actions in `AppStateContext.jsx` (`startAutoFeed`, `stopAutoFeed`, `runSimulation`, `runFederation`, `updateCaseStatus`, `handleFeedback`) can trigger toasts directly upon API success or failure, providing automatic coverage across any trigger in the app.
     3. Individual UI buttons can still invoke `toast.success(...)` or `toast.info(...)` for immediate localized interactions.

3. **ESLint `--max-warnings 0` Compliance**:
   - In React 18 with `plugin:react-hooks/recommended`, timer management inside toast state can easily trigger warning errors if `setTimeout` or refs are handled incorrectly.
   - Specifically, copying refs to local variables before cleanup returns:
     ```javascript
     useEffect(() => {
       const timers = timersRef.current;
       return () => {
         timers.forEach((t) => clearTimeout(t));
         timers.clear();
       };
     }, []);
     ```
     guarantees that `npm run lint` passes with 0 warnings.
   - Eliminating all legacy browser `alert(...)` calls in `StatusTransitionActions.jsx:37` and `CaseDetailModal.jsx:19` eliminates intrusive UI blocking and modernizes the codebase.

---

## 3. Caveats

1. **Honeypot Red Alert Traps**:
   - `OverviewPage.jsx` currently has an inline `honeypotAlerts` banner at `fixed top-20 right-6 z-50`.
   - The global toast container should be positioned at `fixed bottom-6 right-6 z-50` (or `top-20 right-6`) so it does not collide with the Honeypot banner, OR the Honeypot banner can be routed through `toast.critical(...)` or `toast.honeypot(...)`.
   - Placing standard toasts at **bottom-right** (`fixed bottom-6 right-6 z-50`) ensures clean visual separation between operational action feedback and top-level intrusion detection alerts.
2. **Read-Only Scope**:
   - This investigation is strictly read-only. No code modifications to `frontend/` have been made yet; the full architectural specification and proposed file changes are provided below for the implementer agent.

---

## 4. Conclusion & Concrete Implementation Architecture

### 4.1 Recommended Toast Architecture Specification

#### Component Structure:
- Create `frontend/src/context/ToastContext.jsx`:
  - Context: `ToastContext`
  - Hook: `useToast()`
  - Provider: `<ToastProvider>`
  - Container & Item: `<ToastContainer />` and `<ToastItem />` using `framer-motion`'s `AnimatePresence` and `<motion.div>`

#### API Surface of `useToast()`:
```javascript
const toast = useToast();

toast.success(title, message, duration = 4000);
toast.error(title, message, duration = 5000);
toast.info(title, message, duration = 3500);
toast.warning(title, message, duration = 4500);
toast.dismiss(id);
```

#### Visual Styling Specs (Tailwind Classes):
- **Container**: `fixed bottom-6 right-6 z-50 flex flex-col-reverse gap-2.5 max-w-md w-full px-4 sm:px-0 pointer-events-none`
- **Toast Card**:
  - `pointer-events-auto rounded-lg shadow-2xl border p-3.5 backdrop-blur-md font-sans text-xs relative overflow-hidden flex items-start gap-3`
  - **Success**: `bg-[#0b1f3a]/95 text-white border-emerald-500/80 shadow-glow-green/30`
    - Icon badge: `bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 px-1.5 py-0.5 rounded font-mono font-bold text-xs` (`✓`)
    - Progress bar: `bg-emerald-500`
  - **Error**: `bg-[#1a0f14]/95 text-white border-rose-500/80 shadow-glow-red/30`
    - Icon badge: `bg-rose-500/20 text-rose-400 border border-rose-500/40 px-1.5 py-0.5 rounded font-mono font-bold text-xs` (`✕`)
    - Progress bar: `bg-rose-500`
  - **Info**: `bg-[#0b1f3a]/95 text-white border-indigo-400/80`
    - Icon badge: `bg-indigo-500/20 text-indigo-300 border border-indigo-400/40 px-1.5 py-0.5 rounded font-mono font-bold text-xs` (`ℹ`)
    - Progress bar: `bg-indigo-400`
  - **Warning**: `bg-[#1a170b]/95 text-white border-amber-500/80`
    - Icon badge: `bg-amber-500/20 text-amber-300 border border-amber-500/40 px-1.5 py-0.5 rounded font-mono font-bold text-xs` (`⚠`)
    - Progress bar: `bg-amber-400`
- **Dismiss Bar**: Smooth CSS animation or Framer Motion width countdown (`100% -> 0%`).

### 4.2 Concrete Implementation Files & Snippets

#### 1. New File: `frontend/src/context/ToastContext.jsx`
```jsx
import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timersRef = useRef(new Map());

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    if (timersRef.current.has(id)) {
      clearTimeout(timersRef.current.get(id));
      timersRef.current.delete(id);
    }
  }, []);

  const addToast = useCallback(
    ({ type = "info", title, message = "", duration = 4000 }) => {
      const id = `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
      const newToast = { id, type, title, message, duration, createdAt: Date.now() };

      setToasts((prev) => [newToast, ...prev.slice(0, 4)]); // Keep max 5

      if (duration > 0) {
        const timer = setTimeout(() => {
          removeToast(id);
        }, duration);
        timersRef.current.set(id, timer);
      }
      return id;
    },
    [removeToast]
  );

  const success = useCallback((title, msg, dur) => addToast({ type: "success", title, message: msg, duration: dur ?? 4000 }), [addToast]);
  const error = useCallback((title, msg, dur) => addToast({ type: "error", title, message: msg, duration: dur ?? 5000 }), [addToast]);
  const info = useCallback((title, msg, dur) => addToast({ type: "info", title, message: msg, duration: dur ?? 3500 }), [addToast]);
  const warning = useCallback((title, msg, dur) => addToast({ type: "warning", title, message: msg, duration: dur ?? 4500 }), [addToast]);

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      timers.forEach((t) => clearTimeout(t));
      timers.clear();
    };
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast, success, error, info, warning }}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

function ToastContainer({ toasts, onDismiss }) {
  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col-reverse gap-2.5 max-w-md w-full px-4 sm:px-0 pointer-events-none">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
        ))}
      </AnimatePresence>
    </div>
  );
}

function ToastItem({ toast, onDismiss }) {
  const { id, type, title, message, duration } = toast;

  const typeConfig = {
    success: {
      border: "border-emerald-500/80 bg-[#0b1f3a]/95 text-white",
      badge: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
      bar: "bg-emerald-400",
      icon: "✓",
    },
    error: {
      border: "border-rose-500/80 bg-[#1a0f14]/95 text-white",
      badge: "bg-rose-500/20 text-rose-400 border-rose-500/40",
      bar: "bg-rose-400",
      icon: "✕",
    },
    warning: {
      border: "border-amber-500/80 bg-[#1a170b]/95 text-white",
      badge: "bg-amber-500/20 text-amber-300 border-amber-500/40",
      bar: "bg-amber-400",
      icon: "⚠",
    },
    info: {
      border: "border-indigo-400/80 bg-[#0b1f3a]/95 text-white",
      badge: "bg-indigo-500/20 text-indigo-300 border-indigo-400/40",
      bar: "bg-indigo-400",
      icon: "ℹ",
    },
  }[type] || {
    border: "border-hairline bg-ink-900/95 text-white",
    badge: "bg-white/10 text-white",
    bar: "bg-saffron",
    icon: "•",
  };

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 10, scale: 0.9, transition: { duration: 0.15 } }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`pointer-events-auto rounded-lg shadow-2xl border p-3.5 backdrop-blur-md relative overflow-hidden ${typeConfig.border}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className={`px-1.5 py-0.5 rounded font-mono font-bold text-xs border shrink-0 mt-0.5 ${typeConfig.badge}`}>
            {typeConfig.icon}
          </span>
          <div>
            <div className="font-serif font-bold text-sm leading-tight text-white">{title}</div>
            {message && <div className="text-xs text-slate-300 mt-1 leading-snug">{message}</div>}
          </div>
        </div>
        <button
          onClick={() => onDismiss(id)}
          className="text-white/60 hover:text-white text-xs font-mono font-bold px-1.5 py-0.5 rounded hover:bg-white/10 transition-colors"
          title="Dismiss notification"
        >
          ✕
        </button>
      </div>

      {duration > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-white/10">
          <motion.div
            initial={{ width: "100%" }}
            animate={{ width: "0%" }}
            transition={{ duration: duration / 1000, ease: "linear" }}
            className={`h-full ${typeConfig.bar}`}
          />
        </div>
      )}
    </motion.div>
  );
}
```

#### 2. Root Mount in `frontend/src/App.jsx`
Wrap `<ToastProvider>` around `<AppStateProvider>`:
```jsx
import { ToastProvider } from "./context/ToastContext";
import { AppStateProvider } from "./context/AppStateContext";
// ...
export default function App() {
  return (
    <ToastProvider>
      <AppStateProvider>
        <BrowserRouter>
          ...
```

#### 3. Automatic Wiring in `frontend/src/context/AppStateContext.jsx`
Inside `AppStateProvider`, import and call `useToast()`:
```javascript
const toast = useToast();

// in startAutoFeed:
const res = await api.startAutoFeed({ rate_tps: tps, fraud_ratio: fraudRatio, bursty });
toast.success("Live Feed Started", `Streaming autonomous transactions at ${tps} tx/s`);

// in stopAutoFeed:
const res = await api.stopAutoFeed();
toast.info("Live Feed Stopped", "Autonomous transaction rail paused");

// in runSimulation:
const result = await api.simulate(count, fraudRatio);
toast.success("Batch Simulation Complete", `Scored ${result.processed || count} txns (${Math.round(fraudRatio * 100)}% fraud)`);

// in runFederation:
await api.runFederation();
toast.info("Federation Consensus", "Mesh sync complete across participating PSP nodes");

// in updateCaseStatus:
toast.success("Case Status Updated", `Case ${caseId} transitioned to ${newStatus}`);

// in handleFeedback:
toast.info("Analyst Feedback Saved", confirmed ? "Confirmed fraud pattern" : "Dismissed as legitimate");
```

#### 4. UI Button Integration Snippets
- In `components/ControlBar.jsx`:
  Buttons for "Start Live Feed", "Run batch simulation", and "Federation round" are already wired to `AppStateContext` functions, so they immediately benefit from the toasts above. Additional local toast overrides can be added if needed.
- In `components/investigations/StatusTransitionActions.jsx`:
  Replace `alert(\`Error updating case: \${err.message}\`)` with `toast.error("Case Update Failed", err.message)`.
- In `components/investigations/CaseDetailModal.jsx`:
  Replace `alert(\`Copied Case ID: \${caseData.case_id}\`)` with `toast.info("Case ID Copied", \`Copied \${caseData.case_id} to clipboard\`)`.
- In `components/CaseDrawer.jsx`:
  Add `toast.info("Case ID Copied", ...)` in `handleCopyCaseId` and `toast.success("SAR PDF Generated", ...)` in `handleExportSar`.
- In `pages/SettingsPage.jsx`:
  Add `toast.success("Sensitivity Updated", ...)` and replace temporary inline state strings.

---

## 5. Verification Method

To independently verify this investigation and validate downstream implementation:

1. **Frontend ESLint Validation**:
   ```bash
   cd /home/avi/Downloads/Sampati_v2/frontend && npm run lint
   ```
   *Expected*: Exit code 0, 0 errors, 0 warnings under `--max-warnings 0`.

2. **Frontend Production Build**:
   ```bash
   cd /home/avi/Downloads/Sampati_v2/frontend && npm run build
   ```
   *Expected*: Vite builds `dist/` cleanly without JSX or module syntax errors.

3. **Backend Regression Test Suite**:
   ```bash
   ./.venv/bin/pytest tests/ -v
   ```
   *Expected*: Existing test suite passes with 0 failures.

4. **Visual & Interactive Acceptance Criteria**:
   - Navigate to `/overview` in browser:
     - Click **"⚡ Start Live Feed"**: Bottom-right green toast pops up: *"Live Feed Started — Streaming autonomous transactions at 10 tx/s"*.
     - Click **"Stop Live Feed"**: Blue toast pops up: *"Live Feed Stopped"*.
     - Click **"▶ Run batch simulation"**: Green toast pops up: *"Batch Simulation Complete — Processed 300 txns (15% fraud ratio)"*.
     - Click **"⟲ Federation round"**: Indigo toast pops up: *"Federation Consensus — Mesh sync complete across participating PSP nodes"*.
   - Open a Case Dossier in `/investigations`:
     - Click **"Copy" Case ID**: Toast pops up confirming clipboard copy.
     - Click **"Export SAR"**: Toast pops up confirming PDF dossier download.
     - Click **"Escalate to DPIP"**: Amber warning toast pops up confirming broadcast to RBI DPIP mesh. No browser `alert()` popups appear.

5. **Invalidation Conditions**:
   - If any `npm run lint` warning or error occurs during implementation.
   - If clicking an action button causes no toast to mount in the DOM.
   - If toasts overlap or block critical controls unexpectedly.
