"""Local console for the AI Governance Matrix Flow. Standard library only. No terminal needed during a demo.
Start:  python scripts/gate_ui.py   (or double-click start_demo.cmd)  ->  http://localhost:8765
Lets a person: run a round, decide at the human gates, see live progress, download the versioned Excel, open the status page."""
from __future__ import annotations
import glob, html, json, os, pathlib, re, subprocess, sys, threading, time, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import traceback
from urllib.parse import parse_qs, unquote
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from matrix_flow import importer
from matrix_flow.glossary import GLOSSARY

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA, PENDING, EXPORTS = ROOT / "data", ROOT / "data" / "pending", ROOT / "exports"
LOG = PENDING / "run.log"
PY = sys.executable
PORT = 8765
_proc: subprocess.Popen | None = None

CSS = """<style>
:root{--navy:#1F3A5F;--teal:#2E6E8E;--line:#e5e7eb;--bg:#f8fafc;--muted:#6b7280}
*{box-sizing:border-box} body{margin:0;font:15px/1.5 system-ui,Segoe UI,Arial;color:#1f2937;background:#fff}
header{background:var(--navy);color:#fff;padding:18px 36px;display:flex;align-items:center;justify-content:space-between}
header h1{margin:0;font-size:20px} header nav a{color:#fff;opacity:.9;margin-left:18px;text-decoration:none} header nav a:hover{opacity:1;text-decoration:underline}
main{padding:22px 36px;max-width:1100px} h2{color:var(--teal);font-size:17px;margin:26px 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}
.card{border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:12px 0;background:#fff}
.badge{display:inline-block;padding:2px 9px;border-radius:999px;font-size:12px;margin-right:6px}
.high{background:#dcfce7;color:#166534}.medium{background:#fef3c7;color:#92400e}.low{background:#fee2e2;color:#991b1b}.muted{background:#f1f5f9;color:#475569}
.run{background:#dbeafe;color:#1e3a8a}.idle{background:#f1f5f9;color:#475569}.wait{background:#fef3c7;color:#92400e}
.note{color:var(--muted)} label{display:flex;gap:12px;align-items:flex-start;cursor:pointer} input[type=checkbox]{margin-top:6px;transform:scale(1.3)}
button,.btn{background:var(--teal);color:#fff;border:0;border-radius:8px;padding:10px 18px;font-size:15px;cursor:pointer;margin-right:10px;text-decoration:none;display:inline-block}
button.secondary,.btn.secondary{background:#64748b} button:disabled{background:#cbd5e1;cursor:not-allowed}
.ok{background:#ecfdf5;border-left:4px solid #10b981;padding:12px 16px;border-radius:6px}
.rule{background:#fff7ed;border-left:4px solid #f59e0b;padding:10px 14px;border-radius:6px;margin:10px 0}
pre{background:#0f172a;color:#e2e8f0;padding:12px;border-radius:8px;font-size:12px;max-height:260px;overflow:auto}
table{border-collapse:collapse;width:100%;font-size:13px} th{text-align:left;background:var(--bg);border-bottom:2px solid var(--line);padding:8px} td{border-bottom:1px solid var(--line);padding:7px 8px;vertical-align:top}
.steps{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:12px 0} .step{border:1px solid var(--line);border-radius:8px;padding:8px 10px;font-size:13px;text-align:center}
.step.done{background:#dcfce7} .step.now{background:#dbeafe;font-weight:600}
</style>"""

def esc(x): return html.escape("" if x is None else str(x))
def jload(p, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

def page(body, refresh=None):
    meta = f"<meta http-equiv='refresh' content='{refresh}'>" if refresh else ""
    return (f"<!doctype html><html lang='pt'><head><meta charset='utf-8'>{meta}<title>AI Governance Matrix</title>{CSS}</head><body>"
            "<header><h1>AI Governance Matrix — consola</h1><nav><a href='/'>Ronda</a><a href='/import'>Importar matriz</a><a href='/versions'>Versões Excel</a><a href='/status'>Estado</a><a href='/glossary'>Glossário</a></nav></header>"
            f"<main>{body}</main></body></html>")

# ---------------- flow process ----------------
def running() -> bool:
    return _proc is not None and _proc.poll() is None

def start_flow():
    global _proc
    if running(): return
    PENDING.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "HITL_MODE": "file", "PYTHONUNBUFFERED": "1"}
    # load .env so a double-clicked start has the keys
    envf = ROOT / ".env"
    if envf.exists():
        for line in envf.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1); env.setdefault(k.strip(), v.split("#")[0].strip())
    env["HITL_MODE"] = "file"; env["PYTHONIOENCODING"] = "utf-8"; env["PYTHONUTF8"] = "1"
    logf = open(LOG, "w", encoding="utf-8")
    _proc = subprocess.Popen([PY, "-u", "-m", "matrix_flow.flow"], cwd=ROOT, env=env, stdout=logf, stderr=subprocess.STDOUT)
    logf.close()  # the child keeps its own handle

def pending(name):
    d = jload(PENDING / f"{name}.json", None)
    return None if not d or d.get("decided") else d

def phase():
    """What the person should see now."""
    if running(): return "running"
    if pending("sources"): return "gate1"
    if pending("report"): return "gate2"
    if (PENDING / "state.json").exists(): return "resume"
    return "idle"

def log_tail(n=40):
    if not LOG.exists(): return ""
    lines = [l for l in LOG.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip() and not l.strip().startswith(("╭", "╰", "│  ", "│"))]
    return "\n".join(lines[-n:])

def prepare_sources() -> str:
    """Same as scripts/prepare_demo.py, in-process: reset volatile sources so the next round rediscovers their stages."""
    import shutil
    src_p, bk_dir = DATA / "sources.json", DATA / "backups"
    volatile = {"Draft (prEN)", "Non-binding guidance", "Final text — deferred application"}
    bk_dir.mkdir(exist_ok=True)
    bk = bk_dir / f"sources_before_demo_{time.strftime('%Y%m%d-%H%M%S')}.json"
    shutil.copy(src_p, bk)
    src = jload(src_p, []); n = 0
    for s_ in src:
        if s_.get("status") in volatile:
            s_["stage"] = ""; s_["note"] = ""; s_["verified_on"] = "—"; n += 1
    src_p.write_text(json.dumps(src, ensure_ascii=False, indent=2), encoding="utf-8")
    for f in PENDING.glob("*.json"):
        try: f.unlink()
        except OSError: pass
    return f"Fontes repostas: {n} voláteis a zero (cópia em backups/{bk.name}). A próxima ronda volta a descobrir as fases."

# ---------------- views ----------------
def steps_html(ph):
    order = ["Vigiar fontes", "Gate 1", "Auditar evidência", "Relatório", "Gate 2"]
    now = {"running": 0, "gate1": 1, "resume": 2, "gate2": 4, "idle": -1}[ph]
    log = LOG.read_text(encoding="utf-8", errors="replace") if LOG.exists() else ""
    if ph == "running":
        now = 3 if "report_" in log else 2 if "audit_" in log else 0
    return "<div class='steps'>" + "".join(
        f"<div class='step {'done' if i < now else 'now' if i == now else ''}'>{s}</div>" for i, s in enumerate(order)) + "</div>"

def view_round():
    ph = phase()
    parts = [f"<h2>Ronda <span class='badge {'run' if ph=='running' else 'wait' if ph in ('gate1','gate2') else 'idle'}'>"
             f"{ {'running':'a correr','gate1':'à espera de decisão (gate 1)','gate2':'à espera de decisão (gate 2)','resume':'pronta a continuar','idle':'parada'}[ph] }</span></h2>",
             steps_html(ph)]
    if ph == "idle":
        parts.append("<div class='card'><p>Uma ronda verifica as fontes voláteis em fontes primárias, para para uma pessoa decidir, audita a evidência, escreve o relatório e, depois da aprovação, grava e exporta uma nova versão do Excel.</p>"
                     "<form method='post' action='/run' style='display:inline'><button type='submit'>Correr uma ronda</button></form>"
                     "<form method='post' action='/prepare' style='display:inline'><button class='secondary' type='submit' onclick=\"return confirm('Repor as fontes voláteis ao estado inicial? O histórico fica guardado.')\">Preparar demonstração (repor fontes)</button></form></div>")
    elif ph == "running":
        parts.append(f"<div class='card'><p>A trabalhar. Esta página atualiza-se sozinha.</p><pre>{esc(log_tail())}</pre></div>")
        return page("".join(parts), refresh=5)
    elif ph == "resume":
        parts.append("<div class='card'><p>Decisão gravada. A ronda pode continuar de onde ficou, sem repetir pesquisas.</p>"
                     "<form method='post' action='/run'><button type='submit'>Continuar a ronda</button></form></div>")
    elif ph == "gate1":
        src = pending("sources")
        items = "".join(
            f"<div class='card'><label><input type='checkbox' name='approve' value='{esc(c['source_id'])}' {'checked' if c.get('confidence')=='high' else ''}>"
            f"<div><b>{esc(c['source_id'])}</b> &nbsp;<span class='badge {esc(c.get('confidence','low'))}'>confiança {esc(c.get('confidence'))}</span>"
            f"<span class='badge muted'>{esc(c.get('proposed_status') or 'estado inalterado')}</span>"
            f"{('<span class=badge muted>fase: '+esc(c.get('stage'))+'</span>') if c.get('stage') else ''}"
            f"<div>{esc(c.get('what_changed'))}</div>"
            f"<div class='note'>Evidência: <a href='{esc(c.get('evidence_url'))}' target='_blank'>{esc(c.get('evidence_url'))}</a> {('· datada de '+esc(c.get('evidence_date'))) if c.get('evidence_date') else ''}</div>"
            f"</div></label></div>" for c in src.get("changes", []))
        parts.append("<h2>Gate 1 — mudanças de fontes propostas</h2>"
                     "<div class='rule'>Regra: só aprovar o que tem evidência primária que suporte o facto. Confiança 'low' ou 'medium' fica desmarcada por omissão.</div>"
                     f"<form method='post' action='/decide/sources'>{items}<p><button type='submit'>Gravar decisão e continuar</button>"
                     "<button class='secondary' type='submit' name='none' value='1'>Rejeitar todas e continuar</button></p></form>")
    elif ph == "gate2":
        rep = pending("report"); r = rep.get("report") or {}
        parts.append(f"<h2>Gate 2 — relatório da ronda {esc(rep.get('round'))}</h2><div class='card'><p>{esc(r.get('summary'))}</p>"
                     + ("<ul>" + "".join(f"<li>{esc(c)}</li>" for c in r.get("sources_changed", [])) + "</ul>" if r.get("sources_changed") else "")
                     + f"<p class='note'>Verificações de evidência por fazer: <b>{esc(r.get('evidence_unknown_count'))}</b> · em falta: {esc(len(r.get('evidence_missing', [])))}</p></div>"
                     "<form method='post' action='/decide/report'><button type='submit' name='ok' value='1'>Aprovar, gravar e exportar o Excel</button>"
                     "<button class='secondary' type='submit' name='ok' value='0'>Descartar relatório</button></form>")
    if LOG.exists() and ph != "running":
        parts.append(f"<details><summary class='note'>Registo da última execução</summary><pre>{esc(log_tail(60))}</pre></details>")
    return page("".join(parts))

def view_versions():
    files = sorted(glob.glob(str(EXPORTS / "*.xlsx")), reverse=True)
    rows = "".join(f"<tr><td>{esc(pathlib.Path(f).name)}</td><td>{time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(f)))}</td>"
                   f"<td><a class='btn' href='/download/{esc(pathlib.Path(f).name)}'>Descarregar</a></td></tr>" for f in files)
    return page("<h2>Versões do Excel</h2><p class='note'>Uma versão nova por ronda aprovada. O JSON é a verdade; o Excel é a vista.</p>"
                "<form method='post' action='/export'><button type='submit'>Gerar versão agora</button></form>"
                f"<table><tr><th>Ficheiro</th><th>Gerado</th><th></th></tr>{rows or '<tr><td colspan=3>Ainda não há versões.</td></tr>'}</table>")

def view_status():
    try:
        subprocess.run([PY, str(ROOT / "scripts" / "build_demo.py")], cwd=ROOT, check=True, capture_output=True)
        return (ROOT / "demo" / "index.html").read_text(encoding="utf-8")
    except Exception as e:
        return page(f"<p>Não foi possível gerar a página de estado: {esc(e)}</p>")

def _multipart(body: bytes, ctype: str) -> dict:
    """Minimal multipart/form-data parser (stdlib only, python 3.13 has no cgi)."""
    m = re.search(r'boundary="?([^";]+)"?', ctype); out = {}
    if not m: return out
    for part in body.split(b"--" + m.group(1).encode()):
        if b"\r\n\r\n" not in part: continue
        head, _, content = part.partition(b"\r\n\r\n"); content = content.rstrip(b"\r\n").removesuffix(b"--")
        name = re.search(rb'name="([^"]+)"', head); fname = re.search(rb'filename="([^"]*)"', head)
        if not name: continue
        out[name.group(1).decode()] = (fname.group(1).decode(), content) if fname else content.decode("utf-8", "replace")
    return out

def view_import(msg=""):
    meta = jload(DATA / "matrix_meta.json", None)
    cur = (f"<div class='card'><b>Matriz ativa:</b> {esc(meta['label'])} — {esc(meta['rows'])} linhas, importada a {esc(meta['imported_at'])}. "
           "<form method='post' action='/import/restore' style='display:inline'><button class='secondary' type='submit'>Repor a matriz de base</button></form></div>"
           if meta else "<div class='card'><b>Matriz ativa:</b> catálogo de base (98 linhas).</div>")
    return page(f"<h2>Importar a sua matriz</h2>{('<div class=ok>'+esc(msg)+'</div>') if msg else ''}{cur}"
                "<div class='card'><p>Carregue a sua matriz de risco em Excel (.xlsx) ou CSV. A primeira linha com três ou mais células preenchidas é tratada como cabeçalho. "
                "No passo seguinte mapeia as suas colunas para o formato da plataforma; as rondas passam a correr sobre a sua matriz, com as mesmas fontes vigiadas.</p>"
                "<form method='post' action='/import/upload' enctype='multipart/form-data'><input type='file' name='file' accept='.xlsx,.csv' required> "
                "<input type='text' name='label' placeholder='Nome (ex.: Matriz Banco X 2026)' style='padding:8px;min-width:280px'> <button type='submit'>Carregar e mapear</button></form></div>"
                "<h2>Sincronizar o trabalho feito no Excel</h2><div class='card'><p>Carregue um Excel <b>exportado por esta plataforma</b> em que preencheu as colunas amarelas "
                "(controlo implementado, responsável, estado de implementação, data de revisão). Só essas quatro colunas são lidas, linha a linha pelo ID; cada alteração fica no registo de auditoria com o ator <code>human:excel-sync</code>.</p>"
                "<form method='post' action='/import/sync' enctype='multipart/form-data'><input type='file' name='file' accept='.xlsx' required> <button type='submit'>Sincronizar colunas amarelas</button></form></div>"
                "<p class='note'>O que não existir na sua matriz fica com valores por omissão (papel: qualquer; classe: qualquer; setor: todos), e a aplicabilidade é recalculada pelo Perfil. A matriz anterior fica guardada em data/backups/.</p>")

def view_mapping(headers, nrows, label, auto):
    opts = lambda sel: "<option value=''>— não mapear —</option>" + "".join(f"<option value='{esc(h)}' {'selected' if h==sel else ''}>{esc(h)}</option>" for h in headers)
    rows = "".join(f"<tr><td><b>{esc(lab)}</b>{' <span class=badge style=\"background:#fee2e2;color:#991b1b\">obrigatório</span>' if req else ''}</td>"
                   f"<td><select name='map_{f}'>{opts(auto.get(f))}</select></td></tr>" for f, lab, req, _ in importer.FIELDS)
    return page(f"<h2>Mapear colunas — {esc(label)}</h2><p class='note'>{nrows} linhas detetadas. Colunas encontradas: {', '.join(esc(h) for h in headers)}</p>"
                f"<form method='post' action='/import/apply'><input type='hidden' name='label' value='{esc(label)}'><table><tr><th>Campo da plataforma</th><th>Coluna do seu ficheiro</th></tr>{rows}</table>"
                "<p><button type='submit'>Importar para a plataforma</button> <a class='btn secondary' href='/import'>Cancelar</a></p></form>")

def view_glossary():
    body = "".join(f"<h2>{esc(sec)}</h2><table><tr><th style='width:28%'>Sigla / termo</th><th>Significado</th></tr>"
                   + "".join(f"<tr><td><b>{esc(k)}</b></td><td>{esc(v)}</td></tr>" for k, v in items) + "</table>" for sec, items in GLOSSARY)
    return page("<p class='note'>Siglas e termos usados na matriz, na consola e nos ficheiros exportados.</p>" + body)

# ---------------- server ----------------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, body, code=200, ctype="text/html; charset=utf-8", raw=None):
        b = raw if raw is not None else body.encode("utf-8")
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b)))
        if raw is not None: self.send_header("Content-Disposition", f"attachment; filename=\"{self.path.rsplit('/',1)[-1]}\"")
        self.end_headers(); self.wfile.write(b)
    def _redirect(self, to="/"):
        self.send_response(303); self.send_header("Location", to); self.end_headers()
    def do_GET(self):
        try:
            return self._get()
        except Exception:
            return self._send(page(f"<div class='rule'><b>Erro na consola</b><pre>{esc(traceback.format_exc())}</pre></div><p><a class='btn' href='/'>Voltar</a></p>"), 500)

    def do_POST(self):
        try:
            return self._post()
        except Exception:
            return self._send(page(f"<div class='rule'><b>Erro na consola</b><pre>{esc(traceback.format_exc())}</pre></div><p><a class='btn' href='/'>Voltar</a></p>"), 500)

    def _get(self):
        if self.path == "/": return self._send(view_round())
        if self.path == "/versions": return self._send(view_versions())
        if self.path == "/import": return self._send(view_import())
        if self.path == "/glossary": return self._send(view_glossary())
        if self.path == "/status": return self._send(view_status())
        if self.path.startswith("/download/"):
            f = EXPORTS / unquote(self.path[len("/download/"):])
            if f.exists() and f.suffix == ".xlsx":
                return self._send("", raw=f.read_bytes(), ctype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            return self._send(page("<p>Ficheiro não encontrado.</p>"), 404)
        return self._send(page("<p>Página não encontrada.</p>"), 404)
    def _post(self):
        n = int(self.headers.get("Content-Length", 0)); raw = self.rfile.read(n)
        ctype = self.headers.get("Content-Type", "")
        if self.path == "/import/upload":
            f = _multipart(raw, ctype); up = f.get("file"); label = f.get("label") or (up[0] if up else "import")
            if not up or not up[1]: return self._send(view_import("Nenhum ficheiro recebido."))
            headers, body = importer.read_table(up[0], up[1])
            if not headers: return self._send(view_import("Não encontrei uma linha de cabeçalho com pelo menos três colunas."))
            PENDING.mkdir(parents=True, exist_ok=True)
            (PENDING / "import.json").write_text(json.dumps({"headers": headers, "body": [[(c.isoformat() if hasattr(c, "isoformat") else c) for c in r] for r in body], "label": label}, ensure_ascii=False, default=str), encoding="utf-8")
            return self._send(view_mapping(headers, len(body), label, importer.guess_mapping(headers)))
        if self.path == "/import/sync":
            f = _multipart(raw, ctype); up = f.get("file")
            if not up or not up[1]: return self._send(view_import("Nenhum ficheiro recebido."))
            res = importer.sync_from_export(up[0], up[1])
            if "error" in res: return self._send(view_import(res["error"]))
            extra = (f" IDs desconhecidos ignorados: {', '.join(res['unknown'])}." if res["unknown"] else "")
            return self._send(view_import(f"Sincronização concluída: {res['rows']} linhas lidas, {res['changed']} campo(s) atualizado(s).{extra}"))
        form = parse_qs(raw.decode("utf-8"))
        if self.path == "/import/apply":
            st = jload(PENDING / "import.json", None)
            if not st: return self._send(view_import("Sessão de importação expirada; carregue o ficheiro outra vez."))
            mapping = {f: form.get(f"map_{f}", [""])[0] for f, *_ in importer.FIELDS if form.get(f"map_{f}", [""])[0]}
            if "requirement" not in mapping: return self._send(view_mapping(st["headers"], len(st["body"]), st["label"], mapping) )
            rows = importer.build_rows(st["headers"], st["body"], mapping)
            importer.apply(rows, form.get("label", [st["label"]])[0] or st["label"])
            (PENDING / "import.json").unlink(missing_ok=True)
            return self._send(view_import(f"Importadas {len(rows)} linhas. As próximas rondas correm sobre esta matriz."))
        if self.path == "/import/restore":
            ok = importer.restore_base(); return self._send(view_import("Matriz de base reposta." if ok else "Não há matriz de base guardada."))
        if self.path == "/run":
            start_flow(); time.sleep(1); return self._redirect("/")
        if self.path == "/decide/sources":
            p = PENDING / "sources.json"; d = jload(p, {})
            d.update({"approved": [] if form.get("none") else form.get("approve", []), "decided": True})
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            start_flow(); time.sleep(1); return self._redirect("/")
        if self.path == "/decide/report":
            p = PENDING / "report.json"; d = jload(p, {})
            d.update({"approved_report": form.get("ok", ["0"])[0] == "1", "decided": True})
            p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            start_flow(); time.sleep(1); return self._redirect("/")
        if self.path == "/prepare":
            msg = prepare_sources()
            return self._send(page(f"<div class='ok'><b>{esc(msg)}</b></div><p><a class='btn' href='/'>Voltar à ronda</a></p>"))
        if self.path == "/export":
            subprocess.run([PY, str(ROOT / "scripts" / "export_matrix.py")], cwd=ROOT, capture_output=True)
            return self._redirect("/versions")
        return self._send(page("<p>Pedido desconhecido.</p>"), 404)

if __name__ == "__main__":
    PENDING.mkdir(parents=True, exist_ok=True); EXPORTS.mkdir(exist_ok=True)
    print(f"Consola em http://127.0.0.1:{PORT}  (Ctrl+C para parar)")
    threading.Timer(0.8, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
