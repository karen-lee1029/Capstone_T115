**Independent adversarial review — T115 Feature 003 / US-18**

Reviewed 17 September 2026. **Recommendation: request changes.** Six material findings remain in the verification suite and its traceability deliverable. All are P2: required corrections before claiming specification completion. This review did not identify a confirmed regression introduced by the separate blank-content production fix.

The unmodified package passes **143 tests** and Ruff. That result does not establish the claimed completeness: three independent fault injections each left all 143 tests passing. They introduced fabricated retry criteria, briefing text in exception tracebacks, and a REST storage-outage response incorrectly reported as absence.

I followed [00-START-HERE.md](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/00-START-HERE.md): findings were formed from folders 01–04 before reading the planning documents in 05. Tests ran in a temporary copy, using the pinned dependency set and Python 3.11.15. The original package was not edited. Every supplied file in the temporary snapshot was subsequently verified byte-for-byte against the original.

**1. [P2] The privacy check ignores exception tracebacks.**

Location: [test_briefing_workflow_boundaries.py:125](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/test_briefing_workflow_boundaries.py:125).
Requirements: FR-034, SC-011; constitution X.

The helper joins only `record.getMessage()`. That excludes exception information rendered by a logging formatter. Consequently, the test can approve a log record whose visible traceback contains the exact briefing-text sentinel it is supposed to exclude.

Reproduction: I inserted `logger.exception("generation failed")` into the existing first-attempt generation-exception handler in the disposable copy. **All 143 tests passed.** The failure-path fixtures already put `SECRET_TEXT` into the exception message. A separate direct demonstration confirmed that the existing assertion accepts `record.getMessage()`, while formatting the same record exposes `SECRET_TEXT` in its traceback.

This is a weakness in the new verification; the unmodified handler does not contain this injected logging call.

Correction: check rendered log output including exception information, and inspect structured fields where those are part of operational logging. Keep the existing synthetic sentinels and verify that the injected traceback leak fails the new check. T025's completion claim is unsupported until that works.

**2. [P2] The feedback tests do not establish “exactly as reported, nothing added.”**

Locations: [test_briefing_workflow_retry.py:95](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/test_briefing_workflow_retry.py:95), [workflow_doubles.py:99](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/workflow_doubles.py:99).
Requirements: FR-024, SC-010; User Story 2 acceptance scenario 3.

The direct test checks three substrings. It cannot reject additional fabricated criteria or feedback. The supposedly stronger provider/validator pairing responds only to the fixed header `The previous attempt did not pass validation.`, rather than the actual reported criteria and feedback.

Reproduction:

- Appending `- PLACEHOLDER_CRITERION_INVENTED_BY_RETRY` to the retry criteria block left **all 143 tests passing**.
- Replacing the appended content with just the header, removing all criteria and feedback, still passed `test_second_attempt_succeeds_only_when_feedback_propagated`. This second result concerns that individual test; it is not a claim that the whole suite tolerates removing the payload.

The first mutation directly contradicts the approved requirement and survives the complete suite. The second disproves the causal assurance claimed for the double in research R3.

Correction: assert exact preservation of the supplied payload and reject additional payload values. Exercise criteria-only and feedback-only inputs as well as both together and neither. If retained, the conditional double must depend on the actual reported synthetic values. Avoid making final US-12 prompt wording an acceptance criterion. Reassess T012.

**3. [P2] Storage-read failures are missing from cross-boundary coverage.**

Locations: [test_briefing_workflow_boundaries.py:1](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/test_briefing_workflow_boundaries.py:1), [traceability.md:71](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/specs/003-briefing-workflow-testing/traceability.md:71).
Requirements: FR-032/FR-033, SC-015; explicit edge case “Governed storage is unreachable while reading.”

The existing REST retrieval test covers a stored briefing, absence and an unknown student. Its storage-error test covers a POST write failure. Neither exercises a GET read failure. The new tool storage-error test likewise exercises generation followed by a failed write. Feature-002's store-level read-failure checks do not verify the service/REST/tool mapping.

Reproduction: I changed the REST retrieval exception response from `503 / Validated briefing store unavailable` to `404 / No validated briefing available`. **All 143 tests passed.** This is precisely the outage-versus-absence distinction the specification requires.

Correction: inject list/download failures through the existing fake Files client, exercise stored-briefing retrieval and check the distinct observable responses at the relevant boundaries. Record those scenarios explicitly. The statement that every REST outcome is already covered, repeated in research R8 and T022, is false. Adding this missing verification would satisfy the non-duplication rule.

**4. [P2] Governed-storage parity omits the required failed-write outcome.**

Location: [test_briefing_workflow_storage.py:301](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/test_briefing_workflow_storage.py:301).
Requirement: FR-031; User Story 3 acceptance scenarios 5 and 7.

The six matrix entries are two successful-attempt variants, terminal generation failure, existing retrieval, failed regeneration and rejected drafts. None sets `FakeFilesClient.fail_upload` or otherwise causes a write failure while the workflow uses `VolumeBriefingStore`.

The number “six” has been preserved, but the six required scenario categories have not: the success category is split into two entries, while the failed-write category is absent. The separate failing-store test uses a wrapper that raises before delegating to an in-memory store; it does not cover this governed workflow path. The old upload-failure test tests the Volume adapter in isolation.

Correction: add the approved governed failed-write case with a seeded prior briefing; drive a valid result through the workflow, fail the fake upload, assert an explicit storage failure, and verify that retrieval still returns the prior briefing. Retain both success variants where useful; the acceptance criterion is scenario coverage, not a fixed row count. T020 is incomplete.

**5. [P2] Several new tests duplicate behaviour already adequately verified.**

Locations: [test_briefing_workflow_retry.py:146](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/test_briefing_workflow_retry.py:146), [test_briefing_workflow_retry.py:225](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/test_briefing_workflow_retry.py:225).
Requirements: FR-005, SC-004; constitution XII.

Concrete overlaps include:

| New verification | Existing verification and same observable property |
|---|---|
| `test_retry_request_unchanged_for_a_generation_failure` | [test_retry_workflow.py:149](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/test_retry_workflow.py:149): calls `SingleRetryWorkflow.run` with `GenerationFailed` and asserts the generation prompt is unchanged. |
| `test_retry_result_is_stored_exactly_once_and_not_by_the_workflow` | [test_briefing_retry_integration.py:88](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/test_briefing_retry_integration.py:88): validation failure followed by success, exactly one store write, attempt count 2, and the same two assertions that retry has no `store`/`_store` attribute. |
| The two-validation-failure row of `test_generation_is_attempted_at_most_twice_across_the_matrix` | [test_briefing_retry_integration.py:153](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/test_briefing_retry_integration.py:153): the same request sequence already asserts exactly two generation calls. The new row does not assert boundary order. |

These are assertion-level overlaps, not objections to reusing a scenario to observe a previously untested property. The genuinely new shared ordering assertions are useful. In contrast, relabelling an existing call-count assertion as a “matrix-wide” property does not add assurance.

Correction: remove redundant new checks and cite the existing checks individually. Retain tests only where they add a required observable property. The plan's Principle XII PASS and traceability section 5's “every already-covered behaviour is tracked, not re-implemented” are contradicted by the code.

**6. [P2] The traceability record is incomplete and leaves dependencies outside its self-check.**

Locations: [traceability.md:13](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/specs/003-briefing-workflow-testing/traceability.md:13), [traceability.md:107](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/specs/003-briefing-workflow-testing/traceability.md:107), [test_briefing_workflow_traceability.py:166](C:/Users/<local_user>/Desktop/Feature-003-Review-Package/04-runnable-snapshot/student_attrition_risk_app/tests/test_briefing_workflow_traceability.py:166).
Requirements: FR-039/FR-040, SC-012/SC-016; traceability-record contract; T029/T030.

The scenario map contains **25 of the 34 new test functions**. Nine are absent:

- `test_tool_boundary_terminal_validation_failure_carries_its_own_category`
- `test_none_available_retrieval_record_is_metadata_only`
- `test_returned_existing_record_is_metadata_only`
- `test_generation_failure_path_also_stops_at_two_attempts`
- `test_returning_an_existing_briefing_writes_nothing`
- `test_storage_failure_surfaces_and_leaves_the_prior_briefing_intact`
- `test_blank_content_never_reaches_validation`
- `test_traceability_record_exists_and_has_its_required_sections`
- `test_unverified_criteria_are_recorded_with_a_reason`

Even if the last two administrative checks were excluded from the definition of workflow scenario, seven behavioural verifications would remain unmapped.

Tracked re-verification also names one retry test and refers to “the eight sibling scenarios,” and similarly uses unnamed siblings for storage. The regex resolves explicit names; it cannot guard those unnamed dependencies.

Reproduction: renaming the old `test_configuration_error_on_retry_generation_is_re_raised_not_terminal` so it was no longer a test reduced collection to **142 passing tests**, with the traceability check still passing. The record's aggregate claim remained unchanged.

Correction: map every new scenario once, replace sibling shorthand with explicit file/name citations, and compare the new test inventory with the scenario map. Keep the record hand-maintained, as required. The existing check is useful for explicitly cited names; it does not establish the broader completeness and drift protection claimed.

**What the supplied evidence does support**

- The independent baseline was **143 passed, two dependency deprecation warnings, 4.45 seconds**; Ruff reported all checks passed. This agrees with the team's pass count.
- A subsequent unmodified rerun with an audit hook denying external Python socket/DNS access passed all 143 tests and recorded zero external attempts. Loopback remained allowed for Windows async runtime operation. That instrumentation run emitted one additional pytest import-order warning attributable to the review harness.
- The filtered patches exactly reproduce the six new test/support files and the traceability document in the snapshot.
- PR94's supplied patch matches the filtered production fix. PR95 contains the new tests, traceability and task updates, with no production-source edits. The supplied patches show no changes to the 13 pre-existing files under tests: 12 test modules plus `doubles.py`.
- The blank-content model validator rejects ordinary construction with empty or whitespace-only text, and the supplied workflow tests pass. No separate production-fix defect was confirmed.
- The new support module reuses the three named doubles. It introduces no dependency, fixture framework, plugin or conftest.
- Synthetic criteria, the stated three-path timing check, and the specifically reasoned SC-007 deferral are present.

The per-PR exports establish the supplied change separation. They do not independently prove merge chronology or human approvals; the package contains no Git history database or review audit sufficient to establish those matters. No additional private conversation was requested.

**Limits of the assurance**

Controlled outcomes are expressly approved for US-18. Their use is not itself a defect. This suite can establish orchestration behaviour conditional on those outcomes. It cannot establish actual model responsiveness, briefing quality, final validation criteria, live governed-storage behaviour, or successful integration of the future US-12/13/14 implementations. Research R3's model-like narrative supplies no additional evidence of those properties.

The observed mutation survivors demonstrate missing protection against specific faults. They are not claims that those injected faults exist in the original product. Repairs should follow the feature's test-only scope; any separately discovered production mismatch must be recorded and assigned through the approved defect process.

The planning claims should be revised after the six findings are resolved, particularly T012, T020, T022, T025, T029 and the non-duplication/completion assessments.

**Reproduction artifacts**

- [Mutation driver](C:/Users/<local_user>/AppData/Local/Temp/T115-F003-independent-review/adversarial_probes.py) — makes one temporary change at a time and restores each file in a finally block.
- [Machine-readable results and omitted scenario names](C:/Users/<local_user>/AppData/Local/Temp/T115-F003-independent-review/probe-results.json).
- [Final integrity, scope and offline verification](C:/Users/<local_user>/AppData/Local/Temp/T115-F003-independent-review/final-verification.txt).
- [Rendered traceback demonstration](C:/Users/<local_user>/AppData/Local/Temp/T115-F003-independent-review/traceback-demonstration.txt).

Individual mutation outputs are stored alongside those files. No fixes were applied to the submitted package.

