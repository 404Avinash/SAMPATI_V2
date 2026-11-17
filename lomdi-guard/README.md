# Fox Guard 🛡️

### An on-device AI firewall that stops UPI fraud *before* the payment happens.

**Most fraud detection watches the transaction. Fox Guard watches the context that leads to it.**

---

## 📖 Overview
**Fox Guard** is a real-time, on-device fraud prevention system designed to protect users from UPI scams, vishing (voice phishing), and malicious applications. By continuously monitoring device state, communication channels, and app behaviors, it calculates a live **Severity Coefficient** and forcefully intercepts the user before they execute a dangerous financial transaction.

---

## 🎯 The Problem

Most UPI fraud isn't a technical hack — it's a **conversation**. A caller impersonates a bank official, manufactures urgency, and walks the victim through authorizing their own transaction. From the bank's side, the payment looks completely legitimate: the real account holder approved it.

**Fox Guard reads the intent behind the payment — not just the payment itself.**

### 🛑 Intercepted Scam Patterns

| Pattern | Detection Signal | Example |
|---|---|---|
| ⏰ **Urgency + threats** | NLP-based Urgency Detection | *"Your account will be blocked today."* |
| 🔑 **OTP / PIN requests** | Clipboard & Screen Accessibility Guard | *"Share the OTP to confirm your identity."* |
| 📄 **Fake KYC claims** | SMS Template Analysis | *"Your KYC has expired, update it now."* |
| 💸 **Refund manipulation** | Financial Keyword Filtering | *"We're refunding ₹5,000, just confirm the UPI PIN."* |
| 📈 **Investment scams** | "Reward" & "Won" Signal Mapping | *"Guaranteed 30% returns, act before market close."* |
| 🖥️ **Remote-access** | App Scanner & Display Casting Monitor | *"Install AnyDesk so I can help you."* |

---

## 🚀 How It Works: Context Fusion & ML Engine

Fox Guard fuses multiple signal sources into a single, explainable risk score:

    Communication Context  →  SMS Analysis      →  Interaction Risk
    System Environment     →  Remote App/Root Scan   →  Environment Risk
    User Behavior          →  Clipboard/App Launch   →  Intent Risk
                                        │
                                        ▼
                              Context Fusion Engine
                                        │
                                        ▼
                              Final Risk Score (0–100)
                                        │
                                        ▼
                           Explainable User Intervention

### Risk Tiers

| Score | Level | Response |
|:---:|:---:|---|
| 0–30 | **LOW** | No action needed |
| 31–60 |  **MEDIUM** | Caution flagged in Dashboard |
| 61–80 |  **HIGH** | Active warning banner shown |
| 81–100 |  **CRITICAL** | **Forceful Intervention Triggered** |

### The ML Intent Classifier
To power the SMS Analysis layer, Fox Guard utilizes a FastText supervised machine learning model that reads every incoming SMS and classifies it into one of five intent categories (`fraud`, `urgent`, `otp`, `promo`, `safe`).

1. **Tokenization:** The text is lowercased and split, preserving Devanagari/Unicode characters.
2. **Bag-of-Words Embedding:** Tokens matching our 587-word vocabulary are mapped to a 32-dimensional float vector matrix.
3. **Scoring:** Text representations are dot-producted with label vectors, passed through softmax normalization, and mapped to a numeric risk contribution (e.g., `fraud` adds 20-60 points to the Severity Coefficient).
4. **Offline & Native:** The model is exported to a highly optimized `~80 KB` custom binary format (`.foxg`) read by a pure Kotlin parser. **No NDK or JNI required.**

---

## ✨ Key Features

*   **Live Risk Engine & Severity Coefficient:** Correlates real-time data across calls, SMS, and clipboard contents. If you open a UPI app (GPay, PhonePe, Paytm) while under high threat, Fox Guard blocks the transaction with a persistent alert.
*   **Call & Vishing Interceptor:** Monitors standard PSTN and VoIP calls (WhatsApp, Telegram). Identifies when you are on a call with an unsaved contact while performing financial actions.
*   **SMS Phishing & Link Classifier:** Hybrid Rule-Based + Edge AI engine analyzes messages for urgency, shortened URLs, and fraudulent UPI deep-links.
*   **Clipboard Guard:** Tracks sensitive data (UPI IDs, URLs) with strict TLD filtering to ignore standard emails while capturing high-risk handles copied during suspicious calls.
*   **Malware & App Exploit Auditor:** Actively scans for Banking Trojans (Accessibility misuse), Tapjacking (Overlay permissions), and Keyloggers (Untrusted keyboards).
*   **Screen Cast Monitor:** Detects active, hidden screen-sharing sessions and hardware-level casts used by remote scammers.

---

## 🔐 Privacy First

| Fox Guard does **not**: | Why it's secure: |
|---|---|
| Send your data to a server | All analysis and ML inference happens **locally** on-device. |
| Store raw voice recordings | Speech patterns are processed in real-time. |
| Collect banking credentials | We monitor the *context*, not your PINs or passwords. |
| Access real bank accounts | We work at the OS level to protect your interaction with existing apps. |

---

## 🛠️ Developer Guide & ML Training

### Project Directory Structure
*   **`app/src/main/assets/`** — Contains the trained `intent_model.foxg` binary.
*   **`app/src/main/java/.../ml/`** — The pure-Kotlin `.foxg` reader and classification logic.
*   **`app/src/main/java/.../domain/`** — Hybrid rule engine (`SmsAnalyzer`, `ThreatEvaluator`).
*   **`app/src/main/java/.../ui/`** — Jetpack Compose screens for the Dashboard, SMS Tracker, and Overlay.
*   **`scripts/`** — Python training pipeline (`generate_dataset.py`, `train_and_export.py`).

### Prerequisites
*   **Python 3.11** (Strict requirement to prevent FastText C++ backend NaN errors).
*   **uv** package manager (`pip install uv`).
*   **Android Studio** with JDK 17+ and Gradle 9.3+.

### Training the ML Model
We use a synthetic, multi-lingual dataset (English, Hindi, Hinglish) for training.
1. Create the environment: `uv venv scripts/venv311 --python 3.11`
2. Install dependencies: `uv pip install --python scripts/venv311/bin/python fasttext-wheel numpy`
3. Generate dataset: `scripts/venv311/bin/python scripts/generate_dataset.py`
4. Train & Export: `scripts/venv311/bin/python scripts/train_and_export.py`
   *(This auto-copies the `.foxg` model directly to your Android `assets/` folder).*

### Building the App
Run the following from the project root:
*   Debug: `./gradlew assembleDebug`
*   Release: `./gradlew assembleRelease`

---

## ⚙️ How to Install & Sideload

Because Fox Guard requires advanced system-level permissions to protect you, it must be sideloaded.

### Step 1: Pause Google Play Protect
1. Open **Google Play Store** > Tap **Profile Icon** > **Play Protect**.
2. Tap **Settings (Gear)** > Toggle off **Scan apps with Play Protect**.

### Step 2: Install the APK
1. Download `app-release.apk`.
2. Tap to install and allow "Install from unknown sources" if prompted.

### Step 3: Allow Restricted Settings (Android 13+)
1. Go to **Settings** > **Accessibility**.
2. Find **Fox Guard**. If it says "Restricted setting", dismiss the dialog.
3. Go to **Settings** > **Apps** > **Fox Guard**.
4. Tap **three-dot menu (⋮)** in top right > **Allow restricted settings**.
5. Return to **Accessibility** and toggle **Fox Guard** ON.

---

## 🐛 Troubleshooting

*   **FastText NaN Error:** Ensure you are using Python 3.11. Python 3.13+ breaks the FastText C++ gradient computation.
*   **Model Not Loading:** If the app logs a placeholder warning, ensure `intent_model.foxg` exists in `app/src/main/assets/`. Re-run the python training script if it is missing.
*   **Simulation Overlay Not Appearing:** Ensure the Accessibility Service is enabled. Some Android skins (MIUI/ColorOS) require an additional manual "Draw over other apps" permission in settings.

---

**Built to protect the moment before the payment — not just the payment itself.**