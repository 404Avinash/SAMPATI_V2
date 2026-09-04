import os
import re
import glob

frontend_src = "/home/avi/Downloads/Sampati_v2/frontend/src"

files = glob.glob(f"{frontend_src}/**/*.jsx", recursive=True) + glob.glob(f"{frontend_src}/**/*.tsx", recursive=True) + glob.glob(f"{frontend_src}/**/*.js", recursive=True)

total_buttons = 0
violations = []

def find_button_tags(content):
    idx = 0
    buttons = []
    while True:
        pos = content.find("<button", idx)
        if pos == -1:
            break
        # make sure it's a word boundary
        if pos + 7 < len(content) and content[pos+7] not in (' ', '\t', '\n', '\r', '>'):
            idx = pos + 7
            continue
        # now find the matching closing '>' accounting for curly braces {...} and quotes
        in_curly = 0
        in_quote = None
        tag_end = -1
        for i in range(pos + 7, len(content)):
            ch = content[i]
            if in_quote:
                if ch == in_quote and content[i-1] != '\\':
                    in_quote = None
            else:
                if ch in ('"', "'", '`'):
                    in_quote = ch
                elif ch == '{':
                    in_curly += 1
                elif ch == '}':
                    in_curly -= 1
                elif ch == '>' and in_curly == 0:
                    tag_end = i
                    break
        if tag_end != -1:
            full_tag = content[pos:tag_end+1]
            buttons.append((pos, full_tag))
            idx = tag_end + 1
        else:
            idx = pos + 7
    return buttons

for file_path in files:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    matches = find_button_tags(content)
    for pos, tag in matches:
        total_buttons += 1
        has_onclick = "onClick" in tag or "onclick" in tag
        has_submit = 'type="submit"' in tag or "type='submit'" in tag or 'type={"submit"}' in tag
        if not (has_onclick or has_submit):
            line_num = content[:pos].count("\n") + 1
            violations.append((file_path, line_num, tag))

print(f"Total <button> elements checked: {total_buttons}")
if violations:
    print(f"FOUND {len(violations)} VIOLATIONS:")
    for v in violations:
        print(f"  {v[0]}:{v[1]} -> {v[2]}")
else:
    print("ALL <button> elements have onClick or type='submit'! 100% compliant.")
