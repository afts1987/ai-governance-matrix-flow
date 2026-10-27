"""Pydantic models. Every agent output is validated against one of these before it touches state.
An output that does not validate is routed to manual review, never silently accepted."""
from __future__ import annotations
from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


SourceStatus = Literal[
    "Final text — in force",
    "Final text — deferred application",
    "Harmonised standard cited in the OJ",
    "Published standard (not harmonised)",
    "Draft (prEN)",
    "Non-binding guidance",
    "Internal proposal (to validate)",
]


class SourceCheck(BaseModel):
    """What the Source Watcher returns for ONE source."""
    source_id: str = Field(description="ID from sources.json, e.g. S07")
    changed: bool = Field(description="True only if an official or primary source shows a change since verified_on")
    proposed_status: Optional[SourceStatus] = Field(default=None, description="New status, only when changed is True")
    stage: Optional[str] = Field(default=None, description="Stage within the status, when the source shows one: e.g. 'enquiry', 'under approval', 'published', 'adopted', 'draft for consultation'")
    what_changed: str = Field(default="", description="One or two sentences, factual, no speculation")
    evidence_url: Optional[str] = Field(default=None, description="URL of the primary source that shows the change (https://...)")
    evidence_date: Optional[date] = Field(default=None, description="Date on the primary source")
    confidence: Literal["high", "medium", "low"] = "low"
    needs_human: bool = Field(default=True, description="Always True when changed is True; the human gate decides")

    @field_validator("evidence_url")
    @classmethod
    def _url_ok(cls, v):
        if v in (None, ""):
            return None
        if not v.startswith(("http://", "https://")):
            raise ValueError("evidence_url must be an absolute http(s) URL")
        # CEN-CENELEC project pages carry a session token (cs=...) that expires; keep the stable part.
        if "cencenelec.eu" in v and "&cs=" in v:
            v = v.split("&cs=")[0]
        return v


class EvidenceCheck(BaseModel):
    """What the Evidence Auditor returns for ONE applicable row. It never judges sufficiency."""
    row_id: str
    found: Literal["found", "not_found", "outdated", "unknown"]
    location: Optional[str] = Field(default=None, description="Path, URL or document title where the evidence lives")
    last_modified: Optional[date] = None
    note: str = ""


class RoundReport(BaseModel):
    """What the Reporter writes after a round, for the owners."""
    period: str
    sources_changed: list[str] = Field(description="One entry per approved source: '<id>: <what changed>'")
    rows_pending_review: list[str]
    evidence_missing: list[str]
    evidence_unknown_count: int = Field(default=0, description="Rows whose evidence could not be checked (store not configured or error)")
    summary: str = Field(description="Plain prose, under 200 words, no bullet lists, no claims about evidence being in order unless every check returned 'found'")


class MatrixState(BaseModel):
    """Flow state. Persisted between steps; the human gates read and write it."""
    round_id: str = ""
    applicable_rows: list[str] = []
    sources_to_check: list[str] = []
    source_checks: list[SourceCheck] = []
    approved_source_changes: list[str] = []
    rejected_source_changes: list[str] = []
    evidence_checks: list[EvidenceCheck] = []
    report: Optional[RoundReport] = None
    report_approved: bool = False
    errors: list[str] = []
