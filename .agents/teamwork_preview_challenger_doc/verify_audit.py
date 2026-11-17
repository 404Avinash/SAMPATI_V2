import re
import os
import sys

doc_path = '/home/avi/Downloads/Sampati_v2/SAMPATI_V2_TECHNICAL_DOCUMENTATION.md'
with open(doc_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Pattern for file paths in backticks or code blocks or parentheses
patterns = [
    r'`([^`\n]+)`',
    r'\(([a-zA-Z0-9_\-\./]+\.[a-zA-Z0-9_]+)\)'
]

raw_candidates = set()
for p in patterns:
    for match in re.findall(p, text):
        match = match.strip()
        raw_candidates.add(match)

file_extensions = (
    '.py', '.jsx', '.js', '.json', '.md', '.css', '.html', '.svg', 
    '.txt', '.lock', '.toml', '.env', '.sh', '.pyc', '.sql', '.yml', '.yaml'
)

paths_to_test = set()
for c in raw_candidates:
    # check if looks like file path
    if any(c.endswith(ext) for ext in file_extensions) or ('/' in c and not c.startswith(('http:', 'https:', 'git@', 'localhost:', 'ws:'))):
        # clean up candidate
        clean_c = c.split()[0].strip('`\'",:;')
        # filter out things like "v1.0.0", math expressions, routes like "/upi/score"
        if not clean_c.startswith(('/upi', '/intel', '/ws', '/federation', '/notifications', '/adapters', '/health', '/api', '/docs')):
            if any(clean_c.endswith(ext) for ext in file_extensions) or clean_c.startswith(('app/', 'frontend/', 'tests/', './', 'src/')):
                paths_to_test.add(clean_c)

print(f"Total potential file paths identified: {len(paths_to_test)}")

results = []
for p in sorted(paths_to_test):
    # Try multiple ways to resolve relative to repo root
    variations = [
        p,
        p.lstrip('/'),
        os.path.join('/home/avi/Downloads/Sampati_v2', p.lstrip('/')),
        os.path.join('/home/avi/Downloads/Sampati_v2/frontend', p.lstrip('/'))
    ]
    exists = any(os.path.exists(v) for v in variations)
    results.append((p, exists))

missing = [(p, exists) for p, exists in results if not exists]
existing = [(p, exists) for p, exists in results if exists]

print(f"Existing files verified: {len(existing)}")
print(f"Missing or doubtful paths: {len(missing)}")
print("\n--- MISSING / ERRONEOUS PATHS ---")
for p, _ in missing:
    print(f"  [X] {p}")

print("\n--- SAMPLE EXISTING PATHS (first 25) ---")
for p, _ in existing[:25]:
    print(f"  [OK] {p}")

