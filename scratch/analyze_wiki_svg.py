"""
Download and analyze the Wikipedia Sweden SVG to extract coordinate system.
"""
import urllib.request
import re

url = "https://upload.wikimedia.org/wikipedia/commons/5/54/Map_of_Sweden_Cities_%28polar_stereographic%29.svg"
print("Downloading SVG...")
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    content = resp.read().decode("utf-8")

print(f"Downloaded {len(content)} chars")

# Extract viewBox / width / height from root element
vb = re.search(r'viewBox=["\']([^"\']+)["\']', content)
w = re.search(r'<svg[^>]+width=["\']([^"\']+)["\']', content)
h = re.search(r'<svg[^>]+height=["\']([^"\']+)["\']', content)
print(f"viewBox: {vb.group(1) if vb else 'NOT FOUND'}")
print(f"width: {w.group(1) if w else 'NOT FOUND'}")
print(f"height: {h.group(1) if h else 'NOT FOUND'}")

# Look for Sweden outline / boundary path
# Search for id/label patterns
ids = re.findall(r'id=["\']([^"\']{2,40})["\']', content[:5000])
print("\nFirst 20 IDs:", ids[:20])

# Look for Sweden main boundary
for pattern in ['sweden', 'boundary', 'outline', 'coast', 'land']:
    hits = [(m.start(), content[max(0,m.start()-50):m.start()+100])
            for m in re.finditer(pattern, content, re.IGNORECASE)]
    if hits:
        print(f"\n--- '{pattern}' occurrences: {len(hits)} ---")
        for pos, ctx in hits[:2]:
            print(f"  pos={pos}: ...{ctx}...")

# Find cities mentioned to locate their coordinates
stockholm_hits = [(m.start(), content[max(0,m.start()-200):m.start()+100])
                  for m in re.finditer('Stockholm', content)]
print(f"\n--- 'Stockholm' occurrences: {len(stockholm_hits)} ---")
for pos, ctx in stockholm_hits[:2]:
    print(f"  ...{ctx}...")

# Save the SVG for local analysis
with open("scratch/sweden_wiki.svg", "w", encoding="utf-8") as f:
    f.write(content)
print("\nSaved to scratch/sweden_wiki.svg")
print("First 1000 chars:")
print(content[:1000])
