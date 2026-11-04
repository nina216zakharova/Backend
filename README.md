# Backend Design System & Architectural Standards

## 1. Selected Architecture

The Tribe backend adopts a **Modular Monolith with a Clean Layered Architecture** built on **Django** and **Django REST Framework (DRF)**.

The system is organized into four distinct operational layers per domain module:
1. **Presentation / Interface Layer (`views.py`)**: Thin API views and viewsets responsible exclusively for HTTP routing, request context parsing, permission checks, service delegation, and formatting standardized responses.
2. **Serialization & Validation Layer (`serializers.py`)**: Data Transfer Object (DTO) mapping, data transformation, input sanitization, and structural validation.
3. **Domain / Service Layer (`services.py` & domain logic)**: Pure business rules, state transitions (e.g., application acceptance, project status transitions), capacity control checks, and atomic database transaction boundaries (`transaction.atomic`).
4. **Data Access & Persistence Layer (`models.py`)**: Django ORM models inheriting from shared audit bases (`TimeStampedModel`), relational constraints, indexes, and optimized query encapsulation.

---

## 2. Reasons for Selection

* **MVP Velocity & Operational Simplicity**: Eliminates microservice overhead (network latency, RPC serialization, distributed tracing, and multi-repo deployment) while maintaining strict modular boundaries that can be extracted into independent services if scaling demands require it later.
* **Separation of Concerns (Anti-Fat Views / Anti-Fat Models)**: Django applications commonly suffer from bloated views or overly monolithic models. Placing multi-model workflows, capacity checks, and state transitions into dedicated service functions keeps business logic testable in isolation without mocking HTTP requests.
* **Native Django / DRF Alignment**: Directly leverages Django's mature ORM, migration engine, authentication framework, and DRF's serializer and permission ecosystem without introducing non-standard third-party abstractions.
* **Frontend-Backend Contract Predictability**: A single envelope contract simplifies API client consumption across all mobile and web clients (React/Vite), providing predictable schemas for both success and failure cases.
* **Database Portability**: Supports dual-mode persistence (cloud PostgreSQL instance on Liara with automatic fallback to local SQLite for isolated testing and development environments).

---

## 3. Recommended Backend Structure

```text
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── skillswap_backend/           # Core project configuration
│   ├── __init__.py
│   ├── settings.py             # Environment-aware Django settings
│   ├── urls.py                 # Root URL routing
│   ├── wsgi.py
│   └── asgi.py
├── apps/                       # Domain-driven modular applications
│   ├── common/                 # Cross-cutting utilities & base classes
│   │   ├── apps.py
│   │   ├── models.py           # TimeStampedModel abstract base
│   │   ├── responses.py        # api_success_response & api_error_response helpers
│   │   ├── exceptions.py       # Centralized DRF custom exception handler
│   │   └── views.py            # System health check & diagnostic endpoints
│   ├── accounts/               # User identity, profiles, and contact channels
│   ├── skills/                 # Skill taxonomy, mentoring offerings, and skill tags
│   ├── projects/               # Projects, membership lists, and capacity tracking
│   └── applications/           # Membership applications and status workflows
└── scripts/
    └── seed_data.py            # Development seed data generators
```

### Module Responsibilities

| Component | Responsibility | Allowed Dependencies |
| :--- | :--- | :--- |
| `views.py` | Handles HTTP requests/responses, permissions, invokes services | Serializers, Services, Permissions |
| `serializers.py` | Serializes models to JSON and validates input payloads | Models |
| `services.py` | Executes business logic, enforces business invariants, coordinates transactions | Models, Repositories/Selectors |
| `models.py` | Defines table schemas, constraints, field validations, and relationships | `apps.common.models` |

---

## 4. Essential Coding Conventions

### 4.1. Application and Module Organization
* All domain logic resides under the `apps/` directory. Each app represents a distinct bounded context (e.g., `projects`, `accounts`).
* Shared cross-cutting concerns (base models, response wrappers, exception handlers) belong exclusively to `apps.common`.
* Cross-app imports must flow unidirectionally to avoid circular dependencies (e.g., `applications` depends on `projects` and `accounts`, but `accounts` must never depend on `applications`).

### 4.2. Models and Database Access Conventions
* **Base Model**: Every persistent model must inherit from `apps.common.models.TimeStampedModel` to automatically track `created_at` and `updated_at`.
* **Field Integrity**: Critical constraints (minimum capacity >= 2, non-negative numbers) must be enforced at both model-level (`clean()`) and database-level (`CheckConstraint`, `UniqueConstraint`).
* **Query Optimization**: Views and services must avoid N+1 queries by explicitly using `select_related` for `ForeignKey`/`OneToOne` and `prefetch_related` for `ManyToManyField`/reverse relations.
* **Transactions**: Multi-table write operations or state changes involving capacity checks must be wrapped in `transaction.atomic()`.

### 4.3. API and Request/Response Structure
All endpoints must respond using the standardized unified envelope format:

#### Success Envelope (HTTP 200, 201)
```json
{
  "success": true,
  "message": "Resource retrieved successfully.",
  "data": {},
  "meta": {
    "page": 1,
    "page_size": 12,
    "total_items": 1
  }
}
```

#### Error Envelope (HTTP 4xx, 5xx)
```json
{
  "success": false,
  "message": "Validation failed.",
  "errors": {
    "field_name": ["Specific error description."]
  },
  "error_code": "VALIDATION_ERROR"
}
```

### 4.4. Validation and Centralized Error Handling
* Views must not handle low-level framework exceptions manually.
* Uncaught exceptions and DRF validation errors are intercepted globally by `apps.common.exceptions.custom_exception_handler`.
* Error responses must return an explicit `error_code` string:
  * `VALIDATION_ERROR` (400)
  * `UNAUTHORIZED` (401)
  * `PERMISSION_DENIED` (403)
  * `NOT_FOUND` (404)
  * `CAPACITY_EXCEEDED` (400)
  * `DATABASE_UNAVAILABLE` (503)
  * `INTERNAL_SERVER_ERROR` (500)

### 4.5. Authentication and Authorization
* Endpoints default to `rest_framework.permissions.IsAuthenticatedOrReadOnly` at the project level.
* Resource ownership is guarded through explicit permission classes (e.g., `IsCreatorOrReadOnly`).
* Destructive actions (status change, member deletion) require explicit permission verification prior to service invocation.

### 4.6. Configuration and Environment Management
* No sensitive values (secrets, database passwords, API keys) may be hardcoded.
* Configuration is managed via environment variables loaded through `python-dotenv` from `.env`.
* A clean `.env.example` must be maintained at all times documenting required environment keys with non-production dummy values.
* Settings support a graceful database fallback: if PostgreSQL is unreachable or unconfigured during local development, settings fall back safely to SQLite unless `DB_STRICT=True` is provided.

### 4.7. Naming Conventions & Code Style
* **Python Standards**: Strict adherence to PEP 8.
* **Classes**: `PascalCase` (e.g., `ProjectViewSet`, `ProjectMember`, `TimeStampedModel`).
* **Functions, methods, variables**: `snake_case` (e.g., `remaining_slots`, `toggle_status`).
* **Constants & Choice Tuples**: `UPPER_SNAKE_CASE` (e.g., `STATUS_CHOICES = [('RECRUITING', 'Recruiting'), ...]`).
* **API URLs**: Lowercase kebab-case or plural noun paths (e.g., `/api/projects/`, `/api/health/`).

---

## 5. Architectural Decisions (ADR Summary)

* **ADR-001 (Unified Response Contract)**: Enforces uniform JSON envelopes across all successful and failed API responses to decouple client error parsers from internal Django error schemas.
* **ADR-002 (Layered Service Pattern)**: Prohibits business calculations and multi-step mutations inside DRF `views.py` and `serializers.py`, centralizing transaction safety in service modules.
* **ADR-003 (Dual-Mode Database Adapter)**: Enables cloud PostgreSQL connectivity (Liara) for staging/production while maintaining zero-setup SQLite fallback for local developer velocity.
* **ADR-004 (Global Exception Interceptor)**: Maps DRF exception hierarchies to standardized envelope payloads with machine-readable `error_code` identifiers.

