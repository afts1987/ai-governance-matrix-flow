"""Same logic as column M of the workbook, in Python, so the agents never have to reason about it.
Pure function; no LLM involved."""
from __future__ import annotations


def applicability(row: dict, profile: dict) -> str:
    role_ok = (
        row["required_role"] in ("Any", "Both")
        or profile.get("role") == "Both"
        or row["required_role"] == profile.get("role")
    )
    cond = row.get("condition") or "—"
    cond_ok = cond == "—" or profile.get(cond) == "Yes"
    sector = row.get("sector") or "All"
    sector_ok = (
        sector == "All"
        or sector == profile.get("sector")
        or (sector == "NIS2" and profile.get("nis2") == "Yes")
    )
    if not (role_ok and cond_ok and sector_ok):
        return "Not applicable"

    cls = row.get("required_risk_class") or "Any"
    if cls != "Any" and profile.get("high_risk") == "To be determined":
        return "Depends"
    if cls == "Any":
        return "Applicable"
    if profile.get("high_risk") != "Yes":
        return "Not applicable"
    annex = profile.get("annex")
    annex_ok = (
        cls == "High-risk"
        or annex == "Both"
        or (cls == "High-risk (Annex III)" and annex == "Annex III")
        or (cls == "High-risk (Annex I)" and annex == "Annex I")
    )
    return "Applicable" if annex_ok else "Not applicable"
