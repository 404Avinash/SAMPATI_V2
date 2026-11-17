package com.lomdi.dsih.data.source

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue

/**
 * Singleton store for user configuration such as Phone Number and UPI IDs.
 */
object UserSettingsStore {
    var phoneNumber by mutableStateOf("")
    val upiIds = mutableStateListOf<String>()

    fun setPhone(phone: String) {
        phoneNumber = phone
    }

    fun setUpiList(list: Collection<String>) {
        upiIds.clear()
        upiIds.addAll(list)
    }

    fun addUpi(upi: String) {
        if (!upiIds.contains(upi)) {
            upiIds.add(upi)
        }
    }

    fun removeUpi(upi: String) {
        upiIds.remove(upi)
    }
}
