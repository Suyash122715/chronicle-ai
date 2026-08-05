# ADR-0006: Extraction Framework Architecture

- **Status:** Accepted
- **Date:** 2026-08-05
- **Decision Makers:** Chronicle AI Engineering Team
- **Related ADRs:**
  - ADR-0001: Clean Architecture
  - ADR-0002: Authentication Architecture
  - ADR-0003: Artifact Processing Pipeline
  - ADR-0004: Deterministic Classification
  - ADR-0005: Processing Pipeline

---

# Context

Chronicle AI processes multiple document types including resumes, certificates, marksheets, project reports, internship letters, portfolios, and GitHub repositories.

The extraction system must:

- support multiple document types
- support multiple LLM providers
- support evolving prompts
- support structured outputs
- maintain field-level provenance
- remain vendor independent
- remain testable
- support future providers without modifying business logic

A direct integration between application code and an LLM SDK would tightly couple business logic to a single provider and make future maintenance difficult.

---

# Decision

Chronicle AI adopts a layered extraction architecture.

```
Artifact
      │
      ▼
BaseLLMExtractor
      │
      ▼
PromptRepository
      │
      ▼
PromptRenderer
      │
      ▼
RenderedPrompt
      │
      ▼
LLMProviderInterface
      │
      ▼
GeminiLLMProvider
      │
      ▼
LLMResponse
      │
      ▼
ExtractionResult
```

Each component has exactly one responsibility.

---

# Architecture Decisions

## 1. PromptRepository

PromptRepository is responsible only for loading prompt assets.

Responsibilities:

- load prompt
- load schema
- resolve prompt version

PromptRepository does NOT:

- render prompts
- replace variables
- validate templates
- call an LLM
- contain business logic

This keeps prompt storage independent from prompt execution.

---

## 2. PromptRenderer

Prompt rendering is separated from prompt storage.

PromptRenderer receives:

- PromptBundle
- variables

and produces:

- RenderedPrompt

Responsibilities:

- placeholder replacement
- JSON formatting
- missing variable detection

PromptRenderer performs no filesystem access.

---

## 3. BaseLLMExtractor

BaseLLMExtractor orchestrates extraction.

It performs the following pipeline:

```
Load Prompt

↓

Render Prompt

↓

Call LLM Provider

↓

Receive Response

↓

Create ExtractionResult
```

Document-specific logic is intentionally excluded.

Concrete extractors implement only:

- prepare_variables()
- post_process()

This prevents duplication across extractors.

---

## 4. LLMProviderInterface

The application communicates only through LLMProviderInterface.

The interface contains no references to:

- Gemini
- OpenAI
- Anthropic
- provider SDKs

Providers are infrastructure implementations.

Examples:

- GeminiLLMProvider
- OpenAIProvider
- LocalLLMProvider

No application code changes are required when switching providers.

---

## 5. Gemini as Infrastructure

Gemini is treated as an infrastructure adapter.

It is responsible only for:

- sending prompts
- receiving responses
- converting responses into LLMResponse

Gemini does not contain:

- extraction logic
- prompt loading
- prompt rendering
- business rules

This preserves Clean Architecture dependency direction.

---

## 6. Prompt Storage

Prompt templates are stored outside Python code.

Example:

```
backend/prompts/

resume/
    v1.md
    schema.json

certificate/
    v1.md
    schema.json

project/
    v1.md
    schema.json
```

Markdown stores human-editable instructions.

JSON stores expected structured output.

This allows prompt evolution without modifying application code.

---

## 7. ExtractionResult

Every extractor returns the same canonical output object.

ExtractionResult contains:

- artifact_id
- document_type
- structured_data
- provenance
- warnings
- confidence
- extractor_version
- prompt_version
- llm_metadata
- started_at
- completed_at
- status

This standardizes downstream processing.

---

## 8. Provenance

Every extracted field may include provenance.

Provenance records:

- evidence snippet
- source location
- extraction method
- confidence
- metadata

This enables explainability and future audit capabilities.

---

## 9. Provider Independence

Chronicle AI is designed so providers are replaceable.

Replacing Gemini with another provider requires implementing only:

```
LLMProviderInterface
```

No domain or application code should change.

---

# Consequences

## Benefits

- Clear separation of responsibilities
- Provider independence
- Prompt versioning
- Testability
- Reusable extraction pipeline
- Consistent extraction results
- Easier maintenance
- Future extensibility

---

## Trade-offs

- More abstraction layers
- Additional interfaces
- Slightly higher implementation complexity

These trade-offs are accepted because they improve maintainability and scalability.

---

# Future Work

The following enhancements build upon this architecture:

- Prompt version management
- Prompt performance evaluation
- Multiple LLM provider support
- Cost tracking
- Retry strategies
- Streaming responses
- Structured output validation
- Automatic prompt experimentation
- Resume-specific extractor
- Certificate-specific extractor
- Project-specific extractor
- Embedding generation
- Knowledge graph construction
- Timeline generation

---

# Status

**Accepted**

This ADR defines the extraction framework used throughout Chronicle AI. Future extraction-related features should conform to the architecture described in this document.