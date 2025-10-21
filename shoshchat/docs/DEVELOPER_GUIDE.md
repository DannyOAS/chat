# ShoshChat Developer Guide

This guide explains the architecture, code structure, and key workflows implemented in the ShoshChat AI platform. It is aimed at developers onboarding to the project and provides a reference for extending or maintaining the system.

## Table of Contents

1. [System Overview](#system-overview)
2. [Backend Architecture](#backend-architecture)
   - [Core Apps](#core-apps)
   - [Authentication & Accounts](#authentication--accounts)
   - [Tenant Provisioning](#tenant-provisioning)
   - [Chat Service](#chat-service)
   - [Billing & Subscription](#billing--subscription)
   - [Knowledge Base](#knowledge-base)
3. [Frontend Architecture](#frontend-architecture)
   - [Routing & Layout](#routing--layout)
   - [Authentication Flow](#authentication-flow)
   - [Dashboard & Knowledge Center](#dashboard--knowledge-center)
4. [Knowledge Acquisition Pipeline](#knowledge-acquisition-pipeline)
   - [Upload and Sources](#upload-and-sources)
   - [Processing & Chunking](#processing--chunking)
   - [Embedding Generation](#embedding-generation)
   - [Retrieval During Chat](#retrieval-during-chat)
5. [Asynchronous Processing](#asynchronous-processing)
6. [API Surface](#api-surface)
7. [Configuration & Environment](#configuration--environment)
8. [Database Schema & Migrations](#database-schema--migrations)
9. [Testing & Local Validation](#testing--local-validation)
10. [Deployment Notes](#deployment-notes)
11. [Further Enhancements](#further-enhancements)

---

## System Overview

ShoshChat AI is a multi-tenant SaaS chatbot platform. Tenants provision their accounts, upload knowledge sources, and interact with an AI assistant that retrieves tenant-specific context before responding. Key capabilities include:

- Schema-based tenant isolation via `django-tenants`.
- JWT-secured REST API for authentication, onboarding, and chat operations.
- Knowledge ingestion pipeline (documents, URLs, text snippets) with chunking, embedding, and retrieval.
- Billing integration (Stripe webhook + subscription switching) and usage tracking.
- React + Tailwind frontend with dashboard, knowledge management UI, onboarding workflow, and embeddable chat widget.

---

## Backend Architecture

### Core Apps

The Django project is organized into domain-focused apps:

| App         | Responsibility                                                                   |
|-------------|------------------------------------------------------------------------------------|
| `accounts`  | Authentication, user registration, email verification, password reset, profiles.  |
| `tenancy`   | Tenant models, provisioning API, widget customization, domain management.         |
| `chatbot`   | Chat endpoints, analytics, orchestration (`ChatbotService`).                       |
| `billing`   | Plans, subscriptions, Stripe webhook handling, usage summaries, plan switching.    |
| `knowledge` | Knowledge source ingestion, chunk storage, embeddings, retrieval.                  |
| `nlp`       | LLM configuration models and adapters (Gradient/OpenAI fallback).                  |
| `compliance`| Audit logging middleware/models.                                                   |

Shared configuration lives in `core/settings.py`, with REST framework, throttles, security headers, SimpleJWT, and the new knowledge app registered.

### Authentication & Accounts

- `accounts/api/views.py` exposes endpoints under `/api/v1/auth/`:
  - `register/` and `register/onboard/` for classic or tenant-provisioning signup.
  - `login/`, `refresh/` (SimpleJWT token flow).
  - `password/reset/` + `/confirm/` and `email/verify/` + `/confirm/` for account recovery and verification.
  - All rate-limited via DRF throttle scopes (`auth_login`, `auth_register`, `auth_reset`, `auth_verify`).
- `accounts/models.py` defines `UserProfile` storing `email_verified`.
- Signals ensure profiles are created for new users.

### Tenant Provisioning

- `tenancy/services.py:create_tenant_with_subscription` creates the tenant schema, optional subscription, domain, and default widget settings.
- REST endpoints (`tenancy/api/views.py`) cover:
  - `POST /api/v1/tenants/` for onboarding (plan, accent, domain, etc.).
  - `GET /api/v1/tenants/me/` for dashboard metadata.
  - `PATCH /api/v1/tenants/me/settings/` for widget customization.
  - `POST /api/v1/tenants/me/domains/` for domain assignment.
  - `GET /api/v1/tenants/me/embed/` to retrieve the embeddable script snippet.

### Chat Service

- `ChatbotService` (chatbot/services/chatbot_service.py) now retrieves knowledge chunks before generating responses. It builds an enriched prompt containing contextual snippets from the knowledge base.
- `chatbot/api/views.py` exposes:
  - `POST /chat/` for chat messages (AllowAny, scoped throttling `chat`).
  - `GET /chat/sessions/` for authenticated history.
  - `GET /chat/analytics/` summarizing session/message counts and recent activity.

### Billing & Subscription

- `/api/v1/billing/` endpoints include usage, active subscription, plan list, plan switching, and Stripe webhook.
- `billing/api/views.py` ensures subscription updates set tenant trial flags and paid-through dates.

### Knowledge Base

New app `knowledge` manages business-specific context:

- Models:
  - `KnowledgeSource`: metadata for uploaded files, URLs, or raw text per tenant.
  - `KnowledgeChunk`: chunked text with embedding vector (256-dim array) and sequence ordering.
- Tasks:
  - `process_knowledge_source` extracts text (PDF/DOCX/TXT/URL), chunks it, generates embeddings (deterministic hash-based fallback), and persists chunks.
- Retrieval:
  - `knowledge/retrieval.py` ranks chunks by cosine similarity to the query embedding and returns top K for context injection.
- API:
  - `GET/POST /api/v1/knowledge/sources/` (list + create), `GET /sources/<id>/`, `GET /sources/<id>/chunks/`.
  - Uploads queue Celery tasks automatically.

---

## Frontend Architecture

### Routing & Layout

- Routing lives in `src/App.tsx`. Protected routes wrap components with `RequireAuth`, while `TenantProvider` (context) supplies tenant metadata throughout the app.
- `DashboardLayout` handles navigation (Dashboard, Knowledge, Onboarding) and sign out.

### Authentication Flow

- `Login`, `Register`, `ForgotPassword`, `ResetPassword`, and `VerifyEmail` pages orchestrate the end-to-end auth flows.
- The `register` helper hits `/auth/register/onboard/` and then logs in automatically, redirecting to the onboarding guide.

### Dashboard & Knowledge Center

- `Dashboard`: shows live analytics (sessions, messages), usage, plan status, domain management, widget customization, embed snippet, and recent sessions.
- `Knowledge`: new page for uploading files/URLs/text, viewing source status, and understanding the ingestion pipeline.
- `Onboarding`: final step after signup, surfacing embed code, widget preview, and next-step guidance.

The embeddable widget (`ChatWidget`) now auto-focuses, handles context injection, renders statuses, and previews tenant branding.

---

## Knowledge Acquisition Pipeline

### Upload and Sources

1. Frontend posts to `/knowledge/sources/` with `FormData` (file/url/text). 
2. `KnowledgeSource` row is created with `status=pending`. 
3. Celery task `process_knowledge_source` runs asynchronously.

### Processing & Chunking

- Extraction uses helper functions:
  - `extract_text_from_file`: PDF -> PyPDF2, DOCX -> python-docx, plain text fallback.
  - `extract_text_from_html`: Fetch via `requests`, parse with BeautifulSoup, strip scripts/styles.
  - `combine_segments` normalizes whitespace.
- `chunk_text` yields overlapping segments (700 chars, 100 overlap by default) to preserve context continuity.

### Embedding Generation

- Embeddings use a deterministic hash-based fallback (256-dim) to avoid external dependencies in development. If a tenant has an `LLMConfig`, its `model_name` seeds the vector for model-specific determinism.
- Vectors are stored in `KnowledgeChunk.embedding` (Postgres `ArrayField` of floats).

### Retrieval During Chat

1. `ChatbotService.process_message` calls `retrieve_relevant_chunks` with the query.
2. Chunks are scored via cosine similarity and top results concatenated as contextual notes.
3. The enriched prompt instructs the adapter to ground responses in this context.
4. Audit logging includes the enriched prompt, preserving compliance traceability.

---

## Asynchronous Processing

- Celery worker (`docker-compose` service `worker`) handles long-running tasks.
- Knowledge ingestion tasks are idempotent; status transitions ensure re-processing resilience.
- Stripe sync task (`billing/tasks.py`) and knowledge ingestion tasks both rely on environment-configured API keys.

---

## API Surface

Key REST endpoints (non-exhaustive):

| Endpoint                              | Method | Description                              |
|--------------------------------------|--------|------------------------------------------|
| `/api/v1/auth/register/`             | POST   | Basic user registration                  |
| `/api/v1/auth/register/onboard/`     | POST   | Registration + tenant provisioning       |
| `/api/v1/auth/login/`                | POST   | Obtain JWT pair                          |
| `/api/v1/tenants/`                   | POST   | Create tenant (admin onboarding)         |
| `/api/v1/tenants/me/`                | GET    | Tenant detail for dashboard              |
| `/api/v1/knowledge/sources/`         | GET/POST | List or upload knowledge sources       |
| `/api/v1/chat/`                      | POST   | Chat with knowledge-backed prompt        |
| `/api/v1/chat/analytics/`            | GET    | Sessions, messages, recent activity      |
| `/api/v1/billing/plans/`             | GET    | View available subscription plans        |
| `/api/v1/billing/subscription/switch/`| POST  | Change tenant plan                       |

Authentication is enforced via JWT except for public webhook / onboarding endpoints flagged with `AllowAny`.

---

## Configuration & Environment

Important environment variables (see `core/settings.py` for defaults):

- `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_*` connection settings, `REDIS_URL`
- Stripe keys: `STRIPE_TEST_PUBLIC_KEY`, `STRIPE_TEST_SECRET_KEY`, etc.
- DRF throttles: `DRF_THROTTLE_*`
- Email backend: `DJANGO_EMAIL_BACKEND` (defaults to console), `DJANGO_DEFAULT_FROM_EMAIL`
- Security headers: `DJANGO_SECURE_SSL_REDIRECT`, `DJANGO_SESSION_COOKIE_SECURE`, etc.

New Python dependencies: `PyPDF2`, `python-docx`, `beautifulsoup4` (install via `pip install -r requirements.txt`).

---

## Database Schema & Migrations

Generated migrations include:

- `accounts/migrations/0001_initial.py` (UserProfile).
- `tenancy/migrations/0002_...` (widget accent, color, welcome message).
- `knowledge/migrations/0001_initial.py` (knowledge sources & chunks).

Tenants continue to use schema-per-tenant through `django-tenants` migrations. Run migrations with `python manage.py migrate` (ensure Postgres host reachable or docker-compose services running).

---

## Testing & Local Validation

- Frontend: `npm run build` (TypeScript + Vite).
- Backend: `python manage.py check` and `python manage.py test` once dependencies installed and Postgres reachable.
- Knowledge ingestion can be smoke-tested by uploading a small `.txt` file; monitor Celery worker logs for processing status.

---

## Deployment Notes

1. Apply migrations across public and tenant schemas (`manage.py migrate_schemas`).
2. Ensure Celery worker and Redis are running; configure worker for autoscaling.
3. Provision the email backend (SendGrid, SES) for verification and reset flows.
4. Configure Stripe webhook endpoint to `/api/v1/billing/stripe/webhook/`.
5. If scaling beyond Postgres for embeddings, replace the hash fallback with real vector embeddings + pgvector or managed vector DB.

---

## Further Enhancements

- Replace deterministic embeddings with managed embeddings (OpenAI, Azure, etc.) and integrate pgvector indexes for similarity search.
- Add versioning / reprocessing for updated knowledge sources.
- Implement team management and fine-grained roles.
- Expand analytics (per-intent accuracy, conversation summaries) once knowledge context is in place.
- Build automated tests covering ingestion, retrieval, and prompt construction.

---

Welcome aboard! Review the sections above to understand how components interact and where to extend functionality. For questions or contributions, start with the app-specific services and API layers described here.
