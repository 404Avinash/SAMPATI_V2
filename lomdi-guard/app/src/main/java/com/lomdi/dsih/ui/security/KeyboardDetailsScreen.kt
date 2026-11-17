package com.lomdi.dsih.ui.security

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Keyboard
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.lomdi.dsih.data.source.AppSecurityStore

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun KeyboardDetailsScreen(onBack: () -> Unit) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Keyboard Auditor") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        val isUntrusted = AppSecurityStore.isUntrustedKeyboard
        val keyboard = AppSecurityStore.activeKeyboardPackage ?: "Unknown"
        
        Column(
            modifier = Modifier.padding(padding).fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            KeyboardStatusHeader(
                title = if (!isUntrusted) "Keyboard Secure" else "Untrusted IME Active",
                subtitle = "Active: $keyboard",
                isError = isUntrusted
            )
            
            KeyboardInfoCard(
                title = "Keylogger Protection",
                description = "Your keyboard has access to every character you type, including passwords and UPI PINs. Fox ensures you are using a trusted system keyboard (like Gboard or Samsung Keyboard) to prevent your keystrokes from being exfiltrated to malicious servers."
            )
            
            if (isUntrusted) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = "⚠️ ACTION REQUIRED: You are using a third-party keyboard that has not been verified. We recommend switching to a system-default keyboard for financial transactions.",
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onErrorContainer,
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
            }
        }
    }
}

@Composable
private fun KeyboardStatusHeader(title: String, subtitle: String, isError: Boolean) {
    val color = if (isError) Color(0xFFFBC02D) else Color(0xFF388E3C)
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f))
    ) {
        Column(modifier = Modifier.padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(Icons.Default.Keyboard, null, tint = color, modifier = Modifier.size(48.dp))
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = title, style = MaterialTheme.typography.headlineSmall, color = color, fontWeight = FontWeight.Black)
            Text(text = subtitle, style = MaterialTheme.typography.bodyMedium, color = color)
        }
    }
}

@Composable
private fun KeyboardInfoCard(title: String, description: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = description, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
