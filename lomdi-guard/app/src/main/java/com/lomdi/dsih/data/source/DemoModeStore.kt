package com.lomdi.dsih.data.source

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * Singleton to track Developer Demo Mode status.
 */
object DemoModeStore {
    var isDemoModeEnabled by mutableStateOf(false)
}
