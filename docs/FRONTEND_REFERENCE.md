# 5. Frontend Reference

**TL;DR:** The frontend is a Vite + React 18 SPA using react-router-dom v6 for routing, TanStack Query for server state (partially adopted), and 42 shadcn/ui primitives for the design system. The chat page (660 lines) and mention system (~2,500 lines across 11 files) contain the majority of the complexity; most other pages are placeholder stubs. Data fetching is split between TanStack Query hooks and raw `useEffect` + `fetch` patterns — this inconsistency is tech debt, not an intentional architecture.

---

## Assumptions

1. This document describes the code at `frontend/otis-ui/src/` as it exists today, not a planned future state.
2. The backend API lives at the same origin (or at `VITE_API_BASE_URL`) and exposes routes under `/v1/`.
3. `agentApi.ts` hardcodes `http://localhost:8000` — this is assumed intentional for local dev and a known deployment-time override requirement.
4. The `next-themes` library is used for theming despite this being a Vite app (not Next.js). It works at runtime but contributes `"use client"` directives that are dead code.
5. `embeddings-table.tsx` is empty (0 bytes). It is assumed to be a planned but unimplemented file.
6. `App.css` contains the default Vite template CSS and is assumed entirely unused.
7. The shadcn/ui registry entry for `@ai-elements` points to `https://ai-sdk.dev/elements/api/registry/{name}.json` — Vercel AI SDK UI elements that were pulled in and then customized locally.

---

## 5.1 Project Structure

```text
frontend/otis-ui/src/
├── main.tsx                          # Entry point, router definition, provider tree
├── App.tsx                           # App shell: sidebar + header + Outlet
├── authContext.tsx                    # AuthProvider / useAuth (React context)
├── index.css                         # Tailwind 4.1 import, oklch color tokens, global overrides
├── App.css                           # ⚠ Unused Vite template CSS (dead code)
│
├── api/                              # HTTP client layer
│   ├── authApi.ts                    # Axios instance, auth CRUD, token refresh interceptor
│   ├── chatApi.ts                    # Chat CRUD + SSE streaming (478 lines)
│   ├── docApi.ts                     # Document operations (user-level + project-scoped)
│   ├── embeddingsApi.ts              # Vectorstore sync/status/clear
│   ├── agentApi.ts                   # Agent graph SSE start/resume (229 lines)
│   ├── mcqApi.ts                     # MCQ operations with URL fallback
│   ├── projectApi.ts                 # Project CRUD
│   ├── queryKeys.ts                  # TanStack Query key factory
│   └── authApi.test.ts              # Auth API tests
│
├── hooks/                            # Custom React hooks
│   ├── useDocuments.ts               # TanStack Query: document list
│   ├── useUploadDocument.ts          # TanStack mutation: upload + optimistic update
│   ├── useDeleteDocuments.ts         # TanStack mutation: batch delete
│   ├── useDocumentSelection.ts       # Checkbox state by project
│   ├── useThumbnail.ts              # Blob fetch + global Map cache
│   ├── useAgentStream.ts            # Agent SSE state machine (198 lines)
│   └── use-mobile.ts                # 768px breakpoint detection
│
├── pages/                            # Route-level page components
│   ├── data-library.tsx              # Document management (478 lines)
│   ├── vector-store.tsx              # Embedding sync UI (303 lines)
│   ├── analytics.tsx                 # ⚠ Placeholder — "Coming soon"
│   ├── capture.tsx                   # ⚠ Placeholder
│   ├── help.tsx                      # ⚠ Placeholder
│   ├── prompts.tsx                   # ⚠ Placeholder
│   ├── proposal.tsx                  # ⚠ Placeholder
│   ├── reports.tsx                   # ⚠ Placeholder
│   ├── search.tsx                    # ⚠ Placeholder
│   ├── settings.tsx                  # ⚠ Placeholder
│   ├── team.tsx                      # ⚠ Placeholder
│   └── word-assistant.tsx            # ⚠ Placeholder
│
├── components/
│   ├── ai-elements/                  # Vercel AI SDK-derived composable UI
│   │   ├── prompt-input.tsx          # PromptInputProvider + 31 sub-components (1,341 lines)
│   │   ├── chain-of-thought.tsx      # Collapsible thinking step visualization (223 lines)
│   │   ├── conversation.tsx          # Message list with auto-scroll (167 lines)
│   │   └── inline-citation.tsx       # Source attribution carousel (294 lines)
│   │
│   ├── features/                     # Domain feature components
│   │   ├── auth/                     # login-form, signup-form, requireAuth
│   │   ├── chat/                     # chat-page (659 lines), chat-message (341 lines)
│   │   ├── mention/                  # 11 files, ~2,500 lines total
│   │   ├── documents/                # DocumentsTab, grid/table views, thumbnails
│   │   ├── generation/               # ConceptSelector, GenerateTab, ReviewTab
│   │   ├── projects/                 # Project CRUD, detail page, tabs
│   │   ├── mcq/                      # Reusable MCQ export dropdown/button
│   │   ├── dashboard/                # Charts, stat cards (hardcoded data)
│   │   └── embeddings/               # Column defs, empty table file
│   │
│   ├── layouts/                      # App shell components
│   │   ├── app-sidebar.tsx           # Sidebar with nav sections
│   │   ├── nav-main.tsx              # Primary nav + recent chats list
│   │   ├── nav-documents.tsx         # Document links section
│   │   ├── nav-secondary.tsx         # Secondary nav (settings, help)
│   │   ├── nav-user.tsx              # User menu with logout
│   │   ├── site-header.tsx           # Page title + breadcrumb
│   │   └── theme-provider.tsx        # next-themes wrapper
│   │
│   ├── shared/                       # Reusable non-primitive components
│   │   ├── alert-dialog.tsx          # ⚠ Hardcoded "delete account" text
│   │   └── data-table.tsx            # ⚠ Hardcoded to EmbeddingVersion type (725 lines)
│   │
│   └── ui/                           # 42 shadcn/ui primitives
│
├── lib/                              # Utilities and type definitions
│   ├── utils.ts                      # cn() — clsx + tailwind-merge
│   ├── chat-types.ts                 # ChatMessage, ThinkingStep, Citation
│   ├── mock-chat-data.ts            # Mock data for development
│   ├── data.json                     # Static data
│   └── project_data.json            # Static project data
│
└── assets/                           # Static images, SVGs
```

---

## 5.2 Routing & Navigation

### Route Table

| Path              | Component           | Auth Required | Status                        |
| ----------------- | ------------------- | ------------- | ----------------------------- |
| `/`               | `ChatPage`          | Yes           | Active — default landing page |
| `/c/:chatId`      | `ChatPage`          | Yes           | Active — existing chat        |
| `/dashboard`      | `Dashboard`         | Yes           | Active — hardcoded demo data  |
| `/projects`       | `Projects`          | Yes           | Active                        |
| `/p/:projectId`   | `ProjectDetailPage` | Yes           | Active                        |
| `/mcqs`           | `MCQs`              | Yes           | Active — persistent MCQ list + export |
| `/data-library`   | `DataLibrary`       | Yes           | Active                        |
| `/vector-store`   | `VectorStore`       | Yes           | Active                        |
| `/reports`        | `Reports`           | Yes           | Placeholder                   |
| `/word-assistant` | `WordAssistant`     | Yes           | Placeholder                   |
| `/settings`       | `Settings`          | Yes           | Placeholder                   |
| `/help`           | `Help`              | Yes           | Placeholder                   |
| `/search`         | `Search`            | Yes           | Placeholder                   |
| `/login`          | `LoginForm`         | No            | Active                        |
| `/signup`         | `SignupForm`        | No            | Active                        |

### Commented-Out Routes

These routes are defined in `main.tsx` but commented out:

```tsx
// { path: "analytics", element: <Analytics /> }
// { path: "team",      element: <Team /> }
// { path: "capture",   element: <Capture /> }
// { path: "proposal",  element: <Proposal /> }
// { path: "prompts",   element: <Prompts /> }
```

The corresponding page components exist in `src/pages/` and are imported at the top of `main.tsx` — the imports are not tree-shaken because they are not commented out. This adds dead code to the bundle.

### RequireAuth Guard

Location: `src/components/features/auth/requireAuth.tsx` (32 lines)

```tsx
export function RequireAuth({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  const token = localStorage.getItem("access_token");

  if (loading) return <Spinner />;
  if (!token || !user) {
    return (
      <Navigate
        to="/Login"
        replace
        state={{ from: location.pathname || "/" }}
      />
    );
  }
  return children;
}
```

Logic:

1. While `AuthProvider` is resolving the `/me` call, show a full-screen spinner.
2. If no `access_token` in `localStorage` **or** no `user` object in context, redirect to `/Login`.
3. The redirect path is `/Login` (capital L) — this works because `createBrowserRouter` path matching is case-sensitive and the actual route is `/login` (lowercase). The browser navigates to `/Login`, which does not match any route. **This is a bug**.
4. **Fix path:** update `src/components/features/auth/requireAuth.tsx` to `Navigate to="/login"` and add/extend a route-guard test to prevent casing regressions.
5. The `from` location is preserved in router state for potential post-login redirect (not currently consumed by `LoginForm`).

### Provider Tree

Defined in `main.tsx`, the provider nesting order (outermost first):

```text
StrictMode
  └─ ThemeProvider (next-themes: attribute="class", defaultTheme="light")
       └─ AuthProvider (custom React context)
            └─ QueryClientProvider (TanStack Query, default config)
                 └─ RouterProvider
```

The `App` component (rendered inside `RequireAuth`) provides the visual shell:

```text
SidebarProvider
  ├─ AppSidebar
  └─ SidebarInset
       ├─ SiteHeader
       ├─ Outlet (chat routes get raw div, others get ScrollArea)
       └─ Toaster (sonner)
```

---

## 5.3 State Management Patterns

### Pattern 1: Server State via TanStack Query

Used by the document management system and partially by the chat page.

```ts
// src/api/queryKeys.ts
export const queryKeys = {
  documents: {
    all: ["documents"] as const,
    detail: (docId: string) => ["documents", docId] as const,
  },
  chat: {
    all: ["chat"] as const,
    detail: (chatId: string) => ["chat", chatId] as const,
    messages: (chatId: string) => ["chat", chatId, "messages"] as const,
    attachments: (chatId: string) => ["chat", chatId, "attachments"] as const,
  },
};
```

The `QueryClient` is instantiated with default configuration (no custom `defaultOptions`). Stale time and GC time are configured per-query in hooks:

```ts
// src/hooks/useDocuments.ts
useQuery<Document[]>({
  queryKey: queryKeys.documents.all,
  queryFn: getAllUserDocuments,
  staleTime: 5 * 60 * 1000, // 5 minutes
  gcTime: 10 * 60 * 1000, // 10 minutes
});
```

**Components using TanStack Query:** `data-library.tsx`, `chat-page.tsx` (via `useDocuments`, `useQueryClient`), `ThumbnailImage` (via `useThumbnail` — not actually TanStack, raw hook), `documents-data-table.tsx` (TanStack Table, not Query).

### Pattern 2: Auth State via React Context

```ts
// src/authContext.tsx
type AuthContextType = {
  user: User | null;
  loading: boolean;
  refreshUser: () => Promise<void>;
  logout: () => void;
};
```

`AuthProvider` checks `localStorage` for `access_token` on mount, calls `GET /v1/auth/me` to hydrate the user object, and exposes the result via context. The `logout` handler calls `apiLogout()` then `refreshUser()` — the refresh is redundant since `setUser(null)` is called immediately before it.

**Consumers:** `RequireAuth`, `AppSidebar`, `NavUser`, `LoginForm`.

### Pattern 3: Local UI State (useState)

Most page components manage their own state via `useState`. This includes:

- `chat-page.tsx`: `messages`, `isLoadingMessages`, `useWebSearch`, `isDragging`
- `vector-store.tsx`: `status`, `isLoading`, `isSyncing`, `hasSyncStarted`
- `projects.tsx`: `projects`, `isLoading`, `searchQuery`, `filteredProjects`, `isCreateDialogOpen`
- `ProjectDetailPage.tsx`: `project`, `isLoading`, `error`
- `DocumentsTab.tsx`: 13 separate `useState` hooks

### Pattern 4: Session Storage

`vector-store.tsx` persists the syncing flag to `sessionStorage` under key `"vectorstore_syncing_state"`:

```ts
sessionStorage.setItem(
  "vectorstore_syncing_state",
  JSON.stringify({
    isSyncing: true,
    pendingAtStart: status?.pending_documents ?? 0,
  }),
);
```

This survives page navigations within the SPA but is lost on tab close. The intent is to maintain the "syncing in progress" UI if the user navigates away and returns.

### Inconsistency: Raw useEffect Fetch vs TanStack Query

The following components fetch data with raw `useEffect` + direct API calls instead of TanStack Query:

| Component               | API Calls                                                                                         |
| ----------------------- | ------------------------------------------------------------------------------------------------- |
| `vector-store.tsx`      | `getEmbeddingStatus()`, `syncEmbeddings()`                                                        |
| `projects.tsx`          | `projectApi.getAll()`, `projectApi.create()`, `projectApi.delete()`                               |
| `ProjectDetailPage.tsx` | `projectApi.getOne()`                                                                             |
| `DocumentsTab.tsx`      | `getAllDocuments()`, `uploadDocuments()`, `deleteDocumentsFromProject()`, `getAllUserDocuments()` |
| `section-cards.tsx`     | `mcqApi.getAll()`                                                                                 |
| `nav-main.tsx`          | `chatApi.list()`                                                                                  |
| `App.tsx`               | `projectApi.getOne()`                                                                             |

This is tech debt. There is no design rationale for the split — it happened because TanStack Query was adopted mid-project for the document hooks and was not backported to older components.

---

## 5.4 API Layer (`src/api/`)

### `authApi.ts` — Axios Instance & Auth

**Lines:** 131

The shared Axios instance used by all API modules except `agentApi.ts`.

```ts
const API_BASE_URL = resolveApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
// Falls back to "/" if env var is empty/undefined

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});
```

**Token management:** Tokens are stored in `localStorage` (`access_token`, `refresh_token`). A request interceptor attaches `Authorization: Bearer <token>` to every outbound request.

**Token refresh:** A response interceptor catches 401 errors, calls `POST /v1/auth/refresh` with the refresh token, stores the new tokens, and retries the original request. Concurrent 401s are coalesced via a shared `refreshPromise`. Login and refresh endpoints are excluded from retry to prevent loops.

**Failure behavior:** If refresh fails, both tokens are removed from `localStorage` and the original error propagates. The user is not automatically redirected to login — they will see the error and must navigate manually (or `RequireAuth` will catch it on next render).

| Function  | Method | Path                | Parameters                               | Returns                    | Error Handling                        |
| --------- | ------ | ------------------- | ---------------------------------------- | -------------------------- | ------------------------------------- |
| `signup`  | POST   | `/v1/auth/register` | `{ email, password, uname }`             | `res.data` (shape untyped) | Throws Axios error                    |
| `login`   | POST   | `/v1/auth/login`    | `URLSearchParams { username, password }` | `res.data`; stores tokens  | Throws Axios error                    |
| `fetchMe` | GET    | `/v1/auth/me`       | —                                        | `res.data` (User)          | Throws Axios error                    |
| `logout`  | POST   | `/v1/auth/logout`   | —                                        | `void`; clears tokens      | Swallows errors, always clears tokens |

### `chatApi.ts` — Chat CRUD + SSE Streaming

**Lines:** 478

Exports a `chatApi` object with REST operations and streaming methods.

**REST Operations:**

| Method | Function                        | Path                                             | Parameters                    | Returns                          |
| ------ | ------------------------------- | ------------------------------------------------ | ----------------------------- | -------------------------------- |
| POST   | `chatApi.create`                | `/v1/chats/`                                     | `ChatCreate { title? }`       | `ChatResponse`                   |
| GET    | `chatApi.list`                  | `/v1/chats/`                                     | `{ limit?, skip?, status? }`  | `ChatResponse[]`                 |
| GET    | `chatApi.get`                   | `/v1/chats/{chatId}`                             | `chatId: string`              | `ChatResponse`                   |
| PATCH  | `chatApi.update`                | `/v1/chats/{chatId}`                             | `chatId, ChatUpdate`          | `ChatResponse`                   |
| DELETE | `chatApi.delete`                | `/v1/chats/{chatId}`                             | `chatId: string`              | `{ message: string }`            |
| POST   | `chatApi.messages.create`       | `/v1/chats/{chatId}/messages`                    | `chatId, ChatMessageCreate`   | `ChatMessageResponse`            |
| GET    | `chatApi.messages.list`         | `/v1/chats/{chatId}/messages`                    | `chatId, { limit?, skip? }`   | `ChatMessageResponse[]`          |
| GET    | `chatApi.messages.get`          | `/v1/chats/{chatId}/messages/{messageId}`        | `chatId, messageId`           | `ChatMessageResponse`            |
| PATCH  | `chatApi.messages.update`       | `/v1/chats/{chatId}/messages/{messageId}`        | `chatId, messageId, data`     | `ChatMessageResponse`            |
| DELETE | `chatApi.messages.delete`       | `/v1/chats/{chatId}/messages/{messageId}`        | `chatId, messageId`           | `{ message: string }`            |
| GET    | `chatApi.messages.replayEvents` | `/v1/chats/{chatId}/messages/{messageId}/events` | `chatId, messageId, afterSeq` | `ChatMessageEventReplayResponse` |

**SSE Streaming: `chatApi.messages.stream`**

```ts
stream: async (
  chatId: string,
  message: string,
  handlers: {
    onStarted?: (event: ChatInvokeStartedEvent) => void;
    onToken:    (chunk: string) => void;
    onDone:     (message: ChatMessageResponse) => void;
    onError:    (error: string) => void;
    onThinking?:       (event: ChatInvokeThinkingEvent) => void;
    onReasoningToken?: (event: ChatInvokeReasoningTokenEvent) => void;
  },
  docIds?: string[],
  mentions?: { id: string; label: string; triggerChar: string }[],
): Promise<{ close: () => void }>
```

Implementation uses `fetch()` (not Axios) for streaming support — Axios does not support `ReadableStream`. The SSE protocol is manual: reads chunks from `response.body.getReader()`, accumulates into a line buffer, splits on `\n`, and parses lines starting with `data: ` as JSON.

**Event types in the stream:**

| Event             | Payload                                      | When                     |
| ----------------- | -------------------------------------------- | ------------------------ |
| `started`         | `{ user_message, assistant_message_id }`     | Stream begins            |
| `token`           | `{ content: string }`                        | Each text chunk          |
| `thinking`        | `{ node, status, label, detail? }`           | Agent processing step    |
| `reasoning_token` | `{ content, node? }`                         | Internal reasoning chunk |
| `done`            | `{ assistant_message: ChatMessageResponse }` | Stream complete          |
| `error`           | `{ detail: string }`                         | Stream-level error       |

**Abort:** Returns `{ close }` — sets `isAborted = true` and calls `reader.cancel()`.

**Failure behavior:**

- Non-OK HTTP response: throws `Error` with response text body.
- No response body: calls `handlers.onError("No response body")`.
- JSON parse failure on individual SSE lines: logs to console, skips line, continues.
- Network error mid-stream: calls `handlers.onError` with the error message (only if not aborted).

**SSE Replay: `chatApi.messages.replayEventsSSE`**

Dual-mode: checks `Content-Type` header. If `application/json`, it is a completed message — events are dispatched synchronously from the JSON array. If `text/event-stream`, it reads the stream identical to the `stream` method.

### `docApi.ts` — Document Operations

**Lines:** 115

Two scopes of operations:

**Project-scoped:**

| Function                     | Method | Path                                         | Parameters                        | Returns      |
| ---------------------------- | ------ | -------------------------------------------- | --------------------------------- | ------------ |
| `uploadDocuments`            | POST   | `/v1/project/{projectId}/documents/`         | `projectId, files: File[]`        | `Document[]` |
| `getAllDocuments`            | GET    | `/v1/project/{projectId}/documents/`         | `projectId`                       | `Document[]` |
| `getDocument`                | GET    | `/v1/project/{projectId}/documents/{docId}`  | `projectId, docId`                | `Document`   |
| `deleteDocuments`            | DELETE | `/v1/project/{projectId}/documents/`         | `projectId, { doc_id: string[] }` | `void`       |
| `downloadDocuments`          | GET    | `/v1/project/{projectId}/documents/download` | `projectId`                       | `Blob`       |
| `deleteDocumentsFromProject` | DELETE | `/v1/project/{projectId}/documents/`         | `projectId, { doc_id: string[] }` | `void`       |

Note: `deleteDocuments` and `deleteDocumentsFromProject` are **duplicate** functions with identical implementations.

**User-level:**

| Function                | Method | Path                                     | Parameters         | Returns        |
| ----------------------- | ------ | ---------------------------------------- | ------------------ | -------------- |
| `getAllUserDocuments`   | GET    | `/v1/documents/`                         | —                  | `Document[]`   |
| `getUserDocument`       | GET    | `/v1/documents/{docId}`                  | `docId`            | `Document`     |
| `linkDocumentToProject` | POST   | `/v1/project/{projectId}/documents/link` | `projectId, docId` | `{ message }`  |
| `downloadDocument`      | GET    | `/v1/documents/{docId}/download`         | `docId`            | `Blob`         |
| `uploadUserDocuments`   | POST   | `/v1/documents/`                         | `files: File[]`    | `Document[]`   |
| `getThumbnailUrl`       | —      | —                                        | `docId`            | `string` (URL) |

`getThumbnailUrl` is a pure string builder — it is not used by `useThumbnail` (which calls the endpoint directly via Axios).

### `embeddingsApi.ts` — Vectorstore Sync

**Lines:** 53

| Function             | Method                                      | Path                    | Parameters | Returns                                     |
| -------------------- | ------------------------------------------- | ----------------------- | ---------- | ------------------------------------------- |
| `syncEmbeddings`     | POST                                        | `/v1/embeddings/sync`   | —          | `SyncResponse { message, job_id?, status }` |
| `getEmbeddingStatus` | GET                                         | `/v1/embeddings/status` | —          | `VectorstoreStatus`                         |
| `clearVectorstore`   | POST (frontend) / DELETE (backend expected) | `/v1/embeddings/clear`  | —          | `{ message }`                               |

`clearVectorstore` is exported but not called anywhere in the frontend. **Contract mismatch bug:** frontend uses `POST`, while backend route is `DELETE /v1/embeddings/clear`.

### `agentApi.ts` — Agent Graph SSE

**Lines:** 229

**⚠ Hardcoded base URL:**

```ts
const API_BASE = "http://localhost:8000";
```

This differs from `authApi.ts` which reads `VITE_API_BASE_URL`. Agent API requests will fail in any non-local deployment unless this is changed.

**Auth:** Reads `localStorage.getItem("access_token")` directly — does not use the Axios interceptor. Token refresh will not happen automatically for agent requests.

| Function            | Method | Path                          | Parameters                         | Returns                      |
| ------------------- | ------ | ----------------------------- | ---------------------------------- | ---------------------------- |
| `startGraphStream`  | POST   | `/v1/graph/start`             | `{ doc_ids, user_prompt? }`        | `{ close, threadIdPromise }` |
| `resumeGraphStream` | POST   | `/v1/graph/resume/{threadId}` | `{ selected_concepts: Concept[] }` | `{ close }`                  |

Both use the same manual SSE reader pattern as `chatApi`. The event protocol differs:

```ts
interface AgentEvent {
  mode: string;
  payload: {
    status?: string;
    overview?: Overview[];
    overview_for_user?: Overview[];
    num_docs?: number;
    num_queries?: number;
    docs?: number;
    error?: string;
  };
}
```

`startGraphStream` extracts `X-Thread-ID` from response headers to identify the server-side thread.

### `mcqApi.ts` — MCQ Operations

**Lines:** ~90

| Function          | Method | Path                          | Parameters             | Returns               | Error Handling                             |
| ----------------- | ------ | ----------------------------- | ---------------------- | --------------------- | ------------------------------------------ |
| `mcqApi.getAll`   | GET    | `/v1/mcqs/`                   | `limit, skip`          | `ReadMCQ[]`           | Falls back to `/mcqs/`                     |
| `mcqApi.getById`  | GET    | `/v1/mcqs/{id}`               | `id`                   | `ReadMCQ[]`           | Falls back to `/mcqs/{id}`                 |
| `mcqApi.download` | GET    | `/v1/mcqs/download/{id}`      | `id`                   | `Blob`                | Falls back to `/mcqs/download/{id}`        |
| `mcqApi.exportMcq`| GET    | `/v1/mcqs/{id}/export`        | `id, mode, format`     | `AxiosResponse<Blob>` | Falls back to `/mcqs/{id}/export`          |

Every method uses a try/catch fallback pattern: first attempts the `/v1/` prefixed path, then retries without it. This handles backend version ambiguity but means every failed request produces two HTTP calls.

The MCQ payload is now strongly typed on the client (`MCQTest`, `MCQQuestion`, `MCQOption`), including export mode/format unions:

- `MCQExportMode = "raw" | "test"`
- `MCQExportFormat = "md" | "json" | "pdf" | "docx"`

### Reusable MCQ export UI

The export dropdown is centralized in `src/components/features/mcq/mcq-export-button.tsx` and reused across:

- `src/pages/mcqs.tsx` (persistent MCQ list)
- `src/components/features/chat/chat-message.tsx` (assistant MCQ messages)

The component implements a 2-step dropdown flow:

1. choose mode (`Raw` / `Test`)
2. choose file type (`MD`, `PDF`, `JSON`, `DOCX`) with a Back action

It uses `DropdownMenuItem` `onSelect` handlers with `event.preventDefault()` so the menu stays open when transitioning from mode step to format step.

### `projectApi.ts` — Project CRUD

**Lines:** 52

| Function            | Method | Path                       | Parameters                                     | Returns             |
| ------------------- | ------ | -------------------------- | ---------------------------------------------- | ------------------- |
| `projectApi.getAll` | GET    | `/v1/projects/`            | `limit, skip`                                  | `ProjectResponse[]` |
| `projectApi.getOne` | GET    | `/v1/projects/{projectId}` | `projectId`                                    | `ProjectResponse`   |
| `projectApi.create` | POST   | `/v1/projects/`            | `ProjectInput { project_name, project_desc? }` | `ProjectResponse`   |
| `projectApi.delete` | DELETE | `/v1/projects/{projectId}` | `projectId`                                    | `{ message }`       |

No update/patch endpoint is exposed.

### `queryKeys.ts` — TanStack Query Key Factory

**Lines:** 17

```ts
export const queryKeys = {
  documents: {
    all: ["documents"] as const,
    detail: (docId: string) => ["documents", docId] as const,
  },
  chat: {
    all: ["chat"] as const,
    detail: (chatId: string) => ["chat", chatId] as const,
    messages: (chatId: string) => ["chat", chatId, "messages"] as const,
    attachments: (chatId: string) => ["chat", chatId, "attachments"] as const,
  },
};
```

Only `queryKeys.documents.all` is actively used (by `useDocuments`, `useUploadDocument`, `useDeleteDocuments`). The chat keys are defined but not yet consumed; they are the intended key namespace for migrating `chat-page.tsx` chat/message fetching to TanStack Query.

---

## 5.5 Custom Hooks (`src/hooks/`)

### `useDocuments()`

**File:** `useDocuments.ts` (30 lines)

```ts
function useDocuments(): {
  documents: Document[];
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  refetch: () => void;
};
```

TanStack Query wrapper around `getAllUserDocuments()`. All components sharing this hook read from a single cache entry (`queryKeys.documents.all`). Stale time: 5 min. GC time: 10 min.

**Consumers:** `data-library.tsx`, `chat-page.tsx` (for mention document resolution).

### `useUploadDocument()`

**File:** `useUploadDocument.ts` (36 lines)

```ts
function useUploadDocument(): {
  uploadDocuments: (files: File[]) => Promise<Document[]>;
  isUploading: boolean;
  error: Error | null;
  reset: () => void;
};
```

TanStack mutation that calls `uploadUserDocuments(files)`. On success, optimistically prepends new documents to the cache without a refetch.

**Failure behavior:** If `uploadUserDocuments` throws, `error` is populated. The mutation does not roll back the optimistic update because the optimistic update is applied in `onSuccess`, not `onMutate` — so it only runs after a successful response.

### `useDeleteDocuments()`

**File:** `useDeleteDocuments.ts` (38 lines)

```ts
function useDeleteDocuments(): {
  deleteDocuments: ({
    projectId,
    docIds,
  }: {
    projectId: string;
    docIds: string[];
  }) => Promise<void>;
  isDeleting: boolean;
  error: Error | null;
  reset: () => void;
};
```

Calls `deleteDocumentsFromProject(projectId, docIds)`. On success, removes deleted IDs from the cached document list.

**Note:** This hook calls the project-scoped delete endpoint, but the `useDocuments` cache is the user-level document list. If a document belongs to multiple projects, deleting it from one project removes it from the global cache — this may cause UI inconsistency.

### `useDocumentSelection()`

**File:** `useDocumentSelection.ts` (37 lines)

```ts
function useDocumentSelection(): {
  getSelection: (projectId: string) => string[];
  setSelection: (projectId: string, docIds: string[]) => void;
  clearSelection: (projectId: string) => void;
};
```

Manages checkbox selection state keyed by `projectId`. Pure local state — no persistence, no API interaction.

### `useThumbnail(docId)`

**File:** `useThumbnail.ts` (73 lines)

```ts
function useThumbnail(docId: string): {
  thumbnailUrl: string | null;
  isLoading: boolean;
  error: Error | null;
};
```

Fetches `GET /v1/documents/{docId}/thumbnail` as a blob, creates an object URL via `URL.createObjectURL`, and stores it in a **module-level `Map<string, string>`** (global cache).

**⚠ Memory leak risk:** Object URLs in the global `thumbnailCache` map are never revoked during normal operation. The `clearThumbnailCache()` helper is exported but never called by any component. If a user views hundreds of documents, blob URLs accumulate in memory for the lifetime of the page.

**Failure behavior:** On fetch error, sets `error` state and `thumbnailUrl` to null. The component renders a fallback icon. The failed docId is not cached — subsequent renders will retry the fetch.

### `useAgentStream()`

**File:** `useAgentStream.ts` (198 lines)

```ts
type AgentPhase =
  | "idle"
  | "extracting"
  | "selecting"
  | "processing"
  | "complete"
  | "error";

function useAgentStream(): {
  phase: AgentPhase;
  status: string;
  overviews: Overview[];
  threadId: string | null;
  error: string | null;
  retrievedDocsCount: number | null;
  startStream: (docIds: string[], userPrompt?: string) => Promise<void>;
  resumeWithConcepts: (selectedConcepts: Concept[]) => Promise<void>;
  reset: () => void;
};
```

State machine for the agent graph SSE flow:

```text
idle → extracting → selecting → processing → complete
                                     ↓
                                   error
```

- `startStream`: cleans up existing stream, resets state, calls `startGraphStream`, stores thread ID.
- `resumeWithConcepts`: sends selected concepts to `resumeGraphStream`, transitions to `processing`.
- `reset`: aborts any open stream, resets to `initialState`.

**Event handling:** The `handleEvent` callback maps `AgentEvent.payload` fields:

- `payload.status` → updates status text
- `payload.overview` or `payload.overview_for_user` → transitions to `"selecting"` phase
- `payload.docs` → stores retrieved document count
- Stream `onComplete` → transitions to `"complete"` (only from `"processing"` phase)

**Failure behavior:** On error, transitions to `"error"` phase. The stream `close` ref is managed — callers do not need to handle cleanup.

### `useIsMobile()`

**File:** `use-mobile.ts` (19 lines)

```ts
function useIsMobile(): boolean;
```

Returns `true` when viewport width < 768px. Uses `window.matchMedia` with a `change` event listener. Returns `false` during SSR/initial render (since `isMobile` starts as `undefined` and `!!undefined === false`).

---

## 5.6 Pages (`src/pages/`)

### `chat-page.tsx` (659 lines)

Location: `src/components/features/chat/chat-page.tsx` (rendered by the router, not in `src/pages/`)

**State:**

```ts
const [messages, setMessages] = useState<ChatMessageType[]>([]);
const [isLoadingMessages, setIsLoadingMessages] = useState(false);
const [useWebSearch, setUseWebSearch] = useState(false);
const [isDragging, setIsDragging] = useState(false);
```

**Data dependencies:**

- `useParams()` → `chatId`
- `useNavigate()`
- `useQueryClient()` (TanStack — for cache invalidation)
- `useDocuments()` → cached document list
- `useUploadDocument()` → `uploadDocuments`, `isUploading`
- `useMentionPicker({ triggers })` → mention state machine

**Key complexity: SSE lifecycle**

1. On mount or `chatId` change, messages are loaded via `chatApi.messages.list()`.
2. For each assistant message with `status === "streaming"`, events are replayed via `chatApi.messages.replayEvents()` and reconstructed into `ThinkingStep[]` by `eventsToThinkingSteps()` (~80 lines).
3. When the user submits a message, `handleSubmit`:
   - Resolves mention names to document IDs (first from cache, then fresh fetch as fallback)
   - Creates a new chat if none exists (`chatApi.create()`)
   - Navigates to `/c/{chatId}` if this was a new chat
   - Injects optimistic user + assistant placeholder messages into state
   - Calls `chatApi.messages.stream()` with SSE callbacks
   - On each `onToken`, appends to the assistant message's content in-place
   - On `onThinking`, updates thinking step state on the assistant message
   - On `onDone`, replaces the optimistic assistant message with the final server response (preserving client-side thinking steps)
4. Abort handling: stream `close()` is available but not wired to a UI cancel button (the `PromptInputSubmit` stop button is present but the abort plumbing is not connected).

**Drag-and-drop:** Supports file drop to upload documents. The `handleDrop` dependency array contains `[projectId]` which is not defined in `ChatPage` scope — this is copy-paste tech debt from `DocumentsTab`.

**Child components:** `Conversation`, `ConversationContent`, `ConversationEmptyState`, `ConversationScrollButton`, `ChatMessage`, `MentionPicker`, `MentionDropdown`, `MentionInputEditable`, all `PromptInput` sub-components.

### `data-library.tsx` (478 lines)

**State:** Uses TanStack Query hooks (`useDocuments`, `useUploadDocument`, `useDeleteDocuments`) for server state. Local `useState` for: `selectedDocs` (Set), `searchQuery`, `viewMode` ("grid"/"table"), `isDragging`, `isDownloading`, `deleteDialogOpen`, `docsToDelete`, `duplicateFiles`, `showDuplicateAlert`.

**Key features:**

- Grid/list toggle with `ToggleGroup`
- Search filtering (case-insensitive substring on filename)
- Drag-and-drop file upload (accepts `.pdf,.txt,.doc,.docx,.md`)
- Duplicate detection: HTTP 409 from upload triggers a duplicate alert
- Multi-select download: iterates documents sequentially in a `for` loop (no parallelism)
- Delete confirmation via `AlertDialog`

**Failure behavior:** Upload errors (non-409) show `toast.error`. Download creates blob URLs via `URL.createObjectURL` + programmatic anchor click, then revokes.

### `vector-store.tsx` (303 lines)

**State:** Raw `useState` + `useEffect` — no TanStack Query. Uses `sessionStorage` key `"vectorstore_syncing_state"` for cross-navigation persistence.

**Polling:** During sync, a `setInterval` at 3-second intervals calls `getEmbeddingStatus()`. Auto-stops when `pending_documents === 0`.

**States rendered:**

1. Loading spinner (initial fetch)
2. Empty state: no documents → redirect CTA to Data Library
3. Empty state: docs pending, no sync started → prompt to sync
4. Main view: 3 `DataCard`s (Total / Embedded / Pending) + sync button with progress

**⚠ Dead ref:** `pendingAtSyncStart` ref is set but never read.

### `projects.tsx` (465 lines)

Location: `src/components/features/projects/projects.tsx`

**State:** `projects`, `isLoading`, `searchQuery`, `filteredProjects`, `isCreateDialogOpen`.

**Data fetching:** `useEffect` + `projectApi.getAll()`. No TanStack Query.

**Filtering:** Uses `useEffect` to filter `projects` into `filteredProjects` on `searchQuery` change. Could be replaced with `useMemo`.

**Delete:** Uses native `confirm()` dialog — not the `AlertDialog` component used elsewhere.

**⚠ Duplicate code:** This file contains an inline ~160-line `CreateProjectDialog` definition. A separate standalone `CreateProjectDialog.tsx` also exists in the same directory.

### `project-detail.tsx` (ProjectDetailPage — 94 lines)

Route wrapper that fetches a single project via `projectApi.getOne(projectId)`. Renders error states mapped from HTTP status codes:

- 403 → "You don't have permission"
- 404 → "Project not found"
- Other → "Failed to load project"

On success, renders `ProjectDetail`.

### `ProjectDetail.tsx` (181 lines)

Tab container with three tabs: Documents, Generate, Review.

**State:** `activeTab`, `hasDocuments`, `selectedDocIds`, `documents`.

Lifts document state between `DocumentsTab` and `GenerateTab`. Tab navigation includes Previous/Next buttons fixed at the bottom.

**⚠ Unused props:** `projectName` is destructured but aliased to `_projectName` and never used.

### `dashboard.tsx` (12 lines)

Thin wrapper rendering `SectionCards` + `ChartAreaInteractive`. All data is hardcoded.

### `login.tsx` / `signup.tsx`

**LoginForm** (222 lines): Two-column layout. Left side shows a random decorative SVG selected on mount. Client-side email regex + field error display. Calls `login()` from `authApi`, then `refreshUser()` from `useAuth()`, then navigates to `/`.

**⚠ Google button:** "Login with Google" button is present but has no handler — purely decorative.

**SignupForm** (328 lines): Zod-style inline validation with a `ValidationChecklist` component showing password requirements (length, uppercase, lowercase, number, match). On success navigates to `/login`.

**Failure behavior:** Both forms display server errors inline. `signup` checks for "already exists" text in error response and shows "Email already in use."

### Placeholder Pages

All 10 placeholder pages share an identical 12-line structure:

```tsx
export default function PageName() {
  return (
    <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6 px-4 md:px-6">
      <h1 className="text-2xl font-bold">Page Name</h1>
      <p className="text-muted-foreground">Feature coming soon...</p>
    </div>
  );
}
```

Pages: `analytics`, `capture`, `help`, `prompts`, `proposal`, `reports`, `search`, `settings`, `team`, `word-assistant`.

---

## 5.7 Feature Components

### `chat/`

**`ChatMessage`** (`chat-message.tsx`, 341 lines)

```ts
interface ChatMessageProps {
  message: ChatMessageType;
}
```

Props: a single `ChatMessage` from `lib/chat-types.ts`.

**Internal state:** None (pure render).

**Rendering logic:**

- Assistant messages: renders `ChainOfThought` (if thinking steps exist), then content with citation parsing.
- User messages: renders mention tokens inline via regex replacement (`[mention: label]` → `MentionChip`).
- Custom markdown renderer (`MessageMarkdown`) — hand-rolled, handles code blocks, headings, lists, bold, inline code. Does **not** use a markdown parsing library (no remark/rehype).
- `renderContentWithCitations()`: splits content on `[N]` markers, renders `InlineCitationCarousel` for each bracket.
- `getStepIcon()`: maps thinking step labels to Lucide icons via keyword matching (e.g., "retriev" → `Search`, "generat" → `MessageSquare`).

### `mention/` (~2,500 lines, 11 files)

Self-contained mention/typeahead system. Well-architected with clear separation of concerns.

**`mention-types.ts`** (88 lines) — Type definitions:

```ts
type Token = TextToken | MentionToken;
type TextToken = { type: "text"; text: string };
type MentionToken = {
  type: "mention";
  id: string;
  label: string;
  triggerChar: string;
};
type MentionItem = { id: string; label: string; [key: string]: unknown };
type TriggerConfig = {
  char: string;
  items: MentionItem[];
  isLoading?: boolean;
  error?: string;
};
type ActiveTrigger = { char: string; query: string; startIndex: number };
```

**`use-mention-picker.ts`** (680 lines) — Core state machine hook:

```ts
function useMentionPicker(options: {
  triggers: TriggerConfig[];
  initialValue?: string;
  onValueChange?: (value: string) => void;
  getDisplayValue?: () => string;
  getSelectionRange?: () => [number, number] | null;
  setSelectionRange?: (start: number, end: number) => void;
  getCaretCoordinates?: () => { top: number; left: number };
}): {
  displayValue: string;
  tokens: Token[];
  isOpen: boolean;
  activeTrigger: ActiveTrigger | null;
  activeIndex: number;
  filteredItems: MentionItem[];
  caretCoords: { top: number; left: number };
  status: MentionStatus;
  textareaRef: RefObject<HTMLTextAreaElement | HTMLDivElement | null>;
  handleChange: (e: ChangeEvent) => void;
  handleKeyDown: (e: KeyboardEvent) => void;
  handleClick: () => void;
  selectItem: (item: MentionItem) => void;
  closeDropdown: () => void;
  replaceDisplayValue: (newWire: string, preserveTrigger?: boolean) => void;
  buildTokenizedMessage: () => string;
  clearTokens: () => void;
};
```

Uses `useReducer` with 7 action types. Key logic:

- **Trigger detection:** On input change, scans backward from cursor for trigger chars (`@`). Prevents false positives inside email addresses.
- **Item filtering:** Case-insensitive substring match against `item.label`.
- **Token reconciliation:** `rebuildTokens()` scans the display string for known mention labels and reconstructs the token array.
- **Keyboard navigation:** Arrow keys move `activeIndex`, Enter/Tab select, Escape closes, Backspace deletes whole mention chips.
- Supports both `HTMLTextAreaElement` and `HTMLDivElement` (contenteditable) via strategy callbacks.

**`mention-picker.tsx`** (80 lines) — Context provider. Two modes:

1. Self-managed: creates internal picker state.
2. External picker: receives an existing `useMentionPicker` return value.

Always calls `useMentionPicker` (rules of hooks compliance) but discards the result when an external picker is provided.

**`mention-dropdown.tsx`** (178 lines) — Floating panel positioned above the textarea. Uses `createPortal` to `document.body`. Auto-scrolls to the active item. Shows loading/error/empty sub-states.

**`mention-input-editable.tsx`** (470 lines) — ContentEditable implementation:

- Rebuilds DOM nodes via `useLayoutEffect`: text nodes + `<span>` elements with React roots (`createRoot`) for each `MentionChip`.
- Manages React root cleanup via `mentionChipRootsRef`.
- Custom paste handler (strips to plain text).
- IME composition handling.
- Selection management via `desiredSelectionRef`.
- Form submit on Enter (finds closest `<form>`, calls `requestSubmit()`).
- Hidden `<input name="message">` for form data compatibility.

**`mention-input.tsx`** (82 lines) — Simple `<textarea>` wrapper wired to `useMentionPickerContext()`. ARIA combobox attributes. Simpler alternative to the contenteditable version.

**`mention-chip.tsx`** (95 lines) — Badge rendering. Two variants: `"input"` (inside textarea) and `"chat"` (in message bubbles). Click handler shows a toast (TODO: open PDF viewer). Remove button is commented out.

**`mention-item.tsx`** (58 lines) — `React.memo`-wrapped list item for the dropdown. Prevents textarea blur on mousedown.

**`mention-utils.ts`** (435 lines) — Pure utility functions:

- Wire format: `[mention:@:Label:id]`
- `parse(wire)` / `serialize(tokens)` — bidirectional conversion
- `detectTrigger()` — regex-based, email-safe
- `getCaretCoords()` — mirror-div technique for textarea caret measurement
- ContentEditable helpers for selection management

**`use-editable-history.ts`** (131 lines) — Undo/redo stack for contenteditable. Coalesces rapid edits within a configurable window (default: 300ms). Max 200 entries.

### `documents/`

**`DocumentsTab`** (`DocumentsTab.tsx`, 777 lines)

```ts
interface DocumentsTabProps {
  projectId: string;
  onDocumentsChange?: (documents: Document[]) => void;
  onDocumentsLoaded?: (hasDocuments: boolean) => void;
  onSelectionChange?: (selectedDocIds: string[]) => void;
  selectedDocIds?: string[];
}
```

**Internal state:** 13 `useState` hooks (documents, viewMode, isDragging, isUploading, isDownloading, isLoading, deleteDialogOpen, docsToDelete, isDeleting, linkDialogOpen, userDocuments, selectedLinkedDocs, isLoadingUserDocs, isLinking).

**Data dependencies:** Direct API calls (no TanStack Query): `getAllDocuments`, `getAllUserDocuments`, `uploadDocuments`, `deleteDocumentsFromProject`, `linkDocumentToProject`, `downloadDocuments`, `downloadDocument`.

**⚠ Code duplication:** This component largely duplicates `data-library.tsx` logic with the addition of project scoping and a "Link from Library" dialog. The link operation processes documents **sequentially** in a loop.

**`DocumentPreview`** (48 lines) — Badge list of selected document filenames.

**`ThumbnailImage`** (64 lines) — Wrapped in `React.memo` with custom comparator. Three render states: loading spinner, error icon, image.

**`ScrollingFileName`** (65 lines) — CSS marquee animation on hover when text overflows container.

**`document-grid.tsx`** (125 lines) — Grid of cards with `Checkbox`, `ThumbnailImage`, `ScrollingFilename`, context menu. Pure render.

**`documents-data-table.tsx`** (190 lines) — TanStack Table wrapper. Converts `selectedDocIds` to `RowSelectionState`. Uses `getRowId: (row) => row.doc_id`.

**`documents-table-columns.tsx`** (180 lines) — Column factory `createColumns(onDownload, onDelete)`.

### `generation/`

**`ConceptSelector`** (139 lines) — Controlled component. Toggle buttons grouped by document. Select All / Clear. Tooltips show concept summaries.

**`GenerateTab`** (294 lines) — Multi-phase wizard consuming `useAgentStream()` hook. Renders different card layouts per phase (idle → extracting → selecting → processing → complete → error).

**⚠ Unused prop:** `projectId` is destructured but aliased to `_projectId`.

**`ReviewTab`** (13 lines) — Placeholder.

### `projects/`

**`projects.tsx`** (465 lines) — Project list page. `useEffect` fetch. Search filtering. Card grid. Inline `CreateProjectDialog` (duplicated).

**`CreateProjectDialog.tsx`** (188 lines) — Zod-validated form via `react-hook-form`. Schema: name 3–50 chars, no duplicates, description max 300 chars.

**⚠ Bug:** Imports `Form` from `react-router-dom` instead of the UI Form component. The spread `<Form {...form}>` will not work correctly.

**`ProjectDetailPage.tsx`** (94 lines) — Route wrapper with HTTP status error mapping.

**`ProjectDetail.tsx`** (181 lines) — Tab container for Documents / Generate / Review.

### `dashboard/`

**`dashboard.tsx`** (12 lines) — Renders `SectionCards` + `ChartAreaInteractive`.

**`chart-area-interactive.tsx`** (288 lines) — Recharts `AreaChart` with hardcoded 90 data points (April–June 2024). Time range filter (90d/30d/7d). Responsive: `ToggleGroup` on desktop, `Select` on mobile.

**`section-cards.tsx`** (200 lines) — Four stat cards: Total MCQs, MCQs Today, Avg Questions/MCQ, Latest MCQ. Fetches `mcqApi.getAll()` on mount. Uses `useMemo` for derived values.

**`data-card.tsx`** (80 lines) — Generic KPI card with status-driven icon/color.

### `auth/`

**`login-form.tsx`** (222 lines) — Email/password form with client-side validation.

**`signup-form.tsx`** (328 lines) — Registration with `ValidationChecklist`.

**`requireAuth.tsx`** (32 lines) — Route guard. See §5.2.

### `embeddings/`

**`columns.tsx`** (147 lines) — TanStack Table column definitions for `EmbeddingVersion`. Factory: `getColumns({ onDelete })`.

**`embeddings-table.tsx`** (0 lines) — **Empty file.** Not referenced anywhere.

---

## 5.8 Layout Components (`src/components/layouts/`)

### `AppSidebar` (`app-sidebar.tsx`, 172 lines)

```ts
type AppSidebarProps = React.ComponentProps<typeof Sidebar> & {};
```

Renders the main navigation sidebar. Navigation items are hardcoded in a module-level `data` object:

```ts
const data = {
  user: { ... },        // ⚠ Dead code — real user from useAuth()
  navMain: [{ title: "Chat", url: "/", icon: IconMessage2 }],
  navClouds: [
    { title: "Projects",       url: "/projects",       icon: Folder },
    { title: "Data Library",   url: "/data-library",   icon: Database },
    { title: "Vector Store",   url: "/vector-store",   icon: DatabaseZap },
    // ...
  ],
  navSecondary: [
    { title: "Settings", url: "/settings", icon: Settings2 },
    { title: "Get Help", url: "/help",     icon: HelpCircle },
    { title: "Search",   url: "/search",   icon: Search },
  ],
  documents: [ ... ],   // Static document links
};
```

**Data dependencies:** `useAuth()` → `{ user }`. Passes `user!` (non-null assertion) to `NavUser`.

### `NavMain` (`nav-main.tsx`, 143 lines)

Renders primary nav items and a **recent chats** list.

**State:** `chats: ChatResponse[]`

**Data fetching:** Calls `chatApi.list({ limit: 20, status: "active" })` on mount and **on every `location.pathname` change**. This means navigating between pages triggers a fresh API call.

**Chat deletion:** `handleDeleteChat` calls `chatApi.delete(chatId)` then locally filters the state array. Does not invalidate any TanStack Query cache.

### `NavDocuments` (`nav-documents.tsx`, 97 lines)

Static document link list. Dropdown actions (Open, Share, Delete) are placeholder — no handlers attached.

Has `"use client"` directive.

### `NavSecondary` (`nav-secondary.tsx`, 58 lines)

Renders secondary nav items. Differentiates internal links (react-router `<Link>`) from external links (`<a>`).

Has `"use client"` directive.

### `NavUser` (`nav-user.tsx`, 131 lines)

User dropdown menu with logout confirmation. Avatar image is hardcoded to `/avatars/shadcn.jpg` with fallback `CN`. Account, Billing, Notifications items are UI-only (no handlers).

### `SiteHeader` (`site-header.tsx`, 54 lines)

```ts
interface SiteHeaderProps {
  title: string;
  icon?: JSX.Element;
}
```

Three render modes:

1. Icon mode: shows icon next to title (used during project loading).
2. Breadcrumb mode: splits `title` on `" / "` — renders parent as a clickable button (navigates to `/projects`) and leaf as `<h1>`.
3. Plain title mode: renders `<h1>`.

### `ThemeProvider` (`theme-provider.tsx`, 13 lines)

Thin wrapper around `next-themes`'s `ThemeProvider`. Exists to re-export with the `"use client"` directive (shadcn/ui convention from Next.js). The directive is a no-op in Vite.

---

## 5.9 AI Element Components (`src/components/ai-elements/`)

These components originate from the [Vercel AI SDK UI Elements](https://ai-sdk.dev/elements) registry and are customized locally.

### `PromptInput` (`prompt-input.tsx`, 1,341 lines)

The largest file in the frontend. Contains 3 context definitions, 6 public hooks, and 31+ exported sub-components.

**Context architecture:**

| Context                         | Scope               | Purpose                                                                           |
| ------------------------------- | ------------------- | --------------------------------------------------------------------------------- |
| `PromptInputController`         | Provider-level      | Coordinates `textInput` + `attachments` across multiple `<PromptInput>` instances |
| `ProviderAttachmentsContext`    | Provider-level      | Shared attachment state within a `PromptInputProvider`                            |
| `LocalAttachmentsContext`       | Per-`<PromptInput>` | Local attachment state when no provider wraps the form                            |
| `LocalReferencedSourcesContext` | Per-`<PromptInput>` | Source document references                                                        |

**`PromptInputProvider`** (lines 154–243):

```ts
function PromptInputProvider({ children, initialInput?: string }): JSX.Element
```

**State:** `textInput: string`, `attachmentFiles: (FileUIPart & { id: string })[]`.

Manages blob URL lifecycle (revokes on remove/clear/unmount). Optional — if absent, `<PromptInput>` manages its own state.

**`PromptInput`** (lines 314–780):

```ts
interface PromptInputProps extends Omit<
  HTMLAttributes<HTMLFormElement>,
  "onSubmit" | "onError"
> {
  accept?: string;
  multiple?: boolean;
  globalDrop?: boolean;
  syncHiddenInput?: boolean;
  maxFiles?: number;
  maxFileSize?: number;
  onError?: (error: string) => void;
  onSubmit: (value: {
    input: string;
    files: FileUIPart[];
    sources: SourceDocumentUIPart[];
  }) => void | Promise<void>;
}
```

Dual-mode attachment management: local state when standalone, provider state when wrapped in `PromptInputProvider`. Both paths validate `accept`, `maxFiles`, `maxFileSize`. Blob URLs are created for file uploads and revoked on removal/unmount.

Six `useEffect` hooks handle:

1. Sync `filesRef` with current files
2. Register file input with provider
3. Reset file input when files empty
4. Form-level drag/drop
5. Document-level drag/drop (when `globalDrop`)
6. Cleanup blob URLs

**`PromptInputTextarea`** (lines 789–936):

```ts
interface PromptInputTextareaProps extends Omit<
  TextareaHTMLAttributes<HTMLTextAreaElement>,
  "value" | "onChange"
> {
  disableAutoResize?: boolean;
}
```

Auto-resizing textarea. Enter submits the form, Shift+Enter inserts newline. Paste handler extracts files from clipboard. Backspace on empty input removes the last attachment. IME composition tracking prevents premature submission.

**`PromptInputSubmit`** (lines 1057–1108):

```ts
interface PromptInputSubmitProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  status?: "submitted" | "streaming" | "ready" | "error";
  onStop?: () => void;
}
```

Adaptive button: `submitted` → spinner, `streaming` → stop square, `error` → X icon, default → corner-down-left (send). When `status` is `"submitted"` or `"streaming"`, clicking calls `onStop` instead of submitting.

**Other sub-components** (lines 938–1276): `PromptInputHeader`, `PromptInputFooter`, `PromptInputTools`, `PromptInputButton`, `PromptInputActionMenu*` (dropdown), `PromptInputSelect*` (select), `PromptInputHoverCard*`, `PromptInputTab*` (tab layout), `PromptInputCommand*` (cmdk-based command palette for mentions/slash commands).

### `ChainOfThought` (`chain-of-thought.tsx`, 223 lines)

Collapsible thinking step visualization using Radix primitives.

**Exported components:**

| Component                     | Props                                                   | Description                                       |
| ----------------------------- | ------------------------------------------------------- | ------------------------------------------------- |
| `ChainOfThought`              | `{ open?, defaultOpen?, onOpenChange?, children }`      | Root wrapper, creates context                     |
| `ChainOfThoughtHeader`        | `{ children }`                                          | Collapsible trigger with brain icon + chevron     |
| `ChainOfThoughtStep`          | `{ status: "complete"\|"active"\|"pending", children }` | Individual step with status dot + connecting line |
| `ChainOfThoughtContent`       | `{ children }`                                          | Animated collapsible body                         |
| `ChainOfThoughtSearchResults` | `{ children }`                                          | Flex container for search result badges           |
| `ChainOfThoughtSearchResult`  | `{ children }`                                          | Badge for a single search result                  |
| `ChainOfThoughtImage`         | `{ src, alt, caption? }`                                | Captioned image                                   |

All components are wrapped in `React.memo`. Supports both controlled and uncontrolled open/close via `@radix-ui/react-use-controllable-state`.

Has `"use client"` directive (dead code in Vite).

### `Conversation` (`conversation.tsx`, 167 lines)

Scrollable message list with auto-scroll-to-bottom behavior via the `use-stick-to-bottom` library.

**Exported components:**

| Component                  | Props                                             | Description                                                |
| -------------------------- | ------------------------------------------------- | ---------------------------------------------------------- |
| `Conversation`             | `{ className?, children }`                        | Root wrapper with `StickToBottom`                          |
| `ConversationContent`      | `{ className?, children }`                        | Scrollable content area                                    |
| `ConversationEmptyState`   | `{ icon?, title?, description? }`                 | Centered empty state                                       |
| `ConversationScrollButton` | `{ className? }`                                  | Floating "scroll to bottom" button (hidden when at bottom) |
| `ConversationDownload`     | `{ messages: ConversationMessage[], className? }` | Export messages as Markdown file                           |

**`messagesToMarkdown()`:** Utility that formats messages into `## User\n\ncontent\n\n---` markdown.

Has `"use client"` directive.

### `InlineCitation` (`inline-citation.tsx`, 294 lines)

Source attribution with hover card and carousel navigation.

**Exported components (14):**

| Component                       | Key Props                     | Description                       |
| ------------------------------- | ----------------------------- | --------------------------------- |
| `InlineCitation`                | —                             | Root `<span>` wrapper             |
| `InlineCitationText`            | —                             | Text with hover highlight         |
| `InlineCitationCard`            | `{ openDelay?: number }`      | HoverCard wrapper (0ms default)   |
| `InlineCitationCardTrigger`     | `{ sources: string[] }`       | Badge showing hostname + count    |
| `InlineCitationCardBody`        | —                             | HoverCard content                 |
| `InlineCitationCarousel`        | —                             | Carousel wrapper with API context |
| `InlineCitationCarouselContent` | —                             | Carousel content                  |
| `InlineCitationCarouselItem`    | —                             | Carousel item                     |
| `InlineCitationCarouselHeader`  | —                             | Header with navigation            |
| `InlineCitationCarouselIndex`   | —                             | "1/3" page indicator              |
| `InlineCitationCarouselPrev`    | —                             | Previous arrow                    |
| `InlineCitationCarouselNext`    | —                             | Next arrow                        |
| `InlineCitationSource`          | `{ title, url, description }` | Source card                       |
| `InlineCitationQuote`           | —                             | Blockquote                        |

**⚠ Runtime error risk:** `InlineCitationCardTrigger` calls `new URL(sources[0]).hostname` — throws `TypeError` if `sources[0]` is not a valid URL or if `sources` is empty.

Has `"use client"` directive.

---

## 5.10 Shared & UI Components

### Shared Components

**`alert-dialog.tsx`** (33 lines) — Hardcoded delete-account confirmation dialog:

```tsx
// Hardcoded text, not parameterized:
<AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
<AlertDialogDescription>
  This action cannot be undone. This will permanently delete your
  account and remove your data from our servers.
</AlertDialogDescription>
```

`AlertDialogAction` has **no `onClick` handler**. The `children` prop is rendered as the trigger button text. This is a template/demo component.

**`data-table.tsx`** (725 lines) — Generic-looking data table that is actually **hardcoded to `EmbeddingVersion` type**:

```ts
function DataTable({
  data: initialData,
  onDelete,
}: {
  data: EmbeddingVersion[];
  onDelete?: (versionIds: string[]) => void;
});
```

Features: drag-and-drop row reordering (dnd-kit), column visibility toggle, pagination, batch delete with `confirm()`. Contains ~250 lines of commented-out code (a `TableCellViewer` drawer with chart and form — leftover from shadcn template). Action handlers use `alert()` placeholders.

### shadcn/ui Primitives (42 files)

All in `src/components/ui/`. Standard shadcn/ui components with Tailwind styling.

| Component                  | Customization Notes                                                               |
| -------------------------- | --------------------------------------------------------------------------------- |
| `alert-dialog.tsx`         | Standard Radix AlertDialog                                                        |
| `alert.tsx`                | Standard                                                                          |
| `avatar.tsx`               | Standard                                                                          |
| `badge.tsx`                | Standard                                                                          |
| `breadcrumb.tsx`           | Standard                                                                          |
| `button.tsx`               | Standard — variant system (default, destructive, outline, secondary, ghost, link) |
| `card.tsx`                 | Standard                                                                          |
| `carousel.tsx`             | Embla Carousel                                                                    |
| `chart.tsx`                | Recharts wrapper (355 lines)                                                      |
| `checkbox.tsx`             | Standard Radix Checkbox                                                           |
| `collapsible.tsx`          | Standard Radix Collapsible                                                        |
| `command.tsx`              | cmdk + Radix Dialog                                                               |
| `context-menu.tsx`         | Standard Radix ContextMenu                                                        |
| `dialog.tsx`               | Standard Radix Dialog                                                             |
| `download-button.tsx`      | Custom — download icon button                                                     |
| `drawer.tsx`               | Vaul drawer                                                                       |
| `dropdown-menu.tsx`        | Standard Radix DropdownMenu                                                       |
| `empty.tsx`                | Custom — empty state with icon/title/description                                  |
| `field.tsx`                | Custom — form field wrapper                                                       |
| `form.tsx`                 | react-hook-form + Radix Label                                                     |
| `hover-card.tsx`           | Standard Radix HoverCard                                                          |
| `input-group.tsx`          | Custom — input with addons                                                        |
| `input.tsx`                | Standard                                                                          |
| `item.tsx`                 | Custom — generic list item                                                        |
| `label.tsx`                | Standard Radix Label                                                              |
| `password-input.tsx`       | Custom — input with show/hide toggle                                              |
| `scroll-area.tsx`          | Standard Radix ScrollArea                                                         |
| `search-input.tsx`         | Custom — input with search icon                                                   |
| `select.tsx`               | Standard Radix Select                                                             |
| `separator.tsx`            | Standard Radix Separator                                                          |
| `sheet.tsx`                | Standard Radix Dialog variant                                                     |
| `sidebar.tsx`              | Custom — complex sidebar system (726 lines)                                       |
| `skeleton.tsx`             | Standard                                                                          |
| `sonner.tsx`               | Sonner toast wrapper                                                              |
| `spinner.tsx`              | Custom — loading spinner                                                          |
| `table.tsx`                | Standard                                                                          |
| `tabs.tsx`                 | Standard Radix Tabs                                                               |
| `textarea.tsx`             | Standard                                                                          |
| `toggle-group.tsx`         | Standard Radix ToggleGroup                                                        |
| `toggle.tsx`               | Standard Radix Toggle                                                             |
| `tooltip.tsx`              | Standard Radix Tooltip                                                            |
| `validation-checklist.tsx` | Custom — password validation display                                              |

---

## 5.11 Styling & Theming

### Tailwind 4.1 Setup

Build toolchain: `@tailwindcss/vite` plugin (Tailwind v4 Vite integration) + `@vitejs/plugin-react-swc`.

```ts
// vite.config.ts
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "./src") } },
});
```

### Color System

Colors use the **oklch** color space, defined as CSS custom properties in `index.css`:

```css
:root {
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0.004 285.823);
  --primary: oklch(0.205 0.042 265.755);
  --primary-foreground: oklch(0.985 0.002 247.839);
  /* ... 20+ more tokens */
}

.dark {
  --background: oklch(0.145 0.004 285.823);
  --foreground: oklch(0.985 0.002 247.839);
  --primary: oklch(0.922 0.077 264.052);
  /* ... */
}
```

Sidebar, chart, and ring colors are also tokenized. The `@theme inline` block maps every custom property to a Tailwind utility (e.g., `bg-primary`, `text-muted-foreground`).

### Dark/Light Mode

Managed by `next-themes` with `attribute="class"`:

```tsx
<ThemeProvider attribute="class" defaultTheme="light" enableSystem disableTransitionOnChange>
```

The `ThemeProvider` adds/removes the `dark` class on `<html>`. CSS uses `&:is(.dark *)` selector variant.

### Global Overrides (`index.css`)

```css
/* Hides ALL native scrollbars globally */
* {
  scrollbar-width: none;
}
*::-webkit-scrollbar {
  display: none;
}

/* Re-enables scrollbars only inside shadcn ScrollArea */
[data-slot="scroll-area-viewport"] {
  scrollbar-width: thin;
}
[data-slot="scroll-area-viewport"]::-webkit-scrollbar {
  display: block;
}
```

This means any overflow content outside of a `<ScrollArea>` component is not scrollable via native scrollbar. The scroll content is accessible via mouse wheel / trackpad / touch, but no visual scrollbar indicator is shown.

Additional base overrides:

- `html, body, :root, #root` → `overflow: hidden; height: 100%`
- `.marquee` animation (horizontal scroll, 8s) — used by `ScrollingFileName`
- `.squircle` — uses experimental `corner-shape: squircle` CSS

### `App.css` (42 lines)

Default Vite/React template CSS (logo animation, centered layout). **Entirely unused** — the app is styled via Tailwind.

### `components.json`

```json
{
  "style": "new-york",
  "rsc": false,
  "tsx": true,
  "tailwind": { "cssVariables": true, "baseColor": "neutral" },
  "iconLibrary": "lucide",
  "registries": {
    "@ai-elements": {
      "url": "https://ai-sdk.dev/elements/api/registry/{name}.json"
    }
  }
}
```

`rsc: false` confirms React Server Components are disabled. The `@ai-elements` registry is the source for the ai-elements components.

### ⚠ "use client" Directives (Dead Code)

20 files contain `"use client"` directives. In Vite, this string literal is a no-op — it is only meaningful in Next.js/RSC environments. Files with this directive:

**ai-elements/**: `prompt-input.tsx`, `chain-of-thought.tsx`, `conversation.tsx`, `inline-citation.tsx`
**layouts/**: `nav-documents.tsx`, `nav-main.tsx`, `nav-secondary.tsx`, `theme-provider.tsx`
**features/**: `chart-area-interactive.tsx`, `section-cards.tsx`
**ui/**: `tabs.tsx`, `dropdown-menu.tsx`, `toggle-group.tsx`, `command.tsx`, `carousel.tsx`, `password-input.tsx`, `sidebar.tsx`, `select.tsx`, `sheet.tsx`, `avatar.tsx`, `toggle.tsx`

These should be documented as dead code and optionally removed. They were inherited from shadcn/ui templates and AI SDK elements (which target Next.js by default).

---

## Things a First-Time Contributor Would Likely Misunderstand

1. **Where the chat page lives.** The router renders `ChatPage` from `src/components/features/chat/chat-page.tsx`, **not** from `src/pages/`. The `src/pages/` directory contains the data-library, vector-store, and placeholder pages. The most important page component is inside `components/features/`.

2. **Which data fetching pattern to follow.** Some components use TanStack Query hooks (`useDocuments`, `useUploadDocument`), others use raw `useEffect` + direct API calls. A contributor might assume one pattern is the standard and be confused when they encounter the other. The TanStack Query pattern is the intended direction — raw `useEffect` fetching is tech debt.

3. **The `"use client"` directives mean something.** A contributor familiar with Next.js might assume these directives control server/client rendering boundaries. In this Vite SPA, they are completely inert. No component runs on a server. Removing them changes nothing.
