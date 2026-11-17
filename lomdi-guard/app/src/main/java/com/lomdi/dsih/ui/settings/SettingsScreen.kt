package com.lomdi.dsih.ui.settings

import androidx.compose.animation.*
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.lomdi.dsih.R
import com.lomdi.dsih.data.source.DataStoreManager
import com.lomdi.dsih.data.source.ThemeMode
import com.lomdi.dsih.data.source.ThemeStore
import com.lomdi.dsih.data.source.UserSettingsStore
import com.lomdi.dsih.ui.components.LanguagePickerMenu
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(padding: PaddingValues) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val dataStoreManager = remember { DataStoreManager(context) }

    var phoneInput by remember { mutableStateOf(UserSettingsStore.phoneNumber) }
    var upiInput by remember { mutableStateOf("") }
    
    var phoneErrorMsg by remember { mutableStateOf("") }
    var phoneSuccessMsg by remember { mutableStateOf("") }
    var upiErrorMsg by remember { mutableStateOf("") }
    var upiSuccessMsg by remember { mutableStateOf("") }

    val systemDark = isSystemInDarkTheme()
    val isDark = ThemeStore.isDarkTheme(systemDark)

    // Sync input if UserSettingsStore changes externally
    LaunchedEffect(UserSettingsStore.phoneNumber) {
        if (phoneInput.isEmpty() && UserSettingsStore.phoneNumber.isNotEmpty()) {
            phoneInput = UserSettingsStore.phoneNumber
        }
    }

    LazyColumn(
        modifier = Modifier
            .padding(padding)
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
        contentPadding = PaddingValues(top = 16.dp, bottom = 40.dp)
    ) {
        // Title Header
        item {
            Column {
                Text(
                    text = stringResource(R.string.settings_title),
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Black
                )
                Text(
                    text = stringResource(R.string.settings_subtitle),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        // SECTION 1: App Preferences
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "App Preferences",
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold
                )

                OutlinedCard(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column {
                        // Language Picker Row
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                modifier = Modifier.weight(1f)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Translate,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier.size(20.dp)
                                )
                                Spacer(Modifier.width(12.dp))
                                Column {
                                    Text(
                                        text = stringResource(R.string.language_picker_title),
                                        fontWeight = FontWeight.Bold,
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                    Text(
                                        text = "English, हिन्दी, मराठी, বাংলা, తెలుగు, தமிழ்",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }

                            LanguagePickerMenu(iconTint = MaterialTheme.colorScheme.primary)
                        }

                        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))

                        // Light / Dark Theme Switch Row
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                modifier = Modifier.weight(1f)
                            ) {
                                Icon(
                                    imageVector = if (isDark) Icons.Default.DarkMode else Icons.Default.LightMode,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier.size(20.dp)
                                )
                                Spacer(Modifier.width(12.dp))
                                Column {
                                    Text(
                                        text = "Dark Theme Mode",
                                        fontWeight = FontWeight.Bold,
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                    Text(
                                        text = if (isDark) "Dark mode enabled" else "Light mode enabled",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }

                            Switch(
                                checked = isDark,
                                onCheckedChange = { checked ->
                                    val newMode = if (checked) ThemeMode.DARK else ThemeMode.LIGHT
                                    ThemeStore.themeMode = newMode
                                    scope.launch {
                                        dataStoreManager.saveThemeMode(newMode.name)
                                    }
                                }
                            )
                        }
                    }
                }
            }
        }

        // SECTION 2: Identity & Verification
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "Identity & Verification",
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold
                )

                OutlinedCard(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(14.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.Phone,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.size(20.dp)
                            )
                            Spacer(Modifier.width(10.dp))
                            Text(
                                text = stringResource(R.string.phone_number_title),
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface,
                                fontSize = 16.sp
                            )
                        }

                        Text(
                            text = stringResource(R.string.phone_number_desc),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )

                        OutlinedTextField(
                            value = phoneInput,
                            onValueChange = { 
                                phoneInput = it 
                                phoneErrorMsg = ""
                                phoneSuccessMsg = ""
                            },
                            label = { Text(stringResource(R.string.lbl_mobile_number)) },
                            placeholder = { Text("e.g. +91 9876543210") },
                            singleLine = true,
                            isError = phoneErrorMsg.isNotEmpty(),
                            keyboardOptions = KeyboardOptions(
                                keyboardType = KeyboardType.Phone,
                                imeAction = ImeAction.Done
                            ),
                            modifier = Modifier.fillMaxWidth(),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = MaterialTheme.colorScheme.primary,
                                unfocusedBorderColor = MaterialTheme.colorScheme.outline,
                                focusedLabelColor = MaterialTheme.colorScheme.primary,
                                unfocusedLabelColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                focusedTextColor = MaterialTheme.colorScheme.onSurface,
                                unfocusedTextColor = MaterialTheme.colorScheme.onSurface,
                                cursorColor = MaterialTheme.colorScheme.primary,
                                errorBorderColor = MaterialTheme.colorScheme.error,
                                errorLabelColor = MaterialTheme.colorScheme.error
                            ),
                            leadingIcon = {
                                Icon(Icons.Default.Smartphone, null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        )

                        AnimatedVisibility(visible = phoneErrorMsg.isNotEmpty()) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.Error, null, tint = MaterialTheme.colorScheme.error, modifier = Modifier.size(16.dp))
                                Spacer(Modifier.width(6.dp))
                                Text(phoneErrorMsg, color = MaterialTheme.colorScheme.error, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                            }
                        }

                        AnimatedVisibility(visible = phoneSuccessMsg.isNotEmpty()) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.CheckCircle, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(16.dp))
                                Spacer(Modifier.width(6.dp))
                                Text(phoneSuccessMsg, color = MaterialTheme.colorScheme.primary, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                            }
                        }

                        Button(
                            onClick = {
                                val trimmed = phoneInput.trim()
                                if (!isValidIndianPhoneNumber(trimmed)) {
                                    phoneErrorMsg = "Please enter a valid 10-digit Indian mobile number starting with 6, 7, 8, or 9 (e.g. +91 9876543210)."
                                    phoneSuccessMsg = ""
                                } else {
                                    val formatted = formatIndianPhoneNumber(trimmed)
                                    phoneErrorMsg = ""
                                    phoneInput = formatted
                                    UserSettingsStore.setPhone(formatted)
                                    scope.launch {
                                        dataStoreManager.savePhoneNumber(formatted)
                                        phoneSuccessMsg = "Phone number verified & saved successfully!"
                                    }
                                }
                            },
                            modifier = Modifier.fillMaxWidth(),
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                            shape = RoundedCornerShape(10.dp)
                        ) {
                            Icon(Icons.Default.Save, null, tint = MaterialTheme.colorScheme.onPrimary, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(8.dp))
                            Text(stringResource(R.string.btn_save_phone_number), color = MaterialTheme.colorScheme.onPrimary, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        // SECTION 3: Payment Profiles
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "Payment Profiles",
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold
                )

                OutlinedCard(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(14.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    imageVector = Icons.Default.AccountBalanceWallet,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier.size(20.dp)
                                )
                                Spacer(Modifier.width(10.dp))
                                Text(
                                    text = stringResource(R.string.registered_upi_ids_title),
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onSurface,
                                    fontSize = 16.sp
                                )
                            }
                            
                            Surface(
                                color = MaterialTheme.colorScheme.primaryContainer,
                                shape = RoundedCornerShape(20.dp)
                            ) {
                                Text(
                                    text = "${UserSettingsStore.upiIds.size} Saved",
                                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                                    color = MaterialTheme.colorScheme.onPrimaryContainer,
                                    fontSize = 11.sp,
                                    fontWeight = FontWeight.Bold
                                )
                            }
                        }

                        Text(
                            text = stringResource(R.string.registered_upi_ids_desc),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )

                        OutlinedTextField(
                            value = upiInput,
                            onValueChange = { 
                                upiInput = it
                                upiErrorMsg = ""
                                upiSuccessMsg = ""
                            },
                            label = { Text(stringResource(R.string.lbl_new_upi_id)) },
                            placeholder = { Text("e.g. username@bank / 9876543210@paytm") },
                            singleLine = true,
                            isError = upiErrorMsg.isNotEmpty(),
                            keyboardOptions = KeyboardOptions(
                                keyboardType = KeyboardType.Email,
                                imeAction = ImeAction.Done
                            ),
                            modifier = Modifier.fillMaxWidth(),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedBorderColor = MaterialTheme.colorScheme.primary,
                                unfocusedBorderColor = MaterialTheme.colorScheme.outline,
                                focusedLabelColor = MaterialTheme.colorScheme.primary,
                                unfocusedLabelColor = MaterialTheme.colorScheme.onSurfaceVariant,
                                focusedTextColor = MaterialTheme.colorScheme.onSurface,
                                unfocusedTextColor = MaterialTheme.colorScheme.onSurface,
                                cursorColor = MaterialTheme.colorScheme.primary,
                                errorBorderColor = MaterialTheme.colorScheme.error,
                                errorLabelColor = MaterialTheme.colorScheme.error
                            ),
                            leadingIcon = {
                                Icon(Icons.Default.QrCode, null, tint = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        )

                        AnimatedVisibility(visible = upiErrorMsg.isNotEmpty()) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.Error, null, tint = MaterialTheme.colorScheme.error, modifier = Modifier.size(16.dp))
                                Spacer(Modifier.width(6.dp))
                                Text(upiErrorMsg, color = MaterialTheme.colorScheme.error, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                            }
                        }

                        AnimatedVisibility(visible = upiSuccessMsg.isNotEmpty()) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.CheckCircle, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(16.dp))
                                Spacer(Modifier.width(6.dp))
                                Text(upiSuccessMsg, color = MaterialTheme.colorScheme.primary, fontSize = 12.sp, fontWeight = FontWeight.Medium)
                            }
                        }

                        Button(
                            onClick = {
                                val (isValid, errorReason) = validateUpiId(upiInput)
                                if (!isValid) {
                                    upiErrorMsg = errorReason
                                    upiSuccessMsg = ""
                                } else {
                                    val trimmed = upiInput.trim()
                                    UserSettingsStore.addUpi(trimmed)
                                    scope.launch {
                                        dataStoreManager.addUpiId(trimmed)
                                        upiSuccessMsg = "Added '$trimmed' to trusted UPI list!"
                                        upiInput = ""
                                        upiErrorMsg = ""
                                    }
                                }
                            },
                            modifier = Modifier.fillMaxWidth(),
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                            shape = RoundedCornerShape(10.dp)
                        ) {
                            Icon(Icons.Default.Add, null, tint = MaterialTheme.colorScheme.onPrimary, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(8.dp))
                            Text(stringResource(R.string.btn_add_upi_id), color = MaterialTheme.colorScheme.onPrimary, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        // List of Added UPI IDs
        item {
            Text(
                text = stringResource(R.string.your_saved_handles),
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
                fontWeight = FontWeight.Bold
            )
        }

        if (UserSettingsStore.upiIds.isEmpty()) {
            item {
                OutlinedCard(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(24.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Icon(
                                imageVector = Icons.Default.AccountBalanceWallet,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.size(36.dp)
                            )
                            Spacer(Modifier.height(8.dp))
                            Text(
                                text = stringResource(R.string.no_upi_registered),
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                fontSize = 14.sp
                            )
                            Text(
                                text = stringResource(R.string.no_upi_registered_sub),
                                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                                fontSize = 12.sp
                            )
                        }
                    }
                }
            }
        } else {
            items(UserSettingsStore.upiIds) { upiId ->
                OutlinedCard(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp, vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.weight(1f)
                        ) {
                            Surface(
                                color = MaterialTheme.colorScheme.primaryContainer,
                                shape = RoundedCornerShape(8.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.CheckCircle,
                                    contentDescription = null,
                                    tint = MaterialTheme.colorScheme.onPrimaryContainer,
                                    modifier = Modifier
                                        .padding(8.dp)
                                        .size(18.dp)
                                )
                            }
                            Spacer(Modifier.width(12.dp))
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    text = upiId,
                                    color = MaterialTheme.colorScheme.onSurface,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 15.sp
                                )
                                Text(
                                    text = stringResource(R.string.verified_handle),
                                    color = MaterialTheme.colorScheme.primary,
                                    fontSize = 11.sp
                                )
                            }
                        }

                        IconButton(
                            onClick = {
                                UserSettingsStore.removeUpi(upiId)
                                scope.launch {
                                    dataStoreManager.removeUpiId(upiId)
                                }
                            }
                        ) {
                            Icon(
                                imageVector = Icons.Default.Delete,
                                contentDescription = "Delete UPI ID",
                                tint = MaterialTheme.colorScheme.error
                            )
                        }
                    }
                }
            }
        }
    }
}

/**
 * Validates an Indian 10-digit mobile number starting with 6, 7, 8, or 9.
 */
private fun isValidIndianPhoneNumber(input: String): Boolean {
    val digitsOnly = input.replace(Regex("[^0-9]"), "")
    val normalized = when {
        digitsOnly.startsWith("91") && digitsOnly.length == 12 -> digitsOnly.substring(2)
        digitsOnly.startsWith("0") && digitsOnly.length == 11 -> digitsOnly.substring(1)
        digitsOnly.length == 10 -> digitsOnly
        else -> ""
    }
    return normalized.matches(Regex("^[6-9]\\d{9}$"))
}

/**
 * Formats a valid Indian mobile number into standard +91 XXXXX XXXXX format.
 */
private fun formatIndianPhoneNumber(input: String): String {
    val digitsOnly = input.replace(Regex("[^0-9]"), "")
    val normalized = when {
        digitsOnly.startsWith("91") && digitsOnly.length == 12 -> digitsOnly.substring(2)
        digitsOnly.startsWith("0") && digitsOnly.length == 11 -> digitsOnly.substring(1)
        digitsOnly.length == 10 -> digitsOnly
        else -> digitsOnly
    }
    return if (normalized.matches(Regex("^[6-9]\\d{9}$"))) {
        "+91 ${normalized.substring(0, 5)} ${normalized.substring(5)}"
    } else {
        input.trim()
    }
}

/**
 * Validates a UPI ID handle (must be username@handle, not email domain).
 */
private fun validateUpiId(input: String): Pair<Boolean, String> {
    val trimmed = input.trim()
    if (trimmed.isEmpty()) {
        return Pair(false, "Please enter a valid UPI ID.")
    }

    // Check if user accidentally entered an email
    val emailTLDs = setOf("com", "in", "org", "net", "edu", "gov", "ai", "co", "io", "co.in")
    val atIndex = trimmed.indexOf('@')
    if (atIndex != -1) {
        val domain = trimmed.substring(atIndex + 1).lowercase()
        if (domain.contains(".") || emailTLDs.any { domain == it || domain.endsWith(".$it") }) {
            return Pair(false, "Enter a valid UPI handle (e.g. name@okaxis or mobile@paytm), not an email address.")
        }
    }

    // Strict UPI ID format: username@bankhandle
    val upiRegex = Regex("^[a-zA-Z0-9._\\-]{3,50}@[a-zA-Z0-9]{2,30}$")
    if (!upiRegex.matches(trimmed)) {
        return Pair(false, "Invalid UPI ID format. Format must be username@handle (e.g. name@okaxis, 9876543210@paytm).")
    }

    if (UserSettingsStore.upiIds.contains(trimmed)) {
        return Pair(false, "This UPI ID is already registered.")
    }

    return Pair(true, "")
}
