package com.lomdi.dsih

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.telephony.TelephonyManager
import com.lomdi.dsih.data.source.CallStateStore
import com.lomdi.dsih.domain.usecase.ContactValidator

/**
 * Receiver to detect call state changes.
 */
class CallReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context?, intent: Intent?) {
        if (intent?.action == TelephonyManager.ACTION_PHONE_STATE_CHANGED) {
            val state = intent.getStringExtra(TelephonyManager.EXTRA_STATE)
            val number = intent.getStringExtra(TelephonyManager.EXTRA_INCOMING_NUMBER)

            when (state) {
                TelephonyManager.EXTRA_STATE_RINGING, TelephonyManager.EXTRA_STATE_OFFHOOK -> {
                    CallStateStore.isActiveCall = true
                    if (number != null) {
                        CallStateStore.activeNumber = number
                        context?.let {
                            CallStateStore.isUnsavedNumber = !ContactValidator.isNumberInContacts(it, number)
                        }
                    }
                }
                TelephonyManager.EXTRA_STATE_IDLE -> {
                    CallStateStore.isActiveCall = false
                    CallStateStore.activeNumber = null
                    CallStateStore.isUnsavedNumber = false
                }
            }
        }
    }
}
