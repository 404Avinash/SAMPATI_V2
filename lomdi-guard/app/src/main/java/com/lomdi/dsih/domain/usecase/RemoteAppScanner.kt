package com.lomdi.dsih.domain.usecase

import android.content.Context
import android.content.pm.PackageManager

/**
 * Utility to scan for installed remote access applications with Android 11+ visibility support.
 */
object RemoteAppScanner {

    private val remoteAccessPackages = listOf(
        "com.anydesk.anydeskandroid",
        "com.teamviewer.teamviewer.market.mobile",
        "com.teamviewer.quicksupport.market",
        "com.rustdesk.android",
        "com.splashtop.remote.pad.v2",
        "com.realvnc.viewer.android"
    )

    /**
     * Scans for specific known malicious/remote packages using the manifest-declared <queries>.
     */
    fun scanInstalledApps(context: Context): List<String> {
        val pm = context.packageManager
        val detected = mutableListOf<String>()

        for (pkg in remoteAccessPackages) {
            try {
                // Safely check for specific package without throwing exception if not found
                val appInfo = pm.getApplicationInfo(pkg, 0)
                val label = pm.getApplicationLabel(appInfo).toString()
                detected.add(label)
            } catch (e: PackageManager.NameNotFoundException) {
                // Expected if the app is not installed
            }
        }
        return detected
    }
}
