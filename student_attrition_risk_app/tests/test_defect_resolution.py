"""Feature-004 (US-20) — Final Defect Resolution regression groups.

One section per defect fixed by Feature-004, named after its ID in
``specs/004-final-defect-resolution/defect-register.md``, in the order B2, B4, C3, B1.
Each group fails against the sweep commit ``3181882`` and passes once its fix lands
(spec FR-023, FR-024).

Offline: controlled generation, validation and storage outcomes only. The Feature-002
``doubles.py`` and Feature-003 ``workflow_doubles.py`` modules are imported read-only; any extra
double a group needs is defined locally in its own section. No merged test file is edited.
"""

import logging
from datetime import timedelta

from workflow_doubles import validated_briefing, volume_store

# ---- B2: validator exception escapes the retry workflow (register B2) ----








# ---- B4: unrelated files in a student's Volume folder hide the briefing (register B4) ----

B4_STUDENT = "synthetic-student-b4"
B4_DIR = f"/Volumes/main/advising/briefings/{B4_STUDENT}"
B4_STRAY_BODY = "not a briefing"


def test_b4_folder_with_only_an_unrelated_file_has_no_briefing():
    store, fake = volume_store()
    fake.files[f"{B4_DIR}/notes.txt"] = B4_STRAY_BODY

    assert store.has_validated(B4_STUDENT) is False
    assert store.get_latest_validated(B4_STUDENT) is None


def test_b4_unrelated_file_sorting_last_does_not_hide_the_stored_briefing():
    store, fake = volume_store()
    stored = validated_briefing(B4_STUDENT, "Stored B4 briefing.")
    store.save_validated(stored)
    fake.files[f"{B4_DIR}/zzz-readme.json"] = B4_STRAY_BODY

    assert store.has_validated(B4_STUDENT) is True
    assert store.get_latest_validated(B4_STUDENT) == stored


def test_b4_save_after_a_stray_file_becomes_latest_and_leaves_the_file_untouched():
    store, fake = volume_store()
    stray = f"{B4_DIR}/zzz-readme.json"
    fake.files[stray] = B4_STRAY_BODY
    first = validated_briefing(B4_STUDENT, "First B4 briefing.")
    store.save_validated(first)
    newest = validated_briefing(B4_STUDENT, "Newest B4 briefing.").model_copy(
        update={"generated_at": first.generated_at + timedelta(seconds=1)}
    )
    store.save_validated(newest)

    assert store.get_latest_validated(B4_STUDENT) == newest
    assert fake.files[stray] == B4_STRAY_BODY


def test_b4_unrelated_files_are_ignored_without_logging(caplog):
    store, fake = volume_store()
    store.save_validated(validated_briefing(B4_STUDENT, "Logged-nothing B4 briefing."))
    fake.files[f"{B4_DIR}/notes.txt"] = B4_STRAY_BODY
    fake.files[f"{B4_DIR}/zzz-readme.json"] = B4_STRAY_BODY

    with caplog.at_level(logging.DEBUG):
        store.has_validated(B4_STUDENT)
        store.get_latest_validated(B4_STUDENT)

    assert caplog.records == []








# ---- C3: briefing tools leak raw backend error text (register C3, Renny half) ----








# ---- B1: store read outage reported as "could not be stored" (register B1) ----







