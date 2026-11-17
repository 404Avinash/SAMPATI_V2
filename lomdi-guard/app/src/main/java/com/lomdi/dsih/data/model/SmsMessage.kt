package com.lomdi.dsih.data.model

/**
 * Result of the detailed SMS analysis.
 */
data class SmsAnalysisResult(
    val totalRiskScore: Int = 0,
    val senderRisk: String = "",
    val linkRisk: String = "",
    val contentRisk: String = "",
    val requiresEdgeAi: Boolean = false
)

/**
 * Data model for an intercepted SMS message with threat assessment.
 */
data class SmsMessage(
    val id: Long = System.currentTimeMillis(),
    val sender: String,
    val body: String,
    val extractedLinks: List<String> = emptyList(),
    val threatLevel: ThreatLevel = ThreatLevel.LOW,
    val riskScore: Int = 0,
    val analysisResult: SmsAnalysisResult = SmsAnalysisResult()
)
