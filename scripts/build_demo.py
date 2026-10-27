"""Build a self-contained HTML page from data/*.json so the result can be shown without a terminal.
Usage:  python scripts/build_demo.py     ->  demo/index.html  (open in any browser, works offline)"""
from __future__ import annotations
import html, json, pathlib
from collections import Counter
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "demo" / "index.html"

def load(name, default):
    p = DATA / f"{name}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

def esc(x): return html.escape("" if x is None else str(x))

matrix, profile, sources = load("matrix", []), load("profile", {}), load("sources", [])
history, reports = load("history", []), load("reports", [])

appl = Counter(r.get("applicability") or "—" for r in matrix)
by_theme = Counter(r["theme"] for r in matrix if r.get("applicability") == "Applicable")
src_status = Counter(s.get("status") for s in sources)
verified = sum(1 for s in sources if str(s.get("verified_on") or "").startswith("20"))
human_writes = sum(1 for h in history if str(h.get("actor","")).startswith("human:"))
agent_writes = len(history) - human_writes
last_report = reports[-1] if reports else None

def badge(v):
    cls = {"Applicable":"ok","Depends":"warn","Not applicable":"muted"}.get(v,"muted")
    return f'<span class="badge {cls}">{esc(v)}</span>'

def status_badge(v):
    cls = {"Final text — in force":"ok","Final text — deferred application":"info","Harmonised standard cited in the OJ":"ok2",
           "Draft (prEN)":"warn","Non-binding guidance":"muted","Published standard (not harmonised)":"info"}.get(v,"muted")
    return f'<span class="badge {cls}">{esc(v)}</span>'

rows_sources = "".join(
    f"<tr><td>{esc(s['id'])}</td><td>{esc(s['source'])}</td><td>{status_badge(s.get('status'))}</td>"
    f"<td>{esc(s.get('stage') or '')}</td><td>{esc(s.get('verified_on') or '—')}</td><td class='note'>{esc(s.get('note') or '')}</td></tr>"
    for s in sources)

rows_hist = "".join(
    f"<tr><td>{esc(h['ts'][:16].replace('T',' '))}</td><td>{esc(h['id'])}</td><td>{esc(h['field'])}</td>"
    f"<td class='note'>{esc(h.get('old'))}</td><td class='note'>{esc(h.get('new'))}</td>"
    f"<td><span class='badge {'ok' if str(h.get('actor','')).startswith('human:') else 'warn'}'>{esc(h.get('actor'))}</span></td>"
    f"<td class='note'><a href='{esc(h.get('basis'))}' target='_blank'>{esc(str(h.get('basis'))[:60])}</a></td></tr>"
    for h in reversed(history[-80:]))

rounds_html = "".join(
    f"<details {'open' if i == len(reports)-1 else ''}><summary><b>Ronda {esc(r['round'])}</b> — "
    f"{len(r.get('sources_changed',[]))} fonte(s) alterada(s), {esc(r.get('evidence_unknown_count', 0))} verificações de evidência por fazer</summary>"
    f"<p class='summary'>{esc(r.get('summary'))}</p>"
    + ("<ul>" + "".join(f"<li>{esc(c)}</li>" for c in r.get("sources_changed", [])) + "</ul>" if r.get("sources_changed") else "")
    + "</details>"
    for i, r in enumerate(reports))

applicable_rows = "".join(
    f"<tr><td>{esc(r['id'])}</td><td>{esc(r['theme'])}</td><td class='note'>{esc(r['requirement'][:160])}{'…' if len(r['requirement'])>160 else ''}</td>"
    f"<td>{esc(r.get('ai_act_basis'))}</td><td>{status_badge(r.get('source_status'))}</td><td>{esc(r.get('implementation_status') or '')}</td></tr>"
    for r in matrix if r.get("applicability") == "Applicable")

profile_html = "".join(f"<tr><td>{esc(k)}</td><td><b>{esc(v)}</b></td></tr>" for k, v in profile.items())

page = f"""<!doctype html><html lang="pt"><head><meta charset="utf-8"><title>AI Governance Risk Matrix — estado</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{{--ink:#1f2937;--muted:#6b7280;--line:#e5e7eb;--bg:#f8fafc;--navy:#1F3A5F;--teal:#2E6E8E}}
*{{box-sizing:border-box}} body{{margin:0;font:15px/1.5 system-ui,Segoe UI,Arial,sans-serif;color:var(--ink);background:#fff}}
header{{background:var(--navy);color:#fff;padding:28px 40px}} header h1{{margin:0 0 4px;font-size:24px}} header p{{margin:0;opacity:.85}}
main{{padding:24px 40px;max-width:1400px}} h2{{color:var(--teal);font-size:18px;margin:32px 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px}}
.card{{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:14px 16px}} .card .n{{font-size:30px;font-weight:700;color:var(--navy)}} .card .l{{color:var(--muted);font-size:13px}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th{{text-align:left;background:var(--bg);border-bottom:2px solid var(--line);padding:8px}} td{{border-bottom:1px solid var(--line);padding:7px 8px;vertical-align:top}}
.note{{color:var(--muted);max-width:520px}} .badge{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px;white-space:nowrap}}
.ok{{background:#dcfce7;color:#166534}} .ok2{{background:#bbf7d0;color:#14532d}} .warn{{background:#fef3c7;color:#92400e}} .info{{background:#dbeafe;color:#1e3a8a}} .muted{{background:#f1f5f9;color:#475569}}
details{{border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:8px 0;background:#fff}} summary{{cursor:pointer}} .summary{{margin:10px 0}}
.rule{{background:#fff7ed;border-left:4px solid #f59e0b;padding:10px 14px;border-radius:6px;margin:10px 0}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:24px}} @media(max-width:900px){{.two{{grid-template-columns:1fr}}}}
footer{{color:var(--muted);font-size:12px;padding:24px 40px}}
</style></head><body>
<header><h1>AI Governance Risk Matrix — estado atual</h1>
<p>Gerado a {datetime.now().strftime('%Y-%m-%d %H:%M')} a partir de data/*.json. O catálogo é fixo; o Perfil decide o que se aplica; os agentes propõem; as pessoas decidem.</p></header>
<main>
<div class="cards">
<div class="card"><div class="n">{len(matrix)}</div><div class="l">linhas no catálogo</div></div>
<div class="card"><div class="n">{appl.get('Applicable',0)}</div><div class="l">aplicáveis a esta organização</div></div>
<div class="card"><div class="n">{appl.get('Depends',0)}</div><div class="l">dependem da classificação</div></div>
<div class="card"><div class="n">{verified}/{len(sources)}</div><div class="l">fontes com data de verificação</div></div>
<div class="card"><div class="n">{len(reports)}</div><div class="l">rondas gravadas</div></div>
<div class="card"><div class="n">{human_writes}</div><div class="l">escritas aprovadas por pessoas</div></div>
<div class="card"><div class="n">{agent_writes}</div><div class="l">escritas automáticas (só datas de reconfirmação)</div></div>
</div>

<p><a href="http://127.0.0.1:8765" target="_blank"><b>Abrir a consola</b></a> · <a href="http://127.0.0.1:8765/glossary" target="_blank">Glossário de siglas</a> (decisões pendentes) · regenerar esta página: <code>python scripts/build_demo.py</code></p>
<div class="rule"><b>O que os agentes nunca escrevem:</b> classe de risco, aplicabilidade, estado de implementação, controlo implementado, responsável. Imposto em código (<code>store.update_field</code>), não por prompt. Cada escrita fica em <code>history.json</code> com ator e base.</div>

<h2>Última ronda</h2>
{f"<p class='summary'><b>{esc(last_report['round'])}</b> — {esc(last_report['summary'])}</p>" if last_report else "<p>Ainda não há rondas gravadas.</p>"}

<div class="two"><div>
<h2>Perfil da organização</h2><table>{profile_html}</table>
</div><div>
<h2>Aplicáveis por tema</h2><table>{"".join(f"<tr><td>{esc(t)}</td><td><b>{n}</b></td></tr>" for t,n in by_theme.most_common())}</table>
<h2>Estado das fontes</h2><table>{"".join(f"<tr><td>{status_badge(k)}</td><td><b>{n}</b></td></tr>" for k,n in src_status.most_common())}</table>
</div></div>

<h2>Fontes vigiadas</h2>
<table><tr><th>ID</th><th>Fonte</th><th>Estado</th><th>Fase</th><th>Verificada em</th><th>Nota (o que o agente encontrou, aprovado por uma pessoa)</th></tr>{rows_sources}</table>

<h2>Rondas</h2>{rounds_html or "<p>—</p>"}

<h2>Linhas aplicáveis ({appl.get('Applicable',0)})</h2>
<table><tr><th>ID</th><th>Tema</th><th>Requisito / risco</th><th>Base AI Act</th><th>Estado da fonte</th><th>Implementação</th></tr>{applicable_rows}</table>

<h2>Registo de auditoria (últimas {min(80,len(history))} escritas)</h2>
<table><tr><th>Quando</th><th>ID</th><th>Campo</th><th>Antes</th><th>Depois</th><th>Ator</th><th>Base</th></tr>{rows_hist or "<tr><td colspan=7>Sem escritas ainda.</td></tr>"}</table>
</main>
<footer>AI Governance Risk Matrix · CrewAI Flow com gates humanos · ficheiro gerado localmente, sem dados enviados a terceiros.</footer>
</body></html>"""
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(page, encoding="utf-8")
print(f"{OUT}  ({len(matrix)} rows, {len(sources)} sources, {len(reports)} rounds, {len(history)} history entries)")
