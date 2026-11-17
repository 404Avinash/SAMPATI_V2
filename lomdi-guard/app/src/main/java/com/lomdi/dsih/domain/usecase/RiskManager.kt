package com.lomdi.dsih.domain.usecase

import com.lomdi.dsih.data.model.ThreatLevel
import com.lomdi.dsih.data.source.AppSecurityStore
import com.lomdi.dsih.data.source.CallStateStore
import com.lomdi.dsih.data.source.ClipboardStore
import com.lomdi.dsih.data.source.DemoModeStore
import com.lomdi.dsih.data.source.DeviceSecurityStore
import com.lomdi.dsih.data.source.RemoteAppStore

/**
 * Data model for an itemized risk factor contribution with evidence.
 */
data class RiskFactor(
    val title: String,
    val contributionPercentage: Int,
    val details: String,
    val evidence: String? = null
)

/**
 * Global risk manager to evaluate the current system threat level including VoIP, PSTN, hardware, and app-level signals.
 */
object RiskManager {

    /**
     * Returns the current ThreatLevel based on all active signals.
     */
    fun getCurrentThreatLevel(): ThreatLevel {
        // Developer Demo Mode Override
        if (DemoModeStore.isDemoModeEnabled) {
            return ThreatLevel.CRITICAL
        }

        // 1. STANDALONE CRITICAL: Device is rooted/compromised
        if (DeviceSecurityStore.isDeviceRooted) {
            return ThreatLevel.CRITICAL
        }

        val isAnyUnsavedCallActive = (CallStateStore.isActiveCall && CallStateStore.isUnsavedNumber) ||
                                     (CallStateStore.isVoipCallActive && CallStateStore.isUnsavedVoipCaller)

        // 2. Critical Scenario: Active Unsaved Call + Remote Access/Screen Share/Accessibility Trojan
        if (isAnyUnsavedCallActive && (RemoteAppStore.hasRemoteApps || 
                                       DeviceSecurityStore.isActiveScreenShare || 
                                       AppSecurityStore.activeAccessibilityTrojans.isNotEmpty())) {
            return ThreatLevel.CRITICAL
        }

        // 3. High Risk: Combinations or standalone high threats
        if (isAnyUnsavedCallActive && (ClipboardStore.hasSensitiveData || AppSecurityStore.isUntrustedKeyboard)) {
            return ThreatLevel.HIGH
        }
        
        if (DeviceSecurityStore.isActiveScreenShare || AppSecurityStore.activeAccessibilityTrojans.isNotEmpty()) {
            return ThreatLevel.HIGH
        }

        // 4. Medium Risk: Just Active Unsaved Call, Just Remote Apps, or Just Overlays
        if (isAnyUnsavedCallActive || 
            RemoteAppStore.hasRemoteApps || 
            AppSecurityStore.activeOverlayApps.isNotEmpty() ||
            AppSecurityStore.isUntrustedKeyboard) {
            return ThreatLevel.MEDIUM
        }

        return ThreatLevel.LOW
    }

    /**
     * Returns true if the system is in a state requiring an immediate warning overlay.
     */
    fun isSystemAtCriticalRisk(): Boolean {
        return getCurrentThreatLevel() == ThreatLevel.CRITICAL
    }

    /**
     * Returns a detailed list of risk factors contributing to the current score.
     */
    fun getRiskBreakdown(): List<RiskFactor> {
        if (DemoModeStore.isDemoModeEnabled) {
            return listOf(
                RiskFactor(
                    "Simulated Threat Override", 
                    100, 
                    "Manual presentation trigger enabled via Dashboard switch.",
                    "DEMO_MODE_ACTIVE"
                )
            )
        }

        val factors = mutableListOf<RiskFactor>()
        
        if (DeviceSecurityStore.isDeviceRooted) {
            factors.add(RiskFactor("Device Integrity Compromised", 100, "Root access or dangerous binaries detected. Device is unsafe for transactions.", "ROOT_DETECTED"))
            return factors 
        }

        val isAnyUnsavedCallActive = (CallStateStore.isActiveCall && CallStateStore.isUnsavedNumber) ||
                                     (CallStateStore.isVoipCallActive && CallStateStore.isUnsavedVoipCaller)

        if (DeviceSecurityStore.isActiveScreenShare) {
            factors.add(RiskFactor("Active Screen Sharing", 50, "Device screen is currently being shared or recorded.", "VIRTUAL_DISPLAY_ACTIVE"))
        }

        if (AppSecurityStore.activeAccessibilityTrojans.isNotEmpty()) {
            val apps = AppSecurityStore.activeAccessibilityTrojans.joinToString(", ")
            factors.add(RiskFactor("Accessibility Exploit Risk", 40, "Third-party apps holding screen-reading permissions detected.", apps))
        }

        if (RemoteAppStore.hasRemoteApps) {
            val apps = RemoteAppStore.detectedApps.joinToString(", ")
            factors.add(RiskFactor("Remote Access Tool", 40, "Active screen-sharing or remote desktop app detected.", apps))
        }
        
        if (isAnyUnsavedCallActive) {
            val caller = if (CallStateStore.isVoipCallActive) CallStateStore.voipCallerName else CallStateStore.activeNumber
            val callerStr = if (caller != null) "($caller)" else "Unsaved Number"
            factors.add(RiskFactor("Active Unsaved Call", 30, "User is on a call with an unknown contact.", callerStr))
        }

        if (AppSecurityStore.isUntrustedKeyboard) {
            factors.add(RiskFactor("Keyboard Integrity Risk", 35, "Active default keyboard is an untrusted third-party app.", AppSecurityStore.activeKeyboardPackage))
        }

        if (ClipboardStore.hasSensitiveData) {
            val evidence = listOfNotNull(ClipboardStore.lastCopiedUpi, ClipboardStore.lastCopiedUrl).joinToString(" | ")
            factors.add(RiskFactor("Sensitive Clipboard Data", 30, "Suspicious UPI handle or link detected in device clipboard.", evidence))
        }

        if (AppSecurityStore.activeOverlayApps.isNotEmpty()) {
            factors.add(RiskFactor("Tapjacking Risk", 25, "Third-party apps possess permissions to draw over other applications.", "COUNT: \${AppSecurityStore.activeOverlayApps.size}"))
        }

        return factors
    }

    /**
     * Returns a list of active threat reasons.
     */
    fun getActiveThreatReasons(): List<String> {
        return getRiskBreakdown().map { it.title }
    }
}
