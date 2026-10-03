# Contract: Failure messages after Feature-004

**Plan**: [../plan.md](../plan.md)

Only the rows Feature-004 changes are listed; every other mapping stays as it is.

| Failure | REST `POST /briefing` | REST `GET /briefing` | Tool `generate_student_briefing` | Tool `get_student_briefing` | Advisor surface |
|---|---|---|---|---|---|
| Store **read** fails (B1) | 503 `Validated briefing store unavailable` *(was "could not be stored")* | 503 `Validated briefing store unavailable` *(unchanged)* | `validated briefing store unavailable` *(was "could not be stored")* | `validated briefing store unavailable` *(was raw text — C3)* | Red notice: **Store unavailable** — `Validated briefing store unavailable.` *(was "generated but could not be stored")* |
| Store **write** fails | 503 `Validated briefing could not be stored` *(unchanged)* | — | `validated briefing could not be stored` *(unchanged)* | — | unchanged (GuaGuaGua88's handler) |
| Validator raises on Attempt 2, or on both attempts (B2) | 502 `Briefing could not be produced (validation)` *(was 503 data source)* | — | `briefing could not be produced (validation)` *(was raw text)* | — | unchanged handler shows "could not be produced (validation)" |
| Any other unexpected failure (C3) | 503 `Databricks data source unavailable` *(unchanged)* | 503 `Validated briefing store unavailable` *(unchanged; C7 logged)* | `databricks data source unavailable` *(was raw text)* | `validated briefing store unavailable` *(was raw text)* | unchanged |

Rules:

- Tool messages are the REST message lower-cased (existing convention). No tool-specific wording.
- No message contains a Volume path, student-directory path, warehouse error text or credential.
- Not found (404 / `student hash not found`), not at risk (409), configuration failure (503 with
  its own text) are unchanged at every boundary.
- The advisor-surface notice uses class `.store-error-notice` (background `#fee4e2`, border
  `#d92d20`, text `#b42318`), rendered through `render_notice` (HTML-escaped), never a built-in
  Streamlit alert.
