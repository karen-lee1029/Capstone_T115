"""Shared offline test doubles for the Feature-002 (US-15) test suites.

None of these touch the network or a Databricks workspace.
"""

from __future__ import annotations

from databricks.sdk.errors import NotFound

from student_attrition_risk.models import DraftBriefing, ValidationOutcome


class ScriptedGenerationProvider:
    """``GenerationProvider`` double.

    Each positional action is consumed by one ``generate`` call, in order: a
    ``DraftBriefing`` is returned, an exception instance is raised. Calling
    ``generate`` more times than there are scripted actions is a test bug and
    raises ``AssertionError`` (this is how "no third attempt" is asserted).
    """

    def __init__(self, *actions: DraftBriefing | BaseException) -> None:
        self._actions: list[DraftBriefing | BaseException] = list(actions)
        self.calls = 0

    def generate(self, context) -> DraftBriefing:
        self.calls += 1
        if not self._actions:
            raise AssertionError(
                "ScriptedGenerationProvider.generate called more times than scripted"
            )
        action = self._actions.pop(0)
        if isinstance(action, BaseException):
            raise action
        return action


class ScriptedValidator:
    """``BriefingValidator`` double returning one scripted ``ValidationOutcome`` per call."""

    def __init__(self, *outcomes: ValidationOutcome) -> None:
        self._outcomes: list[ValidationOutcome] = list(outcomes)
        self.calls = 0

    def validate(self, draft, context) -> ValidationOutcome:
        self.calls += 1
        if not self._outcomes:
            raise AssertionError(
                "ScriptedValidator.validate called more times than scripted"
            )
        return self._outcomes.pop(0)


class _Download:
    def __init__(self, body: bytes) -> None:
        self.contents = _Stream(body)


class _Stream:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body


class _DirEntry:
    def __init__(self, path: str) -> None:
        self.path = path
        self.name = path.rsplit("/", 1)[-1]
        self.is_directory = False


class FakeFilesClient:
    """In-memory stand-in for ``databricks.sdk.WorkspaceClient().files``.

    Implements just the surface ``VolumeBriefingStore`` uses: ``upload``,
    ``download``, ``list_directory_contents``. A missing path raises the real
    ``databricks.sdk.errors.NotFound`` so the store's not-found handling is
    exercised. Set ``fail_upload`` / ``fail_download`` / ``fail_list`` to an
    exception instance to emulate a transient Files-API failure.
    """

    def __init__(self) -> None:
        self.files: dict[str, str] = {}
        self.fail_upload: BaseException | None = None
        self.fail_download: BaseException | None = None
        self.fail_list: BaseException | None = None

    def upload(self, file_path: str, contents, *, overwrite: bool | None = None) -> None:
        if self.fail_upload is not None:
            raise self.fail_upload
        if not overwrite and file_path in self.files:
            raise RuntimeError(f"file already exists: {file_path}")
        data = contents.read() if hasattr(contents, "read") else contents
        if isinstance(data, bytes):
            data = data.decode()
        self.files[file_path] = str(data)

    def download(self, file_path: str) -> _Download:
        if self.fail_download is not None:
            raise self.fail_download
        if file_path not in self.files:
            raise NotFound(f"not found: {file_path}")
        return _Download(self.files[file_path].encode())

    def list_directory_contents(self, directory_path: str):
        if self.fail_list is not None:
            raise self.fail_list
        prefix = directory_path.rstrip("/") + "/"
        entries = [_DirEntry(path) for path in sorted(self.files) if path.startswith(prefix)]
        if not entries:
            raise NotFound(f"not found: {directory_path}")
        return iter(entries)
