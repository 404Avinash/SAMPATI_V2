package com.lomdi.dsih.ui.security

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.BugReport
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
fun AccessibilityDetailsScreen(onBack: () -> Unit) {
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Accessibility Auditor") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        val trojans = AppSecurityStore.activeAccessibilityTrojans
        LazyColumn(
            modifier = Modifier.padding(padding).fillMaxSize().padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                StatusHeader(
                    title = if (trojans.isEmpty()) "System Shield: Active" else "Trojan Risk Detected",
                    subtitle = if (trojans.isEmpty()) "No malicious accessibility services found." else "\${trojans.size} non-system apps have full screen access.",
                    isError = trojans.isNotEmpty()
                )
            }
            item {
                SecurityInfoCard(
                    title = "Why this matters",
                    description = "Accessibility services can read your screen, intercept OTPs, and capture UPI PINs. Banking trojans often abuse this permission to steal funds. Fox audits all active services to ensure only trusted system apps are running."
                )
            }
            if (trojans.isNotEmpty()) {
                item {
                    Text("Flagged Applications", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                }
                items(trojans) { app ->
                    AppRiskItem(name = app, risk = "High: Screen Reading Active")
                }
            }
        }
    }
}

@Composable
fun StatusHeader(title: String, subtitle: String, isError: Boolean) {
    val color = if (isError) Color(0xFFB71C1C) else Color(0xFF388E3C)
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.1f))
    ) {
        Column(modifier = Modifier.padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Icon(Icons.Default.BugReport, null, tint = color, modifier = Modifier.size(48.dp))
            Spacer(modifier = Modifier.height(16.dp))
            Text(text = title, style = MaterialTheme.typography.headlineSmall, color = color, fontWeight = FontWeight.Black)
            Text(text = subtitle, style = MaterialTheme.typography.bodyMedium, color = color)
        }
    }
}

@Composable
fun SecurityInfoCard(title: String, description: String) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(text = title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Text(text = description, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

@Composable
fun AppRiskItem(name: String, risk: String) {
    ListItem(
        headlineContent = { Text(name, fontWeight = FontWeight.Bold) },
        supportingContent = { Text(risk, color = Color(0xFFB71C1C)) },
        leadingContent = { Icon(Icons.Default.BugReport, null, tint = Color(0xFFB71C1C)) },
        colors = ListItemDefaults.colors(containerColor = MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.3f))
    )
}
