package com.lomdi.dsih.domain.usecase

import android.net.Uri

enum class LinkType {
    UPI_MONEY_REQUEST,      // upi://pay?... with &am= or &tr= requesting money
    UPI_PAYMENT_DEEPLINK,   // upi://, gpay://, phonepe://, paytm://
    APK_DOWNLOAD_LINK,      // Direct .apk links, mediafire, drive file downloads
    SUSPICIOUS_SHORTENER,   // bit.ly, tinyurl.com, rb.gy, t.co, is.gd
    RAW_IP_ADDRESS,         // Links using raw IP addresses (e.g., http://192.168.1.1/pay)
    GENERAL_URL             // Standard web links
}

data class ClassifiedLink(
    val url: String,
    val type: LinkType,
    val riskScore: Int,
    val description: String
)

/**
 * Enhanced logic to extract and classify links for threat analysis.
 */
object SmsLinkExtractor {
    
    // Regex for standard URLs and UPI payment links
    private val linkRegex = "(https?://[^\\s]+|www\\.[^\\s]+|upi://pay\\?[^\\s]+)".toRegex(RegexOption.IGNORE_CASE)
    
    private val shorteners = setOf("bit.ly", "tinyurl.com", "rb.gy", "t.co", "is.gd", "goo.gl", "ow.ly")
    private val ipRegex = """^https?://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}""".toRegex()

    fun extractLinks(text: String): List<String> {
        return linkRegex.findAll(text).map { it.value }.toList()
    }

    /**
     * Classifies a link based on its URI scheme and host patterns.
     */
    fun classifyLink(url: String): ClassifiedLink {
        val lower = url.lowercase()
        
        // 1. UPI Money Request detection
        if (lower.startsWith("upi://pay") || (lower.contains("pa=") && lower.contains("am="))) {
            return ClassifiedLink(
                url = url,
                type = LinkType.UPI_MONEY_REQUEST,
                riskScore = 90,
                description = "Direct attempt to initiate or collect payment via UPI deep-link."
            )
        }
        
        if (lower.startsWith("upi://") || lower.startsWith("gpay://") || lower.startsWith("phonepe://")) {
            return ClassifiedLink(
                url = url,
                type = LinkType.UPI_PAYMENT_DEEPLINK,
                riskScore = 70,
                description = "Standard UPI or payment app deep-link detected."
            )
        }

        // 2. Malware / APK detection
        if (lower.endsWith(".apk") || lower.contains("/download/")) {
            return ClassifiedLink(
                url = url,
                type = LinkType.APK_DOWNLOAD_LINK,
                riskScore = 100,
                description = "Critical Risk: Sideloading malware risk detected (.apk or download path)."
            )
        }

        // 3. Shortener & IP detection
        val uri = try { Uri.parse(url) } catch (e: Exception) { null }
        val host = uri?.host?.lowercase() ?: ""
        
        if (shorteners.any { host == it || host.endsWith(".$it") }) {
            return ClassifiedLink(
                url = url,
                type = LinkType.SUSPICIOUS_SHORTENER,
                riskScore = 60,
                description = "Message uses a URL shortener to obfuscate the final destination."
            )
        }

        if (ipRegex.containsMatchIn(lower)) {
            return ClassifiedLink(
                url = url,
                type = LinkType.RAW_IP_ADDRESS,
                riskScore = 80,
                description = "Suspicious Link: Uses a raw IP address instead of a verified domain."
            )
        }

        return ClassifiedLink(
            url = url,
            type = LinkType.GENERAL_URL,
            riskScore = 10,
            description = "Standard web link."
        )
    }

    /**
     * Legacy check for suspicious links.
     */
    fun isSuspicious(link: String): Boolean {
        return classifyLink(link).riskScore > 50
    }
}
