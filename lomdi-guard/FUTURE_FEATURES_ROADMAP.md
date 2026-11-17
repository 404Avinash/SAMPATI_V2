# 🔮 Fox Guard: Future Features & Implementation Roadmap

This document outlines the features mentioned in the conceptual vision (`DRAFT_README.md`) that are either partially implemented or currently missing from the **Fox Guard** Android prototype. It also provides technical approaches for each.

---

## 🚧 Half-Baked Features (Partially Implemented)

### 1. Edge AI NLP (SMS Intent Analysis)
*   **Current State:** Implemented as a **Semantic Heuristic Engine** in `SmsAnalyzer.kt`. It uses keyword-based scoring to simulate AI behavior.
*   **Missing:** Real-time inference using a localized Neural Network.
*   **Implementation Approaches:**
    *   **TFLite Integration:** Port a BERT-mini or MobileBERT model to TensorFlow Lite and bundle it with the APK for on-device inference.
    *   **MediaPipe NLP:** Use Google's MediaPipe Tasks API for text classification, which provides a higher-level abstraction over TFLite.
    *   **ML Kit:** Utilize Google's ML Kit "Smart Reply" or "Entity Extraction" to identify sensitive financial intents.

---

## ❌ Leftover Features (Missing from Prototype)

### 1. Multilingual & Dialect Support (Hinglish/Hindi/Telugu)
*   **Status:** **Not Implemented.** Current detection is focused on English keywords.
*   **Why it's needed:** Most Indian scams happen in regional languages or "Hinglish."
*   **Implementation Approaches:**
    *   **Polyglot Embeddings:** Use multilingual models like `mBERT` or `XLM-RoBERTa` that are trained on Indian dialects.
    *   **Regex Expansion:** Expand current keyword lists to include common romanized Hindi/Telugu scam phrases (e.g., "khata block ho gaya", "inaam mila hai").

### 2. Real-Time Vishing Audio Analysis (The "Holy Grail")
*   **Status:** **Not Implemented.** Current logic only detects *if* you are on a call, not *what* is being said.
*   **Challenge:** Modern Android versions strictly block third-party apps from recording cellular call audio (`VOICE_CALL` source).
*   **Implementation Approaches:**
    *   **Accessibility Audio Scraper:** Attempt to read on-screen captions if the user has "Live Caption" enabled.
    *   **Accessibility Node Scraping:** While on a WhatsApp/Telegram call, monitor the UI for duration and caller identifiers (Partially done).
    *   **User-Mediated STT:** Provide a "Quick Scan" floating button that uses the microphone to listen to the *speakerphone* audio for 10 seconds to detect scam intent.

### 3. Recipient Intelligence & Global Blacklists
*   **Status:** **Not Implemented.** Currently, we only check if a number is in the local contact list.
*   **Why it's needed:** Identifying numbers or UPI handles that have been globally reported for fraud.
*   **Implementation Approaches:**
    *   **API Integration:** Connect with crowdsourced databases like Truecaller SDK or a private government fraud registry.
    *   **Local Bloom Filter:** Periodically download a compressed "Scammer Signature" database to the device for offline reputation checks.

### 4. Elderly Safety Mode (UI/UX)
*   **Status:** **Not Implemented.** Current UI is technical and high-fidelity.
*   **Implementation Approaches:**
    *   **Simplified UI Toggle:** A high-contrast, large-font mode with simplified explanations ("This person is lying to you" instead of "Severity Coefficient 90%").
    *   **Guardian Alerts:** Option to automatically send an SMS alert to a trusted family member when a **CRITICAL** threat is intercepted on the senior's phone.

### 5. Intra-App Transaction Monitoring
*   **Status:** **Not Implemented.** We currently intercept the *opening* of GPay/Paytm, but not the specific actions *inside* them.
*   **Implementation Approaches:**
    *   **Accessibility Text Monitoring:** Use `LomdiAccessibilityService` to continuously read the text nodes inside payment apps to detect if the user is entering a PIN or sending a specific high-value amount to a flagged recipient.

---

## 🧠 Technical Evolution: The Fusion Path

To achieve the "Context Fusion" mentioned in the draft, the `RiskManager` should evolve into a **Dynamic Weighted Graph**:
*   Instead of static if-else chains, implement a weight-based scoring system where the duration of a call increases the "Vishing Weight" over time, making a transaction attempt more suspicious the longer the call lasts.
