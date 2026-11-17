package com.lomdi.dsih.domain.usecase

import com.lomdi.dsih.data.model.ThreatLevel

/**
 * Evaluates the risk score of an SMS message based on content, links, call state, clipboard, and remote apps.
 */
object ThreatEvaluator {

    private val urgencyKeywords = listOf(
        "immediate", "blocked", "suspended", "action required", 
        "kyc", "expired", "verify", "unauthorized", "won", "reward"
    )

    /**
     * Calculates a threat score from 0-100 and assigns a ThreatLevel.
     */
    fun evaluate(
        body: String, 
        links: List<String>, 
        isOnActiveCallWithUnsaved: Boolean = false,
        hasCopiedSensitiveData: Boolean = false,
        hasRemoteAppsInstalled: Boolean = false
    ): Pair<ThreatLevel, Int> {
        
        // 1. Critical Combination: Active Call + Remote Access App
        if (isOnActiveCallWithUnsaved && hasRemoteAppsInstalled) {
            return Pair(ThreatLevel.CRITICAL, 100)
        }

        var score = 0
        val lowerBody = body.lowercase()

        // 2. Evaluate Keywords (up to 40 points)
        val matchedKeywords = urgencyKeywords.count { lowerBody.contains(it) }
        score += (matchedKeywords * 15).coerceAtMost(40)

        // 3. Evaluate Links (up to 60 points)
        var hasSuspiciousLink = false
        links.forEach { link ->
            if (SmsLinkExtractor.isSuspicious(link)) {
                score += 30
                hasSuspiciousLink = true
            } else {
                score += 5
            }
        }
        score = score.coerceAtMost(100)

        // 4. Multi-Factor Escalations
        
        // Malicious link arrives during active call with unsaved number -> Critical
        if (isOnActiveCallWithUnsaved && hasSuspiciousLink) {
            return Pair(ThreatLevel.CRITICAL, 100)
        }

        // Copied UPI/URL during call with unsaved number -> High Threat
        if (isOnActiveCallWithUnsaved && hasCopiedSensitiveData) {
            return Pair(ThreatLevel.HIGH, 90)
        }

        // 5. Determine Level
        val level = when {
            score >= 70 -> ThreatLevel.HIGH
            score >= 30 -> ThreatLevel.MEDIUM
            else -> ThreatLevel.LOW
        }

        return Pair(level, score)
    }
}
