package com.lomdi.dsih.ui.security

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Layers
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
fun TapjackingDetailsScreen(onBack: () -> Unit) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Overlay & Tapjacking") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        val overlayApps = AppSecurityStore.activeOverlayApps
        LazyColumn(
            modifier = Modifier.padding(padding).fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                TapjackingStatusHeader(
                    title = if (overlayApps.isEmpty()) "System Intact" else "Overlay Risk Detected",
                    subtitle = if (overlayApps.isEmpty()) "No suspicious third-party overlays found." else "${overlayApps.size} apps can draw over other apps.",
                    isError = overlayApps.isNotEmpty()
                )
            }
            item {
                TapjackingInfoCard(
                    title = "Tapjacking Defense",
                    description = "Apps with 'Draw over other apps' permissions can create invisible overlays or fake UI elements. This allows them to trick you into clicking 'Pay' or 'Approve' without your knowledge. Fox identifies all non-system apps with this capability."
                )
            }
            if (overlayApps.isNotEmpty()) {
                item {
                    Text("Flagged Applications", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                }
                items(overlayApps) { app ->
                    ListItem(
                        headlineContent = { Text(app, fontWeight = FontWeight.Bold) },
                        supportingContent = { Text("Risk: UI Spoofing / Tapjacking") },
                        leadingContent = { Icon(Icons.Default.Layers, null, tint = Color(0xFFF57C00)) }
                    )
                }
            }
        }
    }
}

@Composable
private fun TapjackingStatusHeader(title: String, subtitle: String, isError: Boolean) {
    val color = if (isError) Color(0xFFF57C00) else Color(0xFF388E3C)
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f))
    ) {
        Column(modifier = Modifier.padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(Icons.Default.Layers, null, tint = color, modifier = Modifier.size(48.dp))
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = title, style = MaterialTheme.typography.headlineSmall, color = color, fontWeight = FontWeight.Black)
            Text(text = subtitle, style = MaterialTheme.typography.bodyMedium, color = color)
        }
    }
}

@Composable
private fun TapjackingInfoCard(title: String, description: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = description, style = MaterialTheme.typography.bodyMedium)
        }
    }
}
