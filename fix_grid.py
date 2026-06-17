import os
import glob
import re

for f in glob.glob('d:/Tender-Bid-management/templates/**/*.html', recursive=True):
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace grid-cols-X that don't have sm: or md: prefix
    # Look for ' grid-cols-2 ' or '"grid-cols-2 ' etc
    new_content = re.sub(r'(?<=[\s\"])grid-cols-2(?=[\s\"])', 'grid-cols-1 sm:grid-cols-2', content)
    new_content = re.sub(r'(?<=[\s\"])grid-cols-3(?=[\s\"])', 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3', new_content)
    new_content = re.sub(r'(?<=[\s\"])grid-cols-4(?=[\s\"])', 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4', new_content)

    if content != new_content:
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Updated {f}')
