package com.lomdi.dsih.ui.home

import android.widget.Toast
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.lomdi.dsih.R
import com.lomdi.dsih.data.model.ThreatLevel
import com.lomdi.dsih.data.source.DemoModeStore
import com.lomdi.dsih.domain.usecase.RiskManager
import com.lomdi.dsih.ui.dashboard.ReferenceGreen
import com.lomdi.dsih.ui.dashboard.ReferenceRed
import com.lomdi.dsih.ui.dashboard.ReferenceYellow

/**
 * High-level Home Screen featuring the dynamic Status Card, Circular Risk Score Gauge,
 * and Quick Action buttons adapting to Light/Dark theme.
 */
@Composable
fun HomeScreen(
    padding: PaddingValues,
    onNavigateToThreatDetails: () -> Unit,
    onNavigateToDashboard: () -> Unit
) {
    val context = LocalContext.current
    val threatLevel = RiskManager.getCurrentThreatLevel()

    // Compute Overall Risk Score (0-100%)
    val riskScore = remember(threatLevel, DemoModeStore.isDemoModeEnabled) {
        if (DemoModeStore.isDemoModeEnabled) {
            100
        } else {
            when (threatLevel) {
                ThreatLevel.CRITICAL -> 95
                ThreatLevel.HIGH -> 75
                ThreatLevel.MEDIUM -> 45
                ThreatLevel.LOW -> 12
            }
        }
    }

    LazyColumn(
        modifier = Modifier
            .padding(padding)
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp),
        contentPadding = PaddingValues(top = 16.dp, bottom = 40.dp)
    ) {
        // 1. Large Dynamic Status Card
        item {
            LargeStatusCard(
                threatLevel = threatLevel,
                onClick = onNavigateToThreatDetails
            )
        }

        // 2. Circular Risk Score Gauge
        item {
            OutlinedCard(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    Text(
                        text = stringResource(R.string.system_threat_level),
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )

                    CircularRiskGauge(
                        score = riskScore,
                        level = threatLevel
                    )
                }
            }
        }

        // 3. Quick Action Buttons
        item {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    text = stringResource(R.string.quick_actions_title),
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // Simulate Threat Quick Action
                    QuickActionButton(
                        title = stringResource(R.string.simulate_threat_toggle),
                        icon = if (DemoModeStore.isDemoModeEnabled) Icons.Default.Warning else Icons.Default.BugReport,
                        iconColor = if (DemoModeStore.isDemoModeEnabled) ReferenceRed else ReferenceYellow,
                        isActive = DemoModeStore.isDemoModeEnabled,
                        onClick = {
                            DemoModeStore.isDemoModeEnabled = !DemoModeStore.isDemoModeEnabled
                            val msg = if (DemoModeStore.isDemoModeEnabled) {
                                "Simulated Threat Activated (Score: 100%)"
                            } else {
                                "Simulated Threat Cleared"
                            }
                            Toast.makeText(context, msg, Toast.LENGTH_SHORT).show()
                        },
                        modifier = Modifier.weight(1f)
                    )

                    // Quick System Scan
                    QuickActionButton(
                        title = stringResource(R.string.quick_scan_title),
                        icon = Icons.Default.Refresh,
                        iconColor = ReferenceGreen,
                        isActive = false,
                        onClick = {
                            Toast.makeText(context, "System re-scan complete. All parameters safe.", Toast.LENGTH_SHORT).show()
                        },
                        modifier = Modifier.weight(1f)
                    )

                    // View Details / Parameters
                    QuickActionButton(
                        title = stringResource(R.string.parameters_title),
                        icon = Icons.Default.GridView,
                        iconColor = MaterialTheme.colorScheme.primary,
                        isActive = false,
                        onClick = onNavigateToDashboard,
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }
    }
}

/**
 * Large status hero card dynamically reflecting current ThreatLevel:
 * CRITICAL -> "Immediate Action Required" (Red)
 * HIGH -> "System At Risk" (Orange)
 * MEDIUM -> "Attention Needed" (Yellow)
 * LOW -> "System Secure" (Green)
 */
@Composable
fun LargeStatusCard(
    threatLevel: ThreatLevel,
    onClick: () -> Unit
) {
    val (titleText, subtitleText, color, icon) = when (threatLevel) {
        ThreatLevel.CRITICAL -> Quadruple(
            "Immediate Action Required",
            "Critical vulnerability or active interception detected",
            ReferenceRed,
            Icons.Default.GppBad
        )
        ThreatLevel.HIGH -> Quadruple(
            "System At Risk",
            "High risk activity or unverified session detected",
            Color(0xFFF97316), // Orange
            Icons.Default.Warning
        )
        ThreatLevel.MEDIUM -> Quadruple(
            "Attention Needed",
            "Unsaved call or permission caution flagged",
            ReferenceYellow,
            Icons.Default.Info
        )
        ThreatLevel.LOW -> Quadruple(
            stringResource(R.string.system_secure_title),
            stringResource(R.string.system_secure_subtitle),
            ReferenceGreen,
            Icons.Default.GppGood
        )
    }

    val bgColor = color.copy(alpha = 0.12f)

    OutlinedCard(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.outlinedCardColors(containerColor = bgColor),
        border = androidx.compose.foundation.BorderStroke(1.dp, color.copy(alpha = 0.3f))
    ) {
        Row(
            modifier = Modifier.padding(24.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = titleText,
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Black,
                    color = MaterialTheme.colorScheme.onSurface
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    text = subtitleText,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            val infiniteTransition = rememberInfiniteTransition(label = "pulse")
            val pulseScale by infiniteTransition.animateFloat(
                initialValue = 1f,
                targetValue = 1.15f,
                animationSpec = infiniteRepeatable(tween(1000), RepeatMode.Reverse),
                label = "scale"
            )

            Box(contentAlignment = Alignment.Center) {
                Surface(
                    modifier = Modifier
                        .size(64.dp)
                        .scale(pulseScale),
                    shape = CircleShape,
                    color = color.copy(alpha = 0.15f)
                ) {}
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = color,
                    modifier = Modifier.size(38.dp)
                )
            }
        }
    }
}

private data class Quadruple<A, B, C, D>(val first: A, val second: B, val third: C, val fourth: D)

/**
 * Circular progress gauge for the overall Risk Score.
 */
@Composable
fun CircularRiskGauge(
    score: Int,
    level: ThreatLevel
) {
    val targetProgress = (score.coerceIn(0, 100)) / 100f
    val animatedProgress by animateFloatAsState(
        targetValue = targetProgress,
        animationSpec = tween(durationMillis = 800, easing = FastOutSlowInEasing),
        label = "progress"
    )

    val color = when (level) {
        ThreatLevel.CRITICAL -> ReferenceRed
        ThreatLevel.HIGH -> Color(0xFFF97316)
        ThreatLevel.MEDIUM -> ReferenceYellow
        ThreatLevel.LOW -> ReferenceGreen
    }

    val trackColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.08f)

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier.size(180.dp)
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val strokeWidth = 14.dp.toPx()
            
            // Background Track Circle
            drawArc(
                color = trackColor,
                startAngle = 135f,
                sweepAngle = 270f,
                useCenter = false,
                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
            )

            // Foreground Progress Arc
            drawArc(
                color = color,
                startAngle = 135f,
                sweepAngle = 270f * animatedProgress,
                useCenter = false,
                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
            )
        }

        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "${(animatedProgress * 100).toInt()}%",
                fontSize = 32.sp,
                fontWeight = FontWeight.Black,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = stringResource(R.string.overall_risk_score),
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(Modifier.height(6.dp))

            Surface(
                color = color.copy(alpha = 0.15f),
                shape = RoundedCornerShape(20.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, color.copy(alpha = 0.3f))
            ) {
                Text(
                    text = level.name,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 2.dp),
                    color = color,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

/**
 * Quick Action Button component.
 */
@Composable
fun QuickActionButton(
    title: String,
    icon: ImageVector,
    iconColor: Color,
    isActive: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    OutlinedCard(
        modifier = modifier.clickable { onClick() },
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.outlinedCardColors(
            containerColor = if (isActive) iconColor.copy(alpha = 0.15f) else MaterialTheme.colorScheme.surface
        ),
        border = if (isActive) androidx.compose.foundation.BorderStroke(1.dp, iconColor) else CardDefaults.outlinedCardBorder()
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 16.dp, horizontal = 8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = title,
                tint = iconColor,
                modifier = Modifier.size(24.dp)
            )
            Spacer(Modifier.height(8.dp))
            Text(
                text = title,
                color = MaterialTheme.colorScheme.onSurface,
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                maxLines = 1
            )
        }
    }
}
