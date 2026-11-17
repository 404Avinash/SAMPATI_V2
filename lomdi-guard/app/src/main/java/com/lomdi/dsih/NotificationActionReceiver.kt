package com.lomdi.dsih

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationManagerCompat

class NotificationActionReceiver : BroadcastReceiver() {
    companion object {
        const val ACTION_IGNORE_RISK = "com.lomdi.dsih.ACTION_IGNORE_RISK"
        const val NOTIFICATION_ID = 101
    }

    override fun onReceive(context: Context?, intent: Intent?) {
        if (intent?.action == ACTION_IGNORE_RISK) {
            context?.let {
                NotificationManagerCompat.from(it).cancel(NOTIFICATION_ID)
            }
        }
    }
}
