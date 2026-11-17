package com.lomdi.dsih.ui.security

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Monitor
import androidx.compose.material.icons.filled.Warning
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
fun ScreenShareDetailsScreen(onBack: () -> Unit) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Screen Share Monitor") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        },
        containerColor = Color(0xFF0C0C0C)
    ) { padding ->
        val isActive = DeviceSecurityStore.isActiveScreenShare
        
        LazyColumn(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp)
        ) {
            item {
                ScreenStatusHeader(isActive)
            }

            item {
                ScreenSecurityInfoCard(
                    title = "Why is this a threat?",
                    description = "Remote scammers use screen casting and virtual displays to see your UPI PINs and banking credentials in real-time. Even if they don't have control of your device, seeing your screen allows them to steal sensitive data during a payment session."
                )
            }

            if (isActive) {
                item {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF2D1616)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Warning, null, tint = Color(0xFFF87171))
                            Spacer(modifier = Modifier.width(16.dp))
                            Text(
                                text = "CRITICAL: An active virtual display or screen mirror is detected. Scammers may be watching your screen.",
                                color = Color(0xFFF87171),
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ScreenStatusHeader(isActive: Boolean) {
    val color = if (isActive) Color(0xFFF87171) else Color(0xFF4ADE80)
    val bgColor = if (isActive) Color(0xFF2D1616) else Color(0xFF152A1C)
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = bgColor)
    ) {
        Column(
            modifier = Modifier.padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(Icons.Default.Monitor, null, tint = color, modifier = Modifier.size(48.dp))
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = if (isActive) "SCREEN BEING SHARED" else "PRIVACY SECURE",
                style = MaterialTheme.typography.headlineSmall,
                color = Color.White,
                fontWeight = FontWeight.Black
            )
            Text(
                text = if (isActive) "Active Virtual Display Detected" else "No active casts or recording found",
                style = MaterialTheme.typography.bodyMedium,
                color = Color.White.copy(alpha = 0.7f)
            )
        }
    }
}

@Composable
private fun ScreenSecurityInfoCard(title: String, description: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF141414))
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold, color = Color.White)
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = description, style = MaterialTheme.typography.bodyMedium, color = Color.LightGray)
        }
    }
}
