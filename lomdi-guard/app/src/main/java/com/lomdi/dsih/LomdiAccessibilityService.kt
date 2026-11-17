package com.lomdi.dsih

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent
import android.view.accessibility.AccessibilityNodeInfo
import com.lomdi.dsih.data.config.PaymentAppsConfig
import com.lomdi.dsih.data.source.ClipboardStore
import com.lomdi.dsih.domain.usecase.ClipboardGuard
import com.lomdi.dsih.domain.usecase.RiskManager
import com.lomdi.dsih.ui.notification.ThreatNotificationManager

/**
 * Service to intercept on-screen text and manage security alerts for payment apps.
 * Switched from WindowManager overlays to High-Priority Notifications for better FLAG_SECURE support.
 */
class LomdiAccessibilityService : AccessibilityService() {

    private val ignoredPackages = setOf(
        "com.android.systemui",
        "com.google.android.inputmethod.latin",
        "android",
        "com.google.android.apps.nexuslauncher",
        "com.android.launcher3"
    )

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return

        // 1. Recursive Guard: Ignore events from Lomdi itself
        if (event.packageName == packageName) return

        // 2. Identify the Active Package with multi-step validation
        val activePackage = resolveActivePackage(event)

        // 3. Process Security Logic
        if (PaymentAppsConfig.isTargetApp(activePackage)) {
            checkAndTriggerAlert()
        }

        // 4. Continuous UPI extraction from on-screen nodes
        val rootNode = rootInActiveWindow
        if (rootNode != null) {
            findUpiInNode(rootNode)
        }
    }

    private fun resolveActivePackage(event: AccessibilityEvent): String? {
        val rootPkg = try { rootInActiveWindow?.packageName?.toString() } catch (e: Exception) { null }
        if (rootPkg != null) return rootPkg

        try {
            val windows = windows
            for (window in windows) {
                if (window.isFocused) {
                    val nodePkg = window.root?.packageName?.toString()
                    if (nodePkg != null) return nodePkg
                }
            }
        } catch (e: Exception) { }

        return event.packageName?.toString()
    }

    private fun checkAndTriggerAlert() {
        if (RiskManager.isSystemAtCriticalRisk()) {
            // Log the interception event
            com.lomdi.dsih.data.source.ThreatLogStore.addLog(
                type = "Payment App Threat Detected",
                level = com.lomdi.dsih.data.model.ThreatLevel.CRITICAL,
                score = 100
            )
            
            // Trigger high-priority heads-up notification
            ThreatNotificationManager.showNotification(this)
        }
    }

    private fun findUpiInNode(node: AccessibilityNodeInfo?) {
        if (node == null) return

        val text = node.text?.toString()
        if (!text.isNullOrBlank()) {
            val upi = ClipboardGuard.extractUpi(text)
            if (upi != null) {
                ClipboardStore.lastCopiedUpi = upi
                ClipboardStore.hasSensitiveData = true
            }
        }

        for (i in 0 until node.childCount) {
            try {
                findUpiInNode(node.getChild(i))
            } catch (e: Exception) {}
        }
    }

    override fun onInterrupt() {
        // Accessibility interrupted
    }
}
