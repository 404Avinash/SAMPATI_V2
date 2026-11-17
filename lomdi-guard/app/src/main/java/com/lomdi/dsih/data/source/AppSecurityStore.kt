package com.lomdi.dsih.data.source

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * Singleton to track app-level security vulnerabilities and exploits.
 */
object AppSecurityStore {
    val activeAccessibilityTrojans = mutableStateListOf<String>()
    val activeOverlayApps = mutableStateListOf<String>()
    val riskyPermissionApps = mutableStateListOf<String>()
    
    var activeKeyboardPackage by mutableStateOf<String?>(null)
    var isUntrustedKeyboard by mutableStateOf(false)
    
    var isVpnActive by mutableStateOf(false)
    var networkType by mutableStateOf("Unknown")
    
    var isDeviceEncrypted by mutableStateOf(true)
    var vaultStatus by mutableStateOf("Protected")
}
