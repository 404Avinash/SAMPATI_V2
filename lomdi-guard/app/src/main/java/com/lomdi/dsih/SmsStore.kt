package com.lomdi.dsih

import androidx.compose.runtime.mutableStateListOf
import com.lomdi.dsih.data.model.SmsMessage

/**
 * Singleton store for intercepted SMS messages.
 */
object SmsStore {
    // Observable list of structured SmsMessage objects.
    val messages = mutableStateListOf<SmsMessage>()
}
