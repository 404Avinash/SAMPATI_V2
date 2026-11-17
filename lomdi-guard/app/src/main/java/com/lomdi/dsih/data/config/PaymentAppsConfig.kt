package com.lomdi.dsih.data.config

/**
 * Central configuration for target payment and banking applications.
 */
object PaymentAppsConfig {
    val targetPackages = mutableSetOf(
        "com.google.android.apps.nbu.paisa.user", // Google Pay
        "net.one97.paytm",                        // Paytm
        "com.phonepe.app",                        // PhonePe
        "in.amazon.mShop.android.shopping",       // Amazon Pay
        "com.mobikwik_new",                       // MobiKwik
        "me.fampay.in",                           // FamPay
        "com.fampay",                             // FamPay Variant
        "club.pop.app",                           // Pop UPI
        "in.org.npci.upiapp",                     // BHIM
        "com.dreamplug.androidapp",               // CRED
        "org.sliceit.android"                     // Slice
    )

    /**
     * Checks if the given package name is in the list of protected payment apps.
     */
    fun isTargetApp(packageName: String?): Boolean {
        if (packageName == null) return false
        // Precise check and broad contains check for safety
        return targetPackages.any { packageName.contains(it) || it.contains(packageName) }
    }
}
