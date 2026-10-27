"""JSON-backed store with an append-only history. Swap for Supabase by re-implementing these four functions;
the Flow does not care where the data lives."""
from __future__ import annotations
import json, pathlib
from datetime import datetime, timezone

DATA = pathlib.Path(__file__).resolve().parents[2] / "data"

# Columns agents are NEVER allowed to write. Enforced here, not by prompt.
HUMAN_ONLY = {"required_risk_class", "applicability", "implementation_status", "implemented_control", "owner"}


def load(name: str):
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


def save(name: str, obj) -> None:
    (DATA / f"{name}.json").write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def log_change(entity: str, entity_id: str, field: str, old, new, actor: str, basis: str) -> None:
    """Every write goes through here. actor is 'agent:<name>' or 'human:<name>'. basis is the URL or reason."""
    hist = load("history") if (DATA / "history.json").exists() else []
    hist.append({
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "entity": entity, "id": entity_id, "field": field,
        "old": old, "new": new, "actor": actor, "basis": basis,
    })
    save("history", hist)


def update_field(entity: str, entity_id: str, field: str, new, actor: str, basis: str) -> None:
    if field in HUMAN_ONLY and not actor.startswith("human:"):
        raise PermissionError(f"{field} is human-only; agent {actor} may not write it")
    items = load(entity)
    for it in items:
        if it["id"] == entity_id:
            old = it.get(field)
            if old != new:
                it[field] = new
                log_change(entity, entity_id, field, old, new, actor, basis)
            break
    else:
        raise KeyError(f"{entity_id} not in {entity}")
    save(entity, items)
