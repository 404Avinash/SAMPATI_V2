# Fox Guard: Technical Documentation

## 🏗️ System Architecture Overview

Fox Guard is built as a multi-layered security middleware for Android. It operates as a set of background observers that feed data into a central **Context Fusion Engine**, which then manages real-time user interventions.

---

## 🛡️ Core Detection Modules

### 1. Hybrid SMS Analysis Engine
*   **File:** `SmsAnalyzer.kt` & `SmsReceiver.kt`
*   **Logic:** Uses a tiered Decision Tree:
    1.  **Institutional Check:** Verifies sender headers against banking formats.
    2.  **Link Classification:** Categorizes URLs into APK Malware, UPI Money Requests, or Suspicious Shorteners.
    3.  **Enhanced NLP Heuristics:** Uses a semantic scoring engine to detect Fear-based pressure, Social Engineering patterns, and Financial Bait.
*   **What it solves:** Intercepts phishing SMS and fraudulent UPI deep-links before the user clicks.
*   **Status:** **Functional Heuristic.** Uses localized semantic analysis to simulate Edge AI behavior without requiring cloud dependencies.

### 2. Vishing & Call Interceptor
*   **Files:** `CallReceiver.kt` (PSTN) & `LomdiNotificationListener.kt` (VoIP)
*   **Logic:** 
    *   **PSTN:** Monitors `PHONE_STATE` to detect active calls and verifies the number against the user's contacts via `ContactValidator.kt`.
    *   **VoIP:** Monitors incoming notifications from WhatsApp/Telegram to identify active voice sessions with unknown callers.
*   **What it solves:** Detects "Social Engineering" sessions where a scammer stays on call while the victim performs a transaction.

### 3. Clipboard Guard (Sensory Data)
*   **File:** `ClipboardGuard.kt`
*   **Logic:** Monitors the system clipboard for strings matching UPI ID or URL patterns. Includes **TLD filtering** to ignore standard email addresses while flagging valid payment handles.
*   **What it solves:** Prevents "Clipboard Swapping" where malware replaces a copied UPI ID with a scammer's ID.

### 4. Network Security (Secure Tunnel)
*   **File:** `NetworkSecurityScanner.kt`
*   **Logic:** Utilizes `ConnectivityManager` to audit the active network transport. Specifically detects active **VPN tunnels** (indicating a secure/private route) vs. standard cellular/WiFi.
*   **What it solves:** Provides visual confirmation of a secured connection and flags when the user is unprotected.

### 5. Data Protection (Vault Status)
*   **File:** `VaultScanner.kt`
*   **Logic:** Queries the system `DevicePolicyManager` to verify the state of **Full Disk Encryption (FDE)** or **File-Based Encryption (FBE)**.
*   **What it solves:** Ensures the device's hardware-level security (Vault) is active and the data partition is secure.

### 6. Spyware & Permission Monitor
*   **File:** `PermissionAuditor.kt`
*   **Logic:** Scans all third-party applications for dangerous "Spyware" permission combinations (e.g., simultaneous access to **SMS** and **Internet**).
*   **What it solves:** Identifies apps that are functionally capable of exfiltrating sensitive banking messages to remote servers.

### 7. Environment & Integrity Scanners
*   **Files:** `DeviceIntegrityScanner.kt`, `RemoteAppScanner.kt`, `ActiveDisplayScanner.kt`
*   **Logic:**
    *   **Integrity:** Checks for `su` binaries and `test-keys` (Root detection).
    *   **Remote Apps:** Scans for known remote desktop packages (AnyDesk, TeamViewer).
    *   **Display Casting:** Monitors `DisplayManager` for virtual/secondary displays indicating an active screen cast.
*   **What it solves:** Protects against remote-access fraud (Vishing + Screen Sharing) and OS-level compromise.

### 8. App Exploit Auditors
*   **Files:** `AccessibilityAuditor.kt`, `OverlayAuditor.kt`, `KeyboardAuditor.kt`
*   **Logic:** Audits third-party (non-system) apps that hold dangerous permissions like `AccessibilityService` (Trojan risk), `SYSTEM_ALERT_WINDOW` (Tapjacking risk), or untrusted IMEs (Keylogger risk).
*   **What it solves:** Identifies stealthy malicious apps that have already bypassed standard antivirus.

---

## 🧠 The "Brain": Context Fusion Engine

*   **File:** `RiskManager.kt`
*   **Logic:** This is the core aggregator. It does not look at signals in isolation. It calculates a **Severity Coefficient** based on the *confluence* of factors:
    *   `Unsaved Call` + `Remote App` = **CRITICAL (100%)**
    *   `Unsaved Call` + `Sensitive Clipboard Data` = **HIGH (70%)**
    *   `Root Access` = **INSTANT CRITICAL**
*   **Integration:** It pulls live states from `CallStateStore`, `ClipboardStore`, and `AppSecurityStore`.

---

## 🚨 Intervention Mechanism

*   **Files:** `LomdiAccessibilityService.kt` & `ThreatNotificationManager.kt`
*   **Logic:**
    1.  The `AccessibilityService` monitors for the launch of target payment apps (GPay, PhonePe, Paytm).
    2.  If an app is launched AND `RiskManager.isSystemAtCriticalRisk()` is true, the service triggers a **Heads-Up Notification**.
    3.  The notification uses **`CallStyle` APIs** to ensure it is persistent, full-screen, and colored red, effectively "blocking" the user's flow without standard overlay restrictions.
*   **What it solves:** Forcefully stops a transaction attempt while the user is under active duress from a scammer.

---

## 🚧 Roadmap & Polish

1.  **Production Edge AI:** The current semantic heuristic in `SmsAnalyzer.kt` provides high accuracy for demos, but can be further scaled by integrating a TFLite BERT-mini model for multilingual intent.

---

## 🔗 Integration Flow

1.  **Receivers/Services** detect a state change (New SMS, New Call, Clipboard copy).
2.  **Stores** (Singletons) update their internal `mutableStateOf` variables.
3.  **RiskManager** evaluates the combined state.
4.  **AccessibilityService** detects a Payment App opening.
5.  **Intervention** triggered if Risk > Threshold.
6.  **UI** (Dashboard) recomposes automatically due to Jetpack Compose observing the Stores.
