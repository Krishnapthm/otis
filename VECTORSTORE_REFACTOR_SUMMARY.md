# Vectorstore Refactoring Summary

This document summarizes the changes made to move from a "Project-specific Versioned Embedding" architecture to a "Single User-level Vectorstore" architecture.

## 🏗️ Core Architectural Changes

- **User Ownership**: Documents now belong directly to **Users**, not Projects.
- **Single Vectorstore**: Each user has exactly one vectorstore (collection), simplified from multiple versions per project.
- **Idempotency**: Introduced an `is_embedded` flag on documents to ensure each document is embedded exactly once across the entire system.
- **Document Reusability**: Documents can now be linked to multiple projects without being re-embedded.

---

## 📂 Modified Files

### ⚙️ Database & Models

- **`src/api/db/models/__init__.py`**:
  - Added `UserVectorstore` model.
  - Updated `Documents` with `user_id`, `is_embedded`, and `embedded_at`.
  - Removed legacy `EmbeddingVersions` and `VersionDocuments` tables.
- **`migrations/001_vectorstore_refactor.sql`**:
  - Created migration script to migrate existing data, clear project-based embeddings, and setup the new schema.

### 📝 Pydantic Schemas

- **`src/api/db/schema.py`**:
  - Added `VectorstoreStatus`, `VectorstoreSyncRequest`, and `VectorstoreSyncResponse`.
  - Updated `DocResponse` and `DocBase`.
  - Added `DocLinkRequest` for project linking.

### 🛠️ CRUD Operations

- **`src/api/crud/embeddings.py`**:
  - Complete rewrite for user-level sync, status tracking, and clearing.
- **`src/api/crud/docs.py`**:
  - Updated for user-level ownership.
  - Added `link_docs_to_project`, `get_user_docs`, `get_user_doc_by_id`, and `download_user_doc`.
  - Added auth verification to `doc_thumbnail`.
- **`src/api/crud/projects.py`**:
  - Added ownership checks to `get_project` (prevents users from seeing each other's projects).

### 🚀 API Routers

- **`src/api/v1/routers/embeddings.py`**:
  - Consolidated endpoints to `/v1/embeddings/sync`, `/status`, and `/clear`.
- **`src/api/v1/routers/docs.py`**:
  - Added user-level endpoints (no `project_id` required) for:
    - `GET /v1/documents/` (List all)
    - `GET /v1/documents/{doc_id}` (Get one)
    - `GET /v1/documents/{doc_id}/download` (Download)
    - `GET /v1/documents/{doc_id}/thumbnail` (Thumbnail)
  - Added `POST /v1/project/{project_id}/documents/link` to reuse existing docs.
- **`src/api/v1/routers/agent.py`**:
  - Updated `/graph/start` to automatically use the user's vectorstore collection without requiring a `collection_id` in the request body.
  - Added status check to ensure the vectorstore is `ready` before starting.
- **`src/api/v1/main.py`**:
  - Registered the new `user_docs_router`.

### 🔄 Background Tasks

- **`src/tasks/embedding_tasks.py`**:
  - Refactored for user-level processing.
  - Fixed `MissingGreenlet` error by ensuring synchronous database connections are used in the worker.
  - Updated collection naming convention to `user_{user_id}`.

---

## 🐛 Bug Fixes & Improvements

1.  **Sync Worker Crash**: Fixed the dialect mismatch where the worker tried to use an async driver in a synchronous context.
2.  **Authorization Gaps**: Fixed endpoints like Get Project and Document Thumbnail which were missing ownership verification.
3.  **Endpoint Redundancy**: Removed the requirement for `project_id` in document metadata operations (thumbnail/download) since documents are user-owned.

---

## ⚡ API Quick Reference

| Method   | Endpoint                       | Description                                      |
| :------- | :----------------------------- | :----------------------------------------------- |
| **POST** | `/v1/embeddings/sync`          | Embeds all pending (new) documents for the user. |
| **GET**  | `/v1/embeddings/status`        | Returns counts of embedded vs pending documents. |
| **GET**  | `/v1/documents/`               | Lists all documents owned by the user.           |
| **POST** | `/project/{id}/documents/link` | Links an existing document to a project.         |
| **GET**  | `/documents/{id}/thumbnail`    | Gets a thumbnail (Auth protected).               |
