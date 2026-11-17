package com.lomdi.dsih.domain.usecase

import android.content.Context
import android.net.Uri
import android.provider.ContactsContract
import android.telephony.PhoneNumberUtils

/**
 * Utility to validate if a phone number exists in the user's contact list.
 */
object ContactValidator {

    /**
     * Returns true if the given number is found in the device contacts.
     */
    fun isNumberInContacts(context: Context, phoneNumber: String): Boolean {
        if (phoneNumber.isBlank()) return false
        
        val uri = Uri.withAppendedPath(
            ContactsContract.PhoneLookup.CONTENT_FILTER_URI,
            Uri.encode(phoneNumber)
        )
        
        val projection = arrayOf(ContactsContract.PhoneLookup._ID)
        
        context.contentResolver.query(uri, projection, null, null, null)?.use { cursor ->
            if (cursor.count > 0) {
                return true
            }
        }
        return false
    }
}
