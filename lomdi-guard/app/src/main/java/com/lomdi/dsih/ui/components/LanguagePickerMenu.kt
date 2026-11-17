package com.lomdi.dsih.ui.components

import android.app.Activity
import android.app.LocaleManager
import android.content.Context
import android.os.Build
import android.os.LocaleList
import androidx.appcompat.app.AppCompatDelegate
import androidx.core.os.LocaleListCompat
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Language
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.lomdi.dsih.R

/**
 * Data class representing a supported application language.
 */
data class AppLanguage(
    val code: String,
    val nativeName: String,
    val englishName: String
)

val SupportedLanguages = listOf(
    AppLanguage(code = "en", nativeName = "English", englishName = "English"),
    AppLanguage(code = "hi", nativeName = "हिन्दी", englishName = "Hindi"),
    AppLanguage(code = "mr", nativeName = "मराठी", englishName = "Marathi"),
    AppLanguage(code = "bn", nativeName = "বাংলা", englishName = "Bengali"),
    AppLanguage(code = "te", nativeName = "తెలుగు", englishName = "Telugu"),
    AppLanguage(code = "ta", nativeName = "தமிழ்", englishName = "Tamil")
)

/**
 * Material 3 Language Picker Menu displaying a Globe icon button that opens a DropdownMenu.
 * Uses AppCompatDelegate & LocaleManager to switch the application locale in real-time.
 */
@Composable
fun LanguagePickerMenu(
    modifier: Modifier = Modifier,
    iconTint: Color = MaterialTheme.colorScheme.onSurface
) {
    val context = LocalContext.current
    var expanded by remember { mutableStateOf(false) }

    val configuration = androidx.compose.ui.platform.LocalConfiguration.current
    // Read active locale tag
    val currentLocaleTag = remember(context, configuration) {
        val appLocales = AppCompatDelegate.getApplicationLocales()
        if (!appLocales.isEmpty) {
            appLocales.get(0)?.language ?: "en"
        } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val localeManager = context.getSystemService(Context.LOCALE_SERVICE) as? LocaleManager
            localeManager?.applicationLocales?.get(0)?.language ?: "en"
        } else {
            configuration.locales.get(0)?.language ?: "en"
        }
    }

    Box(modifier = modifier) {
        IconButton(onClick = { expanded = true }) {
            Icon(
                imageVector = Icons.Default.Language,
                contentDescription = stringResource(R.string.language_picker_title),
                tint = iconTint
            )
        }

        DropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
            modifier = Modifier
                .width(220.dp)
                .background(MaterialTheme.colorScheme.surface, RoundedCornerShape(12.dp))
        ) {
            Text(
                text = stringResource(R.string.language_picker_title),
                style = MaterialTheme.typography.labelLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)
            )

            HorizontalDivider(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.12f))

            SupportedLanguages.forEach { language ->
                val isSelected = currentLocaleTag.equals(language.code, ignoreCase = true)

                DropdownMenuItem(
                    text = {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text(
                                    text = language.nativeName,
                                    fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                    fontSize = 15.sp,
                                    color = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                                )
                                if (language.nativeName != language.englishName) {
                                    Text(
                                        text = language.englishName,
                                        fontSize = 11.sp,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }

                            if (isSelected) {
                                Icon(
                                    imageVector = Icons.Default.Check,
                                    contentDescription = "Selected",
                                    tint = MaterialTheme.colorScheme.primary,
                                    modifier = Modifier.size(18.dp)
                                )
                            }
                        }
                    },
                    onClick = {
                        expanded = false
                        changeAppLanguage(context, language.code)
                    },
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                )
            }
        }
    }
}

/**
 * Material 3 Modal Bottom Sheet variant for Language Selection.
 */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LanguagePickerBottomSheet(
    onDismissRequest: () -> Unit
) {
    val context = LocalContext.current
    val configuration = androidx.compose.ui.platform.LocalConfiguration.current
    val currentLocaleTag = remember(context, configuration) {
        val appLocales = AppCompatDelegate.getApplicationLocales()
        if (!appLocales.isEmpty) {
            appLocales.get(0)?.language ?: "en"
        } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val localeManager = context.getSystemService(Context.LOCALE_SERVICE) as? LocaleManager
            localeManager?.applicationLocales?.get(0)?.language ?: "en"
        } else {
            configuration.locales.get(0)?.language ?: "en"
        }
    }

    ModalBottomSheet(onDismissRequest = onDismissRequest) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 20.dp, vertical = 12.dp)
        ) {
            Text(
                text = stringResource(R.string.language_picker_title),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            SupportedLanguages.forEach { language ->
                val isSelected = currentLocaleTag.equals(language.code, ignoreCase = true)

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable {
                            changeAppLanguage(context, language.code)
                            onDismissRequest()
                        }
                        .padding(vertical = 12.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = language.nativeName,
                            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
                            fontSize = 16.sp,
                            color = if (isSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                        )
                        if (language.nativeName != language.englishName) {
                            Text(
                                text = language.englishName,
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    if (isSelected) {
                        Icon(
                            imageVector = Icons.Default.Check,
                            contentDescription = "Selected",
                            tint = MaterialTheme.colorScheme.primary
                        )
                    }
                }

                HorizontalDivider(color = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.08f))
            }

            Spacer(Modifier.height(24.dp))
        }
    }
}

/**
 * Changes the app's locale globally using AppCompatDelegate and LocaleManager.
 */
fun changeAppLanguage(context: Context, languageCode: String) {
    val localeList = LocaleListCompat.forLanguageTags(languageCode)
    AppCompatDelegate.setApplicationLocales(localeList)

    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
        val localeManager = context.getSystemService(Context.LOCALE_SERVICE) as? LocaleManager
        localeManager?.applicationLocales = LocaleList.forLanguageTags(languageCode)
    }

    (context as? Activity)?.recreate()
}
