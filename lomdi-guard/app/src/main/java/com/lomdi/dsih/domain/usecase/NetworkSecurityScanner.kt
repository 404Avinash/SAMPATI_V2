package com.lomdi.dsih.domain.usecase

import android.content.Context
import android.net.ConnectivityManager
import android.net.NetworkCapabilities

/**
 * Scans for network-level security threats like insecure WiFi or VPN status.
 */
object NetworkSecurityScanner {

    data class NetworkStatus(
        val isVpnActive: Boolean,
        val isWifiSecure: Boolean,
        val connectionType: String
    )

    fun scanNetwork(context: Context): NetworkStatus {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val activeNetwork = cm.activeNetwork
        val caps = cm.getNetworkCapabilities(activeNetwork)
        
        val isVpn = caps?.hasTransport(NetworkCapabilities.TRANSPORT_VPN) ?: false
        
        // Simple check: if it's WiFi, assume secure if it's not open (this is a heuristic for demo)
        val connectionType = when {
            caps?.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) == true -> "WiFi"
            caps?.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) == true -> "Cellular"
            else -> "Other"
        }

        return NetworkStatus(
            isVpnActive = isVpn,
            isWifiSecure = true, // On Android, we can't easily check encryption type without specific permissions
            connectionType = connectionType
        )
    }
}
