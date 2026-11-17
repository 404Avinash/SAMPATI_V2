package com.lomdi.dsih.ui.logs

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.lomdi.dsih.R
import com.lomdi.dsih.data.model.ActivityLog
import com.lomdi.dsih.data.model.ThreatLevel
import com.lomdi.dsih.data.source.ActivityLogStore
import com.lomdi.dsih.ui.dashboard.ReferenceGreen
import com.lomdi.dsih.ui.dashboard.ReferenceRed
import com.lomdi.dsih.ui.dashboard.ReferenceYellow
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale

/**
 * Logs Screen displaying a list of ActivityLog data classes grouped by date.
 * Features a single subtle eye icon to toggle dummy logs on and off.
 */
@Composable
fun LogsScreen(
    padding: PaddingValues,
    onNavigateToThreatDetails: (String?) -> Unit
) {
    val visibleLogs = ActivityLogStore.visibleLogs

    // Group activity logs by date header
    val groupedLogs = remember(visibleLogs.size, visibleLogs, ActivityLogStore.showDummyData) {
        visibleLogs.groupBy { formatDateGroup(it.timestamp) }
    }

    Column(
        modifier = Modifier
            .padding(padding)
            .fillMaxSize()
            .padding(horizontal = 16.dp)
    ) {
        // Top Header & Single Subtle Eye Toggle Action
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = 16.dp, bottom = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = stringResource(R.string.activity_logs_title),
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Black
                )
                Text(
                    text = stringResource(R.string.activity_logs_subtitle),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            // Single discrete eye icon button to hide/show dummy logs
            IconButton(
                onClick = {
                    ActivityLogStore.showDummyData = !ActivityLogStore.showDummyData
                },
                modifier = Modifier.size(36.dp)
            ) {
                Icon(
                    imageVector = if (ActivityLogStore.showDummyData) Icons.Default.Visibility else Icons.Default.VisibilityOff,
                    contentDescription = "Toggle Demo Logs",
                    tint = if (ActivityLogStore.showDummyData) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.size(20.dp)
                )
            }
        }

        if (visibleLogs.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Icon(
                        imageVector = Icons.Default.Shield,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(48.dp)
                    )
                    Spacer(Modifier.height(12.dp))
                    Text(
                        text = stringResource(R.string.no_logs_recorded),
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(16.dp),
                contentPadding = PaddingValues(bottom = 32.dp)
            ) {
                groupedLogs.forEach { (dateGroup, logsInGroup) ->
                    // Date Group Header
                    item(key = "header_$dateGroup") {
                        Surface(
                            color = MaterialTheme.colorScheme.surfaceVariant,
                            shape = RoundedCornerShape(8.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp)
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    text = dateGroup,
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary
                                )
                                Text(
                                    text = "${logsInGroup.size} Event${if (logsInGroup.size > 1) "s" else ""}",
                                    fontSize = 11.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }

                    // Log Items for this date group
                    items(
                        items = logsInGroup,
                        key = { log -> log.id }
                    ) { log ->
                        ActivityLogCard(
                            log = log,
                            onClick = { onNavigateToThreatDetails(log.id) }
                        )
                    }
                }
            }
        }
    }
}

/**
 * Styled Card for displaying an individual ActivityLog item.
 */
@Composable
fun ActivityLogCard(
    log: ActivityLog,
    onClick: () -> Unit
) {
    val badgeColor = when (log.level) {
        ThreatLevel.CRITICAL, ThreatLevel.HIGH -> ReferenceRed
        ThreatLevel.MEDIUM -> ReferenceYellow
        ThreatLevel.LOW -> ReferenceGreen
    }

    val timeFormat = remember { SimpleDateFormat("HH:mm:ss", Locale.getDefault()) }

    OutlinedCard(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface),
        border = androidx.compose.foundation.BorderStroke(1.dp, badgeColor.copy(alpha = 0.3f))
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            // Top Row: Title, Threat Badge & Time
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(
                        imageVector = if (log.level == ThreatLevel.LOW) Icons.Default.Shield else Icons.Default.Warning,
                        contentDescription = null,
                        tint = badgeColor,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(Modifier.width(10.dp))
                    Text(
                        text = log.title,
                        color = MaterialTheme.colorScheme.onSurface,
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp
                    )
                }

                // Threat Level Badge Pill
                Surface(
                    color = badgeColor.copy(alpha = 0.15f),
                    shape = RoundedCornerShape(20.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, badgeColor.copy(alpha = 0.4f))
                ) {
                    Text(
                        text = log.level.name,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                        color = badgeColor,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            // Description of intercepted event
            Text(
                text = log.description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            // Bottom Info Row: Timestamp & Score
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = stringResource(R.string.lbl_time, timeFormat.format(log.timestamp)),
                    fontSize = 11.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = stringResource(R.string.lbl_risk_score, log.score.toString()),
                    fontSize = 11.sp,
                    color = badgeColor,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

/**
 * Formats a Date into a date group header string (e.g., "Today", "Yesterday", "September 05, 2026").
 */
private fun formatDateGroup(date: Date): String {
    val now = Calendar.getInstance()
    val target = Calendar.getInstance().apply { time = date }

    val isSameYear = now.get(Calendar.YEAR) == target.get(Calendar.YEAR)
    val dayDiff = now.get(Calendar.DAY_OF_YEAR) - target.get(Calendar.DAY_OF_YEAR)

    return when {
        isSameYear && dayDiff == 0 -> "Today"
        isSameYear && dayDiff == 1 -> "Yesterday"
        else -> SimpleDateFormat("MMMM dd, yyyy", Locale.getDefault()).format(date)
    }
}
