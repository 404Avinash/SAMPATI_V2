package com.lomdi.dsih.ui.notification

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.lomdi.dsih.MainActivity
import com.lomdi.dsih.NotificationActionReceiver
import com.lomdi.dsih.domain.usecase.RiskManager
import com.lomdi.dsih.data.model.ThreatLevel

/**
 * Manages high-priority security notifications using native CallStyle APIs.
 * Ensures full-bleed colorization and visible action buttons on modern Android versions.
 */
object ThreatNotificationManager {
    private const val CHANNEL_ID = "threat_alerts"
    private const val NOTIFICATION_ID = 101
    private var lastNotificationTime = 0L
    private const val COOLDOWN_MS = 30000L // 30 seconds

    fun showNotification(context: Context) {
        val currentTime = System.currentTimeMillis()
        if (currentTime - lastNotificationTime < COOLDOWN_MS) return

        createNotificationChannel(context)

        // 1. Prepare Intents
        val seeRiskIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            putExtra("navigate_to", "threat_details")
        }
        val seeRiskPendingIntent = PendingIntent.getActivity(
            context, 1, seeRiskIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val ignoreIntent = Intent(context, NotificationActionReceiver::class.java).apply {
            action = NotificationActionReceiver.ACTION_IGNORE_RISK
        }
        val ignorePendingIntent = PendingIntent.getBroadcast(
            context, 2, ignoreIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // 2. Fetch Risk Metadata
        val threatLevel = RiskManager.getCurrentThreatLevel()
        val accentColor = if (threatLevel == ThreatLevel.CRITICAL) {
            Color.parseColor("#B71C1C")
        } else {
            Color.parseColor("#E53935")
        }

        // 3. Build Native Call-Style Notification
        val builder = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle("CRITICAL SECURITY ALERT")
            .setContentText("Suspicious transaction activity flagged. Do not proceed.")
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setCategory(NotificationCompat.CATEGORY_CALL)
            .setOngoing(true)
            .setAutoCancel(false)
            .setColor(accentColor)
            .setColorized(true)
            .setDefaults(Notification.DEFAULT_ALL)
            .setFullScreenIntent(seeRiskPendingIntent, true)
            // Add standard actions (Ensures visibility and system styling)
            .addAction(
                NotificationCompat.Action.Builder(
                    null, "SEE RISK", seeRiskPendingIntent
                ).build()
            )
            .addAction(
                NotificationCompat.Action.Builder(
                    null, "IGNORE RISK", ignorePendingIntent
                ).build()
            )

        try {
            with(NotificationManagerCompat.from(context)) {
                notify(NOTIFICATION_ID, builder.build())
                lastNotificationTime = currentTime
            }
        } catch (e: SecurityException) {
            // Permission not granted
        }
    }

    private fun createNotificationChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "Security Alerts"
            val descriptionText = "High priority call-style notifications for fraud prevention"
            val importance = NotificationManager.IMPORTANCE_HIGH
            val channel = NotificationChannel(CHANNEL_ID, name, importance).apply {
                description = descriptionText
            }
            val notificationManager: NotificationManager =
                context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }
}
