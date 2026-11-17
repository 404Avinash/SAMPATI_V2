package com.lomdi.dsih.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import com.lomdi.dsih.data.source.ThemeStore

private val DarkColorScheme = darkColorScheme(
    primary = FoxGreenPrimary,
    onPrimary = FoxGreenOnPrimary,
    primaryContainer = FoxGreenPrimaryContainer,
    onPrimaryContainer = FoxGreenOnPrimaryContainer,
    background = FoxDarkBackground,
    onBackground = FoxDarkOnSurface,
    surface = FoxDarkSurface,
    onSurface = FoxDarkOnSurface,
    surfaceVariant = FoxDarkSurfaceContainer,
    onSurfaceVariant = FoxDarkOnSurfaceVariant,
    outline = FoxDarkOutline,
    outlineVariant = Color(0xFF1E293B)
)

private val LightColorScheme = lightColorScheme(
    primary = Color(0xFF059669),
    onPrimary = Color(0xFFFFFFFF),
    primaryContainer = Color(0xFFD1FAE5),
    onPrimaryContainer = Color(0xFF064E3B),
    background = FoxLightBackground,
    onBackground = FoxLightOnSurface,
    surface = FoxLightSurface,
    onSurface = FoxLightOnSurface,
    surfaceVariant = FoxLightSurfaceContainer,
    onSurfaceVariant = FoxLightOnSurfaceVariant,
    outline = FoxLightOutline,
    outlineVariant = Color(0xFFE2E8F0)
)

@Composable
fun FoxGuardTheme(
    darkTheme: Boolean = ThemeStore.isDarkTheme(isSystemInDarkTheme()),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}

@Composable
fun LomdiTheme(
    darkTheme: Boolean = ThemeStore.isDarkTheme(isSystemInDarkTheme()),
    content: @Composable () -> Unit
) = FoxGuardTheme(darkTheme = darkTheme, content = content)
