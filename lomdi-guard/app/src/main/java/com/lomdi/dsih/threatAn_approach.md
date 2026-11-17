# Threat Analysis Approach: Hybrid Rule-Based + Edge AI

Project Fox utilizes a multi-layered detection strategy to identify and mitigate UPI fraud via SMS and Clipboard monitoring. The analysis follows a deterministic decision tree before invoking localized Edge AI models for semantic validation.

## 1. Decision Tree Architecture

The system processes every incoming message through a tiered evaluation pipeline:

### Tier 1: Institutional Verification (Node 1)
*   **Logic:** Checks if the sender's ID matches registered banking/institutional formats (e.g., `< 10 characters`, contains hyphens).
*   **Action:** If verified as a bank header, the system applies strict regex rules to ensure the message matches legitimate banking templates.

### Tier 2: Payload Extraction & Classification (Node 2)
*   **Logic:** Scans for URLs and payment deep-links.
*   **Categorization:** 
    *   **UPI_MONEY_REQUEST:** Direct payment extraction attempts (e.g., `upi://pay?pa=...&am=...`).
    *   **APK_DOWNLOAD_LINK:** Malware sideloading attempts (e.g., `.apk` links).
    *   **SUSPICIOUS_SHORTENER:** Obfuscated destinations (e.g., `bit.ly`, `tinyurl.com`).
    *   **RAW_IP_ADDRESS:** Non-verified domain hosting.
*   **Action:** High-risk classifications automatically escalate the threat score and trigger **Edge AI Review**.

### Tier 3: Intent Analysis (Node 3)
*   **Logic:** Searches for urgency-based keywords (e.g., "Blocked", "KYC", "Immediate", "Unauthorized").
*   **Action:** If high-urgency keywords are detected, the message is routed to the AI engine for semantic context analysis.

---

## 2. Clipboard Sanitization (UPI vs. Email)

To prevent false positives, Fox applies strict TLD-based filtering for clipboard monitoring:
*   **Email Filtering:** Disqualifies strings that match standard email patterns (containing `.com`, `.in`, `.org`, etc., after the `@`).
*   **UPI Verification:** Only captures handles that maintain a clean alphanumeric domain after the `@` (e.g., `user@okaxis`), ensuring only payment-related data triggers risk evaluation.

---

## 3. Hybrid Analysis Engine

Fox combines the speed of local rules with the intelligence of on-device NLP:

1.  **Rule-Based Engine:** Uses high-speed regex and keyword matching to handle standard transactional traffic.
2.  **Edge AI NLP (ML Kit / TFLite):** Triggered for "Uncertain" or "High-Risk Payload" messages to evaluate if the "Urgency" is a scam pattern.
    *   **Privacy First:** All AI processing happens entirely on-device.

---

## 4. Transparency & User Education

Every flagged threat is decomposed into an itemized breakdown with **Dynamic Evidence**:
*   **Sender Risk:** Direct labeling of unverified numbers.
*   **Link Risk:** Detailed classification of the payload (e.g., "Malware Risk").
*   **Evidence Display:** Shows the exact string (UPI/URL) that triggered the alert, empowering users to make informed decisions.
