package com.lomdi.dsih

import android.app.Notification
import android.media.AudioManager
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.lomdi.dsih.data.source.CallStateStore
import com.lomdi.dsih.domain.usecase.ContactValidator

/**
 * Service to intercept notifications from communication apps like WhatsApp and Telegram.
 */
class LomdiNotificationListener : NotificationListenerService() {

    private val audioManager by lazy { getSystemService(AUDIO_SERVICE) as AudioManager }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        val packageName = sbn?.packageName ?: return
        val extras = sbn.notification.extras
        val title = extras.getString(Notification.EXTRA_TITLE) ?: ""
        val text = extras.getString(Notification.EXTRA_TEXT) ?: ""

        // Check for VoIP Apps
        if (packageName == "com.whatsapp" || packageName == "org.telegram.messenger") {
            // Basic heuristic for incoming call notifications
            val isIncomingCall = title.contains("Incoming", ignoreCase = true) || 
                                 text.contains("Incoming", ignoreCase = true) ||
                                 title.contains("Call", ignoreCase = true)

            if (isIncomingCall) {
                Log.d("LomdiGuard", "VoIP Call Notification from $packageName: $title")
                
                // Update VoIP Caller State
                CallStateStore.voipCallerName = title
                CallStateStore.isUnsavedVoipCaller = !ContactValidator.isNumberInContacts(this, title)
                
                // Check if audio is currently in communication mode
                checkVoipCallActive()
            }
        }
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
        val packageName = sbn?.packageName ?: return
        if (packageName == "com.whatsapp" || packageName == "org.telegram.messenger") {
            // Check if call ended
            checkVoipCallActive()
        }
    }

    private fun checkVoipCallActive() {
        val inComm = audioManager.mode == AudioManager.MODE_IN_COMMUNICATION
        CallStateStore.isVoipCallActive = inComm
        if (!inComm) {
            CallStateStore.voipCallerName = null
            CallStateStore.isUnsavedVoipCaller = false
        }
    }
}
