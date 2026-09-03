<!--
Sync Impact Report
- Version change: (unratified generated draft) → 1.0.0
- Bump rationale: The prior constitution.md was produced without sufficient user direction
  and is treated as an unapproved draft, not an adopted constitution. Per user instruction
  this document is published as the initial ratified constitution and versioned 1.0.0.
- Principles fully replaced (draft → ratified):
  - Removed draft principles: I. Specification-Driven Development;
    II. Synthetic Data and Privacy by Design; III. Decision Support, Not Automation;
    IV. Test-First and Reproducibility; V. Layered Architecture and Interface Parity.
  - Added ratified principles: I. Specification-Driven Development;
    II. Strict Scope Containment; III. Read Broadly, Write Narrowly;
    IV. Minimal Necessary Change; V. Reuse and Extend Existing Architecture;
    VI. No Unnecessary Complexity; VII. Plan-Defined Implementation Structure;
    VIII. Application Technology Compatibility;
    IX. Separation of Responsibilities and Modularity; X. Security and Privacy;
    XI. Input Validation and Explicit Error Handling; XII. Proportionate Testing;
    XIII. Human Review of AI-Generated Development Work;
    XIV. Documentation and Implementation Traceability;
    XV. Completion Means Specification Satisfaction; XVI. Preserve Team Contributions;
    XVII. Human-Controlled Version Control.
- Sections:
  - Removed draft standalone sections: "Technology and Security Constraints";
    "Development Workflow and Quality Gates" (their durable content is now expressed as
    principles VIII, X, XII, and XIII).
  - Added: "Scope and Applicability"; "Development Workflow and Compliance Review".
- Templates and commands: .specify/templates/*.md read this file at runtime. The plan
  template's Constitution Check is generic ("Gates determined based on constitution
  file") and needs no edit. No template source files were modified by this command.
- Deferred items / TODOs: none. Ratification date set to 2026-09-02 per user instruction.
-->

# T115 Student Risk and Intervention Briefing Application Constitution

## Scope and Applicability

This constitution governs development of the software application in this repository. It
applies to Feature-001 (backend functionality supporting the Databricks application) and
Feature-002 (Structured Advisor Briefing validation and single-retry functionality), and
it remains binding on all future application features.

Detailed functional requirements, acceptance criteria, workflow behaviour, and
implementation details for each feature are defined through that feature's own
specification, clarification, plan, and task artifacts. Feature-specific requirements MUST
NOT be promoted into this constitution unless they represent permanent cross-feature
governance.

This constitution does not govern development of the existing machine-learning model,
except where the model imposes a direct constraint on application behaviour, data
interpretation, or integration. Non-negotiable principles are limited to those stated
below; additional principles MUST NOT be inferred from the repository without being
explicitly raised with and approved by the team.

## Core Principles

### I. Specification-Driven Development

The approved specification is the source of truth for required behaviour. A change to
required behaviour MUST be reflected in the specification before implementation begins.
Plans, tasks, code, and tests MUST be kept consistent with the approved specification at
all times. Rationale: multiple contributors and AI agents work from these artifacts, and a
drifting specification silently invalidates every downstream plan, task, and review.

### II. Strict Scope Containment

Development MUST remain within the files, modules, and functionality identified by the
approved plan and tasks. Unrelated team code MUST NOT be modified. Existing notebooks,
model code, data-generation code, and other team-owned components MAY be inspected to
understand interfaces and integration requirements but MUST remain unmodified unless the
approved plan explicitly requires the change. If work outside the defined scope proves
necessary, the dependency MUST be identified and justified before implementation scope is
expanded.

### III. Read Broadly, Write Narrowly

Repository inspection MAY extend beyond implementation scope where necessary to understand
existing interfaces, architecture, and dependencies. Permission to inspect repository code
does not imply permission to modify it. Rationale: understanding the whole system is
required to build a correct, well-integrated change; altering code outside the approved
scope is not.

### IV. Minimal Necessary Change

Implement the simplest change that satisfies the approved specification. Unrelated
refactoring, cleanup, optimisation, architectural redesign, and speculative improvement
MUST NOT be performed as part of feature work.

### V. Reuse and Extend Existing Architecture

Existing application architecture MUST be reused and extended wherever reasonably possible.
Existing services, protocols, adapters, repositories, APIs, models, utilities, data
structures, and dependencies MUST be preferred over new equivalents. A parallel backend
architecture MUST NOT be created when the required behaviour can be implemented through the
existing application structure.

### VI. No Unnecessary Complexity

Additional abstractions, frameworks, dependencies, infrastructure, services, or
architectural layers MUST NOT be introduced solely because they represent a theoretically
better design. A new component MUST address an identified requirement or implementation
need that cannot reasonably be satisfied by the existing architecture.

### VII. Plan-Defined Implementation Structure

Specifications define required behaviour, not filenames, classes, or implementation
structure. The exact files, modules, interfaces, and components to create or modify MUST be
determined during planning, after inspection of the existing architecture. Implementation
MUST then remain within that approved structure unless a necessary dependency is identified
and justified.

### VIII. Application Technology Compatibility

Backend development MUST remain compatible with the existing Databricks application
environment. Python MUST remain the primary backend implementation language. Existing
Databricks technologies such as Delta Tables, Unity Catalog, and Serverless Compute MUST be
reused where appropriate rather than replaced with new equivalents.

### IX. Separation of Responsibilities and Modularity

The existing separation between frontend presentation, API/interface layers, backend
orchestration, data access, briefing generation, validation, retry orchestration, and
persistence MUST be preserved. Related functionality MUST remain modular enough to be
developed and tested independently. New modules MUST NOT be created where existing
components can reasonably support the required behaviour.

### X. Security and Privacy

Student data MUST be handled using the project's deidentified student identifier rather
than personally identifiable information. Credentials and API keys MUST NOT be hard-coded.
Existing Databricks security, secret-management, and Unity Catalog governance mechanisms
MUST be respected.

### XI. Input Validation and Explicit Error Handling

Inputs crossing application boundaries MUST be appropriately validated. Failures MUST be
handled explicitly rather than silently ignored, and errors MUST be propagated in a form
appropriate to the existing application architecture.

### XII. Proportionate Testing

Testing MUST be sufficient to verify the approved acceptance criteria and the project's
testing requirements. Redundant tests, excessive testing infrastructure, and tests added
solely to maximise coverage metrics MUST NOT be created.

### XIII. Human Review of AI-Generated Development Work

AI-generated code, tests, and important technical documentation MUST remain subject to
human review. Successful AI generation, or the passing of AI-generated tests, MUST NOT by
itself be treated as proof that an implementation is correct.

### XIV. Documentation and Implementation Traceability

Implementation decisions and completed work MUST remain traceable through the
specification, plan, tasks, tests, and relevant project documentation. Unnecessary
duplicate documentation MUST NOT be produced.

### XV. Completion Means Specification Satisfaction

Additional functionality, abstraction, optimisation, or complexity is not evidence of
better completion. A feature is complete when its approved requirements and acceptance
criteria are satisfied within the defined scope.

### XVI. Preserve Team Contributions

Development SHOULD remain within newly created or explicitly assigned files and SHOULD
avoid unnecessary changes to files associated with other team members' work. A change that
could alter another contributor's project evidence MUST be made only when it is required
for the approved feature.

### XVII. Human-Controlled Version Control

The AI agent MUST NOT commit, push, merge, rebase, create pull requests, or otherwise
modify Git or GitHub history unless explicitly instructed to perform that specific action.
The agent MAY inspect repository status, diffs, branches, and commit history as needed. All
commits and repository-changing Git operations remain under human control by default.

## Development Workflow and Compliance Review

- Features progress through their Spec Kit artifacts in order: specification, clarification,
  plan, tasks, then implementation. Each stage MUST be consistent with the stage before it.
- The plan's Constitution Check MUST be completed before implementation and MUST record how
  the plan satisfies every principle above, or justify any deviation.
- Pull requests MUST verify compliance with this constitution as part of review. AI-
  generated work MUST carry evidence of the human review required by Principle XIII.
- A deviation from an approved plan or task list MUST be raised and approved before the
  work proceeds, in line with Principles I, II, and VII.

## Governance

This constitution supersedes other development practices for this repository where they
conflict. Amendments MUST be proposed with a written rationale, MUST be approved by the
team, and MUST be published together with a version bump and an updated Sync Impact Report
in this file.

Versioning follows semantic versioning:

- MAJOR: backward-incompatible governance changes, such as removing or redefining a
  principle.
- MINOR: a new principle or section, or materially expanded guidance.
- PATCH: clarifications, wording, and non-semantic refinements.

Compliance is reviewed at planning time through the Constitution Check and again at
pull-request review. Component and repository documentation provides runtime development
guidance that complements these principles; where such documentation and this constitution
disagree, this constitution governs and the documentation MUST be corrected.

**Version**: 1.0.0 | **Ratified**: 2026-09-02 | **Last Amended**: 2026-09-02
