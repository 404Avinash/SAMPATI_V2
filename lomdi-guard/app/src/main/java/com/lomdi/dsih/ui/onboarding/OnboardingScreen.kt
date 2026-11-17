package com.lomdi.dsih.ui.onboarding

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.text.TextUtils
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import com.lomdi.dsih.LomdiAccessibilityService
import kotlinx.coroutines.launch

@Composable
fun OnboardingScreen(
    onFinished: () -> Unit
) {
    val pagerState = rememberPagerState(pageCount = { 3 })
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    // Permission States
    var postNotificationsGranted by remember { mutableStateOf(checkPermission(context, Manifest.permission.POST_NOTIFICATIONS)) }
    var phoneStateGranted by remember { mutableStateOf(checkPermission(context, Manifest.permission.READ_PHONE_STATE)) }
    var callLogGranted by remember { mutableStateOf(checkPermission(context, Manifest.permission.READ_CALL_LOG)) }
    var contactsGranted by remember { mutableStateOf(checkPermission(context, Manifest.permission.READ_CONTACTS)) }
    var smsGranted by remember { mutableStateOf(checkPermission(context, Manifest.permission.RECEIVE_SMS)) }
    var accessibilityEnabled by remember { mutableStateOf(isAccessibilityServiceEnabled(context, LomdiAccessibilityService::class.java)) }
    
    val requiredGranted = (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU || postNotificationsGranted) &&
            phoneStateGranted && callLogGranted && contactsGranted && smsGranted && accessibilityEnabled

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions(),
        onResult = { result ->
            postNotificationsGranted = result[Manifest.permission.POST_NOTIFICATIONS] ?: postNotificationsGranted
            phoneStateGranted = result[Manifest.permission.READ_PHONE_STATE] ?: phoneStateGranted
            callLogGranted = result[Manifest.permission.READ_CALL_LOG] ?: callLogGranted
            contactsGranted = result[Manifest.permission.READ_CONTACTS] ?: contactsGranted
            smsGranted = result[Manifest.permission.RECEIVE_SMS] ?: smsGranted
        }
    )

    // Re-check on resume
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                postNotificationsGranted = checkPermission(context, Manifest.permission.POST_NOTIFICATIONS)
                phoneStateGranted = checkPermission(context, Manifest.permission.READ_PHONE_STATE)
                callLogGranted = checkPermission(context, Manifest.permission.READ_CALL_LOG)
                contactsGranted = checkPermission(context, Manifest.permission.READ_CONTACTS)
                smsGranted = checkPermission(context, Manifest.permission.RECEIVE_SMS)
                accessibilityEnabled = isAccessibilityServiceEnabled(context, LomdiAccessibilityService::class.java)
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    Scaffold { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
        ) {
            HorizontalPager(
                state = pagerState,
                modifier = Modifier.weight(1f)
            ) { page ->
                when (page) {
                    0 -> OnboardingPage(
                        title = "Welcome to Fox",
                        description = "Our mission is to stop UPI fraud before it happens, protecting your hard-earned money in real-time.",
                        icon = Icons.Default.Shield
                    )
                    1 -> OnboardingPage(
                        title = "The Shield",
                        description = "Fox requires core permissions to monitor for scammers and malicious SMS content.",
                        icon = Icons.Default.Security,
                        action = {
                            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                PermissionItem("Notifications", postNotificationsGranted)
                                PermissionItem("Phone & Calls", phoneStateGranted && callLogGranted)
                                PermissionItem("Contacts", contactsGranted)
                                PermissionItem("SMS Monitoring", smsGranted)
                                
                                Button(
                                    modifier = Modifier.fillMaxWidth(),
                                    onClick = { 
                                        val perms = mutableListOf(
                                            Manifest.permission.READ_PHONE_STATE,
                                            Manifest.permission.READ_CALL_LOG,
                                            Manifest.permission.READ_CONTACTS,
                                            Manifest.permission.RECEIVE_SMS
                                        ).apply {
                                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                                                add(Manifest.permission.POST_NOTIFICATIONS)
                                            }
                                        }.toTypedArray()
                                        launcher.launch(perms) 
                                    }
                                ) {
                                    Text("Grant Core Permissions")
                                }
                            }
                        }
                    )
                    2 -> OnboardingPage(
                        title = "Real-Time Protection",
                        description = "Enable Accessibility to block fraudulent transactions the moment they are detected.",
                        icon = Icons.Default.Warning,
                        action = {
                            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                PermissionItem("Accessibility Service", accessibilityEnabled)
                                Spacer(modifier = Modifier.height(8.dp))
                                Button(
                                    modifier = Modifier.fillMaxWidth(),
                                    onClick = { context.startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)) }
                                ) {
                                    Text("Enable Fox Guard")
                                }
                            }
                        }
                    )
                }
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Page Indicator
                Row {
                    repeat(3) { index ->
                        val color = if (pagerState.currentPage == index) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant
                        Surface(
                            modifier = Modifier.size(8.dp).padding(horizontal = 2.dp),
                            shape = androidx.compose.foundation.shape.CircleShape,
                            color = color
                        ) {}
                    }
                }

                if (pagerState.currentPage < 2) {
                    IconButton(onClick = {
                        scope.launch { pagerState.animateScrollToPage(pagerState.currentPage + 1) }
                    }) {
                        Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = "Next")
                    }
                } else {
                    Button(
                        onClick = onFinished,
                        enabled = requiredGranted
                    ) {
                        Text("Finish Setup")
                    }
                }
            }
        }
    }
}

@Composable
fun PermissionItem(label: String, isGranted: Boolean) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(text = label, style = MaterialTheme.typography.bodyMedium)
        if (isGranted) {
            Icon(Icons.Default.CheckCircle, contentDescription = "Granted", tint = Color(0xFF4CAF50))
        } else {
            Text(text = "Missing", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.error)
        }
    }
}

private fun checkPermission(context: Context, permission: String): Boolean {
    if (permission == Manifest.permission.POST_NOTIFICATIONS && Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return true
    return ContextCompat.checkSelfPermission(context, permission) == PackageManager.PERMISSION_GRANTED
}

private fun isAccessibilityServiceEnabled(context: Context, service: Class<*>): Boolean {
    val expectedComponentName = android.content.ComponentName(context, service)
    val enabledServices = Settings.Secure.getString(context.contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES)
    if (enabledServices == null) return false
    val colonSplitter = TextUtils.SimpleStringSplitter(':')
    colonSplitter.setString(enabledServices)
    while (colonSplitter.hasNext()) {
        val componentName = colonSplitter.next()
        if (componentName.equals(expectedComponentName.flattenToString(), ignoreCase = true)) {
            return true
        }
    }
    return false
}

@Composable
fun OnboardingPage(
    title: String,
    description: String,
    icon: ImageVector,
    action: @Composable (() -> Unit)? = null
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(100.dp),
            tint = MaterialTheme.colorScheme.primary
        )
        Spacer(modifier = Modifier.height(24.dp))
        Text(
            text = title,
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
            text = description,
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center
        )
        if (action != null) {
            Spacer(modifier = Modifier.height(32.dp))
            action()
        }
    }
}
