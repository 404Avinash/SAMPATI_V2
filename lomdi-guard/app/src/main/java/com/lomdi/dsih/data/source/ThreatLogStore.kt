package com.lomdi.dsih.data.source

import androidx.compose.runtime.mutableStateListOf
import com.lomdi.dsih.data.model.ThreatLevel
import java.util.Date

/**
 * Data model for a logged threat event.
 */
data class ThreatLog(
    val id: Long = System.currentTimeMillis(),
    val timestamp: Date,
    val type: String,
    val level: ThreatLevel,
    val score: Int
)

/**
 * Singleton store for auditing threat events.
 */
object ThreatLogStore {
    val logs = mutableStateListOf<ThreatLog>()

    fun addLog(type: String, level: ThreatLevel, score: Int) {
        if (level == ThreatLevel.HIGH || level == ThreatLevel.CRITICAL) {
            logs.add(0, ThreatLog(
                timestamp = Date(),
                type = type,
                level = level,
                score = score
            ))
        }
    }
}
