# Contract: `VolumeBriefingStore` (Feature-002 / US-15)

Concrete implementation of the Feature-001 `ports.BriefingStore` protocol, backed by a governed
Databricks Unity Catalog Volume. **No signature change** to the protocol. It must satisfy the
same behavioural scenarios as `InMemoryBriefingStore` (Feature-001 `tests/test_briefing_store.py`,
SC-010). See Feature-001 `contracts/internal-seams.md` for the boundary.

```
has_validated(student_hash: str) -> bool
get_latest_validated(student_hash: str) -> ValidatedBriefing | None
save_validated(briefing: ValidatedBriefing) -> None        # raises BriefingStorageError on failure
```

## Construction

`VolumeBriefingStore(settings: Settings, files=None)` — `files` defaults to
`databricks.sdk.WorkspaceClient().files`; tests inject an in-memory fake with the same
`upload` / `download` / `list_directory_contents` surface. Requires `settings.briefing_volume`
to be set (a validated `/Volumes/…` root); `main.build_service` only constructs it in that case.

## Storage layout

| Aspect | Value |
|---|---|
| Directory | `${settings.briefing_volume}/<student_deidentified_hash>/` |
| File name | `<generated_at:%Y%m%dT%H%M%S%fZ>-attempt<attempt_count>-<6-char token>.json` |
| Body | `briefing.model_dump_json()` — only `ValidatedBriefing` fields; no prompt, no secret (FR-026) |

## Method behaviour

### `save_validated(briefing)`
- `files.upload(<dir>/<file name>, briefing.model_dump_json(), overwrite=False)`.
- A distinct filename per call ⇒ never overwrites, replaces, or deletes an existing file
  (FR-023). A failed `save_validated` therefore cannot corrupt or remove the current
  most-recent briefing (FR-018).
- Any Files-API error (auth, missing/!writable Volume, quota, transport) ⇒
  `raise BriefingStorageError(...) from exc`. A single-file `upload` is atomic — no partial file
  (FR-024). `StudentService._persist` maps this to the existing 503 "could not be stored".

### `get_latest_validated(student_hash)`
- `files.list_directory_contents(<dir>)`.
  - Directory missing or empty ⇒ `return None` (the "none available" result, FR-022).
  - Otherwise take the lexicographically greatest file name (timestamp prefix ⇒ most recent),
    `files.download` it, parse JSON ⇒ `ValidatedBriefing(**data)`, and return it. `source` is
    returned as stored; the retrieval path in `StudentService` applies `source="stored"` as it
    does today.
- A non-not-found read/list/parse error ⇒ `raise BriefingStorageError(...)` — surfaced as the
  existing 503 "store unavailable", which is **distinct** from the `None` "none available"
  result (spec Edge Cases).
- Superseded files are ignored on read and never deleted — storage is append-only and
  Feature-002 performs no pruning (planning decision 4, 2026-09-03).

### `has_validated(student_hash)`
- `True` iff `list_directory_contents(<dir>)` yields ≥1 file. Directory not found ⇒ `False`.

## Parity requirement

The scenarios in `tests/test_briefing_store.py` (unknown hash ⇒ nothing; save then get-latest
returns what was saved; multiple saves expose the most recent; saves isolated per hash) MUST
pass against `VolumeBriefingStore` with the fake Files client, unchanged in intent (SC-010).

## Retained placeholder

`InMemoryBriefingStore` is unchanged and remains the store for local / `USE_MOCK_DATA` / test
runs and whenever `BRIEFING_VOLUME` is unset.
