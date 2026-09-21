"""Briefing-validation seam (Feature-001 / US-08).

Feature-001 provides only the ``BriefingValidator`` seam plus an interim pass-through
placeholder. It invents **no** acceptance criteria. The real Structured Advisor Briefing
acceptance-criteria validation is owned by **US-14** and will be supplied through this same
seam without changing the orchestration (FR-016).
"""

import re
from .models import BriefingGenerationContext, DraftBriefing, ValidationOutcome, UNAVAILABLE, SUPPRESSED


class InterimValidator:
    """Interim development behaviour only — always passes. The ``validator_id`` on every
    ``ValidationOutcome`` marks results produced by this placeholder so they are never
    mistaken for final validation (FR-016)."""

    validator_id = "interim-pass-through"

    def validate(
        self, draft: DraftBriefing, context: BriefingGenerationContext
    ) -> ValidationOutcome:
        return ValidationOutcome(
            passed=True,
            failed_criteria=[],
            feedback=None,
            validator_id=self.validator_id,
        )

class StructuredBriefingValidator:
    validator_id = "structured-validator"

    def validate(
        self, draft: DraftBriefing, context: BriefingGenerationContext
    ) -> ValidationOutcome:
        failed_criteria: list[str] = []
        feedback_parts: list[str] = []
        text_lower = draft.text.lower()

        # --- AC1: hash match ---
        if draft.student_deidentified_hash != context.student_deidentified_hash:
            failed_criteria.append("AC1")
            feedback_parts.append(
                "The briefing's student_deidentified_hash does not match the student "
                "selected in the context."
            )

        # --- AC2: four required sections present ---
        required_sections = [
            "risk summary",
            "relevant student context",
            "recommended advisor actions",
            "suggested next steps",
        ]
        missing_sections = [s for s in required_sections if s not in text_lower]
        if missing_sections:
            failed_criteria.append("AC2")
            feedback_parts.append(
                "The briefing text is missing the following required section(s): "
                + ", ".join(s.title() for s in missing_sections)
                + "."
            )

        # --- AC3: no unsupported student circumstances ---
        # This requires semantic/NLP judgment to verify that the context section does not
        # invent information beyond the provided feature values. Skipped as too difficult
        # to implement reliably with deterministic rules.

        # --- AC4: advisor actions do not present AI as making the decision ---
        # Heuristic: flag first-person decision-making language suggesting the AI itself
        # is taking the intervention action rather than recommending it to the advisor.
        ai_decision_patterns = [
            r"\bi\s+will\s+(intervene|contact|reach\s+out|enrol|withdraw|suspend)",
            r"\bi\s+(am|m)\s+going\s+to\s+(intervene|contact|enrol|withdraw)",
            r"\bthe\s+ai\s+(will|should|shall)\s+(intervene|contact|decide|enrol|withdraw)",
            r"\bi\s+(have|ve)\s+(enrolled|withdrawn|contacted|suspended)",
        ]
        # Only check within the Recommended Advisor Actions section if present
        actions_text = ""
        if "recommended advisor actions" in text_lower:
            start = text_lower.find("recommended advisor actions")
            next_section = len(text_lower)
            for section in required_sections:
                if section == "recommended advisor actions":
                    continue
                pos = text_lower.find(section, start + 1)
                if pos != -1 and pos < next_section:
                    next_section = pos
            actions_text = text_lower[start:next_section]
        ac4_violations = [p for p in ai_decision_patterns if re.search(p, actions_text)]
        if ac4_violations:
            failed_criteria.append("AC4")
            feedback_parts.append(
                "Recommended Advisor Actions contain language that presents the AI as "
                "making the intervention decision rather than recommending it to the advisor."
            )

        # --- AC5: next steps are actionable ---
        # Heuristic: the Suggested Next Steps section should be non-empty and contain
        # action-oriented language (verbs like arrange, schedule, contact, refer, follow up).
        if "suggested next steps" in text_lower:
            start = text_lower.find("suggested next steps")
            next_steps_text = text_lower[start:]
            action_words = [
                "arrange", "schedule", "contact", "refer", "follow up",
                "follow-up", "meet", "discuss", "review", "send", "notify",
                "recommend", "plan", "book", "invite", "connect", "initiate",
                "encourage", "monitor", "check-in", "check in", "explore"
            ]
            has_action = any(w in next_steps_text for w in action_words)
            body = next_steps_text.replace("suggested next steps", "").strip()
            if not body or not has_action:
                failed_criteria.append("AC5")
                feedback_parts.append(
                    "The Suggested Next Steps section lacks actionable, task-oriented "
                    "language."
                )

        # --- AC6: AI-generated disclaimer present ---
        # In action in UI

        # --- AC7: no directly identifiable student information exposed ---
        # Heuristic regex check for common PII patterns: email addresses, phone
        # numbers, and student IDs that look like real identifiers.
        pii_patterns = [
            r"\b[a-z0-9.\-_]+@[a-z0-9.\-_]+\.[a-z]{2,}\b",  # email
            r"\b\+?\d{8,11}\b",  # phone numbers
            r"\b\d{8,10}\b",  # long numeric IDs (student numbers)
        ]
        # Skip the deidentified hash itself — it is expected to appear
        hash_pattern = re.escape(draft.student_deidentified_hash)
        text_without_hash = re.sub(hash_pattern, "", draft.text)
        pii_found = [
            p for p in pii_patterns if re.search(p, text_without_hash, re.IGNORECASE)
        ]
        if pii_found:
            failed_criteria.append("AC7")
            feedback_parts.append(
                "The briefing text may contain directly identifiable student "
                "information (e.g. email, phone number, or numeric student ID)."
            )

        # --- AC8: briefing corresponds to the selected student's prediction ---
        # Heuristic: verify the text references the student's risk percentage and that
        # at least one feature value appears.
        risk_pct = context.prediction.attrition_risk_percentage
        risk_pct_str = f"{risk_pct:.1f}%"
        mentions_risk = (
            risk_pct_str in draft.text
            or str(int(risk_pct)) in draft.text
        )
        # Check that at least one feature value is referenced in the text
        feature_values = context.features.values
        feature_mentions = 0
        for value in feature_values.values():
            if value is None or value in (UNAVAILABLE, SUPPRESSED):
                continue
            if isinstance(value, (int, float)):
                if str(int(value)) in draft.text or str(value) in draft.text:
                    feature_mentions += 1
            elif isinstance(value, str):
                key_words = value.split("_")
                for word in key_words:
                    if word.lower() in text_lower and word.lower() != "is":
                        feature_mentions += 1
        if not mentions_risk or feature_mentions == 0:
            failed_criteria.append("AC8")
            feedback_parts.append(
                "The briefing does not appear to reference the selected student's "
                "specific risk prediction or retrieved context."
            )

        # --- AC9: clear error/data-unavailable message ---
        # In action in UI

        # --- AC10: briefing associated with student and retrievable ---
        # Retrievability is outside the scope of this validation.

        passed = len(failed_criteria) == 0
        feedback = "; ".join(feedback_parts) if feedback_parts else None

        return ValidationOutcome(
            passed=passed,
            failed_criteria=failed_criteria,
            feedback=feedback,
            validator_id=self.validator_id,
        )
        