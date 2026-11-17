package com.lomdi.dsih.data.source

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * Singleton to track the active call state (PSTN and VoIP) of the device.
 */
object CallStateStore {
    // Standard PSTN Calls
    var isActiveCall by mutableStateOf(false)
    var activeNumber by mutableStateOf<String?>(null)
    var isUnsavedNumber by mutableStateOf(false)

    // VoIP Calls (WhatsApp, Telegram)
    var isVoipCallActive by mutableStateOf(false)
    var voipCallerName by mutableStateOf<String?>(null)
    var isUnsavedVoipCaller by mutableStateOf(false)
}
