package com.lomdi.dsih.ui.sms

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.lomdi.dsih.data.model.SmsMessage

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SmsThreatDetailsScreen(
    message: SmsMessage,
    onBack: () -> Unit
) {
    val result = message.analysisResult

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("SMS Threat Analysis") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item {
                ThreatHeader(message)
            }

            item {
                Text(
                    text = "Threat Analysis Breakdown",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
            }

            item {
                AnalysisCard(
                    title = "Sender Verification",
                    description = result.senderRisk,
                    icon = Icons.Default.Info,
                    color = if (result.senderRisk.contains("unverified")) Color(0xFFB71C1C) else Color(0xFF388E3C)
                )
            }

            item {
                AnalysisCard(
                    title = "Link Analysis",
                    description = result.linkRisk,
                    icon = Icons.Default.Warning,
                    color = if (message.extractedLinks.isNotEmpty()) Color(0xFFB71C1C) else Color(0xFF388E3C)
                )
            }

            item {
                AnalysisCard(
                    title = "Language & Intent",
                    description = result.contentRisk,
                    icon = Icons.Default.Info,
                    color = if (result.requiresEdgeAi) Color(0xFFB71C1C) else Color(0xFFFBC02D)
                )
            }

            item {
                if (result.requiresEdgeAi) {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiaryContainer),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.Info, null)
                            Spacer(modifier = Modifier.width(12.dp))
                            Text(
                                text = "Edge AI was triggered to evaluate this message due to high-risk patterns.",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ThreatHeader(message: SmsMessage) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (message.riskScore > 60) Color(0xFFB71C1C) else Color(0xFFFBC02D)
        )
    ) {
        Column(
            modifier = Modifier.padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Severity Coefficient",
                color = Color.White,
                style = MaterialTheme.typography.labelMedium
            )
            Text(
                text = "${message.riskScore}%",
                color = Color.White,
                style = MaterialTheme.typography.displayMedium,
                fontWeight = FontWeight.Black
            )
            Text(
                text = message.threatLevel.label,
                color = Color.White,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
fun AnalysisCard(title: String, description: String, icon: ImageVector, color: Color) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(modifier = Modifier.padding(16.dp)) {
            Icon(icon, null, tint = color, modifier = Modifier.size(32.dp))
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(text = title, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(4.dp))
                Text(text = description, style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}
