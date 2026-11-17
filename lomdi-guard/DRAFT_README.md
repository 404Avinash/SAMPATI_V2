
# 🛡️ UPI Intent Guard

### An on-device AI firewall that stops UPI fraud *before* the payment happens.

**Most fraud detection watches the transaction. This watches the conversation that leads to it.**

[![Track](https://img.shields.io/badge/Hackathon%20Track-FinTech%20%26%20Commerce-6366F1?style=for-the-badge)](#)
[![Status](https://img.shields.io/badge/Status-MVP%20Prototype-orange?style=for-the-badge)](#)
[![License](https://img.shields.io/badge/License-See%20SECURITY.md-blue?style=for-the-badge)](./SECURITY.md)

[![React](https://img.shields.io/badge/React-20232A?style=flat-square&logo=react&logoColor=61DAFB)](#)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=flat-square&logo=typescript&logoColor=white)](#)
[![Vite](https://img.shields.io/badge/Vite-646CFF?style=flat-square&logo=vite&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)](#)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-38B2AC?style=flat-square&logo=tailwind-css&logoColor=white)](#)

[Demo Flow](#-demo-flow) · [How It Works](#-how-it-works) · [Architecture](#️-architecture) · [Setup](#-running-the-project) · [Privacy](#-privacy)

</div>

---

## 🎯 The Problem

Most UPI fraud isn't a hack — it's a **conversation**. A caller impersonates a bank official, manufactures urgency, and walks the victim through authorizing their own transaction. From the bank's side, the payment looks completely legitimate: the real account holder approved it.

Common patterns:

| Pattern | Example |
|---|---|
| 🏦 Bank impersonation | *"I'm calling from your bank's verification team."* |
| ⏰ Urgency + threats | *"Your account will be blocked today."* |
| 🔑 OTP / PIN requests | *"Share the OTP to confirm your identity."* |
| 📄 Fake KYC claims | *"Your KYC has expired, update it now."* |
| 💸 Refund manipulation | *"We're refunding ₹5,000, just confirm the UPI PIN."* |
| 📈 Investment scams | *"Guaranteed 30% returns, act before market close."* |
| 🖥️ Remote-access requests | *"Install this app so I can help you."* |

**UPI Intent Guard reads the intent behind the payment — not just the payment itself.**

---

## 🚀 How It Works

Three signal sources are fused into a single explainable risk score:

```
Conversation Context  →  Scam Signal Detection  →  Conversation Risk
Payment Details       →  Intent Analysis         →  Payment Intent Risk
Recipient Info         →  Recipient Intelligence  →  Recipient Risk
                                    │
                                    ▼
                          Context Fusion Engine
                                    │
                                    ▼
                          Final Risk Score (0–100)
                                    │
                                    ▼
                       Explainable User Intervention
```

### Risk Tiers

| Score | Level | Response |
|:---:|:---:|---|
| 0–30 | **LOW** | No action needed |
| 31–60 |  **MEDIUM** | Caution flagged |
| 61–80 |  **HIGH** | Strong warning shown |
| 81–100 |  **CRITICAL** | Payment intervention triggered |

### Example: Signal → Detection

```
"I'm calling from your bank."             →  Bank impersonation
"Your account will be blocked today."     →  Urgency + Account threat
"Transfer ₹5,000 to verify your account." →  Verification request + Payment request
```

**Output:**

```
🚨 CRITICAL RISK — 90/100

✓ Bank impersonation
✓ Urgency
✓ Account threat
✓ Verification request
✓ Payment request
```

---

## 💳 Payment Intervention

When a risky conversation is followed by a risky payment attempt, Context Fusion kicks in:

```
Conversation Risk       82
Payment Intent Risk     90
Recipient Risk          70
──────────────────────────
Final Risk               94  →  🚨 CRITICAL
```

The user is shown a clear intervention screen — **"This payment may be part of a scam"** — with two explicit choices: **STOP PAYMENT** or **CONTINUE ANYWAY**. No real UPI transaction is ever performed by the prototype.

---

## 🌐 Multilingual by Design

Scam-pattern detection works across **English, Hindi, Telugu, and Hinglish** — because scam warnings only help if people can actually understand them in the language they think in.

---

## 🎙️ Controlled Live Demo

Two demo modes are built in for reliable, repeatable presentation:

- **Simulated Conversation** — six scripted scenarios (bank impersonation, OTP scam, KYC scam, refund scam, investment scam, and a safe control conversation) play out progressively for consistent hackathon demos.
- **Microphone Demo** — an optional, controlled browser speech-recognition mode. This is *not* cellular call interception, and raw voice recordings are never stored.

---

## 🔐 Privacy First

| The prototype does **not**: |
|---|
|  Perform real UPI transactions |
|  Collect banking credentials |
|  Store raw voice recordings |
|  Require real OTPs |
|  Access real bank accounts |

Core detection is designed to run **locally**, without requiring conversation audio to leave the device. Full details in [`SECURITY.md`](./SECURITY.md).

---

##  Architecture

```
                          UPI INTENT GUARD
                                 │
                 ┌───────────────┴───────────────┐
                 │                                │
           Conversation                        Payment
                 │                                │
                 ▼                                ▼
          Signal Detection                Intent Analysis
                 │                                │
                 └───────────────┬────────────────┘
                                 ▼
                          Context Fusion
                                 │
                                 ▼
                            Risk Engine
                                 │
                                 ▼
                       Explainable Warning
                                 │
                                 ▼
                            Intervention
```

---

##  Tech Stack

<table>
<tr>
<td valign="top" width="25%">

**Frontend**
- React
- TypeScript
- Vite
- Tailwind CSS
- Framer Motion
- Lucide React

</td>
<td valign="top" width="25%">

**Backend**
- Python
- FastAPI
- Pydantic

</td>
<td valign="top" width="25%">

**AI / Detection**
- Scam-signal detection
- Intent classification
- Risk scoring
- Explainable output
- Speech-to-text abstraction

</td>
<td valign="top" width="25%">

**Infra**
- REST API
- WebSocket (progressive analysis)
- Local browser storage

</td>
</tr>
</table>

---

##  Project Structure

```
UPI-intent-Guard/
│
├── src/
│   ├── components/
│   ├── pages/
│   ├── services/
│   ├── models/
│   ├── data/
│   ├── hooks/
│   └── utils/
│
├── backend/
│   └── app/
│       ├── api/
│       ├── models/
│       ├── services/
│       ├── ai/
│       ├── risk/
│       └── tests/
│
├── docs/
├── SECURITY.md
└── README.md
```

---

## 🚀 Running the Project

### Frontend

```bash
npm install
npm run dev
```

```bash
npm test        # run tests
npm run build   # production build
```

### Backend (optional)

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
python -m pytest app/tests/ -v   # run backend tests
```

---

## 🧪 Demo Flow

```
START DEMO
     │
     ▼
Simulated Bank Call
     │
     ▼
"Your KYC has expired."          →  Risk ↑
     │
     ▼
"Your account will be blocked."  →  Risk ↑
     │
     ▼
"Transfer ₹5,000 to verify."     →  🚨 CRITICAL RISK
     │
     ▼
Payment Simulator → Context Fusion → 94/100
     │
     ▼
STOP PAYMENT
     │
     ▼
🛡️ ₹5,000 PROTECTED
```

All demonstrations run on synthetic data. No real money ever moves.

---

## 🔮 Roadmap

- [ ] Android implementation with deeper device-level integration
- [ ] Optimized on-device multilingual speech models
- [ ] Improved scam-intent classification
- [ ] Stronger recipient intelligence
- [ ] Accessibility features for elderly users
- [ ] Integration with legitimate payment apps (where platform policy permits)

---

## ⚠️ Disclaimer

UPI Intent Guard is a **hackathon prototype** for demonstrating proactive, conversation-aware scam detection. Risk scores are experimental and should not be treated as a guarantee against fraud. The current web MVP does not intercept cellular calls or perform real financial transactions.

<div align="center">

**Built to protect the moment before the payment — not just the payment itself.**
