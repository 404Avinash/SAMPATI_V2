package com.lomdi.dsih.ui.dashboard

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ScreenShare
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.lomdi.dsih.R
import com.lomdi.dsih.data.source.AppSecurityStore
import com.lomdi.dsih.data.source.CallStateStore
import com.lomdi.dsih.data.source.ClipboardStore
import com.lomdi.dsih.data.source.DeviceSecurityStore
import com.lomdi.dsih.data.source.RemoteAppStore

/**
 * Premium MD3 Dashboard Tab Screen displaying security categories inside OutlinedCard components
 * with clean ListItem parameter rows, distinct Material icons, and dynamic theme colors.
 */
@Composable
fun DashboardTabScreen(
    padding: PaddingValues,
    onNavigateToSmsTracker: () -> Unit,
    onNavigateToRemoteApps: () -> Unit,
    onNavigateToClipboard: () -> Unit,
    onNavigateToAccessibility: () -> Unit,
    onNavigateToTapjacking: () -> Unit,
    onNavigateToKeyboard: () -> Unit,
    onNavigateToCallSecurity: () -> Unit,
    onNavigateToDeviceIntegrity: () -> Unit,
    onNavigateToScreenShare: () -> Unit
) {
    LazyColumn(
        modifier = Modifier
            .padding(padding)
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        verticalArrangement = Arrangement.spacedBy(20.dp),
        contentPadding = PaddingValues(top = 16.dp, bottom = 40.dp)
    ) {
        // Dashboard Title Header
        item {
            Column {
                Text(
                    text = stringResource(R.string.security_dashboard_title),
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Black
                )
                Text(
                    text = stringResource(R.string.security_dashboard_subtitle),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        // 1. App & System Security Category
        item {
            CategoryCard(
                title = stringResource(R.string.category_app_system_security),
                categoryIcon = Icons.Default.Shield
            ) {
                // Clipboard Guard
                ParameterListItem(
                    title = stringResource(R.string.module_clipboard_guard),
                    subtitle = if (ClipboardStore.hasSensitiveData) stringResource(R.string.clipboard_intercept_desc) else "Monitors for payment handle swapping",
                    status = if (ClipboardStore.hasSensitiveData) stringResource(R.string.status_intercepted) else stringResource(R.string.status_secure),
                    statusColor = if (ClipboardStore.hasSensitiveData) ReferenceRed else ReferenceGreen,
                    statusIcon = if (ClipboardStore.hasSensitiveData) Icons.Default.Warning else Icons.Default.CheckCircle,
                    itemIcon = Icons.Default.ContentPaste,
                    onClick = onNavigateToClipboard
                )

                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.4f))

                // Overlay Detection
                ParameterListItem(
                    title = stringResource(R.string.module_overlay_detection),
                    subtitle = "Draw-over app tapjacking protection",
                    status = if (AppSecurityStore.activeOverlayApps.isEmpty()) stringResource(R.string.status_active) else stringResource(R.string.status_risk),
                    statusColor = if (AppSecurityStore.activeOverlayApps.isEmpty()) ReferenceYellow else ReferenceRed,
                    statusIcon = if (AppSecurityStore.activeOverlayApps.isEmpty()) Icons.Default.Visibility else Icons.Default.Warning,
                    itemIcon = Icons.Default.Layers,
                    onClick = onNavigateToTapjacking
                )

                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.4f))

                // Keyboard Auditor
                ParameterListItem(
                    title = stringResource(R.string.module_keyboard_auditor),
                    subtitle = "Audits active input method editor (IME)",
                    status = if (AppSecurityStore.isUntrustedKeyboard) stringResource(R.string.status_untrusted) else stringResource(R.string.status_trusted),
                    statusColor = if (AppSecurityStore.isUntrustedKeyboard) ReferenceRed else ReferenceGreen,
                    statusIcon = if (AppSecurityStore.isUntrustedKeyboard) Icons.Default.Warning else Icons.Default.CheckCircle,
                    itemIcon = Icons.Default.Keyboard,
                    onClick = onNavigateToKeyboard
                )

                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.4f))

                // Permission Monitor
                ParameterListItem(
                    title = stringResource(R.string.module_permission_monitor),
                    subtitle = "Accessibility & Trojan permission scan",
                    status = stringResource(R.string.status_secured),
                    statusColor = ReferenceGreen,
                    statusIcon = Icons.Default.CheckCircle,
                    itemIcon = Icons.Default.AdminPanelSettings,
                    onClick = onNavigateToAccessibility
                )

                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.4f))

                // App Sandbox Isolation
                ParameterListItem(
                    title = stringResource(R.string.module_app_sandbox),
                    subtitle = "Hardware-backed runtime isolation",
                    status = stringResource(R.string.status_active),
                    statusColor = ReferenceGreen,
                    statusIcon = Icons.Default.CheckCircle,
                    itemIcon = Icons.Default.Lock,
                    onClick = { }
                )
            }
        }

        // 2. Communication Security Category
        item {
            CategoryCard(
                title = stringResource(R.string.category_communication_security),
                categoryIcon = Icons.Default.ChatBubbleOutline
            ) {
                // SMS Guard
                ParameterListItem(
                    title = stringResource(R.string.module_sms_guard),
                    subtitle = "Phishing URL & SMS bait classification",
                    status = stringResource(R.string.status_0_suspicious),
                    statusColor = ReferenceGreen,
                    statusIcon = Icons.Default.CheckCircle,
                    itemIcon = Icons.Default.Sms,
                    onClick = onNavigateToSmsTracker
                )

                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.4f))

                // Call Monitor
                val isCallActive = CallStateStore.isActiveCall || CallStateStore.isVoipCallActive
                ParameterListItem(
                    title = stringResource(R.string.module_call_monitor),
                    subtitle = "PSTN & VoIP vishing call analysis",
                    status = if (isCallActive) stringResource(R.string.status_monitoring) else stringResource(R.string.status_idle),
                    statusColor = if (isCallActive) ReferenceYellow else ReferenceGreen,
                    statusIcon = if (isCallActive) Icons.Default.PhoneInTalk else Icons.Default.CheckCircle,
                    itemIcon = Icons.Default.PhoneInTalk,
                    onClick = onNavigateToCallSecurity
                )
            }
        }

        // 3. Real-Time Session Monitors Category
        item {
            CategoryCard(
                title = stringResource(R.string.category_session_monitors),
                categoryIcon = Icons.Default.WifiTethering
            ) {
                // Screen Share Detection
                ParameterListItem(
                    title = stringResource(R.string.module_screenshare_detection),
                    subtitle = "Virtual display casting detection",
                    status = if (DeviceSecurityStore.isActiveScreenShare) stringResource(R.string.status_active) else stringResource(R.string.status_none),
                    statusColor = if (DeviceSecurityStore.isActiveScreenShare) ReferenceRed else MaterialTheme.colorScheme.onSurfaceVariant,
                    statusIcon = if (DeviceSecurityStore.isActiveScreenShare) Icons.Default.Warning else Icons.Default.CheckCircle,
                    itemIcon = Icons.AutoMirrored.Filled.ScreenShare,
                    onClick = onNavigateToScreenShare
                )

                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.4f))

                // Remote Access
                ParameterListItem(
                    title = stringResource(R.string.module_remote_access),
                    subtitle = "Scans for AnyDesk, TeamViewer & VNC",
                    status = if (RemoteAppStore.hasRemoteApps) stringResource(R.string.status_threat) else stringResource(R.string.status_blocked),
                    statusColor = if (RemoteAppStore.hasRemoteApps) ReferenceRed else ReferenceGreen,
                    statusIcon = if (RemoteAppStore.hasRemoteApps) Icons.Default.Warning else Icons.Default.Block,
                    itemIcon = Icons.Default.PhonelinkLock,
                    onClick = onNavigateToRemoteApps
                )
            }
        }

        // 4. Device Integrity Category
        item {
            CategoryCard(
                title = stringResource(R.string.category_device_integrity),
                categoryIcon = Icons.Default.VerifiedUser
            ) {
                // Root & Jailbreak Scanner
                ParameterListItem(
                    title = stringResource(R.string.module_root_scanner),
                    subtitle = "Checks for su binaries & test-keys",
                    status = if (DeviceSecurityStore.isDeviceRooted) stringResource(R.string.status_rooted) else stringResource(R.string.status_intact),
                    statusColor = if (DeviceSecurityStore.isDeviceRooted) ReferenceRed else ReferenceGreen,
                    statusIcon = if (DeviceSecurityStore.isDeviceRooted) Icons.Default.Warning else Icons.Default.CheckCircle,
                    itemIcon = Icons.Default.Security,
                    onClick = onNavigateToDeviceIntegrity
                )
            }
        }
    }
}

/**
 * Premium MD3 Outlined Card wrapper for a major security category.
 */
@Composable
fun CategoryCard(
    title: String,
    categoryIcon: ImageVector,
    content: @Composable ColumnScope.() -> Unit
) {
    OutlinedCard(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.outlinedCardColors(
            containerColor = MaterialTheme.colorScheme.surface
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 6.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    color = MaterialTheme.colorScheme.primaryContainer,
                    shape = CircleShape,
                    modifier = Modifier.size(32.dp)
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Icon(
                            imageVector = categoryIcon,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onPrimaryContainer,
                            modifier = Modifier.size(18.dp)
                        )
                    }
                }
                Spacer(Modifier.width(12.dp))
                Text(
                    text = title,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurface
                )
            }

            HorizontalDivider(
                modifier = Modifier.padding(top = 8.dp, bottom = 4.dp),
                color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f)
            )

            content()
        }
    }
}

/**
 * Premium ListItem component for displaying an individual security parameter inside a category card.
 */
@Composable
fun ParameterListItem(
    title: String,
    subtitle: String? = null,
    status: String,
    statusColor: Color,
    statusIcon: ImageVector,
    itemIcon: ImageVector,
    onClick: () -> Unit
) {
    ListItem(
        headlineContent = {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.SemiBold,
                color = MaterialTheme.colorScheme.onSurface
            )
        },
        supportingContent = subtitle?.let {
            {
                Text(
                    text = it,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        },
        leadingContent = {
            Surface(
                color = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f),
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.size(36.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = itemIcon,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
        },
        trailingContent = {
            Surface(
                color = statusColor.copy(alpha = 0.12f),
                shape = RoundedCornerShape(20.dp),
                border = androidx.compose.foundation.BorderStroke(1.dp, statusColor.copy(alpha = 0.3f))
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(statusIcon, null, tint = statusColor, modifier = Modifier.size(12.dp))
                    Spacer(Modifier.width(6.dp))
                    Text(
                        text = status,
                        style = MaterialTheme.typography.labelSmall,
                        color = statusColor,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        },
        colors = ListItemDefaults.colors(
            containerColor = Color.Transparent
        ),
        modifier = Modifier.clickable { onClick() }
    )
}
