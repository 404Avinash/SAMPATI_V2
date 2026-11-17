package com.lomdi.dsih.domain.usecase

import android.os.Build
import java.io.File

/**
 * Utility to detect if the device environment is compromised (Root/Jailbreak).
 */
object DeviceIntegrityScanner {

    private val dangerousPaths = arrayOf(
        "/system/app/Superuser.apk",
        "/sbin/su",
        "/system/bin/su",
        "/system/xbin/su",
        "/data/local/xbin/su",
        "/data/local/bin/su",
        "/system/sd/xbin/su",
        "/system/bin/failsafe/su",
        "/data/local/su",
        "/su/bin/su"
    )

    /**
     * Checks multiple indicators of device rooting.
     */
    fun isDeviceRooted(): Boolean {
        // 1. Build Tags Check
        val buildTags = Build.TAGS
        if (buildTags != null && buildTags.contains("test-keys")) {
            return true
        }

        // 2. Binary Existence Check
        for (path in dangerousPaths) {
            if (File(path).exists()) return true
        }

        // 3. Runtime Execution Check
        return try {
            val process = Runtime.getRuntime().exec(arrayOf("/system/xbin/which", "su"))
            process.inputStream.bufferedReader().use { it.readLine() != null }
        } catch (e: Exception) {
            false
        }
    }
}
