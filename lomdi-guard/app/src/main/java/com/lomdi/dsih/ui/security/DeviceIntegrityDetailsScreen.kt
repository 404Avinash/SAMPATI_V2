package com.lomdi.dsih.ui.security

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.GppMaybe
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.lomdi.dsih.data.source.DeviceSecurityStore

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DeviceIntegrityDetailsScreen(onBack: () -> Unit) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Device Integrity") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        val isRooted = DeviceSecurityStore.isDeviceRooted
        
        Column(
            modifier = Modifier.padding(padding).fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            IntegrityStatusHeader(
                title = if (!isRooted) "OS Environment: Intact" else "Critical: Root Detected",
                subtitle = if (!isRooted) "Your Android OS is verified as secure." else "Dangerous binaries or test-keys identified.",
                isError = isRooted
            )
            
            IntegrityInfoCard(
                title = "Root & Jailbreak Risk",
                description = "A rooted device bypasses Android's core security sandbox. This allows malware to read data from other apps, intercept PINs, and hide from standard antivirus tools. Fox recommends against using rooted devices for financial transactions."
            )
            
            if (isRooted) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = "🚨 CRITICAL: Root access detected. Your device integrity is compromised. All security protections may be bypassed by advanced malware.",
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onErrorContainer,
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

@Composable
private fun IntegrityStatusHeader(title: String, subtitle: String, isError: Boolean) {
    val color = if (isError) Color(0xFFB71C1C) else Color(0xFF388E3C)
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f))
    ) {
        Column(modifier = Modifier.padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(Icons.Default.GppMaybe, null, tint = color, modifier = Modifier.size(48.dp))
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = title, style = MaterialTheme.typography.headlineSmall, color = color, fontWeight = FontWeight.Black)
            Text(text = subtitle, style = MaterialTheme.typography.bodyMedium, color = color)
        }
    }
}

@Composable
private fun IntegrityInfoCard(title: String, description: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = description, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
