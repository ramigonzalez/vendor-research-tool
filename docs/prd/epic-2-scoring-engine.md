# Epic 2: Scoring Engine

**Epic Goal**: Implement the complete scoring system — Pydantic domain models, LLM-powered capability assessment, and fully deterministic score/confidence/ranking computation.

**Integration Requirements**: Domain models (E2-S1) are the foundation for all other epics. Scoring consumes evidence from Epic 1 and produces results consumed by Epic 3 (persistence) and Epic 4 (UI).

**MoSCoW**: All stories = Must Have
**Total Story Points**: 12

---

## Story 2.1 — Pydantic Domain Models

**As a** development team,
**I want** all domain objects defined as typed Pydantic v2 models,
**so that** every data boundary in the system is type-safe, validated, and self-documenting.

### Acceptance Criteria
1. `Evidence` model with fields: `claim: str`, `source_url: str`, `source_name: str`, `source_type: SourceType`, `content_date: str | None`, `relevance: float` (0–1), `supports_requirement: bool`.
2. `SourceType` enum: `official_docs`, `github`, `comparison`, `blog`, `community`.
3. `CapabilityLevel` enum: `full`, `partial`, `minimal`, `none`, `unknown`.
4. `MaturityLevel` enum: `ga`, `beta`, `experimental`, `planned`, `unknown`.
5. `LLMAssessment` model: `capability_level`, `capability_details: str`, `maturity`, `limitations: list[str]`, `supports_requirement: bool`.
6. `ScoreResult` model: `score: float` (0–10), `confidence: float` (0–1), `capability_level`, `maturity`, `justification: str`, `limitations: list[str]`, `evidence: list[Evidence]`.
7. `JobStatus` enum: `pending`, `running`, `completed`, `failed`.
8. `ResearchJob` model: `id: str`, `status`, `created_at`, `completed_at`, `progress_pct: int`, `progress_message: str`.
9. `Requirement` model: `id: str`, `description: str`, `priority: str`, `weight: float`.
10. `VendorRanking` model: `vendor: str`, `overall_score: float`, `rank: int`.
11. `ResearchResults` model: `vendors: list[str]`, `requirements: list[Requirement]`, `matrix: dict`, `rankings: list[VendorRanking]`, `summary: str`.
12. `ResearchState` TypedDict for LangGraph state with all pipeline fields.
13. All models live in `app/models.py`.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 2

---

## Story 2.2 — LLM Capability Assessment

**As a** scoring engine,
**I want** an LLM to produce a structured capability assessment for each vendor×requirement pair from collected evidence,
**so that** the deterministic scoring engine has a reliable, structured input to compute from.

### Acceptance Criteria
1. LangGraph node `assess_capabilities` processes each vendor×requirement pair with its evidence.
2. LLM receives: vendor name, requirement description, priority, and all collected evidence (claim + source_url + source_type + relevance).
3. LLM outputs `LLMAssessment` via structured output: `capability_level`, `capability_details`, `maturity`, `limitations`, `supports_requirement`.
4. LLM instructed with conservative guidance: use `unknown` when ambiguous, not `partial`.
5. Assessment stored in `ResearchState.assessments` keyed by `(vendor, requirement_id)`.
6. Assessment prompt uses evidence-only context (no vendor pre-knowledge injection).
7. Failed assessment defaults to `capability_level=unknown, maturity=unknown, limitations=[]`.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 3

---

## Story 2.3 — Deterministic Score Computation

**As a** scoring engine,
**I want** to compute a 0–10 per-requirement score from the LLM assessment and evidence metadata using a fixed algorithm,
**so that** scores are transparent, reproducible, and explainable without LLM involvement.

### Acceptance Criteria
1. `compute_requirement_score(assessment, evidence_list) -> float` function in `app/scoring/engine.py`.
2. Capability Coverage (40%): full=10, partial=7, minimal=3, none=0, unknown=2.
3. Evidence Strength (30%): min(len(supporting_evidence), 5) / 5 × 10.
4. Maturity Score (20%): ga=10, beta=7, experimental=4, planned=2, unknown=3.
5. Limitations Penalty (10%): max(0, 10 − len(limitations) × 2).
6. Final score = weighted sum, clamped to [0, 10].
7. Function is pure (no side effects, no LLM calls).
8. Unit tests cover all capability level combinations and edge cases (0 evidence, max limitations).

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 3

---

## Story 2.4 — Confidence Score Computation

**As a** scoring engine,
**I want** to compute a 0–1 confidence score from evidence metadata without any LLM involvement,
**so that** confidence reflects actual evidence quality, not LLM opinion.

### Acceptance Criteria
1. `compute_confidence(evidence_list) -> float` function in `app/scoring/engine.py`.
2. Source Count (30%): min(count, 5) / 5.
3. Source Authority (30%): mean of authority weights per source (official_docs=1.0, github=0.8, comparison=0.6, blog=0.4, community=0.3).
4. Source Recency (25%): proportion of sources with content_date within 6 months = 1.0; within 12 months = 0.7; older or unknown = 0.3.
5. Consistency (15%): ratio of `supports_requirement=True` evidence to total evidence (or 0.5 if mixed).
6. Final confidence = weighted sum, clamped to [0, 1].
7. Empty evidence list returns confidence = 0.0.
8. Unit tests cover zero-evidence, all-authoritative, all-old-dates cases.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 2

---

## Story 2.5 — Weighted Ranking Computation

**As a** scoring engine,
**I want** to compute overall vendor rankings from per-requirement scores, priorities, and confidence,
**so that** the executive summary and UI can present a ranked recommendation.

### Acceptance Criteria
1. `compute_vendor_rankings(matrix, requirements) -> list[VendorRanking]` in `app/scoring/engine.py`.
2. Weighted score per vendor: `Σ(req_score × req_weight × confidence) / Σ(req_weight) × 10`.
3. Rankings sorted descending by weighted score.
4. Each `VendorRanking` includes: `vendor`, `overall_score` (0–10), `rank` (1-based).
5. Returns all 4 vendors ranked even if scores are equal (stable sort by vendor name as tiebreaker).
6. Unit tests verify ranking order with known score fixtures.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 2
