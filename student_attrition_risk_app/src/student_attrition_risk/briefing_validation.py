"""Briefing-validation seam (Feature-001 / US-08).

Feature-001 provides only the ``BriefingValidator`` seam plus an interim pass-through
placeholder. It invents **no** acceptance criteria. The real Structured Advisor Briefing
acceptance-criteria validation is owned by **US-14** and will be supplied through this same
seam without changing the orchestration (FR-016).
"""

import math
import re

from .models import SUPPRESSED, UNAVAILABLE, BriefingGenerationContext, DraftBriefing, ValidationOutcome

# "not at risk" / "not at-risk", and "at risk" / "at-risk" as whole words.
_NEGATED_RISK_LEVEL = re.compile(r"\bnot\s+at[\s-]risk\b")
_RISK_LEVEL = re.compile(r"\bat[\s-]risk\b")


def _mentions_number(text: str, number: str) -> bool:
    """True when ``number`` appears as a whole number in ``text``: "78" does not match
    inside "178", "2026" or "78.5"."""
    return re.search(rf"(?<![\d.]){re.escape(number)}(?!\d|\.\d)", text) is not None


def _numeric_feature_forms(value: int | float) -> list[str]:
    """Written forms of a numeric feature value that count as mentioning it. Booleans, 0/1
    values and non-finite numbers are skipped: they cannot identify a particular student."""
    if isinstance(value, bool) or not math.isfinite(value) or value in (0, 1):
        return []
    if float(value).is_integer():
        return [str(int(value))]
    return [str(value)]


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

        # --- AC1: Correct student context ---
        # The briefing must use the information corresponding to the selected
        # deidentified student and their associated ML attrition risk prediction.
        # The displayed risk level and risk score must correspond to the prediction.

        # Student's deidentified hash is incorrect
        if draft.student_deidentified_hash != context.student_deidentified_hash:
            failed_criteria.append("AC1")
            feedback_parts.append(
                "The briefing's student_deidentified_hash does not match the student "
                "selected in the context."
            )
        
        # Student's risk level is not mentioned, or the opposite classification is stated.
        # "Not At Risk" contains "at risk", so the negated form is checked separately.
        says_not_at_risk = _NEGATED_RISK_LEVEL.search(text_lower) is not None
        says_at_risk = _RISK_LEVEL.search(_NEGATED_RISK_LEVEL.sub("", text_lower)) is not None
        if context.prediction.attrition_risk_flag:
            states_risk_level = says_at_risk and not says_not_at_risk
        else:
            states_risk_level = says_not_at_risk and not says_at_risk
        if not states_risk_level:
            if "AC1" not in failed_criteria:
                failed_criteria.append("AC1")
            feedback_parts.append(
                "The briefing does not state the selected student's risk level from the "
                "prediction record, or states the opposite classification."
            )

        # Student's risk score is not mentioned. Only the score as supplied to the model
        # (one decimal place, e.g. "78.5%") counts; a bare "78" elsewhere does not.
        risk_pct = context.prediction.attrition_risk_percentage
        mentions_risk = (
            re.search(
                rf"(?<![\d.]){re.escape(f'{risk_pct:.1f}')}\s?%", draft.text
            )
            is not None
        )
        if not mentions_risk:
            if "AC1" not in failed_criteria:
                failed_criteria.append("AC1")
            feedback_parts.append(
                "The briefing does not reference the selected student's risk "
                "score from the prediction record."
            )

        # --- AC2: Structured briefing format ---
        # The briefing must contain clearly identifiable sections covering the four
        # required areas, clearly labelled and presented in a readable format.
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

        # --- AC3: Evidence-based briefing content ---
        # Requires semantic/NLP judgment to verify the context section does not
        # invent information beyond the provided feature values, and that global
        # feature importance is not presented as individual student-level evidence.
        # Skipped as too difficult to implement reliably with deterministic rules.

        # --- AC4: Recommended advisor actions ---
        # The actions must be presented as suggestions for the advisor to consider.
        # The AI must not make the intervention decision on behalf of the advisor.
        # Heuristic: flag first-person decision-making language suggesting the AI
        # itself is taking the intervention action rather than recommending it.
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

        # --- AC5: Suggested next steps ---
        # The proposed steps must be actionable and relevant to the available student
        # context. The AI must not invent or assume a timeframe.
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
            # Detect invented timeframes — the AI should not assume specific deadlines.
            timeframe_patterns = [
                r"\bwithin\s+\d+\s+(hour|day|week|month)s?\b",
                r"\bby\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
                r"\bby\s+(tomorrow|next\s+week|next\s+month)\b",
                r"\bby\s+end\s+of\s+(today|week|month|semester)\b",
                r"\bin\s+\d+\s+(hour|day|week|month)s?\b",
            ]
            timeframe_found = [
                p for p in timeframe_patterns if re.search(p, next_steps_text)
            ]
            if timeframe_found:
                failed_criteria.append("AC5")
                feedback_parts.append(
                    "The Suggested Next Steps section contains assumed timeframes. "
                    "The AI must not invent specific deadlines."
                )

        # --- AC6: AI transparency and human review ---
        # The disclaimer that advisor briefing is AI generated and requires human
        # review is present in the user interface.

        # --- AC7: Privacy and de-identification ---
        # The briefing must use only approved project information and maintain the
        # project's privacy and de-identification requirements. The AI must not
        # introduce unnecessary PII or infer sensitive characteristics.
        # Heuristic regex check for common PII patterns.
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

        # --- AC8: Traceability ---
        # The generated briefing must correspond to the selected student's retrieved
        # context and associated ML prediction. It must not provide generic student
        # information unrelated to the selected student.
        # Heuristic: verify at least one feature value from the context is referenced.
        feature_values = context.features.values
        feature_mentions = 0
        for value in feature_values.values():
            if value is None:
                continue
            if isinstance(value, str) and value in (UNAVAILABLE, SUPPRESSED):
                continue
            if isinstance(value, (int, float)):
                if any(_mentions_number(draft.text, form) for form in _numeric_feature_forms(value)):
                    feature_mentions += 1
            elif isinstance(value, str):
                # The whole value as a phrase ("Full_time" -> "full time"), not any one of its
                # words: single words such as "student" or "low" (inside "follow") match
                # almost any briefing.
                phrase = value.replace("_", " ").strip().lower()
                if phrase and re.search(rf"\b{re.escape(phrase)}\b", text_lower):
                    feature_mentions += 1
        if feature_mentions == 0:
            failed_criteria.append("AC8")
            feedback_parts.append(
                "The briefing does not appear to reference the selected student's "
                "specific retrieved context or feature values."
            )

        # --- AC9: Error handling ---
        # Primarily managed by the application UI/backend rather than the AI system
        # prompt. Not validated here.

        # --- AC10: Briefing storage and retrieval ---
        # Primarily managed by the application/backend rather than the AI system
        # prompt. Retrievability is outside the scope of this validation.

        # ========== FINAL OUTPUT ==========
        passed = len(failed_criteria) == 0
        feedback = "; ".join(feedback_parts) if feedback_parts else None

        return ValidationOutcome(
            passed=passed,
            failed_criteria=failed_criteria,
            feedback=feedback,
            validator_id=self.validator_id,
        )
        