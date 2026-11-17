package com.lomdi.dsih.domain.usecase

import android.content.Context
import android.content.pm.ApplicationInfo
import android.provider.Settings

/**
 * Audits the active keyboard to detect potential keyloggers.
 */
object KeyboardAuditor {

    private val trustedKeyboards = setOf(
        "com.google.android.inputmethod.latin", // Gboard
        "com.samsung.android.honeyboard",       // Samsung Keyboard
        "com.swiftkey.swiftkeyconfig",         // SwiftKey
        "com.touchtype.swiftkey",              // SwiftKey Variant
        "com.microsoft._69_85_70"              // Microsoft SwiftKey
    )

    /**
     * Checks if the active keyboard is a non-system third-party app not in the trusted list.
     */
    fun isUntrustedKeyboardActive(context: Context): Pair<Boolean, String> {
        val defaultIME = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.DEFAULT_INPUT_METHOD
        ) ?: return Pair(false, "Unknown")

        val packageName = defaultIME.substringBefore('/')
        
        if (trustedKeyboards.contains(packageName)) return Pair(false, packageName)

        return try {
            val pm = context.packageManager
            val appInfo = pm.getApplicationInfo(packageName, 0)
            
            val isSystemApp = (appInfo.flags and ApplicationInfo.FLAG_SYSTEM) != 0
            if (isSystemApp) {
                Pair(false, packageName)
            } else {
                Pair(true, packageName)
            }
        } catch (e: Exception) {
            Pair(true, packageName)
        }
    }
}
