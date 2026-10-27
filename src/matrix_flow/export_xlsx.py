"""Export data/*.json back to a workbook snapshot (values only) so non-technical owners keep their Excel view.
For the fully formatted workbook, re-run the original builder with these values."""
import json, pathlib, sys
from openpyxl import Workbook
DATA = pathlib.Path(__file__).resolve().parents[2] / "data"

def main(out="matrix_export.xlsx"):
    wb = Workbook(); ws = wb.active; ws.title = "Matrix"
    rows = json.loads((DATA / "matrix.json").read_text(encoding="utf-8"))
    ws.append(list(rows[0].keys()))
    for r in rows:
        ws.append(["; ".join(v) if isinstance(v, list) else v for v in r.values()])
    hs = wb.create_sheet("History")
    hist = json.loads((DATA / "history.json").read_text(encoding="utf-8")) if (DATA / "history.json").exists() else []
    if hist:
        hs.append(list(hist[0].keys()))
        for h in hist: hs.append(list(h.values()))
    wb.save(out); print(out)

if __name__ == "__main__":
    main(*sys.argv[1:])
