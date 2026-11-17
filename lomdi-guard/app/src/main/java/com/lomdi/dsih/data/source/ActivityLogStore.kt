package com.lomdi.dsih.data.source

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.lomdi.dsih.data.model.ActivityLog
import com.lomdi.dsih.data.model.ThreatLevel
import java.util.Calendar
import java.util.Date

/**
 * Singleton store for managing activity logs with support for toggling sample/demo data.
 */
object ActivityLogStore {
    var showDummyData by mutableStateOf(true)
    val logs = mutableStateListOf<ActivityLog>()

    init {
        // Pre-populate with sample activity logs marked as dummy
        val calendar = Calendar.getInstance()
        val now = calendar.time

        calendar.add(Calendar.HOUR_OF_DAY, -2)
        val todayEarlier = calendar.time

        calendar.add(Calendar.DAY_OF_YEAR, -1)
        val yesterday = calendar.time

        calendar.add(Calendar.DAY_OF_YEAR, -2)
        val twoDaysAgo = calendar.time

        logs.addAll(
            listOf(
                ActivityLog(
                    timestamp = now,
                    title = "Clipboard Guard Intercepted",
                    description = "Intercepted suspicious UPI ID (scam_merchant@okaxis) copied during active call.",
                    level = ThreatLevel.HIGH,
                    score = 85,
                    isDummy = true
                ),
                ActivityLog(
                    timestamp = todayEarlier,
                    title = "Remote Desktop App Warning",
                    description = "Detected background AnyDesk session while payment application was foregrounded.",
                    level = ThreatLevel.CRITICAL,
                    score = 100,
                    isDummy = true
                ),
                ActivityLog(
                    timestamp = yesterday,
                    title = "SMS Phishing Blocked",
                    description = "Flagged SMS from unknown sender containing urgent account suspension bait & shortened link.",
                    level = ThreatLevel.HIGH,
                    score = 75,
                    isDummy = true
                ),
                ActivityLog(
                    timestamp = yesterday,
                    title = "Unsaved Call Monitored",
                    description = "Monitored active incoming call from unregistered contact (+91 98765 43210).",
                    level = ThreatLevel.MEDIUM,
                    score = 45,
                    isDummy = true
                ),
                ActivityLog(
                    timestamp = twoDaysAgo,
                    title = "Overlay Security Audit",
                    description = "Scanned 34 installed packages. No unauthorized draw-over-apps detected.",
                    level = ThreatLevel.LOW,
                    score = 10,
                    isDummy = true
                ),
                ActivityLog(
                    timestamp = twoDaysAgo,
                    title = "System Sandbox Integrity",
                    description = "Device root binaries and SELinux status verified intact.",
                    level = ThreatLevel.LOW,
                    score = 5,
                    isDummy = true
                )
            )
        )
    }

    /**
     * Returns logs filtered based on whether sample/dummy data is currently toggled on.
     */
    val visibleLogs: List<ActivityLog>
        get() = if (showDummyData) logs else logs.filter { !it.isDummy }

    fun addLog(title: String, description: String, level: ThreatLevel, score: Int, isDummy: Boolean = false) {
        logs.add(
            0,
            ActivityLog(
                timestamp = Date(),
                title = title,
                description = description,
                level = level,
                score = score,
                isDummy = isDummy
            )
        )
    }

    fun clearAll() {
        logs.clear()
    }
}
