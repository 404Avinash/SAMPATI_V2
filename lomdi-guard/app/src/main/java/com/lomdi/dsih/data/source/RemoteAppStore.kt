package com.lomdi.dsih.data.source

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * Singleton to track detected remote access applications.
 */
object RemoteAppStore {
    var hasRemoteApps by mutableStateOf(false)
    val detectedApps = mutableStateListOf<String>()
}
