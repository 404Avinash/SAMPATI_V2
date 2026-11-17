package com.lomdi.dsih.data.source

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * Singleton to track sensitive data copied to the clipboard.
 */
object ClipboardStore {
    var lastCopiedUpi by mutableStateOf<String?>(null)
    var lastCopiedUrl by mutableStateOf<String?>(null)
    var hasSensitiveData by mutableStateOf(false)
}
