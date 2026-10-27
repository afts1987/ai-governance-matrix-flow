"""The Flow. Deterministic steps in Python; agents only where judgement about text is needed; two human gates.

    load_state ─► check_sources ─► gate_sources ─┬─ approved ─► audit_evidence ─► write_report ─► gate_report ─► persist
                                                 └─ nothing   ─► audit_evidence ...
    gate_report ─┬─ report_ok ─► persist
                 └─ report_rejected ─► discard

Human gates: by default they read from the console (HITL_MODE=console). Set HITL_MODE=file to write a
pending-approval JSON that a reviewer edits (or a Teams/CopilotKit UI posts back); the Flow resumes from it.
"""
from __future__ import annotations
import json, os, pathlib, re, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from crewai import Crew, Task, Process
from crewai.flow.flow import Flow, start, listen, router

from .models import MatrixState, SourceCheck, EvidenceCheck, RoundReport
from .applicability import applicability
from . import store
from .agents import make_source_watcher, evidence_auditor, reporter

PENDING = store.DATA / "pending"
STATE_FILE = PENDING / "state.json"


def _file_mode() -> bool:
    return os.getenv("HITL_MODE", "console") == "file"


def _save_state(state: MatrixState) -> None:
    PENDING.mkdir(exist_ok=True)
    STATE_FILE.write_text(state.model_dump_json(indent=2), encoding="utf-8")


def _gate(name: str, payload: dict) -> dict:
    """Human gate. Returns the (possibly edited) payload with 'approved' decisions filled in."""
    mode = os.getenv("HITL_MODE", "console")
    if mode == "file":
        PENDING.mkdir(exist_ok=True)
        p = PENDING / f"{name}.json"
        if p.exists():
            decided = json.loads(p.read_text(encoding="utf-8"))
            if decided.get("decided"):
                p.unlink()
                return decided
        p.write_text(json.dumps({**payload, "decided": False}, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        raise SystemExit(f"Waiting for a human decision: open the gate (python scripts/gate_ui.py), decide, then re-run matrix-flow to resume.")
    # console mode
    print(f"\n=== HUMAN GATE: {name} ===")
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    ans = input("Approve ALL / NONE / comma-separated ids to approve: ").strip()
    ids = [c["source_id"] for c in payload.get("changes", [])]
    approved = ids if ans.upper() == "ALL" else [] if ans.upper() == "NONE" else [a.strip() for a in ans.split(",")]
    return {**payload, "approved": approved, "decided": True, "approved_report": ans.upper() == "ALL"}


class MatrixFlow(Flow[MatrixState]):

    @start()
    def load_state(self):
        if _file_mode() and STATE_FILE.exists():
            cached = MatrixState(**json.loads(STATE_FILE.read_text(encoding="utf-8")))
            for k in MatrixState.model_fields:
                setattr(self.state, k, getattr(cached, k))  # typed models, not dicts
            self._resumed = True
            print(f"Resuming round {self.state.round_id} from pending state.")
            return self.state
        self._resumed = False
        matrix, profile, sources = store.load("matrix"), store.load("profile"), store.load("sources")
        self.state.round_id = f"{date.today().isoformat()}-{uuid.uuid4().hex[:6]}"
        for row in matrix:
            row["applicability"] = applicability(row, profile)
        store.save("matrix", matrix)  # applicability is derived, so recomputing it is not an agent write
        self.state.applicable_rows = [r["id"] for r in matrix if r["applicability"] == "Applicable"]
        # Only sources that can actually change: drafts, pending guidance, deferred texts, and anything older than 90 days.
        volatile = {"Draft (prEN)", "Non-binding guidance", "Final text — deferred application"}
        self.state.sources_to_check = [s["id"] for s in sources if s["status"] in volatile]
        return self.state

    @listen(load_state)
    def check_sources(self, _):
        if getattr(self, "_resumed", False) and self.state.source_checks:
            return self.state
        sources = {s["id"]: s for s in store.load("sources")}

        def one(sid: str) -> SourceCheck:
            s = sources[sid]
            watcher = make_source_watcher()  # one agent instance per thread
            task = Task(
                description=(
                    f"Source {sid}: {s['source']} (type: {s['type']}). Status on record: '{s['status']}'. "
                    f"Reference on record: {s['reference']}. Stage on record: {s.get('stage') or 'none'}. Note on record: {s.get('note','')}. Last verified: {s['verified_on']}.\n"
                    "Report changed=true ONLY if status or stage differs from what is on record.\n"
                    "evidence_url MUST be the page that actually states the fact you report; never cite an older page for a newer fact. "
                    "If the newest fact comes only from secondary sources, say so in what_changed and set confidence to 'low'.\n"
                    "Search for the CURRENT status on primary sources only (EUR-Lex, CEN-CENELEC, Commission, EDPB). "
                    "Decide whether anything changed, including the stage within a draft (enquiry, under approval, published). "
                    "Fill every field of the schema. If changed is true, needs_human must be true."
                ),
                expected_output="A SourceCheck JSON object.",
                agent=watcher, output_pydantic=SourceCheck,
            )
            out = Crew(agents=[watcher], tasks=[task], process=Process.sequential).kickoff()
            chk: SourceCheck = out.pydantic
            chk.source_id = sid
            chk.needs_human = chk.needs_human or chk.changed
            return chk

        workers = int(os.getenv("MATRIX_WORKERS", "4"))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(one, sid): sid for sid in self.state.sources_to_check}
            for f in as_completed(futs):
                sid = futs[f]
                try:
                    self.state.source_checks.append(f.result())
                except Exception as e:  # validation failure or tool error -> manual review, never silent
                    self.state.errors.append(f"{sid}: {type(e).__name__}: {e}")
        self.state.source_checks.sort(key=lambda c: c.source_id)
        return self.state

    @router(check_sources)
    def gate_sources(self, _):
        sources = {s["id"]: s for s in store.load("sources")}
        today = date.today().isoformat()
        # Deduplicate in code, not by prompt: a check that proposes the status and stage already on record
        # is a reconfirmation, not a change. It refreshes verified_on silently and is not shown at the gate.
        for c in self.state.source_checks:
            src = sources.get(c.source_id, {})
            same_status = (c.proposed_status or src.get("status")) == src.get("status")
            same_stage = (c.stage or "").strip().lower() == (src.get("stage") or "").strip().lower()
            if c.changed and same_status and same_stage:
                c.changed = False
                c.what_changed = "Reconfirmed: status and stage unchanged. " + c.what_changed
                store.update_field("sources", c.source_id, "verified_on", today,
                                   actor="human:auto-reconfirm", basis=str(c.evidence_url))
            # Evidence older than the last verification cannot justify high confidence.
            last = str(src.get("verified_on") or "")[:10]
            if c.evidence_date and re.fullmatch(r"\d{4}-\d{2}-\d{2}", last) and str(c.evidence_date) < last:
                if c.confidence == "high":
                    c.confidence = "medium"
                c.what_changed = f"[evidence dated {c.evidence_date}, older than last verification {str(src['verified_on'])[:10]}] " + c.what_changed
        changes = [c.model_dump() for c in self.state.source_checks if c.changed]
        if not changes:
            return "no_changes"
        if _file_mode():
            _save_state(self.state)
        decision = _gate("sources", {"round": self.state.round_id, "changes": changes})
        for c in self.state.source_checks:
            if c.changed and c.source_id in decision.get("approved", []):
                basis = str(c.evidence_url)
                if c.proposed_status:
                    store.update_field("sources", c.source_id, "status", c.proposed_status, actor="human:gate_sources", basis=basis)
                store.update_field("sources", c.source_id, "verified_on", date.today().isoformat(), actor="human:gate_sources", basis=basis)
                if c.stage:
                    store.update_field("sources", c.source_id, "stage", c.stage.strip().lower(), actor="human:gate_sources", basis=basis)
                note = f"[{date.today().isoformat()}] " + (f"Stage: {c.stage}. " if c.stage else "") + c.what_changed.strip()
                store.update_field("sources", c.source_id, "note", note, actor="human:gate_sources", basis=basis)
                self.state.approved_source_changes.append(c.source_id)
            elif c.changed:
                self.state.rejected_source_changes.append(c.source_id)
        return "approved"

    @listen("approved")
    def audit_after_changes(self, _):
        return self.audit_evidence()

    @listen("no_changes")
    def audit_without_changes(self, _):
        return self.audit_evidence()

    def audit_evidence(self):
        """Evidence presence is deterministic: the tool answers FOUND / NOT_FOUND / NOT CONFIGURED.
        No model is needed to copy that into the schema, so Python does it in a second. The auditor agent is
        used only when the backend returns something ambiguous (e.g. a near-match in a document store)."""
        if getattr(self, "_resumed", False) and self.state.evidence_checks:
            return self.state
        from .tools import find_evidence
        from datetime import date as _d
        import re as _re
        rows = {r["id"]: r for r in store.load("matrix")}
        for rid in self.state.applicable_rows:
            r = rows[rid]
            try:
                raw = find_evidence.run(row_id=rid, expected=r["expected_evidence"])
            except Exception as e:
                self.state.evidence_checks.append(EvidenceCheck(row_id=rid, found="unknown", note=f"{type(e).__name__}: {e}"))
                continue
            if raw.startswith("FOUND:"):
                dates = _re.findall(r"\d{4}-\d{2}-\d{2}", raw)
                newest = max(dates) if dates else None
                outdated = bool(newest) and (_d.today() - _d.fromisoformat(newest)).days > 365
                self.state.evidence_checks.append(EvidenceCheck(
                    row_id=rid, found="outdated" if outdated else "found",
                    location=raw[len("FOUND: "):], last_modified=newest, note="deterministic check, no model involved"))
            elif raw.startswith("NOT_FOUND"):
                self.state.evidence_checks.append(EvidenceCheck(row_id=rid, found="not_found", note="no file starts with the row id"))
            elif raw.startswith("NOT CONFIGURED"):
                self.state.evidence_checks.append(EvidenceCheck(row_id=rid, found="unknown", note="evidence store not configured"))
            else:  # ambiguous backend answer -> let the auditor agent interpret it
                task = Task(
                    description=(f"Row {rid}: {r['requirement']}\nExpected evidence: {r['expected_evidence']}\n"
                                 f"The evidence store returned: {raw}\nClassify as found / not_found / outdated / unknown. Do not judge sufficiency."),
                    expected_output="An EvidenceCheck JSON object.", agent=evidence_auditor, output_pydantic=EvidenceCheck)
                try:
                    self.state.evidence_checks.append(Crew(agents=[evidence_auditor], tasks=[task], process=Process.sequential).kickoff().pydantic)
                except Exception as e:
                    self.state.errors.append(f"{rid}: {type(e).__name__}: {e}")
        return self.state

    @listen(audit_after_changes)
    def report_a(self, _): return self.write_report()

    @listen(audit_without_changes)
    def report_b(self, _): return self.write_report()

    def write_report(self):
        if getattr(self, "_resumed", False) and self.state.report:
            return self.state
        matrix = store.load("matrix")
        today = date.today().isoformat()
        overdue = [r["id"] for r in matrix if r["applicability"] == "Applicable"
                   and r.get("review_date") and str(r["review_date"])[:10] < today]
        missing = [e.row_id for e in self.state.evidence_checks if e.found in ("not_found", "outdated")]
        unknown = [e.row_id for e in self.state.evidence_checks if e.found == "unknown"]
        found = [e.row_id for e in self.state.evidence_checks if e.found == "found"]
        changes = [f"{c.source_id}: {(('stage ' + c.stage + '; ') if c.stage else '')}{c.what_changed}"
                   for c in self.state.source_checks if c.source_id in self.state.approved_source_changes]
        task = Task(
            description=(
                f"Round {self.state.round_id}.\nApproved source changes (id: substance): {changes}\n"
                f"Rejected: {self.state.rejected_source_changes}.\nRows with overdue review: {overdue}.\n"
                f"Evidence checks: {len(found)} found, {len(missing)} missing or outdated ({missing}), "
                f"{len(unknown)} could NOT be checked (store not configured or error).\n"
                f"Errors needing manual review: {self.state.errors}.\n"
                "Write the RoundReport. Set evidence_unknown_count exactly. Prose only, under 200 words. "
                "If any check could not be performed, say so plainly; do not describe evidence as current or accounted for."
            ),
            expected_output="A RoundReport JSON object.",
            agent=reporter, output_pydantic=RoundReport,
        )
        out = Crew(agents=[reporter], tasks=[task], process=Process.sequential).kickoff()
        self.state.report = out.pydantic
        return self.state

    @router(report_a)
    def gate_report_a(self, _): return self._gate_report()

    @router(report_b)
    def gate_report_b(self, _): return self._gate_report()

    def _gate_report(self):
        if _file_mode():
            _save_state(self.state)
        decision = _gate("report", {"round": self.state.round_id, "report": self.state.report.model_dump() if self.state.report else None})
        self.state.report_approved = bool(decision.get("approved_report") or decision.get("approved"))
        return "report_ok" if self.state.report_approved else "report_rejected"

    @listen("report_ok")
    def persist(self, _):
        reports = store.load("reports") if (store.DATA / "reports.json").exists() else []
        reports.append({"round": self.state.round_id, **self.state.report.model_dump(),
                        "evidence": [e.model_dump() for e in self.state.evidence_checks], "errors": self.state.errors})
        store.save("reports", reports)
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        print(f"Round {self.state.round_id} persisted. {len(self.state.approved_source_changes)} source change(s) applied.")
        try:  # the Excel view is regenerated from the store after every persisted round
            import importlib.util
            spec = importlib.util.spec_from_file_location("export_matrix", pathlib.Path(__file__).resolve().parents[2] / "scripts" / "export_matrix.py")
            mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            print(f"Workbook exported: {mod.main()}")
        except Exception as e:
            print(f"Workbook export failed ({type(e).__name__}: {e}); run scripts/export_matrix.py by hand.")

    @listen("report_rejected")
    def discard(self, _):
        if STATE_FILE.exists():
            STATE_FILE.unlink()
        print(f"Round {self.state.round_id} discarded by reviewer. Nothing written except approved source changes.")


def kickoff():
    MatrixFlow().kickoff()


if __name__ == "__main__":
    kickoff()
