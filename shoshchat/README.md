# ShoshChat AI

ShoshChat AI is a multi-tenant SaaS chatbot platform built with Django, Django REST Framework, django-tenants, and a React + Tailwind frontend. It integrates with DigitalOcean Gradient for AI-powered conversations and Stripe for subscription billing.

## Features

- Schema-based multi-tenancy powered by `django-tenants`
- Tenant-specific chatbot personas for retail/e-commerce and finance/insurance sectors
- REST API for chat interactions, billing insights, and tenant provisioning
- Stripe billing via `dj-stripe` with Celery-powered synchronization tasks
- Compliance-focused audit logging and consent tracking
- React dashboard with TailwindCSS styling and embeddable chat widget
- Dockerized local development environment using PostgreSQL and Redis

## API Overview

| Method | Endpoint                    | Purpose                         |
| ------ | --------------------------- | -------------------------------- |
| POST   | `/api/v1/chat/`             | Send a message to the chatbot    |
| GET    | `/api/v1/chat/sessions/`    | Retrieve chat session history    |
| GET    | `/api/v1/billing/usage/`    | Retrieve usage statistics        |
| GET    | `/api/v1/billing/subscription/` | Inspect active subscription |
| POST   | `/api/v1/billing/stripe/webhook/` | Stripe webhook receiver   |
| POST   | `/api/v1/tenants/`          | Provision a new tenant           |

## Getting Started

1. Copy `.env.example` to `.env` and update the secrets.
2. Build the containers using Docker Compose:

   ```bash
   docker-compose up --build
   ```

3. Apply migrations and create a superuser:

   ```bash
   docker-compose run --rm web python manage.py migrate
   docker-compose run --rm web python manage.py createsuperuser
   ```

4. Install frontend dependencies and run the Vite dev server:

   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Testing

```bash
pytest
```

## Project Layout

```
shoshchat/
├── core/            # Django project configuration
├── tenancy/         # Tenant & domain models + provisioning API
├── chatbot/         # Chat logic, API, and integration services
├── nlp/             # LLM configuration and adapters
├── billing/         # Plans, subscriptions, usage tracking
├── compliance/      # Audit logging middleware and models
└── frontend/        # React widget and dashboard
```

## Frontend Overview

- `src/components/ChatWidget.tsx` – embeddable widget for tenant sites
- `src/pages/Dashboard.tsx` – tenant portal showing usage and settings
- Axios interceptors and hooks prepare for JWT authentication flows

## Deployment

The repository is ready for deployment on DigitalOcean App Platform. Configure environment variables, connect your GitHub repository, and set up build commands for both backend and frontend.

