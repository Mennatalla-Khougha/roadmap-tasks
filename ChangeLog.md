# ChangeLog.md

---

## Project Objective

**Goal:**  
Build a robust, scalable backend API using FastAPI, Firestore, and Redis to manage learning roadmaps and user-specific to-do lists.

- Each roadmap (e.g., "Flutter", "Python") contains topics and tasks.
- Users can browse roadmaps, add them to their personal to-do list, and track progress.
- All CRUD operations are supported, with user authentication, JWT-based security, and concurrency support (100+ requests).
- The project is structured for maintainability, testing, and best-practice learning.

---

## What Has Been Done

### 1. Project Initialization & Structure

- **Scaffolded directory structure** for modularity:
  - `main.py`, `core/`, `schemas/`, `services/`, `routers/`, `tests/`
- **Dockerized environment** using `Dockerfile` and `compose.yaml` for FastAPI, Redis, and Firestore emulator.
- **.env file** for environment variables and secrets, with `.gitignore` updated to exclude sensitive files.

### 2. Configuration Management

- **Config management refactored** to use Pydantic’s `BaseSettings` in `core/config.py` for type-safe, centralized, and environment-driven configuration.
- **All secrets and settings** (Firestore, Redis, JWT) are loaded from `.env` via `ConfigDict` as per Pydantic v2 best practices.

### 3. Schema Design

- **Pydantic models** for user, roadmap, and to-do/task entities created in `schemas/`.
- **Updated to Pydantic v2+**: Replaced deprecated `class Config` with `model_config = ConfigDict(...)` in all models.
- **Timestamps** (`created_at`, `updated_at`) are always set using timezone-aware UTC datetimes.

### 4. User Authentication & Security

- **Password hashing** implemented using `passlib` (`bcrypt`).
- **JWT-based authentication**:
  - Tokens include standard claims: `sub` (subject), `id`, `iat` (issued at), `exp` (expiration).
  - Tokens are created and validated using `jose` and project secret.
  - JWT logic centralized in `core/security.py` for maintainability.
- **FastAPI dependency** for extracting and validating JWT from `Authorization: Bearer <token>` header.
- **Error handling** standardized for expired/invalid tokens and other auth errors.

### 5. User Services

- **User registration, login, and retrieval** implemented in `services/user_services.py`:
  - Registration checks for duplicate email, hashes password, sets timestamps.
  - Login verifies password, issues JWT with best-practice claims.
  - Retrieval returns all user data except password.
- **Firestore integration**: All user data is stored and retrieved directly from Firestore.

### 6. API Routes

- **User endpoints** (`/register`, `/login`, `/user`) implemented in `routers/users.py`:
  - Registration and login endpoints return appropriate response models or JWTs.
  - `/user` endpoint is protected and requires valid JWT.
- **Error handling**: All endpoints return clear HTTP status codes and messages for errors.

### 7. Testing

- **Comprehensive test suite**:
  - `tests/test_user_services.py`: Unit tests for user registration, login, error cases.
  - `tests/test_user_routes.py`: Integration tests for endpoints, including protected route access.
  - `tests/test_security.py`: Tests for password hashing/verification and JWT creation/validation.
- **Test coverage** includes both positive and negative cases (e.g., duplicate registration, invalid login).
- **Pytest and pytest-asyncio** used for running tests.
- **Test warnings addressed**: Guidance provided for updating pytest and Pydantic v2 config usage.

### 8. Continuous Integration

- **GitHub Actions workflow** (`.github/workflows/ci.yml`) runs tests on every push/PR.
- Ensures code quality and catches regressions early, even for solo development.

### 9. Roadmap CRUD API & Service Layer

- **CRUD endpoints for roadmaps** (`/roadmaps`) implemented, following RESTful conventions and best practices.
- **Service layer** (`services/roadmap_services.py`) encapsulates Firestore and Redis logic, using async/await for concurrency.
- **Batch writes** used for atomic multi-document operations, with awareness of Firestore's 500-operation batch limit.
- **ID generation** for roadmaps uses a slugified, collision-resistant approach.
- **Pagination** and filtering supported for roadmap listing.
- **Redis caching** integrated for roadmap retrieval, with cache invalidation on update/delete.
- **Custom exceptions** defined for domain-specific error handling and mapped to appropriate HTTP status codes in routes.

---

## What Still Needs to Be Done

### 1. To-Do CRUD APIs

- **Implement CRUD endpoints** for user-specific to-do lists and tasks.
- **Design Firestore schemas** for to-dos, ensuring efficient queries and updates.
- **Support user actions**: add roadmap to to-do, mark tasks complete, remove tasks, and update tasks.
- **Test all to-do endpoints** for correctness, security, and edge cases.

### 2. Redis Integration (Advanced)

- **Expand Redis caching** to cover paginated roadmap lists and user to-dos.
- **Make cache TTL configurable** and ensure cache invalidation logic is robust for all update/delete operations.
- **Write tests** to ensure cache is used and invalidated correctly.

### 3. Performance & Concurrency

- **Load testing**: Use tools like Locust or autocannon to ensure the API handles 100+ concurrent requests.
- **Optimize FastAPI and Redis connection settings** for high concurrency and low latency.

### 4. Documentation

- **Ensure all endpoints** have OpenAPI docstrings and are visible in `/docs`.
- **Write detailed README**: Setup, usage, API reference, and contribution guidelines.

### 5. Advanced Features (Optional/Later)

- **Role-based access control**: Support admin/user roles for certain operations.
- **Rate limiting**: Prevent abuse of endpoints.
- **Email verification or 2FA**: For enhanced security.
- **Frontend CORS config**: To be added when frontend is ready.
- **Deployment scripts**: For production deployment (Docker Compose, cloud, etc.).

---

## Why Each Step Was Needed

- **Project structure & Docker**: Ensures maintainability, scalability, and easy onboarding for new developers.
- **Config management**: Centralizes settings, improves security, and supports different environments.
- **Pydantic schemas**: Guarantees data validation and serialization, critical for API reliability.
- **Authentication & security**: Protects user data and ensures only authorized access.
- **Testing**: Catches bugs early, ensures code quality, and builds confidence in the system.
- **CI/CD**: Automates quality checks and prepares the project for future deployment and collaboration.
- **Batch writes**: Boost performance, simplify testing, and keep code modular and scalable.

---

## Project Status Summary

| Area                    | Status      | Notes/Next Steps                                  |
|-------------------------|-------------|---------------------------------------------------|
| Project Structure       | ✅ Complete | Modular, scalable, Dockerized                     |
| Config Management       | ✅ Complete | Pydantic v2, .env, centralized                    |
| User Auth & Security    | ✅ Complete | JWT, bcrypt, robust error handling                |
| User Services           | ✅ Complete | Registration, login, retrieval                    |
| User Routes             | ✅ Complete | Endpoints, error handling, protection             |
| Testing                 | ✅ Complete | Unit, integration, security, CI                   |
| Roadmap CRUD            | ✅ Complete | RESTful, batch writes, caching, DI                |
| To-Do CRUD              | 🚧 Pending  | Next milestone                                    |
| Redis Integration       | 🚧 Ongoing  | Expand caching, test invalidation                 |
| Performance/Load        | 🚧 Pending  | Load testing, optimize concurrency                |
| Documentation           | 🚧 Pending  | Expand README, endpoint docs                      |
| Advanced Features       | 🚧 Optional | Roles, rate limiting, email verification, CORS    |

---

## How to Continue

1. **Finish CRUD for user to-dos and tasks.**
2. **Expand and test Redis caching logic.**
3. **Add and run load tests for concurrency.**
4. **Document all endpoints and usage.**
5. **(Optional) Add roles, rate limiting, and advanced auth.**
6. **Prepare for frontend integration and deployment.**

---
