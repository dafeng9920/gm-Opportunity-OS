"""Audit reference validation protocol for future Triad execution."""

from __future__ import annotations

from typing import Protocol


class AuditReferenceLookup(Protocol):
    def get(self, audit_id: str) -> object | None: ...


class AuditReferenceValidator:
    """Validates references only; it never writes audit events or invokes a Runtime."""

    def __init__(self, lookup: AuditReferenceLookup) -> None:
        self._lookup = lookup

    def validate(self, audit_refs: tuple[str, ...]) -> None:
        if not audit_refs:
            raise ValueError("completed role results require audit references")
        for audit_id in audit_refs:
            if self._lookup.get(audit_id) is None:
                raise KeyError(f"audit reference not found: {audit_id}")