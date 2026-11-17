package com.lomdi.dsih.domain.usecase

import android.Manifest
import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager

/**
 * Audits third-party apps holding SYSTEM_ALERT_WINDOW permissions.
 */
object OverlayAuditor {

    /**
     * Returns a list of user-installed third-party apps possessing overlay permissions.
     */
    fun getSuspiciousOverlayApps(context: Context): List<String> {
        val pm = context.packageManager
        val suspiciousApps = mutableListOf<String>()
        
        val installedPackages = pm.getInstalledPackages(PackageManager.GET_PERMISSIONS)
        
        for (pkgInfo in installedPackages) {
            val appInfo = pkgInfo.applicationInfo ?: continue
            
            // Exclude system apps and our own app
            if ((appInfo.flags and ApplicationInfo.FLAG_SYSTEM) == 0 && pkgInfo.packageName != context.packageName) {
                val requestedPermissions = pkgInfo.requestedPermissions
                if (requestedPermissions != null && requestedPermissions.contains(Manifest.permission.SYSTEM_ALERT_WINDOW)) {
                    val label = pm.getApplicationLabel(appInfo).toString()
                    suspiciousApps.add(label)
                }
            }
        }
        return suspiciousApps
    }
}
