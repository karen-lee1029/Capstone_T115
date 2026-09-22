"""Advisor-facing message copy for the briefing workflow.

Separate from ``ui.py`` because that module executes Streamlit calls at import time and so
cannot be imported by a test. This module has no Streamlit, service or model dependency, which
keeps the wording required by Feature-002 FR-038/FR-039/FR-041 directly unit-testable.
"""

# Store-neutral by requirement (FR-041): the in-memory store remains the local and test
# implementation, so the advisor is never told which storage technology was used. The copy also
# carries no attempt or retry language — the persistence confirmation reports storage, not the
# attempt that produced the briefing (FR-032, FR-040).
_SAVED = (
    "This briefing passed validation and has been saved to the validated briefing store."
)
_REPLACED = " It supersedes the briefing previously saved for this student."
_ALREADY_SAVED = (
    "This student already has a validated briefing, so it was shown rather than generated "
    "again. Use Regenerate to produce a new one."
)


def storage_confirmation_message(*, replaced: bool) -> str:
    """Confirm to the advisor that a newly produced briefing has been saved (FR-038).

    ``replaced`` is ``True`` when the save superseded a briefing the student already had, which
    the advisor needs to know because the superseded briefing is no longer the one the retrieval
    path returns (FR-039).
    """
    return _SAVED + (_REPLACED if replaced else "")


_RETRIEVED = (
    "Retrieved the validated briefing saved for this student."
)


def retrieved_briefing_message() -> str:
    """Confirm an explicit Retrieve Saved action succeeded.

    Distinct from the save confirmation: nothing was generated or written, the stored briefing
    was read back. Distinct from the already-has-one notice too, so the advisor can tell which
    of the two paths produced what is on screen.
    """
    return _RETRIEVED


def existing_briefing_message() -> str:
    """Explain a briefing that was returned from the store rather than newly generated.

    The request generated and saved nothing, so it must not claim a save (FR-038, and the spec's
    "A non-regeneration request returns an already-stored briefing" edge case). It is rendered
    through the neutral notice, never the confirmation, and it names the action that would
    actually produce a new briefing so the advisor is not left guessing why nothing changed.
    """
    return _ALREADY_SAVED
