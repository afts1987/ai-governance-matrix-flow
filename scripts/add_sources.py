"""One-off: add sources that were missing (prEN 18229-4 and -5). Safe to run twice."""
import json, pathlib
p = pathlib.Path(__file__).resolve().parents[1] / "data" / "sources.json"
src = json.loads(p.read_text(encoding="utf-8")); ids = {s["id"] for s in src}
new = [
 {"id":"S33","source":"prEN 18229-4 — Trustworthiness framework: accuracy","type":"CEN-CENELEC JTC 21 project","status":"Draft (prEN)","stage":"","reference":"Supports Art. 15 (accuracy)","verified_on":"—","how_verified":"Listed in a secondary overview (O. Patel, 21 Oct 2026) as working draft; not verified on CEN-CENELEC","note":""},
 {"id":"S35","source":"CNCS — Centro Nacional de Cibersegurança (Portugal): NIS2 authority, incident notification point, national cybersecurity framework (QNRCS) and guidance","type":"National regulator","status":"Non-binding guidance","stage":"","reference":"https://www.cncs.gov.pt — Decree-Law 125/2025 (NIS2 transposition)","verified_on":"—","how_verified":"Added as a watched regulator; publications not yet verified by the agent","note":"Watch: new guidance, notification templates, deadlines, QNRCS updates."},
 {"id":"S36","source":"CNPD — Comissão Nacional de Proteção de Dados (Portugal): GDPR authority; list of processing requiring a DPIA, deliberations and guidance on AI","type":"National regulator","status":"Non-binding guidance","stage":"","reference":"https://www.cnpd.pt","verified_on":"—","how_verified":"Added as a watched regulator; publications not yet verified by the agent","note":"Watch: DPIA list, deliberations on AI and automated decisions, guidance on AI tools at work."},
 {"id":"S34","source":"prEN 18229-5 — Trustworthiness framework: robustness","type":"CEN-CENELEC JTC 21 project","status":"Draft (prEN)","stage":"","reference":"Supports Art. 15 (robustness)","verified_on":"—","how_verified":"Listed in a secondary overview (O. Patel, 21 Oct 2026) as working draft; not verified on CEN-CENELEC","note":""},
]
added = [s for s in new if s["id"] not in ids]; src.extend(added)
p.write_text(json.dumps(src, ensure_ascii=False, indent=2), encoding="utf-8"); print(f"added {len(added)}")
