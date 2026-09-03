"""Briefing persistence + retrieval seam (Feature-001 / US-08).

Feature-001 provides only the ``BriefingStore`` seam plus an in-memory implementation for
tests and local mode. The concrete governed Databricks Unity Catalog Volume storage — path,
file format, naming, retention, most-recent selection — is owned by **US-15** and will be
supplied through this same interface (FR-025, FR-028, FR-030).
"""

from .models import ValidatedBriefing


class InMemoryBriefingStore:
    """Non-persistent placeholder. Holds one ordered list of ``ValidatedBriefing`` per
    student hash. ``save_validated`` only ever appends (it never removes or replaces an
    existing entry — FR-037); ``get_latest_validated`` returns the most recently saved."""

    def __init__(self) -> None:
        self._by_hash: dict[str, list[ValidatedBriefing]] = {}

    def has_validated(self, student_hash: str) -> bool:
        return bool(self._by_hash.get(student_hash))

    def get_latest_validated(self, student_hash: str) -> ValidatedBriefing | None:
        entries = self._by_hash.get(student_hash)
        return entries[-1] if entries else None

    def save_validated(self, briefing: ValidatedBriefing) -> None:
        self._by_hash.setdefault(briefing.student_deidentified_hash, []).append(briefing)
