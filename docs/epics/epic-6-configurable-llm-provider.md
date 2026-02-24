# Epic 6: Configurable LLM Provider

**Epic Goal**: Make the LLM provider and model switchable via environment variables, defaulting to a free OpenRouter model for zero-cost prototyping, while allowing clients to upgrade to Anthropic or OpenAI by simply setting their API key and changing the provider.

**Integration Requirements**: Touches `app/config.py`, `app/graph/nodes.py`, `tests/test_nodes.py`, and `requirements.txt`. No database or frontend changes. All API keys are optional — only the selected provider's key is validated.

**MoSCoW**: Stories 6.1 + 6.2 + 6.3 = Must Have | Story 6.4 = Should Have | Story 6.5 = Could Have
**Total Story Points**: 9

---

## Multi-Key Coexistence Strategy

Users may set API keys for all three providers simultaneously in `.env`. The strategy is:

1. **`LLM_PROVIDER` is the single selector** — determines which provider is active. Defaults to `openrouter`.
2. **Only the selected provider's key is validated** — `get_llm()` raises `ValueError` only if the active provider's key is missing.
3. **Switching is a one-line change** — change `LLM_PROVIDER=anthropic` (and set `LLM_MODEL` if desired).
4. **All keys coexist peacefully** — having all three keys set simultaneously is valid.

### Quick-switch scenarios

| Goal | Change in `.env` |
|------|-----------------|
| Free prototyping (default) | No changes needed — OpenRouter + Llama 3.3 70B |
| Premium Anthropic results | `LLM_PROVIDER=anthropic` + `LLM_MODEL=claude-sonnet-4-5` |
| OpenAI alternative | `LLM_PROVIDER=openai` + `LLM_MODEL=gpt-4o` |
| Different free model | `LLM_MODEL=google/gemma-2-9b-it:free` (keep provider=openrouter) |

---

## Story 6.1 — Settings & Environment Variables

**As a** developer deploying the tool,
**I want** LLM provider, model, and temperature configurable via `.env` variables,
**so that** I can switch providers without editing source code.

### Acceptance Criteria
1. `app/config.py` `Settings` class gains new fields with defaults: `LLM_PROVIDER`, `LLM_MODEL`, `LLM_TEMPERATURE`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY`.
2. `ANTHROPIC_API_KEY` changes from required to optional (`str = ""`). Validated at runtime only when provider=anthropic.
3. `.env.example` updated with all new variables documented, showing the multi-key setup pattern.
4. All API key fields default to `""`. Only the active provider's key is validated at runtime.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 1

---

## Story 6.2 — LLM Factory Function

**As a** research pipeline,
**I want** a single `get_llm()` factory that returns the correct `BaseChatModel` based on settings,
**so that** LLM construction logic is centralized and testable.

### Acceptance Criteria
1. `get_llm() -> BaseChatModel` added to `app/config.py`.
2. `openrouter` (default) returns `ChatOpenAI` with `base_url="https://openrouter.ai/api/v1"`. Raises `ValueError` if key empty.
3. `anthropic` returns `ChatAnthropic`. Raises `ValueError` if key empty.
4. `openai` returns `ChatOpenAI` without custom `base_url`. Raises `ValueError` if key empty.
5. Unknown provider raises `ValueError` listing valid providers.
6. Imports for `ChatAnthropic` / `ChatOpenAI` are lazy (inside function body).
7. `langchain-openai>=0.3.0` added to `requirements.txt`.
8. New `tests/test_llm_factory.py` with 9 tests covering all providers, missing keys, unknown provider, multi-key coexistence, and case-insensitivity.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 3

---

## Story 6.3 — Replace Hardcoded LLM Instantiations

**As a** research pipeline,
**I want** all LLM instantiation sites to use `get_llm()`,
**so that** the provider switch takes effect across the entire pipeline.

### Acceptance Criteria
1. Remove `from langchain_anthropic import ChatAnthropic` from `app/graph/nodes.py`.
2. Add `from app.config import get_llm` and `from langchain_core.language_models import BaseChatModel` to imports.
3. Replace 4 `ChatAnthropic(...)` calls with `get_llm()`.
4. Update 3 helper function type hints from `ChatAnthropic` to `BaseChatModel`.
5. Update all `patch("app.graph.nodes.ChatAnthropic", ...)` in `tests/test_nodes.py` to `patch("app.graph.nodes.get_llm", ...)`.
6. All existing tests pass. Lint and type checks pass.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 3

---

## Story 6.4 — Documentation & Startup Validation

**As a** developer or evaluator,
**I want** the README and startup updated to reflect multi-provider support,
**so that** setup instructions are accurate and misconfiguration is caught early.

### Acceptance Criteria
1. `README.md` Configuration section updated with LLM Provider subsection, env var table, quick-switch examples, and multi-key coexistence explanation.
2. `run.sh` API key validation updated to check only the key for the selected `LLM_PROVIDER`.
3. Startup log line in `app/main.py` prints active provider and model on boot. Never prints API keys.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 1

---

## Story 6.5 — OpenRouter Smoke Test

**As a** developer testing with free models,
**I want** a documented manual test procedure for OpenRouter,
**so that** I can verify end-to-end functionality before demoing.

### Acceptance Criteria
1. Optional integration test in `tests/test_openrouter_integration.py` (skipped when `OPENROUTER_API_KEY` not set).
2. Known model compatibility notes: which free OpenRouter models produce usable JSON output.
3. Step-by-step manual test procedure documented in story file.

**Executor**: @dev | **Quality Gate**: @architect
**Story Points**: 1

---

## Implementation Sequence

```
6.1 (Settings) -> 6.2 (Factory + tests) -> 6.3 (Replace instantiations) -> 6.4 (Docs) -> 6.5 (Smoke test)
```

## Files Modified

| File | Stories | Change |
|------|---------|--------|
| `app/config.py` | 6.1, 6.2 | Add 5 settings fields + `get_llm()` factory |
| `app/graph/nodes.py` | 6.3 | Replace import, 4 instantiations, 3 type hints |
| `requirements.txt` | 6.2 | Add `langchain-openai>=0.3.0` |
| `.env.example` | 6.1 | Add documented env vars with multi-key pattern |
| `tests/test_llm_factory.py` | 6.2 | New: 9 factory tests |
| `tests/test_nodes.py` | 6.3 | Update 20 patch targets |
| `README.md` | 6.4 | Update Configuration section |
| `run.sh` | 6.4 | Update API key validation |
| `app/main.py` | 6.4 | Add startup log line |
| `tests/test_openrouter_integration.py` | 6.5 | New: 2 integration tests (skipped without key) |

## Key Design Decisions

1. **OpenRouter is the default provider** — enables zero-cost prototyping out of the box.
2. **Single selector, multi-key coexistence** — `LLM_PROVIDER` picks the active provider.
3. **Lazy imports** — `ChatAnthropic` and `ChatOpenAI` imported inside `get_llm()` body.
4. **Three providers, not a plugin system** — simple `if/elif/else` is sufficient.
5. **Patch target**: `patch("app.graph.nodes.get_llm", ...)` — patch where it's looked up.
