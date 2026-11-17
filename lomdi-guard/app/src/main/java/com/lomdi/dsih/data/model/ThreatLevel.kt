package com.lomdi.dsih.data.model

/**
 * Represents the calculated risk level of an intercepted message or event.
 */
enum class ThreatLevel(val label: String) {
    LOW("Low Risk"),
    MEDIUM("Caution"),
    HIGH("Dangerous"),
    CRITICAL("CRITICAL THREAT")
}
