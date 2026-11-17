package com.lomdi.dsih.domain.usecase

import android.content.Context
import android.hardware.display.DisplayManager
import android.view.Display

/**
 * Utility to detect active screen-sharing or virtual displays.
 */
object ActiveDisplayScanner {

    /**
     * Returns true if any active display is a non-private secondary display.
     */
    fun isScreenBeingShared(context: Context): Boolean {
        val dm = context.getSystemService(Context.DISPLAY_SERVICE) as DisplayManager
        val displays = dm.displays
        
        for (display in displays) {
            // Ignore the built-in primary display
            if (display.displayId != Display.DEFAULT_DISPLAY) {
                // If a secondary display is not flagged as PRIVATE, it's likely a cast/mirror
                val isPrivate = (display.flags and Display.FLAG_PRIVATE) != 0
                if (!isPrivate) {
                    return true
                }
            }
        }
        return false
    }
}
