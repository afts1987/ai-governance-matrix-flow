"""One-off: derive the 'stage' field from notes written before stage was stored as a field.
python scripts/backfill_stage.py"""
import json, pathlib, re
p = pathlib.Path(__file__).resolve().parents[1] / "data" / "sources.json"
src = json.loads(p.read_text(encoding="utf-8"))
n = 0
for s in src:
    if not s.get("stage"):
        m = re.search(r"Stage:\s*([^.]+)\.", s.get("note") or "")
        if m:
            s["stage"] = m.group(1).strip().lower(); n += 1
        elif "under approval" in (s.get("note") or "").lower():
            s["stage"] = "under approval"; n += 1
p.write_text(json.dumps(src, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"stage set on {n} source(s)")
