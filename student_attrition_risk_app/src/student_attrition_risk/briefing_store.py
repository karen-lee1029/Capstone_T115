"""Briefing persistence + retrieval seam.

Feature-001 provides the ``BriefingStore`` seam plus ``InMemoryBriefingStore`` for tests and
local mode. Feature-002 / US-15 adds ``VolumeBriefingStore``, the concrete governed Databricks
Unity Catalog Volume implementation, behind the same interface (FR-021, FR-025).
"""

import io
import secrets
from typing import Any

from databricks.sdk.errors import NotFound

from .config import ConfigurationError, Settings
from .models import ValidatedBriefing
from .student_service import BriefingStorageError


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


class VolumeBriefingStore:
    """Governed ``BriefingStore`` backed by a Databricks Unity Catalog Volume (Feature-002 / US-15).

    One JSON document per validated briefing at
    ``${BRIEFING_VOLUME}/<student_hash>/<timestamp>-attempt<n>-<token>.json``. Append-only:
    every ``save_validated`` writes a new file and nothing is ever overwritten or deleted
    (approved planning decision 4). "Most recent" is the lexicographically greatest file name;
    the fixed-width timestamp prefix makes name order chronological. A missing student
    directory is an explicit "none available" (``None`` / ``False``), never an error (FR-022);
    any other Files-API failure is surfaced as ``BriefingStorageError`` (FR-024).
    """

    def __init__(self, settings: Settings, files: Any = None) -> None:
        if not settings.briefing_volume:
            raise ConfigurationError("BRIEFING_VOLUME is required for VolumeBriefingStore.")
        self._root = settings.briefing_volume.rstrip("/")
        if files is not None:
            self._files = files
        else:
            # Imported lazily so the module (and the test suite) needs no live workspace.
            from databricks.sdk import WorkspaceClient

            self._files = WorkspaceClient().files

    def has_validated(self, student_hash: str) -> bool:
        try:
            for entry in self._files.list_directory_contents(self._dir(student_hash)):
                if not getattr(entry, "is_directory", False):
                    return True
            return False
        except NotFound:
            return False
        except Exception as exc:
            raise BriefingStorageError(
                f"could not check stored briefings for {student_hash}"
            ) from exc

    def get_latest_validated(self, student_hash: str) -> ValidatedBriefing | None:
        try:
            entries = list(self._files.list_directory_contents(self._dir(student_hash)))
        except NotFound:
            return None
        except Exception as exc:
            raise BriefingStorageError(
                f"could not list stored briefings for {student_hash}"
            ) from exc
        names = sorted(
            entry.path for entry in entries if not getattr(entry, "is_directory", False)
        )
        if not names:
            return None
        latest = names[-1]
        try:
            raw = self._files.download(latest).contents.read()
        except Exception as exc:
            raise BriefingStorageError(f"could not read stored briefing {latest}") from exc
        try:
            return ValidatedBriefing.model_validate_json(raw)
        except ValueError as exc:
            raise BriefingStorageError(
                f"stored briefing {latest} is not a valid briefing document"
            ) from exc

    def save_validated(self, briefing: ValidatedBriefing) -> None:
        path = self._file_path(briefing)
        body = briefing.model_dump_json().encode("utf-8")
        try:
            self._files.upload(path, io.BytesIO(body), overwrite=False)
        except Exception as exc:
            raise BriefingStorageError(
                f"could not store validated briefing for {briefing.student_deidentified_hash}"
            ) from exc

    def _dir(self, student_hash: str) -> str:
        return f"{self._root}/{student_hash}"

    def _file_path(self, briefing: ValidatedBriefing) -> str:
        stamp = briefing.generated_at.strftime("%Y%m%dT%H%M%S%fZ")
        name = f"{stamp}-attempt{briefing.attempt_count}-{secrets.token_hex(3)}.json"
        return f"{self._dir(briefing.student_deidentified_hash)}/{name}"
