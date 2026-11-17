package com.lomdi.dsih.domain.usecase

import android.content.Context
import android.content.pm.ApplicationInfo
import android.provider.Settings
import android.text.TextUtils

/**
 * Audits other apps with active AccessibilityService permissions.
 */
object AccessibilityAuditor {

    /**
     * Returns a list of non-system third-party apps with active Accessibility Services.
     */
    fun getSuspiciousAccessibilityApps(context: Context): List<String> {
        val enabledServices = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return emptyList()

        val suspiciousApps = mutableListOf<String>()
        val pm = context.packageManager
        val splitter = TextUtils.SimpleStringSplitter(':')
        splitter.setString(enabledServices)

        while (splitter.hasNext()) {
            val componentName = splitter.next()
            val packageName = componentName.substringBefore('/')
            
            if (packageName == context.packageName) continue

            try {
                val appInfo = pm.getApplicationInfo(packageName, 0)
                // Filter for non-system apps
                if ((appInfo.flags and ApplicationInfo.FLAG_SYSTEM) == 0) {
                    val label = pm.getApplicationLabel(appInfo).toString()
                    suspiciousApps.add(label)
                }
            } catch (e: Exception) {
                // Package not found or restricted
            }
        }
        return suspiciousApps
    }
}
