import re
content = open('data/input/sweden-military-map.svg', encoding='utf-8').read()
got_idx = content.find('class="gotland"')
print('Gotland path found:', got_idx > 0)
for bid in ['F21','VID','STO','MUS','GOT','KRL']:
    found = f'id="base-{bid}"' in content
    print(f'Base {bid}: {found}')
paths = re.findall(r'<path ', content)
print(f'Total paths: {len(paths)}')
print(f'SVG size: {len(content)} chars')
