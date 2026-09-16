# Traceability Record: Feature-003 — Structured Advisor Briefing Workflow Testing (US-18)

**Created**: 2026-09-16 | **Spec**: [spec.md](./spec.md) | **Contract**: [contracts/traceability-record.md](./contracts/traceability-record.md)

Hand-maintained, and self-checked: `test_briefing_workflow_traceability.py::test_every_cited_verification_resolves`
confirms every verification name cited below still exists (FR-040, SC-016). A cited name that no
longer resolves fails that verification.

All verification names are in `student_attrition_risk_app/tests/`.

---

## 1. Scenario map

Feature-003 scenarios against what they satisfy.

| Scenario | Satisfies |
|---|---|
| `test_briefing_workflow_outcomes.py::test_configuration_failure_is_surfaced_unchanged_and_never_retried` | FR-016, SC-001 · US-18 |
| `test_briefing_workflow_outcomes.py::test_unknown_student_attempts_no_generation` | FR-019, SC-001 · US-18 |
| `test_briefing_workflow_outcomes.py::test_every_outcome_reaches_exactly_one_explicit_result` | FR-022, SC-002 · US-18 |
| `test_briefing_workflow_retry.py::test_first_attempt_success_engages_boundaries_in_specified_order` | FR-023, SC-009 · US-18 |
| `test_briefing_workflow_retry.py::test_retry_path_engages_boundaries_in_specified_order` | FR-023, SC-009 · US-18 |
| `test_briefing_workflow_retry.py::test_reported_criteria_and_feedback_reach_the_second_attempt` | FR-024, SC-010 · US-18 |
| `test_briefing_workflow_retry.py::test_second_attempt_succeeds_only_when_feedback_propagated` | FR-024, SC-010 · US-18 |
| `test_briefing_workflow_retry.py::test_retry_request_unchanged_when_nothing_was_reported` | FR-025, SC-010 · US-18 |
| `test_briefing_workflow_retry.py::test_retry_request_unchanged_for_a_generation_failure` | FR-025, SC-010 · US-18 |
| `test_briefing_workflow_retry.py::test_identity_fields_are_preserved_across_the_retry_request` | FR-025 · US-18 |
| `test_briefing_workflow_retry.py::test_generation_is_attempted_at_most_twice_across_the_matrix` | FR-026, SC-009 · US-18 |
| `test_briefing_workflow_retry.py::test_retry_result_is_stored_exactly_once_and_not_by_the_workflow` | FR-027, SC-007 · US-18 |
| `test_briefing_workflow_storage.py::test_write_count_is_one_for_every_successful_outcome` | FR-028, SC-007 · US-18 |
| `test_briefing_workflow_storage.py::test_write_count_is_zero_for_every_non_successful_outcome` | FR-028, SC-007 · US-18 |
| `test_briefing_workflow_storage.py::test_nothing_unvalidated_is_stored_or_surfaced_as_validated` | FR-029, SC-007 · US-18 |
| `test_briefing_workflow_storage.py::test_previously_stored_briefing_survives_every_failing_outcome` | FR-030, SC-008 · US-18 |
| `test_briefing_workflow_storage.py::test_storage_decision_outcomes_behave_identically_on_governed_storage` | FR-031 · US-18, US-15 |
| `test_briefing_workflow_boundaries.py::test_tool_boundary_terminal_failure_carries_the_category` | FR-033, SC-015 · US-18 |
| `test_briefing_workflow_boundaries.py::test_tool_boundary_storage_failure_is_surfaced` | FR-033, SC-015 · US-18 |
| `test_briefing_workflow_boundaries.py::test_tool_boundary_configuration_failure_is_surfaced` | FR-033, SC-015 · US-18 |
| `test_briefing_workflow_boundaries.py::test_failure_path_records_are_metadata_only` | FR-034, SC-011 · US-18 |
| `test_briefing_workflow_traceability.py::test_blank_generation_content_is_a_generation_failure` | FR-035, SC-001 · US-18, US-15 |
| `test_briefing_workflow_traceability.py::test_blank_generation_content_is_never_stored` | FR-035, SC-007 · US-18, US-15 |
| `test_briefing_workflow_traceability.py::test_non_generation_requests_complete_within_the_time_budget` | FR-037, SC-013 · US-18, US-08 |
| `test_briefing_workflow_traceability.py::test_every_cited_verification_resolves` | FR-040, SC-016 · US-18 |

Controlled-outcome requirements (FR-007–FR-011) are satisfied by `tests/workflow_doubles.py` and
exercised by every scenario above. Scope requirements (FR-001–FR-006) are satisfied by the
absence of change: see § 5.

---

## 2. Tracked re-verification

Behaviour already verified accurately by Feature-001 or Feature-002. Under FR-005 and FR-032 this
is **complete** and is recorded here rather than re-implemented (spec Edge Cases).

### Service boundary — outcome coverage (FR-012–FR-021)

| Outcome | Satisfied by | Feature-003 requirement |
|---|---|---|
| Validated briefing on attempt 1, stored | `test_briefing_orchestration.py::test_happy_path_assembles_context_calls_seams_in_order_and_stores` | FR-012 |
| Validation failure then successful retry | `test_briefing_retry_integration.py::test_validation_fail_then_pass_returns_attempt_2_and_persists_via_service` | FR-013 |
| Generation failure then successful retry | `test_briefing_retry_integration.py::test_generation_fail_then_pass_returns_attempt_2` | FR-013 |
| Terminal failure, no briefing produced | `test_briefing_retry_integration.py::test_two_generation_failures_terminate_with_generation_category_and_store_nothing` | FR-014 |
| Terminal failure, briefing never validated | `test_briefing_retry_integration.py::test_two_validation_failures_terminate_with_validation_category_and_store_nothing` | FR-015 |
| Storage failure surfaced, prior intact | `test_briefing_orchestration.py::test_persistence_failure_is_surfaced_and_previous_briefing_is_intact` | FR-017 |
| Not-at-risk refusal, no generation | `test_briefing_orchestration.py::test_not_flagged_request_makes_no_generation_seam_call` | FR-018 |
| Unknown student, not-found result | `test_briefing_orchestration.py::test_unknown_hash_is_not_found` | FR-019 (result only — see § 1 for the no-generation clause) |
| Existing briefing returned without generation | `test_briefing_orchestration.py::test_existing_briefing_is_returned_without_calling_generation` | FR-020 |
| Regeneration succeeds and supersedes | `test_briefing_orchestration.py::test_explicit_regenerate_supersedes_on_success` | FR-021 |
| Regeneration fails, prior retained | `test_briefing_orchestration.py::test_regenerate_terminal_failure_retains_the_previous_briefing` | FR-021 |

### REST boundary (FR-032)

Feature-001 verifies every briefing outcome at this boundary. **No REST verification is written by
Feature-003.**

| Outcome at REST | Satisfied by |
|---|---|
| Success returns the validated briefing | `test_api.py::test_post_briefing_generates_and_returns_validated_briefing` |
| Configuration failure → 503, never a template | `test_api.py::test_post_briefing_unconfigured_generation_returns_503_not_a_template` |
| Not flagged → 409 | `test_api.py::test_post_briefing_not_flagged_returns_409` |
| Unknown student → 404 | `test_api.py::test_post_briefing_unknown_hash_returns_404` |
| Get-or-create, then regenerate | `test_api.py::test_post_briefing_returns_existing_then_regenerates_on_flag` |
| Terminal failure → 502 with category | `test_api.py::test_post_briefing_retry_terminal_maps_to_502_with_category_in_detail` |
| Storage failure → 503 | `test_api.py::test_post_briefing_storage_failure_maps_to_503` |
| Stored retrieval, and none-available → 404 | `test_api.py::test_get_stored_briefing_returns_it_or_404_none_available` |

### Tool boundary — already covered (FR-032)

| Outcome at the tool interface | Satisfied by |
|---|---|
| The five shared tools are registered | `test_mcp_tools.py::test_mcp_registers_the_five_shared_service_tools` |
| Get-or-create, then regenerate | `test_mcp_tools.py::test_generate_student_briefing_returns_existing_then_regenerates` |
| Not-at-risk and not-found messages | `test_mcp_tools.py::test_generate_student_briefing_error_messages` |
| Stored retrieval, and none-available | `test_mcp_tools.py::test_get_student_briefing_returns_value_or_none_available` |

Terminal failure, storage failure and configuration failure had no coverage at this boundary and
are covered by Feature-003 under FR-033 — see § 1.

### Retry and storage properties (FR-023–FR-031)

Feature-002 verifies the retry **outcome** matrix and the governed store's **contract**. Those are
complete and not re-implemented:

| Behaviour | Satisfied by |
|---|---|
| Retry outcome matrix, both entry points | `test_retry_workflow.py::test_validation_failure_then_retry_success_produces_attempt_2` and the eight sibling scenarios in that file |
| Governed-store contract parity | `test_volume_briefing_store.py::test_save_then_get_latest_returns_an_equal_briefing` and its seven siblings |

Feature-003 adds the properties those verifications do not assert: boundary **order**, feedback
**propagation**, write **counts**, and the storage-decision outcomes exercised at **workflow**
level against governed storage.

---

## 3. Recorded defects

| Defect | Status | Detail |
|---|---|---|
| Blank and whitespace-only briefing content was returned as validated and written to storage | **Resolved** | Contradicted Feature-002 `spec.md` § Edge Cases, which specifies such content as a generation failure. Found during Feature-003 planning by running the workflow directly. Fixed at the generation boundary: the draft type now rejects content with no substance and the `GenerationProvider` contract states the requirement, so the rejection surfaces inside `generate()` and both attempts route it through their existing generation-failure paths. Verified ordinarily by `test_briefing_workflow_traceability.py::test_blank_generation_content_is_a_generation_failure` and `::test_blank_generation_content_is_never_stored` (FR-035). Retained here per FR-036: a defect found during planning and fixed before implementation is evidence the process worked. |

No defect is outstanding, so no expected-fail verification is carried (FR-036).

---

## 4. Unverified criteria

Approved criteria within Feature-003's scope that it does not verify, with reasons (FR-038, FR-041).

| Criterion | Reason |
|---|---|
| **Feature-001 SC-007** — the final instructions (US-12) and acceptance criteria (US-14) can be adopted by substituting the instructions and validation boundaries, verified by re-running the same scenarios | The US-12 and US-14 work is expected to be delivered outside the seam boundary, so the substitution the criterion describes is not anticipated during Feature-003. Building a conformance suite for a substitution that will not occur would be speculative infrastructure. Closeable later if a real implementation is substituted into `main.build_service`; the trigger is that wiring changing from `StubGenerationProvider` / `InterimValidator` to concrete implementations. |

Feature-001 SC-006 was in the same position and **is** closed by Feature-003 — see FR-037 in § 1.

---

## 5. Scope requirements satisfied by absence of change

| Requirement | Evidence |
|---|---|
| FR-003 — no production source file changed | No file under `src/student_attrition_risk/` appears in Feature-003's diff |
| FR-004 — no Feature-001/002 verification file changed | None of the twelve pre-existing files under `tests/` appears in Feature-003's diff |
| FR-005 — no duplication | § 2 above; every already-covered behaviour is tracked, not re-implemented |
| FR-006 — existing conventions reused | `tests/workflow_doubles.py` imports `ScriptedGenerationProvider`, `ScriptedValidator` and `FakeFilesClient` from `tests/doubles.py` unchanged, and adds no `conftest.py`, plugin or framework |
| FR-001, FR-002 — briefing workflow only | No Feature-003 scenario exercises health reporting, the high-risk list, or student-profile retrieval |
| FR-010 — no invented criteria | Fixture criteria are `PLACEHOLDER_CRITERION_A`, `PLACEHOLDER_CRITERION_B`, `PLACEHOLDER_VALIDATION_FEEDBACK` |
| FR-011 — no prompt-content assertions | No scenario asserts on `composed_prompt` content beyond the presence of the retry revision block and the reported criteria and feedback |

