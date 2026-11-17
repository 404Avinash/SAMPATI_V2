package com.lomdi.dsih

import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.lifecycleScope
import androidx.navigation.NavController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.NavType
import androidx.navigation.navArgument
import com.lomdi.dsih.data.source.ClipboardStore
import com.lomdi.dsih.data.source.DataStoreManager
import com.lomdi.dsih.data.source.RemoteAppStore
import android.hardware.display.DisplayManager
import com.lomdi.dsih.data.source.DeviceSecurityStore
import com.lomdi.dsih.domain.usecase.ActiveDisplayScanner
import com.lomdi.dsih.domain.usecase.DeviceIntegrityScanner
import com.lomdi.dsih.domain.usecase.ClipboardGuard
import com.lomdi.dsih.domain.usecase.RemoteAppScanner
import com.lomdi.dsih.ui.dashboard.DashboardScreen
import com.lomdi.dsih.data.source.AppSecurityStore
import com.lomdi.dsih.domain.usecase.AccessibilityAuditor
import com.lomdi.dsih.domain.usecase.FastTextIntentAnalyzer
import com.lomdi.dsih.domain.usecase.KeyboardAuditor
import com.lomdi.dsih.domain.usecase.OverlayAuditor
import com.lomdi.dsih.domain.usecase.PermissionAuditor
import com.lomdi.dsih.domain.usecase.NetworkSecurityScanner
import com.lomdi.dsih.domain.usecase.VaultScanner
import com.lomdi.dsih.ui.details.ClipboardDetailsScreen
import com.lomdi.dsih.ui.details.RemoteAppsDetailsScreen
import com.lomdi.dsih.ui.security.AccessibilityDetailsScreen
import com.lomdi.dsih.ui.security.CallSecurityDetailsScreen
import com.lomdi.dsih.ui.security.DeviceIntegrityDetailsScreen
import com.lomdi.dsih.ui.security.KeyboardDetailsScreen
import com.lomdi.dsih.ui.security.ScreenShareDetailsScreen
import com.lomdi.dsih.ui.security.TapjackingDetailsScreen
import com.lomdi.dsih.ui.onboarding.OnboardingScreen
import com.lomdi.dsih.ui.sms.SmsTrackerScreen
import com.lomdi.dsih.ui.sms.SmsThreatDetailsScreen
import com.lomdi.dsih.data.source.UserSettingsStore
import com.lomdi.dsih.ui.threat.ThreatDetailsScreen
import com.lomdi.dsih.ui.theme.LomdiTheme
import androidx.appcompat.app.AppCompatActivity
import kotlinx.coroutines.launch
import androidx.core.app.NotificationManagerCompat

class MainActivity : AppCompatActivity() {
    
    private lateinit var dataStoreManager: DataStoreManager
    private var navController: NavController? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        dataStoreManager = DataStoreManager(this)
        loadUserSettings()
        setupSecurityMonitors()
        setupIntegrityMonitors()
        runAppExploitAudit()
        FastTextIntentAnalyzer.init(this) // Load ML model from assets

        setContent {
            LomdiTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val isFirstLaunch by dataStoreManager.isFirstLaunch.collectAsState(initial = null)
                    
                    if (isFirstLaunch != null) {
                        val currentNavController = rememberNavController()
                        navController = currentNavController

                        MainContent(
                            navController = currentNavController,
                            startDestination = if (isFirstLaunch == true) "onboarding" else "dashboard",
                            onOnboardingFinished = {
                                lifecycleScope.launch {
                                    dataStoreManager.setFirstLaunchCompleted()
                                }
                            }
                        )
                        
                        LaunchedEffect(intent) {
                            handleIntent(intent)
                        }
                    }
                }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
    }

    private fun handleIntent(intent: Intent?) {
        val target = intent?.getStringExtra("navigate_to")
        if (target == "threat_details") {
            NotificationManagerCompat.from(this).cancel(101)
            navController?.navigate("threat_details") {
                launchSingleTop = true
            }
        }
    }

    private fun loadUserSettings() {
        lifecycleScope.launch {
            dataStoreManager.phoneNumber.collect { phone ->
                UserSettingsStore.setPhone(phone)
            }
        }
        lifecycleScope.launch {
            dataStoreManager.upiIds.collect { upis ->
                UserSettingsStore.setUpiList(upis)
            }
        }
        lifecycleScope.launch {
            dataStoreManager.themeMode.collect { modeStr ->
                com.lomdi.dsih.data.source.ThemeStore.themeMode = try {
                    com.lomdi.dsih.data.source.ThemeMode.valueOf(modeStr)
                } catch (e: Exception) {
                    com.lomdi.dsih.data.source.ThemeMode.SYSTEM
                }
            }
        }
    }

    private fun setupSecurityMonitors() {
        val detected = RemoteAppScanner.scanInstalledApps(this)
        RemoteAppStore.detectedApps.clear()
        RemoteAppStore.detectedApps.addAll(detected)
        RemoteAppStore.hasRemoteApps = detected.isNotEmpty()

        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
        clipboard.addPrimaryClipChangedListener {
            val clipData = clipboard.primaryClip
            if (clipData != null && clipData.itemCount > 0) {
                val text = clipData.getItemAt(0).text?.toString() ?: ""
                val upi = ClipboardGuard.extractUpi(text)
                val url = ClipboardGuard.extractUrl(text)
                ClipboardStore.lastCopiedUpi = upi
                ClipboardStore.lastCopiedUrl = url
                ClipboardStore.hasSensitiveData = upi != null || url != null
            }
        }
    }

    private fun setupIntegrityMonitors() {
        // 1. Root Check
        DeviceSecurityStore.isDeviceRooted = DeviceIntegrityScanner.isDeviceRooted()

        // 2. Initial Screen Share Check
        DeviceSecurityStore.isActiveScreenShare = ActiveDisplayScanner.isScreenBeingShared(this)

        // 3. Register Display Listener for real-time tracking
        val dm = getSystemService(Context.DISPLAY_SERVICE) as DisplayManager
        dm.registerDisplayListener(object : DisplayManager.DisplayListener {
            override fun onDisplayAdded(displayId: Int) {
                DeviceSecurityStore.isActiveScreenShare = ActiveDisplayScanner.isScreenBeingShared(this@MainActivity)
            }
            override fun onDisplayRemoved(displayId: Int) {
                DeviceSecurityStore.isActiveScreenShare = ActiveDisplayScanner.isScreenBeingShared(this@MainActivity)
            }
            override fun onDisplayChanged(displayId: Int) {
                DeviceSecurityStore.isActiveScreenShare = ActiveDisplayScanner.isScreenBeingShared(this@MainActivity)
            }
        }, null)
    }

    private fun runAppExploitAudit() {
        // 1. Accessibility Auditor
        val accessibilityApps = AccessibilityAuditor.getSuspiciousAccessibilityApps(this)
        AppSecurityStore.activeAccessibilityTrojans.clear()
        AppSecurityStore.activeAccessibilityTrojans.addAll(accessibilityApps)

        // 2. Overlay Auditor
        val overlayApps = OverlayAuditor.getSuspiciousOverlayApps(this)
        AppSecurityStore.activeOverlayApps.clear()
        AppSecurityStore.activeOverlayApps.addAll(overlayApps)

        // 3. Keyboard Auditor
        val (isUntrusted, pkg) = KeyboardAuditor.isUntrustedKeyboardActive(this)
        AppSecurityStore.isUntrustedKeyboard = isUntrusted
        AppSecurityStore.activeKeyboardPackage = pkg

        // 4. Risky Permission combinations
        val riskyApps = PermissionAuditor.getRiskyPermissionApps(this)
        AppSecurityStore.riskyPermissionApps.clear()
        AppSecurityStore.riskyPermissionApps.addAll(riskyApps.map { it.name })

        // 5. Network Scan
        val netStatus = NetworkSecurityScanner.scanNetwork(this)
        AppSecurityStore.isVpnActive = netStatus.isVpnActive
        AppSecurityStore.networkType = netStatus.connectionType

        // 6. Vault Scan
        val vaultStatus = VaultScanner.checkVaultStatus(this)
        AppSecurityStore.isDeviceEncrypted = vaultStatus.isEncrypted
        AppSecurityStore.vaultStatus = vaultStatus.storageStatus
    }
}

@Composable
fun MainContent(
    navController: androidx.navigation.NavHostController,
    startDestination: String,
    onOnboardingFinished: () -> Unit
) {
    NavHost(navController = navController, startDestination = startDestination) {
        composable("onboarding") {
            OnboardingScreen(
                onFinished = {
                    onOnboardingFinished()
                    navController.navigate("dashboard") {
                        popUpTo("onboarding") { inclusive = true }
                    }
                }
            )
        }
        composable("dashboard") {
            DashboardScreen(
                onNavigateToSmsTracker = { navController.navigate("sms_tracker") },
                onNavigateToRemoteApps = { navController.navigate("remote_apps_details") },
                onNavigateToClipboard = { navController.navigate("clipboard_details") },
                onNavigateToThreatDetails = { logId -> 
                    if (logId != null) {
                        navController.navigate("threat_details?logId=$logId")
                    } else {
                        navController.navigate("threat_details")
                    }
                },
                onNavigateToAccessibility = { navController.navigate("accessibility_details") },
                onNavigateToTapjacking = { navController.navigate("tapjacking_details") },
                onNavigateToKeyboard = { navController.navigate("keyboard_details") },
                onNavigateToCallSecurity = { navController.navigate("call_security_details") },
                onNavigateToDeviceIntegrity = { navController.navigate("device_integrity_details") },
                onNavigateToScreenShare = { navController.navigate("screen_share_details") }
            )
        }
        composable("sms_tracker") {
            SmsTrackerScreen(
                onBack = { navController.popBackStack() },
                onNavigateToDetails = { id ->
                    navController.navigate("sms_threat_details/$id")
                }
            )
        }
        composable(
            route = "sms_threat_details/{smsId}",
            arguments = listOf(navArgument("smsId") { type = NavType.LongType })
        ) { backStackEntry ->
            val smsId = backStackEntry.arguments?.getLong("smsId")
            val smsMessage = SmsStore.messages.find { it.id == smsId }
            if (smsMessage != null) {
                SmsThreatDetailsScreen(
                    message = smsMessage,
                    onBack = { navController.popBackStack() }
                )
            }
        }
        composable("remote_apps_details") {
            RemoteAppsDetailsScreen(onBack = { navController.popBackStack() })
        }
        composable("clipboard_details") {
            ClipboardDetailsScreen(onBack = { navController.popBackStack() })
        }
        composable("accessibility_details") {
            AccessibilityDetailsScreen(onBack = { navController.popBackStack() })
        }
        composable("tapjacking_details") {
            TapjackingDetailsScreen(onBack = { navController.popBackStack() })
        }
        composable("keyboard_details") {
            KeyboardDetailsScreen(onBack = { navController.popBackStack() })
        }
        composable("call_security_details") {
            CallSecurityDetailsScreen(onBack = { navController.popBackStack() })
        }
        composable("device_integrity_details") {
            DeviceIntegrityDetailsScreen(onBack = { navController.popBackStack() })
        }
        composable("screen_share_details") {
            ScreenShareDetailsScreen(onBack = { navController.popBackStack() })
        }
        composable(
            route = "threat_details?logId={logId}",
            arguments = listOf(navArgument("logId") {
                type = NavType.StringType
                nullable = true
                defaultValue = null
            })
        ) { backStackEntry ->
            val logId = backStackEntry.arguments?.getString("logId")
            ThreatDetailsScreen(
                logId = logId,
                onBack = { navController.popBackStack() }
            )
        }
    }
}
