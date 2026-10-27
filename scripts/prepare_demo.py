"""Prepare a live demo: reset the volatile sources so the next round rediscovers their stages (full gate 1),
after backing up the current sources.json. The audit log (history.json) and reports are untouched.
    python scripts/prepare_demo.py           -> reset
    python scripts/prepare_demo.py --undo    -> restore the backup taken by the last reset"""
import json, pathlib, shutil, sys
from datetime import datetime
DATA = pathlib.Path(__file__).resolve().parents[1] / "data"
P, B = DATA / "sources.json", DATA / "backups"
VOLATILE = {"Draft (prEN)", "Non-binding guidance", "Final text — deferred application"}

if "--undo" in sys.argv:
    bk = sorted(B.glob("sources_before_demo_*.json"))
    if not bk: sys.exit("no backup found")
    shutil.copy(bk[-1], P); print(f"restored {bk[-1].name}"); sys.exit()

B.mkdir(exist_ok=True)
bk = B / f"sources_before_demo_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
shutil.copy(P, bk)
src = json.loads(P.read_text(encoding="utf-8")); n = 0
for s in src:
    if s.get("status") in VOLATILE:
        s["stage"] = ""; s["note"] = ""; s["verified_on"] = "—"; n += 1
P.write_text(json.dumps(src, ensure_ascii=False, indent=2), encoding="utf-8")
for f in (DATA / "pending").glob("*"):
    f.unlink()
print(f"reset {n} volatile source(s); backup in {bk.name}; pending decisions cleared")
