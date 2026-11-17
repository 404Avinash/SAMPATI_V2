import re
import os

doc_path = '/home/avi/Downloads/Sampati_v2/SAMPATI_V2_TECHNICAL_DOCUMENTATION.md'
with open(doc_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Let's extract:
# 1. Tree lines: e.g. "│   ├── AppStateContext.jsx"
# 2. Backticked items containing .py, .jsx, .js, .json, .css, .html, .svg, .toml, .env, .sh, .pyc, .md
# 3. Explicit path mentions like app/... frontend/... tests/...

file_mentions = set()

# Section 2 tree parsing:
tree_matches = re.findall(r'^[│\s├└─]+\s*([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9_]+)', text, re.MULTILINE)
for tm in tree_matches:
    file_mentions.add(tm)

# Backticked files
backtick_matches = re.findall(r'`([^`\n]+)`', text)
for bm in backtick_matches:
    bm = bm.strip()
    # Check if contains file extension
    if any(bm.endswith(ext) or (ext in bm and ('/' in bm or ' ' in bm)) for ext in ['.py', '.jsx', '.js', '.json', '.css', '.html', '.svg', '.toml', '.env', '.sh', '.pyc', '.md']):
        # extract words that look like file path
        words = bm.split()
        for w in words:
            w = w.strip('(),:;`\'"')
            if any(w.endswith(ext) for ext in ['.py', '.jsx', '.js', '.json', '.css', '.html', '.svg', '.toml', '.env', '.sh', '.pyc', '.md']):
                file_mentions.add(w)

print(f"Unique file names/paths extracted: {len(file_mentions)}")

verified = []
missing = []

for f in sorted(file_mentions):
    # Check if exact path exists
    candidate_paths = [
        f,
        f.lstrip('/'),
        os.path.join('/home/avi/Downloads/Sampati_v2', f.lstrip('/')),
        os.path.join('/home/avi/Downloads/Sampati_v2/frontend', f.lstrip('/')),
        os.path.join('/home/avi/Downloads/Sampati_v2/frontend/src', f.lstrip('/')),
        os.path.join('/home/avi/Downloads/Sampati_v2/tests', f.lstrip('/')),
        os.path.join('/home/avi/Downloads/Sampati_v2/app', f.lstrip('/')),
    ]
    # Also recursive find by basename
    basename = os.path.basename(f)
    found_paths = []
    for root, dirs, files in os.walk('/home/avi/Downloads/Sampati_v2'):
        if '.git' in root or '.venv' in root or 'node_modules' in root:
            continue
        if basename in files:
            found_paths.append(os.path.relpath(os.path.join(root, basename), '/home/avi/Downloads/Sampati_v2'))

    exists_direct = any(os.path.exists(p) for p in candidate_paths)
    if exists_direct or found_paths:
        verified.append((f, found_paths if found_paths else ["direct"]))
    else:
        missing.append(f)

print(f"Verified files count: {len(verified)}")
print(f"Missing files count: {len(missing)}")

if missing:
    print("\n--- MISSING FILES ---")
    for m in missing:
        print(f"  FAILED: {m}")
else:
    print("\nALL FILES EXIST ON DISK!")

print("\n--- SAMPLE VERIFIED MAPPINGS ---")
for f, paths in verified[:35]:
    print(f"  {f:35} -> {paths}")

