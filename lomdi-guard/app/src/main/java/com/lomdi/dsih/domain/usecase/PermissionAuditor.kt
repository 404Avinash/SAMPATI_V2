package com.lomdi.dsih.domain.usecase

import android.Manifest
import android.content.Context
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager

/**
 * Audits system permissions to identify apps with high-risk permission combinations.
 */
object PermissionAuditor {

    data class RiskyApp(val name: String, val reason: String)

    /**
     * Returns a list of third-party apps holding combinations of permissions 
     * often used by spyware (SMS + Internet + Accessibility).
     */
    fun getRiskyPermissionApps(context: Context): List<RiskyApp> {
        val pm = context.packageManager
        val riskyApps = mutableListOf<RiskyApp>()
        
        val installedPackages = pm.getInstalledPackages(PackageManager.GET_PERMISSIONS)
        
        for (pkgInfo in installedPackages) {
            val appInfo = pkgInfo.applicationInfo ?: continue
            
            // Exclude system apps and our own app
            if ((appInfo.flags and ApplicationInfo.FLAG_SYSTEM) == 0 && pkgInfo.packageName != context.packageName) {
                val perms = pkgInfo.requestedPermissions?.toList() ?: emptyList()
                
                val hasSms = perms.contains(Manifest.permission.RECEIVE_SMS) || perms.contains(Manifest.permission.READ_SMS)
                val hasInternet = perms.contains(Manifest.permission.INTERNET)
                
                if (hasSms && hasInternet) {
                    val label = pm.getApplicationLabel(appInfo).toString()
                    riskyApps.add(RiskyApp(label, "SMS Interception + Internet Access (Spyware Risk)"))
                }
            }
        }
        return riskyApps
    }
}
