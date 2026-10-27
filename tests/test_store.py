import pytest
from matrix_flow import store

def test_agent_cannot_write_human_only_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA", tmp_path)
    store.save("matrix", [{"id": "R-X", "implementation_status": None, "notes": ""}])
    with pytest.raises(PermissionError):
        store.update_field("matrix", "R-X", "implementation_status", "Implemented", actor="agent:auditor", basis="test")
    store.update_field("matrix", "R-X", "notes", "ok", actor="agent:auditor", basis="test")
    assert store.load("history")[0]["field"] == "notes"
