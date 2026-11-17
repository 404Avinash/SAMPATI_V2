package com.lomdi.dsih.data.source

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

enum class ThemeMode {
    SYSTEM, LIGHT, DARK
}

/**
 * Global reactive singleton store for application theme status.
 */
object ThemeStore {
    var themeMode by mutableStateOf(ThemeMode.SYSTEM)

    fun isDarkTheme(systemInDark: Boolean): Boolean {
        return when (themeMode) {
            ThemeMode.SYSTEM -> systemInDark
            ThemeMode.LIGHT -> false
            ThemeMode.DARK -> true
        }
    }
}
