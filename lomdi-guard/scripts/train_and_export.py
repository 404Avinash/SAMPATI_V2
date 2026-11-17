#!/usr/bin/env python3
"""
Fox Guard - FastText Trainer & Model Exporter
Trains a supervised FastText model on the generated SMS dataset and exports
it to a custom binary format (.foxg) that the Android app can read natively
in pure Kotlin — no NDK or JNI required.

Binary format (.foxg):
  [4]  magic   = 0x464F5847  ('F','O','X','G')
  [4]  version = 1
  [4]  dim     (embedding dimension)
  [4]  num_labels
  [4]  num_words
  For each label : [4] length + [n] UTF-8 bytes
  For each word  : [4] length + [n] UTF-8 bytes
  Input matrix   : num_words * dim * 4 bytes  (float32, row-major)
  Output matrix  : num_labels * dim * 4 bytes (float32, row-major)

Requirements:
  pip install fasttext numpy

Usage:
  cd scripts/
  python generate_dataset.py        # Step 1: create sms_train.txt + sms_test.txt
  python train_and_export.py        # Step 2: train, evaluate, export .foxg

Outputs:
  intent_model.bin   (native FastText binary, for reference)
  intent_model.foxg  (Android-ready custom binary — copy to app/src/main/assets/)
"""

import fasttext
import numpy as np
import struct
import os
import sys
import platform

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
TRAIN_FILE  = os.path.join(SCRIPT_DIR, "sms_train.txt")
TEST_FILE   = os.path.join(SCRIPT_DIR, "sms_test.txt")
BIN_OUT     = os.path.join(SCRIPT_DIR, "intent_model.bin")
FOXG_OUT    = os.path.join(SCRIPT_DIR, "intent_model.foxg")
ASSETS_DST  = os.path.join(SCRIPT_DIR, "..", "app", "src", "main", "assets", "intent_model.foxg")

MAGIC   = 0x464F5847   # 'FOXG'
VERSION = 1

# ─────────────────────────────────────────────
# Step 0: Diagnostics (helps if NaN persists — points to env issues)
# ─────────────────────────────────────────────

print(f"🔎  Python      : {platform.python_version()}")
print(f"🔎  numpy       : {np.__version__}")
try:
    print(f"🔎  fasttext    : {fasttext.__file__}")
except Exception:
    pass

if sys.version_info >= (3, 13):
    print("⚠️  You're on Python 3.13+. The 'fasttext' PyPI package hasn't been")
    print("    actively maintained and may not ship a wheel built/tested for this")
    print("    interpreter, which can (rarely) cause silent numeric corruption.")
    print("    If NaN errors persist after the fixes below, try a Python 3.10/3.11")
    print("    venv as a sanity check.\n")

# ─────────────────────────────────────────────
# Step 1: Check dataset exists
# ─────────────────────────────────────────────

if not os.path.exists(TRAIN_FILE):
    print("❌  sms_train.txt not found. Run generate_dataset.py first.")
    sys.exit(1)

# ─────────────────────────────────────────────
# Step 1.5: Validate & clean the training data
#
# The single most common cause of fastText's "Encountered NaN" is a
# malformed line: a blank line, a line that's only a label with no text,
# or a line with no recognized label at all. Any of these can produce a
# zero-length training example, which blows up the gradient.
# ─────────────────────────────────────────────

def clean_fasttext_file(path: str) -> str:
    """Returns path to a cleaned copy (path.clean) with bad lines removed."""
    kept, dropped = 0, 0
    dropped_examples = []
    clean_path = path + ".clean"

    with open(path, "r", encoding="utf-8") as f_in, \
         open(clean_path, "w", encoding="utf-8") as f_out:
        for line_num, line in enumerate(f_in, 1):
            stripped = line.strip()

            if not stripped:
                dropped += 1
                continue

            tokens = stripped.split()
            label_tokens = [t for t in tokens if t.startswith("__label__")]
            text_tokens  = [t for t in tokens if not t.startswith("__label__")]

            if not label_tokens:
                dropped += 1
                if len(dropped_examples) < 5:
                    dropped_examples.append((line_num, "no __label__ token", stripped[:60]))
                continue

            if not text_tokens:
                dropped += 1
                if len(dropped_examples) < 5:
                    dropped_examples.append((line_num, "label with no text", stripped[:60]))
                continue

            f_out.write(stripped + "\n")
            kept += 1

    print(f"🧹  Cleaned {os.path.basename(path)}: kept {kept} lines, dropped {dropped}")
    if dropped_examples:
        print("    Examples of dropped lines:")
        for ln, reason, snippet in dropped_examples:
            print(f"      line {ln} ({reason}): {snippet!r}")

    if kept == 0:
        print(f"❌  All lines in {path} were dropped — check the file's format.")
        sys.exit(1)

    return clean_path

TRAIN_FILE_CLEAN = clean_fasttext_file(TRAIN_FILE)
TEST_FILE_CLEAN  = clean_fasttext_file(TEST_FILE) if os.path.exists(TEST_FILE) else None

# ─────────────────────────────────────────────
# Step 2: Train FastText supervised model
#
# Key fix: loss="ns" (negative sampling) is designed for large output
# spaces (e.g. word2vec-style vocabularies of thousands of words). With
# only 5 labels, the negative sampler has almost nothing to sample from
# and the loss can diverge to NaN almost immediately. "softmax" is the
# standard, numerically stable choice for small-label-set text
# classification like this.
# ─────────────────────────────────────────────

def train_model(lr, epoch, loss, wordNgrams=1, dim=32, minCount=2):
    print(f"\n🚀  Training FastText model  (lr={lr}, epoch={epoch}, loss={loss}) ...")
    return fasttext.train_supervised(
        input       = TRAIN_FILE_CLEAN,
        epoch       = epoch,
        lr          = lr,
        wordNgrams  = wordNgrams,
        dim         = dim,
        minCount    = minCount,
        thread      = 1,
        loss        = loss,
        verbose     = 2,
    )

# Primary attempt: softmax, conservative lr.
# Fallback attempts progressively lower the lr further in case the data
# itself is still borderline unstable (e.g. very small / repetitive dataset).
attempts = [
    dict(lr=0.05, epoch=25, loss="softmax"),
    dict(lr=0.01, epoch=25, loss="softmax"),
    dict(lr=0.005, epoch=40, loss="softmax"),
]

model = None
last_error = None
for i, params in enumerate(attempts, 1):
    try:
        model = train_model(**params)
        print(f"✅  Training succeeded on attempt {i} with {params}")
        break
    except RuntimeError as e:
        last_error = e
        print(f"⚠️  Attempt {i} failed ({params}): {e}")

if model is None:
    print("\n❌  All training attempts hit NaN. This points to a data or")
    print("    environment problem rather than hyperparameters:")
    print("    1. Open sms_train.txt.clean and skim it for garbage/repeated tokens.")
    print("    2. Confirm fasttext + numpy versions are compatible with your Python")
    print(f"       version ({platform.python_version()}) — consider a 3.10/3.11 venv.")
    raise last_error

# ─────────────────────────────────────────────
# Step 3: Evaluate on test set
# ─────────────────────────────────────────────

if TEST_FILE_CLEAN:
    n, p, r = model.test(TEST_FILE_CLEAN)
    print(f"\n📊  Test results  (N={n})")
    print(f"    Precision : {p:.4f}  ({p*100:.1f}%)")
    print(f"    Recall    : {r:.4f}  ({r*100:.1f}%)")
else:
    print("⚠️  sms_test.txt not found, skipping evaluation.")

# ─────────────────────────────────────────────
# Step 4: Save native .bin for reference
# ─────────────────────────────────────────────

model.save_model(BIN_OUT)
print(f"\n💾  Native model saved  → {BIN_OUT}")

# ─────────────────────────────────────────────
# Step 5: Extract weights for Android export
# ─────────────────────────────────────────────

labels        = model.labels                       # e.g. ['__label__fraud', ...]
words         = model.words                        # vocabulary list
dim           = model.get_dimension()
input_matrix  = model.get_input_matrix()            # shape: [vocab + buckets, dim]
output_matrix = model.get_output_matrix()           # shape: [num_labels, dim]

num_labels = len(labels)
num_words  = len(words)

# Only keep the first num_words rows (actual vocab, not the hash-bucket rows)
word_vectors = input_matrix[:num_words].astype(np.float32)  # [num_words, dim]
out_vectors  = output_matrix.astype(np.float32)              # [num_labels, dim]

# Sanity check: make sure nothing NaN/Inf slipped into the exported weights
if not np.all(np.isfinite(word_vectors)) or not np.all(np.isfinite(out_vectors)):
    print("❌  Exported weights contain NaN/Inf despite training 'succeeding'.")
    print("    Do not ship this model — re-run after investigating the data.")
    sys.exit(1)

print(f"\n📦  Model stats:")
print(f"    Vocabulary  : {num_words} words")
print(f"    Labels      : {num_labels} → {labels}")
print(f"    Dimension   : {dim}")
print(f"    Input mat   : {word_vectors.shape}  ({word_vectors.nbytes/1024:.1f} KB)")
print(f"    Output mat  : {out_vectors.shape}   ({out_vectors.nbytes/1024:.1f} KB)")

# ─────────────────────────────────────────────
# Step 6: Write custom .foxg binary
# ─────────────────────────────────────────────

def write_string(f, s: str):
    encoded = s.encode("utf-8")
    f.write(struct.pack("<I", len(encoded)))
    f.write(encoded)

os.makedirs(os.path.dirname(FOXG_OUT), exist_ok=True) if os.path.dirname(FOXG_OUT) else None

with open(FOXG_OUT, "wb") as f:
    # Header
    f.write(struct.pack("<II", MAGIC, VERSION))
    f.write(struct.pack("<III", dim, num_labels, num_words))
    # Labels
    for lbl in labels:
        write_string(f, lbl)
    # Words
    for word in words:
        write_string(f, word)
    # Matrices
    f.write(word_vectors.tobytes())   # [num_words * dim * 4] bytes
    f.write(out_vectors.tobytes())    # [num_labels * dim * 4] bytes

foxg_size_kb = os.path.getsize(FOXG_OUT) / 1024
print(f"\n✅  Android model exported → {FOXG_OUT}")
print(f"    File size   : {foxg_size_kb:.1f} KB  ({foxg_size_kb/1024:.2f} MB)")

# ─────────────────────────────────────────────
# Step 7: Auto-copy to assets folder
# ─────────────────────────────────────────────

assets_dir = os.path.dirname(ASSETS_DST)
if os.path.isdir(assets_dir):
    import shutil
    shutil.copy2(FOXG_OUT, ASSETS_DST)
    print(f"📲  Auto-copied to app assets  → {ASSETS_DST}")
else:
    print(f"\n⚠️  Assets folder not found at {assets_dir}")
    print(f"    Manually copy {FOXG_OUT} to:")
    print(f"    app/src/main/assets/intent_model.foxg")

print("\n🎉  Done! You can now build the Android app.")