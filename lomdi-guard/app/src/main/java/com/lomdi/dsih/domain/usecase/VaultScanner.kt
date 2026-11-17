package com.lomdi.dsih.domain.usecase

import android.app.admin.DevicePolicyManager
import android.content.Context
import android.os.Build
import android.os.storage.StorageManager

/**
 * Checks for data protection features like device encryption.
 */
object VaultScanner {

    data class VaultStatus(
        val isEncrypted: Boolean,
        val storageStatus: String
    )

    fun checkVaultStatus(context: Context): VaultStatus {
        val dpm = context.getSystemService(Context.DEVICE_POLICY_SERVICE) as DevicePolicyManager
        val encryptionStatus = dpm.storageEncryptionStatus
        
        val isEncrypted = encryptionStatus == DevicePolicyManager.ENCRYPTION_STATUS_ACTIVE ||
                          encryptionStatus == DevicePolicyManager.ENCRYPTION_STATUS_ACTIVE_PER_USER
        
        return VaultStatus(
            isEncrypted = isEncrypted,
            storageStatus = if (isEncrypted) "Hardware Encrypted" else "Unsecured Storage"
        )
    }
}
