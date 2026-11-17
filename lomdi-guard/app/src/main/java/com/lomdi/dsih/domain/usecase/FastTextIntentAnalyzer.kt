package com.lomdi.dsih.domain.usecase

import android.content.Context
import com.lomdi.dsih.ml.FoxGuardModel
import com.lomdi.dsih.ml.IntentResult
import com.lomdi.dsih.ml.SmsIntent
import com.lomdi.dsih.ml.toRiskScore
import com.lomdi.dsih.ml.toSmsIntent

/**
 * High-level wrapper around [FoxGuardModel] for SMS intent analysis.
 *
 * Loads the .foxg model lazily once on first use and caches it in memory.
 * Falls back gracefully to heuristics if the model file is a placeholder.
 */
object FastTextIntentAnalyzer {

    @Volatile
    private var model: FoxGuardModel? = null
    private var modelLoadAttempted = false

    /**
     * Must be called once — e.g. from Application.onCreate() or MainActivity.
     * Safe to call multiple times; loads only once.
     */
    fun init(context: Context) {
        if (modelLoadAttempted) return
        modelLoadAttempted = true
        model = FoxGuardModel.load(context.assets)
        if (model != null) {
            android.util.Log.i("FastTextIntentAnalyzer", "✅ FoxGuard model loaded from assets")
        } else {
            android.util.Log.w("FastTextIntentAnalyzer",
                "⚠️ Model placeholder detected. Run scripts/train_and_export.py to generate the real model.")
        }
    }

    /**
     * Analyze [text] and return an [IntentResult].
     * If the model is not loaded, falls back to a lightweight keyword heuristic.
     */
    fun analyze(text: String): IntentResult {
        val m = model
        return if (m != null) {
            runModel(m, text)
        } else {
            runHeuristicFallback(text)
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Real model path
    // ─────────────────────────────────────────────────────────────────────────

    private fun runModel(model: FoxGuardModel, text: String): IntentResult {
        val (label, confidence) = model.predict(text)
        val intent    = label.toSmsIntent()
        val riskScore = intent.toRiskScore(confidence)
        val pct       = (confidence * 100).toInt()

        val explanation = when (intent) {
            SmsIntent.FRAUD   -> "FastText: Phishing/fraud intent detected ($pct% confidence)"
            SmsIntent.URGENT  -> "FastText: Urgency manipulation pattern detected ($pct% confidence)"
            SmsIntent.OTP     -> "FastText: Legitimate OTP message identified ($pct% confidence)"
            SmsIntent.PROMO   -> "FastText: Promotional message ($pct% confidence)"
            SmsIntent.SAFE    -> "FastText: Message appears safe ($pct% confidence)"
            SmsIntent.UNKNOWN -> "FastText: Intent unclear ($pct% confidence)"
        }

        return IntentResult(
            label       = label,
            confidence  = confidence,
            intent      = intent,
            riskScore   = riskScore,
            explanation = explanation,
        )
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Keyword fallback (used until real .foxg model is in assets)
    // ─────────────────────────────────────────────────────────────────────────

    private val FRAUD_KEYWORDS = setOf(
        // English
        "kyc", "verify", "blocked", "suspended", "click", "link", "claim",
        "won", "lottery", "prize", "refund", "income", "tax", "aadhaar",
        // Hindi / Hinglish
        "band", "karo", "click", "jaldi", "turant", "inam", "verify"
    )
    private val URGENT_KEYWORDS = setOf(
        "urgent", "immediate", "immediately", "final", "notice", "warning",
        "cibil", "emi", "overdue", "disconnect", "tatkal"
    )
    private val OTP_KEYWORDS = setOf("otp", "one time", "one-time", "passcode", "pin")

    private fun runHeuristicFallback(text: String): IntentResult {
        val lower = text.lowercase()
        val words = lower.split(Regex("\\s+")).toSet()

        val fraudHits  = words.count { it in FRAUD_KEYWORDS }
        val urgentHits = words.count { it in URGENT_KEYWORDS }
        val otpHits    = words.count { it in OTP_KEYWORDS }

        val (intent, confidence) = when {
            otpHits > 0                -> SmsIntent.OTP    to 0.85f
            fraudHits >= 2             -> SmsIntent.FRAUD  to 0.70f
            fraudHits == 1             -> SmsIntent.URGENT to 0.55f
            urgentHits > 0             -> SmsIntent.URGENT to 0.60f
            else                       -> SmsIntent.SAFE   to 0.75f
        }

        val label     = "__label__${intent.name.lowercase()}"
        val riskScore = intent.toRiskScore(confidence)

        return IntentResult(
            label       = label,
            confidence  = confidence,
            intent      = intent,
            riskScore   = riskScore,
            explanation = "Heuristic fallback (model not loaded): ${intent.displayName}",
        )
    }
}
