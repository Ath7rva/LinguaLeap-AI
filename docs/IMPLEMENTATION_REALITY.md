# Implementation Reality

This document keeps the college report, resume discussion, and application behavior aligned.

## Implemented

- React and TypeScript learner interface
- FastAPI REST API
- SQLAlchemy persistence
- JWT authentication with bcrypt password hashes
- Groq-hosted LLM tutor and translation
- Groq Whisper speech-to-text
- Rule-based pronunciation similarity score
- Multi-level Hindi, German, and Japanese lesson content
- Simplified SM-2 spaced repetition
- Stored interaction moderators and optional pre/post assessments
- Consent-based experiment assignment
- Computed learner and research analytics
- Explicitly labeled simulated demo data
- Automated backend tests
- Managed Neon PostgreSQL production persistence
- Alembic initial migration for versioned PostgreSQL schema creation
- A1-A2-B1 product placement and adaptive skill mastery
- Explainable next-step recommendations
- Native listening clips and recorded listening attempts
- Word-level transcript comparison for pronunciation practice
- Durable personalized-practice and pronunciation job records
- Translation and generated-practice caching with optional Redis
- Per-user/IP rate limiting with Redis or process-local fallback
- Refresh-token rotation, verification/reset tokens, and session revocation
- Expiring researcher invitations
- Versioned and frozen experiment configurations with stable enrollment
- Confidence intervals, effect sizes, attrition, funnels, cohorts, and sample-size warnings
- Request IDs, security headers, optional Sentry, and AI usage/cost records
- Backend, frontend component, browser smoke, migration, build, and secret-scanning CI checks

## Not Implemented

- TensorFlow or PyTorch
- A custom-trained deep-learning model
- MongoDB or a hybrid MongoDB/PostgreSQL architecture
- Kubernetes
- A clinically or academically validated accuracy score
- A completed controlled study with statistically significant findings

## Claim Boundaries

Pronunciation scoring compares Whisper's transcription with the target phrase and identifies word-level matches, substitutions, omissions, and additions. It is not a phoneme-level acoustic assessment.

The LLM tutor uses a hosted Groq model. LinguaLeap does not train or fine-tune that model.

Analytics summarize stored interactions. They demonstrate an evaluation design but do not prove learning effectiveness without an adequately powered, ethically reviewed study.

Simulated users exist only to make the research dashboard understandable during a demonstration. Their records carry `is_simulated=true` and are excluded from primary observed experiment comparisons.

The deployed Vercel backend uses managed Neon PostgreSQL. Persistence was verified by creating an account, deploying a new production version, and successfully authenticating the same account afterward.

Vercel does not provide an always-running worker process for this application. AI jobs are persisted with statuses, idempotency keys, attempts, and results, then executed opportunistically in background tasks and retried during polling. This is durable orchestration, not a claim of a dedicated queue-worker cluster.
