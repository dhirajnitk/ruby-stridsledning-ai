"""
Deep-analyze the Wikipedia Sweden SVG to find land paths and coordinate system.
"""
import re

with open("scratch/sweden_wiki.svg", encoding="utf-8") as f:
    content = f.read()

# Find layer7 (Land) and layer8 (Islands) sections
layer7_start = content.find('id="layer7"')
layer8_start = content.find('id="layer8"')

print(f"Layer7 (Land) starts at: {layer7_start}")
print(f"Layer8 (Islands) starts at: {layer8_start}")

# Extract the transform on layer7
seg7 = content[layer7_start:layer7_start+300]
print("\nLayer7 context:")
print(seg7)

# Find the Sve path (Sweden mainland - likely starts with id="Sve")
sve_match = re.search(r'id="(Sve[^"]*)"', content)
if sve_match:
    print(f"\nMainland path id: {sve_match.group(1)}")
    path_start = content.rfind('<path', 0, sve_match.start())
    print("Path tag:", content[path_start:path_start+200])

# Find all path IDs in layer7 region (Land layer)
# layer7 ends where layer8 begins
layer7_content = content[layer7_start:layer8_start]
path_ids_in_land = re.findall(r'id="([^"]+)"', layer7_content)
print(f"\nIDs in Land layer: {path_ids_in_land[:20]}")

# Find Gotland path - look in layer8 (Islands)
layer8_end = content.find('</g>', layer8_start + 100)
layer8_content = content[layer8_start:layer8_end+200]
island_ids = re.findall(r'id="([^"]+)"', layer8_content)
print(f"\nIDs in Islands layer: {island_ids[:20]}")

# Extract Stockholm and other city text elements with coordinates
city_texts = re.findall(
    r'<text[^>]*transform="([^"]*)"[^>]*>[^<]*(?:<tspan[^>]*x="([^"]+)"\s+y="([^"]+)"[^>]*>([^<]+)</tspan>)',
    content
)
print("\nCity text elements (first 20):")
for t, x, y, name in city_texts[:20]:
    print(f"  {name:25s} x={x:10s} y={y:10s} transform={t[:40]}")

# Find specific cities we care about
cities_of_interest = ['Stockholm', 'Gothenburg', 'Visby', 'Karlskrona', 'Uppsala', 
                       'Luleå', 'Goteborg', 'Göteborg']
print("\n--- Cities of interest ---")
for city in cities_of_interest:
    for pat in [city, city.replace('å', 'a').replace('ö', 'o')]:
        m = re.search(r'x="([^"]+)"\s+y="([^"]+)"[^>]*>'+pat, content)
        if m:
            print(f"  {city}: x={m.group(1)}, y={m.group(2)}")
            break

# Get transform on the text group (scale factor)
text_transform = re.search(r'<text[^>]*transform="scale\(([^)]+)\)"[^>]*>.*?Stockholm', content[:1400000], re.DOTALL)
if text_transform:
    print(f"\nText scale: {text_transform.group(1)}")
