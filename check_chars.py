with open('mall/core/agreement.tll', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all non-ASCII characters
special_chars = {}
for i, ch in enumerate(content):
    if ord(ch) > 127:
        if ch not in special_chars:
            special_chars[ch] = []
        special_chars[ch].append(i)

print('Non-ASCII characters found:')
for ch, positions in sorted(special_chars.items(), key=lambda x: -len(x[1])):
    print(f'  U+{ord(ch):04X} ({repr(ch)}): {len(positions)} occurrences')
    if len(positions) <= 3:
        for pos in positions[:3]:
            start = max(0, pos - 20)
            end = min(len(content), pos + 20)
            context = content[start:end].replace('\n', '\\n')
            print(f'    at position {pos}: ...{context}...')

# Check for BOM
if content.startswith('\ufeff'):
    print('WARNING: File starts with BOM')
else:
    print('No BOM found')
