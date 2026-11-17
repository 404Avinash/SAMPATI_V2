package com.lomdi.dsih.data.source

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.preferencesDataStore
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.core.stringSetPreferencesKey
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

class DataStoreManager(private val context: Context) {

    companion object {
        val IS_FIRST_LAUNCH = booleanPreferencesKey("is_first_launch")
        val PHONE_NUMBER = stringPreferencesKey("phone_number")
        val UPI_IDS = stringSetPreferencesKey("upi_ids")
        val THEME_MODE = stringPreferencesKey("theme_mode")
    }

    val themeMode: Flow<String> = context.dataStore.data.map { preferences ->
        preferences[THEME_MODE] ?: "SYSTEM"
    }

    suspend fun saveThemeMode(mode: String) {
        context.dataStore.edit { preferences ->
            preferences[THEME_MODE] = mode
        }
    }

    val isFirstLaunch: Flow<Boolean> = context.dataStore.data.map { preferences ->
        preferences[IS_FIRST_LAUNCH] ?: true
    }

    suspend fun setFirstLaunchCompleted() {
        context.dataStore.edit { preferences ->
            preferences[IS_FIRST_LAUNCH] = false
        }
    }

    val phoneNumber: Flow<String> = context.dataStore.data.map { preferences ->
        preferences[PHONE_NUMBER] ?: ""
    }

    suspend fun savePhoneNumber(phone: String) {
        context.dataStore.edit { preferences ->
            preferences[PHONE_NUMBER] = phone
        }
    }

    val upiIds: Flow<Set<String>> = context.dataStore.data.map { preferences ->
        preferences[UPI_IDS] ?: emptySet()
    }

    suspend fun saveUpiIds(ids: Set<String>) {
        context.dataStore.edit { preferences ->
            preferences[UPI_IDS] = ids
        }
    }

    suspend fun addUpiId(upiId: String) {
        context.dataStore.edit { preferences ->
            val current = preferences[UPI_IDS] ?: emptySet()
            preferences[UPI_IDS] = current + upiId
        }
    }

    suspend fun removeUpiId(upiId: String) {
        context.dataStore.edit { preferences ->
            val current = preferences[UPI_IDS] ?: emptySet()
            preferences[UPI_IDS] = current - upiId
        }
    }
}
