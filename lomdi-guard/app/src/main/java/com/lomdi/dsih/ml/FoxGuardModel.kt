package com.lomdi.dsih.ml

import android.content.res.AssetManager
import java.io.DataInputStream
import java.io.IOException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import kotlin.math.exp

/**
 * Pure-Kotlin FastText inference engine for Fox Guard.
 *
 * Reads a custom binary model file (.foxg) exported by train_and_export.py
 * and performs text classification fully on-device — no NDK, no JNI.
 *
 * Binary format (.foxg):
 *   [4]  magic   = 0x464F5847
 *   [4]  version = 1
 *   [4]  dim
 *   [4]  num_labels
 *   [4]  num_words
 *   For each label : [4] length + [n] UTF-8 bytes
 *   For each word  : [4] length + [n] UTF-8 bytes
 *   Input matrix   : num_words × dim × 4 bytes (float32, little-endian)
 *   Output matrix  : num_labels × dim × 4 bytes (float32, little-endian)
 */
class FoxGuardModel private constructor(
    private val labels: List<String>,
    private val vocab: Map<String, Int>,
    private val inputMatrix: Array<FloatArray>,   // [num_words][dim]
    private val outputMatrix: Array<FloatArray>,  // [num_labels][dim]
    private val dim: Int,
) {

    companion object {
        private const val MAGIC   = 0x464F5847.toInt()
        private const val VERSION = 1
        const val ASSET_NAME = "intent_model.foxg"

        /**
         * Load the model from Android assets.
         * Returns null if the model file is a placeholder (< 64 bytes).
         */
        fun load(assets: AssetManager): FoxGuardModel? {
            return try {
                assets.open(ASSET_NAME).use { stream ->
                    val bytes = stream.readBytes()

                    // Return null for placeholder file (script not run yet)
                    if (bytes.size < 64) return null

                    val buf = ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN)

                    // ── Header ──────────────────────────────────────────────
                    val magic = buf.int
                    if (magic != MAGIC) throw IOException("Invalid .foxg magic: 0x${magic.toString(16)}")

                    val version = buf.int
                    if (version != VERSION) throw IOException("Unsupported .foxg version: $version")

                    val dim        = buf.int
                    val numLabels  = buf.int
                    val numWords   = buf.int

                    // ── Labels ──────────────────────────────────────────────
                    val labels = ArrayList<String>(numLabels)
                    repeat(numLabels) { labels.add(readString(buf)) }

                    // ── Vocabulary ──────────────────────────────────────────
                    val vocab = HashMap<String, Int>(numWords * 2)
                    repeat(numWords) { i -> vocab[readString(buf)] = i }

                    // ── Input matrix ─────────────────────────────────────────
                    val inputMatrix = Array(numWords) { FloatArray(dim) { buf.float } }

                    // ── Output matrix ────────────────────────────────────────
                    val outputMatrix = Array(numLabels) { FloatArray(dim) { buf.float } }

                    FoxGuardModel(labels, vocab, inputMatrix, outputMatrix, dim)
                }
            } catch (e: Exception) {
                null // Model not ready; caller will use heuristic fallback
            }
        }

        private fun readString(buf: ByteBuffer): String {
            val len = buf.int
            val bytes = ByteArray(len)
            buf.get(bytes)
            return String(bytes, Charsets.UTF_8)
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Inference
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Predicts the intent label for the given SMS body text.
     * Returns the top-1 label with its softmax confidence.
     */
    fun predict(text: String): Pair<String, Float> {
        val tokens = tokenize(text)

        // 1. Bag-of-words: average word vectors
        val vec = FloatArray(dim) { 0f }
        var count = 0
        for (token in tokens) {
            val idx = vocab[token]
            if (idx != null) {
                val row = inputMatrix[idx]
                for (i in 0 until dim) vec[i] += row[i]
                count++
            }
        }
        if (count > 1) {
            for (i in 0 until dim) vec[i] /= count
        }

        // 2. Compute raw scores: output_matrix · vec
        val scores = FloatArray(labels.size)
        for (l in labels.indices) {
            var s = 0f
            val row = outputMatrix[l]
            for (i in 0 until dim) s += row[i] * vec[i]
            scores[l] = s
        }

        // 3. Softmax
        val maxScore = scores.max()
        val exps = FloatArray(scores.size) { exp((scores[it] - maxScore).toDouble()).toFloat() }
        val sumExp = exps.sum()
        val softmax = FloatArray(exps.size) { exps[it] / sumExp }

        // 4. Top-1
        val topIdx = softmax.indices.maxByOrNull { softmax[it] }!!
        return labels[topIdx] to softmax[topIdx]
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Tokenizer
    // ─────────────────────────────────────────────────────────────────────────

    /**
     * Lowercase + split on whitespace and common punctuation.
     * Keeps Devanagari and other Unicode word characters intact.
     */
    private fun tokenize(text: String): List<String> {
        return text.lowercase()
            .split(Regex("[\\s.,!?;:()/\\[\\]{}<>\"'|\\\\@#%^&*+=~`]+"))
            .filter { it.isNotBlank() && it.length >= 2 }
    }
}
