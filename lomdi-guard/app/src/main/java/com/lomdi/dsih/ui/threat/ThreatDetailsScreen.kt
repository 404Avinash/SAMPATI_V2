package com.lomdi.dsih.ui.threat

import androidx.activity.compose.BackHandler
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.automirrored.filled.FactCheck
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.lomdi.dsih.R
import com.lomdi.dsih.data.model.ThreatLevel
import com.lomdi.dsih.data.source.ActivityLogStore
import com.lomdi.dsih.data.source.DemoModeStore
import com.lomdi.dsih.domain.usecase.RiskFactor
import com.lomdi.dsih.domain.usecase.RiskManager
import com.lomdi.dsih.ui.dashboard.ReferenceGreen
import com.lomdi.dsih.ui.dashboard.ReferenceRed
import com.lomdi.dsih.ui.dashboard.ReferenceYellow
import java.text.SimpleDateFormat
import java.util.Locale

/**
 * Data report for the Severity Analysis screen.
 */
data class SeverityReport(
    val headlineTitle: String,
    val subtitleDescription: String,
    val threatLevel: ThreatLevel,
    val riskScore: Int,
    val isHistoricalLog: Boolean = false,
    val logTimestampStr: String? = null,
    val factors: List<RiskFactor> = emptyList()
)

/**
 * Dynamic Material 3 Severity Analysis Screen / Report.
 * Automatically adapts colors, icons, text, and parameter breakdown based on live system state or historical log state.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ThreatDetailsScreen(
    logId: String? = null,
    onBack: () -> Unit
) {
    // Intercept system back gestures to always pop backstack properly
    BackHandler {
        onBack()
    }

    // Resolve Report State: Historical Log vs Live System State
    val report = remember(logId, DemoModeStore.isDemoModeEnabled) {
        if (logId != null) {
            val log = ActivityLogStore.logs.find { it.id == logId }
            if (log != null) {
                val timeFmt = SimpleDateFormat("MMM dd, yyyy - HH:mm:ss", Locale.getDefault())
                SeverityReport(
                    headlineTitle = log.title,
                    subtitleDescription = log.description,
                    threatLevel = log.level,
                    riskScore = log.score,
                    isHistoricalLog = true,
                    logTimestampStr = timeFmt.format(log.timestamp),
                    factors = listOf(
                        RiskFactor(
                            title = log.title,
                            contributionPercentage = log.score,
                            details = log.description,
                            evidence = "Logged Event #" + log.id.take(8)
                        )
                    )
                )
            } else {
                getLiveSystemReport()
            }
        } else {
            getLiveSystemReport()
        }
    }

    val themeColor = when (report.threatLevel) {
        ThreatLevel.CRITICAL -> ReferenceRed
        ThreatLevel.HIGH -> Color(0xFFF97316) // Orange
        ThreatLevel.MEDIUM -> ReferenceYellow
        ThreatLevel.LOW -> ReferenceGreen
    }

    val themeIcon = when (report.threatLevel) {
        ThreatLevel.CRITICAL -> Icons.Default.GppBad
        ThreatLevel.HIGH -> Icons.Default.Warning
        ThreatLevel.MEDIUM -> Icons.Default.Info
        ThreatLevel.LOW -> Icons.Default.GppGood
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Text(
                        text = "Severity Analysis Report",
                        fontWeight = FontWeight.Bold
                    ) 
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Back",
                            tint = MaterialTheme.colorScheme.onSurface
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                    titleContentColor = MaterialTheme.colorScheme.onSurface
                )
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .padding(horizontal = 20.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(20.dp),
            contentPadding = PaddingValues(top = 8.dp, bottom = 32.dp)
        ) {
            // Context Banner Header
            item {
                if (DemoModeStore.isDemoModeEnabled) {
                    OutlinedCard(
                        colors = CardDefaults.outlinedCardColors(
                            containerColor = MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.4f)
                        ),
                        border = androidx.compose.foundation.BorderStroke(1.dp, ReferenceRed),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = "⚠️ SIMULATED THREAT (MANUAL DEMO OVERRIDE)",
                            color = MaterialTheme.colorScheme.error,
                            modifier = Modifier
                                .padding(12.dp)
                                .fillMaxWidth(),
                            textAlign = TextAlign.Center,
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp
                        )
                    }
                } else if (report.isHistoricalLog) {
                    Surface(
                        color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f),
                        shape = RoundedCornerShape(20.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.3f))
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(Icons.Default.History, null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(16.dp))
                            Spacer(Modifier.width(8.dp))
                            Text(
                                text = "HISTORICAL AUDIT RECORD • ${report.logTimestampStr}",
                                color = MaterialTheme.colorScheme.primary,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }

            // Hero Status Card with Large Icon & Headline
            item {
                OutlinedCard(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.outlinedCardColors(
                        containerColor = themeColor.copy(alpha = 0.08f)
                    ),
                    border = androidx.compose.foundation.BorderStroke(1.dp, themeColor.copy(alpha = 0.25f))
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Surface(
                            color = themeColor.copy(alpha = 0.15f),
                            shape = CircleShape,
                            modifier = Modifier.size(72.dp)
                        ) {
                            Box(contentAlignment = Alignment.Center) {
                                Icon(
                                    imageVector = themeIcon,
                                    contentDescription = null,
                                    modifier = Modifier.size(42.dp),
                                    tint = themeColor
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(16.dp))

                        Text(
                            text = report.headlineTitle,
                            style = MaterialTheme.typography.titleLarge,
                            color = MaterialTheme.colorScheme.onSurface,
                            fontWeight = FontWeight.Black,
                            textAlign = TextAlign.Center
                        )

                        Spacer(modifier = Modifier.height(6.dp))

                        Text(
                            text = report.subtitleDescription,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            textAlign = TextAlign.Center
                        )
                    }
                }
            }

            // Large Circular Risk Score Gauge
            item {
                OutlinedCard(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(20.dp),
                    colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(20.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "Overall Audit Score",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )

                        Spacer(Modifier.height(16.dp))

                        CircularAuditScoreGauge(
                            score = report.riskScore,
                            color = themeColor,
                            levelLabel = report.threatLevel.name
                        )
                    }
                }
            }

            // Parameter Audit Breakdown Header
            item {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.AutoMirrored.Filled.FactCheck,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(Modifier.width(10.dp))
                    Text(
                        text = "Itemized Parameter Breakdown",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                }
            }

            // Parameter Audit Factors / Items
            if (report.factors.isEmpty()) {
                item {
                    OutlinedCard(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.outlinedCardColors(containerColor = MaterialTheme.colorScheme.surface)
                    ) {
                        Row(
                            modifier = Modifier.padding(20.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(Icons.Default.CheckCircle, null, tint = ReferenceGreen, modifier = Modifier.size(24.dp))
                            Spacer(Modifier.width(12.dp))
                            Column {
                                Text(
                                    text = "All Security Checks Cleared",
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                                Text(
                                    text = "SMS link heuristics, vishing call monitors, clipboard guard, and device integrity checked.",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }
            } else {
                items(report.factors) { factor ->
                    RiskFactorAuditCard(factor = factor, themeColor = themeColor)
                }
            }

            // Return Button
            item {
                Spacer(Modifier.height(8.dp))
                Button(
                    onClick = onBack,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, null, tint = MaterialTheme.colorScheme.onPrimary)
                    Spacer(Modifier.width(8.dp))
                    Text("RETURN", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onPrimary)
                }
            }
        }
    }
}

/**
 * Computes live system severity report from RiskManager.
 */
private fun getLiveSystemReport(): SeverityReport {
    val level = RiskManager.getCurrentThreatLevel()
    val factors = RiskManager.getRiskBreakdown()
    val rawScore = factors.sumOf { it.contributionPercentage }

    val score = when {
        DemoModeStore.isDemoModeEnabled -> 100
        level == ThreatLevel.CRITICAL -> 95.coerceAtLeast(rawScore)
        level == ThreatLevel.HIGH -> 75.coerceAtLeast(rawScore)
        level == ThreatLevel.MEDIUM -> 45.coerceAtLeast(rawScore)
        else -> 12
    }

    val (headline, subtitle) = when (level) {
        ThreatLevel.CRITICAL, ThreatLevel.HIGH -> Pair(
            "Unauthorized Access Blocked",
            "Fox Guard halted or flagged suspicious fraud indicators. Severity Coefficient: $score%"
        )
        ThreatLevel.MEDIUM -> Pair(
            "Security Caution Flagged",
            "Monitored caution signals detected during session. Severity Coefficient: $score%"
        )
        ThreatLevel.LOW -> Pair(
            "No Threats Detected",
            "All real-time fraud detection parameters are operating normally with zero active threats."
        )
    }

    return SeverityReport(
        headlineTitle = headline,
        subtitleDescription = subtitle,
        threatLevel = level,
        riskScore = score,
        isHistoricalLog = false,
        factors = factors
    )
}

/**
 * Circular Audit Score Gauge representation.
 */
@Composable
fun CircularAuditScoreGauge(
    score: Int,
    color: Color,
    levelLabel: String
) {
    val targetProgress = (score.coerceIn(0, 100)) / 100f
    val animatedProgress by animateFloatAsState(
        targetValue = targetProgress,
        animationSpec = tween(durationMillis = 800, easing = FastOutSlowInEasing),
        label = "progress"
    )

    val trackColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.08f)

    Box(
        contentAlignment = Alignment.Center,
        modifier = Modifier.size(160.dp)
    ) {
        Canvas(modifier = Modifier.fillMaxSize()) {
            val strokeWidth = 12.dp.toPx()

            drawArc(
                color = trackColor,
                startAngle = 135f,
                sweepAngle = 270f,
                useCenter = false,
                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
            )

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
                fontSize = 30.sp,
                fontWeight = FontWeight.Black,
                color = MaterialTheme.colorScheme.onSurface
            )
            Text(
                text = "RISK SCORE",
                fontSize = 10.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(Modifier.height(4.dp))

            Surface(
                color = color.copy(alpha = 0.15f),
                shape = RoundedCornerShape(20.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, color.copy(alpha = 0.3f))
            ) {
                Text(
                    text = levelLabel,
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                    color = color,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

/**
 * Itemized Risk Factor Audit Card for the breakdown list.
 */
@Composable
fun RiskFactorAuditCard(
    factor: RiskFactor,
    themeColor: Color
) {
    OutlinedCard(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.outlinedCardColors(
            containerColor = MaterialTheme.colorScheme.surface
        )
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = factor.title,
                    style = MaterialTheme.typography.bodyLarge,
                    fontWeight = FontWeight.Bold,
                    color = themeColor,
                    modifier = Modifier.weight(1f)
                )
                Spacer(Modifier.width(8.dp))
                Surface(
                    color = themeColor.copy(alpha = 0.15f),
                    shape = RoundedCornerShape(6.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, themeColor.copy(alpha = 0.3f))
                ) {
                    Text(
                        text = "+${factor.contributionPercentage}%",
                        color = themeColor,
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = factor.details,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            if (!factor.evidence.isNullOrEmpty()) {
                Spacer(modifier = Modifier.height(8.dp))
                Surface(
                    color = MaterialTheme.colorScheme.surfaceVariant,
                    shape = RoundedCornerShape(8.dp),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = "Evidence: ${factor.evidence}",
                        modifier = Modifier.padding(8.dp),
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.SemiBold,
                        color = themeColor
                    )
                }
            }

            Spacer(modifier = Modifier.height(10.dp))

            LinearProgressIndicator(
                progress = { (factor.contributionPercentage / 100f).coerceIn(0f, 1f) },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(4.dp),
                color = themeColor,
                trackColor = themeColor.copy(alpha = 0.1f)
            )
        }
    }
}
