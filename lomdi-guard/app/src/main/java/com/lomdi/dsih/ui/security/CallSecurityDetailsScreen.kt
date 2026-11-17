package com.lomdi.dsih.ui.security

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.lomdi.dsih.data.source.CallStateStore

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CallSecurityDetailsScreen(onBack: () -> Unit) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Communication Security") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        val isCallActive = CallStateStore.isActiveCall || CallStateStore.isVoipCallActive
        val isUnsaved = CallStateStore.isUnsavedNumber || CallStateStore.isUnsavedVoipCaller
        val activeNumber = CallStateStore.activeNumber ?: CallStateStore.voipCallerName ?: "None"
        
        Column(
            modifier = Modifier.padding(padding).fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            CallStatusHeader(
                title = if (!isCallActive) "No Active Threats" else if (isUnsaved) "Scam Risk: Unsaved Call" else "Active Call: Verified",
                subtitle = "Monitored: $activeNumber",
                isError = isCallActive && isUnsaved
            )
            
            CallInfoCard(
                title = "Vishing Protection",
                description = "Fraudsters often stay on a live call while instructing victims to perform UPI transactions. Fox monitors both standard (PSTN) and VoIP (WhatsApp/Telegram) calls to detect when you are communicating with an unsaved number during a payment session."
            )
            
            if (isCallActive && isUnsaved) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = "⚠️ HIGH RISK: You are currently on a call with a number not in your contacts. This is a common pattern in Vishing frauds. Be extremely cautious.",
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
private fun CallStatusHeader(title: String, subtitle: String, isError: Boolean) {
    val color = if (isError) Color(0xFFB71C1C) else Color(0xFF388E3C)
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f))
    ) {
        Column(modifier = Modifier.padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(Icons.Default.Phone, null, tint = color, modifier = Modifier.size(48.dp))
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = title, style = MaterialTheme.typography.headlineSmall, color = color, fontWeight = FontWeight.Black)
            Text(text = subtitle, style = MaterialTheme.typography.bodyMedium, color = color)
        }
    }
}

@Composable
private fun CallInfoCard(title: String, description: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = description, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
