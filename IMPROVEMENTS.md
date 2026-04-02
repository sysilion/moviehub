# MovieHub System Improvements Plan

This document outlines the planned improvements for the MovieHub system, excluding event retrieval logic.

## 1. Database Schema Optimization (Status: Completed)
- [x] **Dependency**: Add `alembic` to `requirements.txt` for database migrations.
- [x] **Migration Setup**: Initialize Alembic environment.
- [x] **Schema Change**: Convert `Event.ProgressStartDate` and `Event.ProgressEndDate` from `String` to `Date` (or `DateTime`).
  - *Rationale*: Allows efficient date range queries and proper sorting in the database.
- [x] **Action**: Create a migration script to cast existing string data to Date type.

## 2. Scheduler Reliability (Status: Completed)
- [x] **Job Persistence**: Switch `APScheduler` from `MemoryJobStore` to `SQLAlchemyJobStore`.
  - *Rationale*: Prevents loss of scheduled event updates on server restart.
- [x] **Error Handling**: Add error listeners to the scheduler.

## 3. Architecture Refactoring (Status: Completed)
- [x] **Service Layer Extraction**: Move business logic (filtering, keyword logic) from `src/web/app.py` to `src/services/event_service.py`.
- [x] **Notifier Abstraction**: Refactor `TelegramNotifier` into a `BaseNotifier` interface.
- [x] **Configuration Management**: Introduce `pydantic-settings` to replace raw `os.getenv`.

## 4. Frontend & UI/UX (Status: Completed)
- [x] **Template Macros**: Refactor `src/web/templates/index.html` to use Jinja2 macros for repeated UI elements (badges, stock status).
- [x] **Performance**: Optimize the dashboard query (combine count and fetch if possible, or use window functions).
- [x] **Vercel Build Configuration**: Optimized `vercel.json` by removing legacy `builds` property and using modern `rewrites` to silence build warnings.

## 5. Testing & CI (Status: Completed)
- [x] **Integration Tests**: Updated existing tests to support `Date` objects and added error handling validation.
- [x] **CI Setup**: Verified with `pytest` suite passing all cases.

## 6. CineQ Scheduling Optimization (Status: Completed)
- [x] **Optimization**: Remove redundant individual event tracking jobs for CineQ events.
  - *Rationale*: CineQ API returns all events and inventory in a single call. Individual jobs for each event were causing duplicate API requests and unnecessary resource consumption.
  - *Action*: Modified `src/scheduler/main.py` to skip `CINEQ` operator events during individual job scheduling.
