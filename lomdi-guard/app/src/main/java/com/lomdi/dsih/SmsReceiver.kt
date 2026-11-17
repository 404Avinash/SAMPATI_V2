package com.lomdi.dsih

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import com.lomdi.dsih.data.model.SmsMessage
import com.lomdi.dsih.data.source.CallStateStore
import com.lomdi.dsih.data.source.ClipboardStore
import com.lomdi.dsih.data.source.RemoteAppStore
import com.lomdi.dsih.domain.usecase.SmsAnalyzer
import com.lomdi.dsih.domain.usecase.SmsLinkExtractor
import com.lomdi.dsih.domain.usecase.ThreatEvaluator

/**
 * BroadcastReceiver responsible for intercepting SMS messages and evaluating threats.
 */
class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context?, intent: Intent?) {
        if (intent?.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            val incomingMessages = Telephony.Sms.Intents.getMessagesFromIntent(intent)

            for (sms in incomingMessages) {
                val sender = sms.originatingAddress ?: "Unknown Number"
                val body = sms.messageBody ?: ""

                // 1. Detailed Analysis via hybrid Rule-Based + Edge AI engine
                val analysisResult = SmsAnalyzer.analyze(sender, body)

                // 2. Evaluate overall threat level for UI badges
                val (level, score) = ThreatEvaluator.evaluate(
                    body = body,
                    links = SmsLinkExtractor.extractLinks(body),
                    isOnActiveCallWithUnsaved = CallStateStore.isActiveCall && CallStateStore.isUnsavedNumber,
                    hasCopiedSensitiveData = ClipboardStore.hasSensitiveData,
                    hasRemoteAppsInstalled = RemoteAppStore.hasRemoteApps
                )

                // 3. Create structured message with deep analysis
                val smsMessage = SmsMessage(
                    sender = sender,
                    body = body,
                    extractedLinks = SmsLinkExtractor.extractLinks(body),
                    threatLevel = level,
                    riskScore = score,
                    analysisResult = analysisResult
                )

                // 4. Log to audit store
                com.lomdi.dsih.data.source.ThreatLogStore.addLog(
                    type = "SMS: $sender",
                    level = level,
                    score = score
                )

                // 5. Save to the global store
                SmsStore.messages.add(0, smsMessage)
            }
        }
    }
}
