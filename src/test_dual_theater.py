"""Dual-theater integration test: validates both CSV loading, encoding, inventory,
coordinate bounds, backend /theater and /state endpoints, and SVG map presence."""
import os, sys, importlib, pathlib, urllib.request, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
ROOT = os.path.dirname(os.path.dirname(__file__))

results = []
def check(label, ok):
    status = "PASS" if ok else "FAIL"
    results.append((label, ok))
    print(f"  [{status}] {label}")

print("=" * 60)
print("DUAL-THEATER INTEGRATION TEST")
print("=" * 60)

# ── Test 1: Sweden CSV — 11 bases including naval ─────────────
print("\n[A] SWEDEN CSV LOADING")
os.environ["SAAB_MODE"] = "sweden"
import core.models as cm; importlib.reload(cm)
state = cm.load_battlefield_state(os.path.join(ROOT, "data", "Swedish_Military_Installations.csv"))
check("Sweden: 11 bases loaded", len(state.bases) == 11)
naval = [b for b in state.bases if "Naval" in b.name]
check("Sweden: 2 naval bases (Musko + Karlskrona)", len(naval) == 2)
inv_keys = set(state.bases[0].inventory.keys())
expected_sweden = {"patriot-pac3", "iris-t-sls", "saab-nimbrix", "meteor", "nasams"}
check("Sweden: 5 correct inventory keys", inv_keys == expected_sweden)
special = [b for b in state.bases if any(c in b.name for c in ["å","ä","ö","Å","Ä","Ö"])]
check("Sweden: Swedish chars decoded correctly (>=3 bases)", len(special) >= 3)
coords_ok = all(-500 <= b.x <= 300 and -450 <= b.y <= 750 for b in state.bases)
check("Sweden: all coords in valid range", coords_ok)

# ── Test 2: Boreal CSV — 12 bases ─────────────────────────────
print("\n[B] BOREAL CSV LOADING")
os.environ["SAAB_MODE"] = "boreal"
importlib.reload(cm)
state2 = cm.load_battlefield_state(os.path.join(ROOT, "data", "input", "Boreal_passage_coordinates.csv"))
check("Boreal: 12 bases loaded", len(state2.bases) == 12)
inv_keys2 = set(state2.bases[0].inventory.keys())
expected_boreal = {"patriot-pac3", "nasams", "coyote-block2", "merops-interceptor"}
check("Boreal: 4 correct inventory keys (incl. coyote+merops)", inv_keys2 == expected_boreal)
coords_ok2 = all(0 <= b.x <= 1600 and 0 <= b.y <= 1400 for b in state2.bases)
check("Boreal: all coords in valid range", coords_ok2)

# ── Test 3: Backend HTTP endpoints ────────────────────────────
print("\n[C] BACKEND HTTP ENDPOINTS")
for port, exp_mode, exp_count in [(8001, "boreal", 12), (8002, "sweden", 11)]:
    for endpoint in ("theater", "state"):
        url = f"http://127.0.0.1:{port}/{endpoint}"
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                d = json.loads(r.read())
                if endpoint == "theater":
                    check(f"Port {port} /theater: mode={d.get('mode')}", d.get("mode") == exp_mode)
                else:
                    check(f"Port {port} /state: base_count={d.get('base_count')}", d.get("base_count") == exp_count)
        except Exception as e:
            check(f"Port {port} /{endpoint}: reachable", False)
            print(f"       (skipped — server not running on port {port}: {e})")

# ── Test 4: SVG map files exist ───────────────────────────────
print("\n[D] SVG MAP FILES")
check("frontend/the-boreal-passage-map.svg exists",
      pathlib.Path(ROOT, "frontend", "the-boreal-passage-map.svg").exists())
check("frontend/sweden-military-map.svg exists",
      pathlib.Path(ROOT, "frontend", "sweden-military-map.svg").exists())
check("data/input/sweden-military-map.svg exists",
      pathlib.Path(ROOT, "data", "input", "sweden-military-map.svg").exists())

# ── Summary ───────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for _, ok in results if ok)
total  = len(results)
print(f"TOTAL: {passed}/{total} checks passed {'✓' if passed==total else '✗'}")
print("=" * 60)
sys.exit(0 if passed == total else 1)
