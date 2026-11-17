package com.lomdi.dsih.ml

/**
 * Result returned by the FoxGuard FastText intent classifier.
 *
 * @param label      Raw FastText label string, e.g. "__label__fraud"
 * @param confidence Softmax probability in [0.0, 1.0]
 * @param intent     Cleaned intent enum for easy branching
 */
data class IntentResult(
    val label: String,
    val confidence: Float,
    val intent: SmsIntent,
    val riskScore: Int,      // 0–100 score contribution
    val explanation: String, // Human-readable reason
)

/**
 * Possible SMS intents detected by the FastText model.
 */
enum class SmsIntent(val displayName: String) {
    FRAUD("Fraud / Phishing"),
    URGENT("Urgency Manipulation"),
    OTP("Legitimate OTP"),
    PROMO("Promotional"),
    SAFE("Benign / Safe"),
    UNKNOWN("Unknown"),
}

/**
 * Maps a raw FastText label string to an [SmsIntent].
 */
fun String.toSmsIntent(): SmsIntent = when (this) {
    "__label__fraud"  -> SmsIntent.FRAUD
    "__label__urgent" -> SmsIntent.URGENT
    "__label__otp"    -> SmsIntent.OTP
    "__label__promo"  -> SmsIntent.PROMO
    "__label__safe"   -> SmsIntent.SAFE
    else              -> SmsIntent.UNKNOWN
}

/**
 * Returns the risk score to add based on intent and confidence.
 */
fun SmsIntent.toRiskScore(confidence: Float): Int = when (this) {
    SmsIntent.FRAUD   -> (confidence * 60).toInt().coerceIn(20, 60)
    SmsIntent.URGENT  -> (confidence * 35).toInt().coerceIn(10, 35)
    SmsIntent.OTP     -> 0
    SmsIntent.PROMO   -> 0
    SmsIntent.SAFE    -> 0
    SmsIntent.UNKNOWN -> 5
}
