package com.lomdi.dsih.data.source

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * Singleton to track low-level device security states.
 */
object DeviceSecurityStore {
    var isActiveScreenShare by mutableStateOf(false)
    var isDeviceRooted by mutableStateOf(false)
}
