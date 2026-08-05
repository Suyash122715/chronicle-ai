# ADR-0005

# Deterministic Document Classification

Status: Accepted

Date: 2026-08-05

---

# Context

Chronicle AI requires every uploaded artifact to be classified before any downstream AI processing can occur.

Future processing depends on knowing the document type.

Examples include:

- Resume
- Certificate
- Marksheet
- Internship Letter
- Project Report
- GitHub Repository
- Portfolio

Initially it was considered to perform classification using an LLM.

However this introduced unnecessary complexity, external dependencies, increased latency, additional cost, and non-deterministic behaviour for a problem that can be solved reliably using document metadata.

---

# Decision

Chronicle AI will use deterministic classification as the first stage of the processing pipeline.

Classification is performed using only:

- filename
- extension
- MIME type
- available metadata
- checksum (when available)

No OCR.

No extracted text.

No LLM.

No AI provider.

---

# Rule Priority

Classification follows deterministic rule precedence.

1. Filename Rules
2. Extension Rules
3. MIME Rules
4. Metadata Rules
5. Unknown

Earlier rules always take precedence over later rules.

---

# Confidence

Confidence is deterministic.

The platform does not generate floating-point confidence values.

Supported levels are:

- HIGH
- MEDIUM
- LOW

Confidence is determined by the rule that produced the classification.

---

# Why Not AI?

Using an LLM for initial document classification was intentionally rejected because:

- deterministic rules are sufficient
- deterministic rules are faster
- deterministic rules are cheaper
- deterministic rules are reproducible
- deterministic rules simplify testing
- deterministic rules remove external dependencies

AI should solve problems that deterministic algorithms cannot.

---

# Classification Ownership

Classification metadata belongs to the Artifact aggregate.

Current fields include:

- document_type
- classification_confidence
- classifier_version
- classified_at

A dedicated Classification aggregate was intentionally not introduced.

If future requirements include:

- classification history
- multiple classifier versions
- audit trails

the architecture may evolve into a dedicated classification model.

---

# API Boundary

Domain Value Objects are not exposed through the API.

Presentation models serialize domain concepts into primitive values.

Example:

Domain

DocumentType

↓

Presentation

"Resume"

This preserves Clean Architecture boundaries.

---

# Provider Independence

Business logic depends only on:

DocumentClassifierInterface

Infrastructure provides implementations.

Current implementation:

DeterministicDocumentClassifier

Future implementations may include:

- GeminiClassifier
- HybridClassifier
- EnsembleClassifier

without changing application code.

---

# Consequences

Positive

- Fast processing
- No AI cost
- Deterministic behaviour
- Easy testing
- Stable architecture
- Replaceable classifier implementations

Trade-offs

- Less flexible than AI classification
- New document types require explicit rules
- Some uncommon documents may initially classify as Unknown

These trade-offs are acceptable for Phase 4.

---

# Future Evolution

Future phases may introduce AI-assisted classification.

The deterministic classifier will remain available as:

- fallback
- validation
- offline mode
- testing implementation

The application layer should never know which classifier implementation is active.

Only the dependency injection layer decides which implementation is used.

---

# Decision Summary

Chronicle AI adopts deterministic document classification as the foundation of its processing pipeline.

Artificial Intelligence will enhance the pipeline in later phases but will not replace deterministic classification as the architectural baseline.