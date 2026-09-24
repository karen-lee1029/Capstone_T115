"""Feature-004 (US-20) — Final Defect Resolution regression groups.

One section per defect fixed by Feature-004, named after its ID in
``specs/004-final-defect-resolution/defect-register.md``, in the order B2, B4, C3, B1.
Each group fails against the sweep commit ``3181882`` and passes once its fix lands
(spec FR-023, FR-024).

Offline: controlled generation, validation and storage outcomes only. The Feature-002
``doubles.py`` and Feature-003 ``workflow_doubles.py`` modules are imported read-only; any extra
double a group needs is defined locally in its own section. No merged test file is edited.
"""


# ---- B2: validator exception escapes the retry workflow (register B2) ----








# ---- B4: unrelated files in a student's Volume folder hide the briefing (register B4) ----








# ---- C3: briefing tools leak raw backend error text (register C3, Renny half) ----








# ---- B1: store read outage reported as "could not be stored" (register B1) ----







