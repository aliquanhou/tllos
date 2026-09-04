import sys

with open('mall/core/agreement.tll', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Chinese quotes with regular quotes
content = content.replace('\u201c', "'").replace('\u201d', "'")
content = content.replace('\u2018', "'").replace('\u2019', "'")

# Replace other special characters
content = content.replace('\u3000', ' ')  # full-width space
content = content.replace('\u00a0', ' ')  # non-breaking space

with open('mall/core/agreement.tll', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed special characters in agreement.tll')
print('File size:', len(content), 'bytes')
