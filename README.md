# AI Governance Matrix Flow

[![Licence: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE) [![Content: CC BY 4.0](https://img.shields.io/badge/content-CC%20BY%204.0-lightgrey.svg)](LICENSE-CONTENT.md)

Final project — Academia Rumos AI Engineer, Certificação Rumos Expert (CRE): AI Expert. Author: André Silva.

A CrewAI Flow that keeps the **AI Governance Risk Matrix** alive without letting agents make the decisions that belong to people.

```
load_state ──► check_sources ──► [human gate 1] ──► audit_evidence ──► write_report ──► [human gate 2] ──► persist | discard
```

| Step | Who | What |
|---|---|---|
| `load_state` | Python | Recomputes applicability from `profile.json`; picks volatile sources |
| `check_sources` | **Source watcher** agent | One source per task; primary sources only; returns a validated `SourceCheck` |
| `gate_sources` | Human | Approves or rejects each proposed status change; approved ones are written with the evidence URL |
| `audit_evidence` | **Evidence auditor** agent | One applicable row per task; reports found / not found / outdated / unknown |
| `write_report` | **Reporter** agent | Plain-prose round report, under 200 words |
| `gate_report` | Human | Approves the report; only then is the round persisted |

## What agents can never write
`required_risk_class`, `applicability`, `implementation_status`, `implemented_control`, `owner`.
Enforced in `store.update_field`, not by prompt. Every write is logged to `data/history.json` with actor and basis.

## Why a Flow and not a Crew
Agents inherit each other's output without validation; one hallucination compounds into the next. The Flow feeds each agent **one source or one row at a time**, validates every output with Pydantic, and routes failures to manual review.

## Documentation
- `docs/EXPLICACAO_SIMPLES.md` — the platform in plain language (PT)
- `docs/GLOSSARIO.md` — 56 acronyms and terms (PT)
- `docs/DEMO.md` — 10-minute demo script (PT)
- `docs/ARQUITETURA.md` — architecture, code-enforced rules, lessons from the first rounds (PT)
- `python scripts/build_demo.py` → `demo/index.html`, a self-contained status page built from `data/*.json`

## Setup
```bash
pip install -e ".[dev]"
cp .env.example .env            # fill ANTHROPIC_API_KEY and SERPER_API_KEY
python scripts/xlsx_to_json.py AI_Governance_Risk_Matrix_v1.2.xlsx data
pytest
matrix-flow                     # console gates; or HITL_MODE=file for unattended runs
```

## Docker
```bash
cp .env.example .env                                   # fill the keys
docker compose build
docker compose --profile tools run --rm test           # 6 tests inside the image
mkdir -p input && cp AI_Governance_Risk_Matrix_v1.2.xlsx input/matrix.xlsx
docker compose --profile tools run --rm convert        # xlsx -> data/*.json
HITL_MODE=console docker compose run --rm matrix-flow  # interactive round, gates on the terminal
docker compose run --rm matrix-flow                    # unattended: stops at the first gate, leaves data/pending/*.json
```
`data/` is a bind mount, so the matrix, history and pending decisions live outside the container. The image runs as a non-root user and holds no data or secrets; `.env` is passed at runtime.

For a weekly job on a server: `0 7 * * 1 cd /srv/matrix && docker compose run --rm matrix-flow`.
`try_one.py` runs a single agent verbosely: `docker compose run --rm --entrypoint python matrix-flow try_one.py`.

## Console (no terminal needed)
`start_demo.cmd` (or `python scripts/gate_ui.py`) opens http://localhost:8765: run a round, decide at the human gates, watch progress, download each versioned Excel export, open the status page. The Flow runs in `HITL_MODE=file`, stops at each gate, saves its state and resumes without repeating searches.

## Evidence auditor
`EVIDENCE_BACKEND=local` checks `data/evidence/` for files whose name starts with the row id (`R-04.01_training_register.pdf`) and reports presence and last-modified date only. Empty = not configured, the auditor reports `unknown`. Replace the backend with Microsoft 365 / SharePoint / iManage via `crewai_tools.MCPServerAdapter` when ready.

## Governance note
This Flow is itself an AI system. Register it in the matrix: it reads external web content (RK-G.B), holds credentials to internal documents (RK-G.C) and must keep reconstructible logs (RK-12.A). `data/history.json` is that log.

## Licences
Code: MIT (`LICENSE`). Matrix content, exports and docs: CC BY 4.0 (`LICENSE-CONTENT.md`). Not legal advice.

## Privacy note
No organisation data is committed: `.env`, `data/pending/`, `data/backups/` and `exports/` are ignored by git. `data/evidence/` holds sample files only.
