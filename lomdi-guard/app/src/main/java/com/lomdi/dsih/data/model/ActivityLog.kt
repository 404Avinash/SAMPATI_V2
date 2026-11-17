package com.lomdi.dsih.data.model

import java.util.Date
import java.util.UUID

/**
 * Data class representing an intercepted security event or activity log.
 */
data class ActivityLog(
    val id: String = UUID.randomUUID().toString(),
    val timestamp: Date,
    val title: String,
    val description: String,
    val level: ThreatLevel,
    val score: Int,
    val isDummy: Boolean = false
)
