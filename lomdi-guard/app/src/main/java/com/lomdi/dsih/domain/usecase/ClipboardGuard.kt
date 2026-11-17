package com.lomdi.dsih.domain.usecase

/**
 * Logic to identify sensitive patterns in clipboard data.
 * Specifically distinguishes between standard Email addresses and UPI IDs.
 */
object ClipboardGuard {

    private val emailRegex = Regex("""(?i)[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(com|in|org|net|co|io|edu|gov|ai|me|info)""")
    private val upiRegex = Regex("""[a-zA-Z0-9.\-_]+@[a-zA-Z0-9]+""")
    private val urlRegex = "(https?://[^\\s]+|www\\.[^\\s]+)".toRegex(RegexOption.IGNORE_CASE)

    /**
     * Extracts a UPI ID if the text doesn't look like an email address.
     */
    fun extractUpi(text: String): String? {
        val trimmed = text.trim()
        
        // 1. Check if it's an email address
        if (emailRegex.matches(trimmed)) return null
        
        // 2. Disqualify if there's a dot in the domain part after @
        val atIndex = trimmed.indexOf('@')
        if (atIndex != -1) {
            val domain = trimmed.substring(atIndex + 1)
            if (domain.contains(".")) return null
        }
        
        // 3. Match against strict UPI pattern
        return if (upiRegex.matches(trimmed)) trimmed else null
    }

    fun extractUrl(text: String): String? {
        return urlRegex.find(text)?.value
    }

    fun isSensitive(text: String): Boolean {
        return extractUpi(text) != null || extractUrl(text) != null
    }
}
