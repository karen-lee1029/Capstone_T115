# Contract: Internal Seams (Feature-001 / US-08)

Five `typing.Protocol` interfaces, alongside the existing `StudentRepository` and
`BriefingProvider`. Feature-001 **defines every seam and ships a placeholder or in-memory
implementation for each**; the concrete implementations are later Product Backlog stories.

| Seam | Feature-001 placeholder | Concrete implementation owner |
|---|---|---|
| `GenerationProvider` | `StubGenerationProvider` (raises "generation not configured") | **US-13** |
| `BriefingInstructions` | `InterimInstructions` (existing safe PoC prompt text) | **US-12** |
| `BriefingValidator` | `InterimValidator` (pass-through, marked non-final) | **US-14** |
| `RetryWorkflow` | `RetryNotConfigured` (returns `TerminalFailure`) | **Feature-002 / US-15** |
| `BriefingStore` | `InMemoryBriefingStore` | **US-15** |

## StudentRepository (existing — one method added)

```
get_model_features(student_hash: str) -> ApprovedModelFeatureValues | None
```

- Returns the 21 approved feature values (fact + `course` + `teaching_period` joins), each a
  value or an `UNAVAILABLE` marker (spec FR-003, FR-007).
- `None` only when the student hash is absent from the fact table; absent *columns* do not
  produce `None`.
- Added alongside the existing 11-field `get_snapshot` (unchanged, and still backing the
  `GET /api/students/{hash}` profile endpoint). Parameterised SQL; read-only.
- Implementations: `DatabricksStudentRepository` (SQL), `MockStudentRepository` (fixtures incl.
  a not-at-risk student and a student with a pre-existing validated briefing).
- This method is the **only** place the 21-feature list and the source-table joins live
  (accepted risk TR-1, `plan.md`). It reads raw approved values only — no encoding, imputation,
  or other ML transformation. A future canonical ML feature-projection table can be adopted by
  swapping in a repository implementation that reads it, with no change to `StudentService` or
  the orchestration.

## GenerationProvider (new — concrete impl US-13)

```
generate(context: BriefingGenerationContext) -> DraftBriefing        # raises on a pre-draft failure
```

- Feature-001 invokes it once per generation/regeneration run (spec FR-013) and maps a raised
  failure to `FirstAttemptOutcome.GenerationFailed(category)` (spec FR-019).
- Placeholder `StubGenerationProvider` raises a "generation not configured" error so an
  unconfigured backend fails fast and explicitly — never a template success (spec FR-014,
  FR-020).
- Test double: `StubGenerationProvider(draft=…)` or `StubGenerationProvider(raises=…)`.

## BriefingInstructions (new — concrete impl US-12)

```
compose(context: BriefingGenerationContext) -> str
instructions_id: str
```

- Produces the prompt string from the risk result + 21 features + instruction text.
- Placeholder `InterimInstructions` (`instructions_id="interim-default"`) reuses the existing
  safe PoC `_prompt` text and renders the 21 features as labelled, non-causal context (spec
  FR-010, FR-011). It defines no final sections or language guidance.

## BriefingValidator (new — concrete impl US-14)

```
validate(draft: DraftBriefing, context: BriefingGenerationContext) -> ValidationOutcome
```

- `ValidationOutcome { passed, failed_criteria, feedback, validator_id }`.
- Placeholder `InterimValidator` (`validator_id="interim-pass-through"`) — always `passed`,
  explicitly interim, recorded as such in logs and the `ValidatedBriefing` (spec FR-016).
  Invents no criteria.
- Test double: `StubValidator(passed=…, failed_criteria=…, feedback=…)` drives both branches
  (spec FR-017). Feature-002 consumes `failed_criteria` / `feedback` from a failing outcome.

## RetryWorkflow (new — concrete impl Feature-002 / US-15)

```
run(context: BriefingGenerationContext, first_outcome: FirstAttemptOutcome) -> BriefingOutcome
```

- `FirstAttemptOutcome` = `GenerationFailed(category)` | `ValidationFailed(ValidationOutcome)`.
- `BriefingOutcome` = `Produced(ValidatedBriefing)` | `TerminalFailure(category)`.
- Placeholder `RetryNotConfigured` performs no generation and returns
  `TerminalFailure(first_outcome.category)` (spec FR-019/FR-021). Keeps Feature-001 complete
  and testable now.
- `main.build_service` swaps in the real implementation when Feature-002 lands — no Feature-001
  orchestration change.

## BriefingStore (new — concrete impl US-15)

```
has_validated(student_hash: str) -> bool
get_latest_validated(student_hash: str) -> ValidatedBriefing | None
save_validated(briefing: ValidatedBriefing) -> None                  # raises BriefingStorageError on failure
```

- Placeholder `InMemoryBriefingStore` — dict of ordered `ValidatedBriefing` lists; "latest" is
  the most recently appended (spec FR-030).
- Only objects with a passing `ValidationOutcome` are ever passed to `save_validated` (spec
  FR-025/FR-026). `save_validated` never removes an existing entry (spec FR-037).
- US-15 provides the governed Unity Catalog Volume implementation (path, format, naming,
  retention, most-recent selection) behind this same interface.

## Orchestration call order (in `StudentService.request_briefing`)

```
1. repository.get_prediction(hash)        → None ⇒ StudentNotFoundError (404)              [FR-023]
2. prediction.attrition_risk_flag         → false ⇒ StudentNotAtRiskError (409)           [FR-034]
3. if not regenerate and store.has_validated(hash):
        return store.get_latest_validated(hash)   (source="stored")                        [FR-035]
4. features = repository.get_model_features(hash)  → assemble ApprovedModelFeatureValues    [FR-003/FR-007]
5. context = BriefingGenerationContext(prediction, features,
             instructions.compose(...), instructions.instructions_id)                       [FR-009/FR-010]
6. try: draft = generation_provider.generate(context)
   except pre-draft failure ⇒ first_outcome = GenerationFailed(category)                    [FR-013/FR-019]
7. else: outcome = validator.validate(draft, context)                                       [FR-015]
        outcome.passed  ⇒ vb = ValidatedBriefing(...); store.save_validated(vb); return vb  [FR-018/FR-025]
        not passed      ⇒ first_outcome = ValidationFailed(outcome)
8. result = retry_workflow.run(context, first_outcome)                                       [FR-019/FR-033]
        Produced(vb)       ⇒ store.save_validated(vb) if not already stored; return vb
        TerminalFailure(c) ⇒ BriefingNotProducedError(c) → 502 (category c in the safe detail text) [FR-021]
```

`get_stored_briefing(hash)` = step 1, then `store.get_latest_validated` (no flag check, no
generation) → 404 "none available" when `None` (spec FR-028/FR-030).

Every branch produces an application-visible result (spec FR-022). No template/deterministic
briefing is ever returned or stored as success (spec FR-020). Logging at each step is
metadata-only (spec FR-031/FR-032).
