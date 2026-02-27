# Otis UI — Frontend Audit Report

> **Generated**: June 2025  
> **Scope**: Every source file under `frontend/otis-ui/src/` (~127 files)

---

## Table of Contents

1. [Build Configuration](#1-build-configuration)
2. [Styling Approach](#2-styling-approach)
3. [Auth Flow](#3-auth-flow)
4. [Routes & Pages](#4-routes--pages)
5. [API Layer](#5-api-layer)
6. [Hooks](#6-hooks)
7. [Type Definitions & Interfaces](#7-type-definitions--interfaces)
8. [State Management](#8-state-management)
9. [Component Inventory](#9-component-inventory)
10. [Tech Debt & Recommendations](#10-tech-debt--recommendations)

---

## 1. Build Configuration

| Item           | Value                                              |
| -------------- | -------------------------------------------------- |
| **Bundler**    | Vite via `rolldown-vite@7.2.2`                     |
| **TS**         | TypeScript 5.9.3 (`tsc -b && vite build`)          |
| **React**      | 19.2.0 with `@vitejs/plugin-react-swc`             |
| **Path alias** | `@` → `./src` (vite.config.ts + tsconfig.app.json) |
| **Scripts**    | `dev`, `build`, `lint` (eslint), `preview`         |

**Key dependencies:**

| Category      | Package                                     | Version |
| ------------- | ------------------------------------------- | ------- |
| Routing       | react-router-dom                            | 7.9.6   |
| Server state  | @tanstack/react-query                       | 5.90    |
| Tables        | @tanstack/react-table                       | 8.21    |
| HTTP          | axios                                       | 1.9     |
| Forms         | react-hook-form + @hookform/resolvers + zod | —       |
| UI primitives | Radix UI (full suite)                       | —       |
| Charts        | recharts                                    | 2.15    |
| AI SDK        | ai (Vercel)                                 | 6.0.94  |
| Drag & drop   | @dnd-kit/core + sortable + modifiers        | —       |
| Carousel      | embla-carousel-react                        | —       |
| Theme         | next-themes                                 | —       |
| Toasts        | sonner                                      | —       |
| Icons         | lucide-react + @tabler/icons-react          | —       |
| Scroll        | use-stick-to-bottom                         | —       |
| IDs           | nanoid                                      | —       |
| Dates         | date-fns                                    | —       |

---

## 2. Styling Approach

- **Tailwind CSS 4.1.17** via `@tailwindcss/vite` plugin + `tw-animate-css`
- **oklch color system** with CSS custom properties for light/dark theme tokens (defined in `src/index.css`)
- **Dark mode**: class-based toggle via `next-themes` → `<ThemeProvider>` wraps `next-themes/ThemeProvider`
- **Utility**: `cn()` (clsx + tailwind-merge) in `src/lib/utils.ts`
- **Custom CSS**: hidden native scrollbars globally (re-enabled on `[data-radix-scroll-area-viewport]`), `.marquee` keyframe animation, `.squircle` clip-path
- **Component library**: ~42 shadcn/ui wrapper components in `src/components/ui/` (standard Radix + Tailwind wrappers — alert-dialog, avatar, badge, breadcrumb, button, card, carousel, chart, checkbox, collapsible, command, context-menu, dialog, download-button, drawer, dropdown-menu, empty, field, form, hover-card, input-group, input, item, label, password-input, scroll-area, search-input, select, separator, sheet, sidebar, skeleton, sonner, spinner, table, tabs, textarea, toggle-group, toggle, tooltip, validation-checklist)

**Tech debt**: `src/App.css` (42 lines) is original Vite template CSS — completely unused, dead code.

---

## 3. Auth Flow

### Flow

1. **Login** (`/Login`): `login-form.tsx` → `POST /v1/auth/login` (form-urlencoded) → stores JWT in `localStorage` as `access_token` → calls `refreshUser()`
2. **Signup** (`/Signup`): `signup-form.tsx` → `POST /v1/auth/register` → redirects to login
3. **Session bootstrap**: `authContext.tsx` on mount calls `GET /v1/auth/me` with Bearer token → sets `user` state
4. **Route guard**: `requireAuth.tsx` checks `loading`, `token`, `user`; redirects to `/Login` if unauthenticated
5. **Logout**: `nav-user.tsx` confirmation dialog → removes `access_token` from localStorage → navigates to `/Login` (no server-side logout endpoint)

### Components

| File                                                       | Purpose                                                                                                        |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `src/authContext.tsx`                                      | `AuthProvider` + `useAuth()` hook. Types: `User { user_id, email, uname }`                                     |
| `src/components/features/auth/login-form.tsx` (218 lines)  | Login page with random hero image, email/password fields, zod validation. Google login button (non-functional) |
| `src/components/features/auth/signup-form.tsx` (329 lines) | Signup with name/email/password/confirm, real-time password validation checklist                               |
| `src/components/features/auth/requireAuth.tsx` (33 lines)  | Route guard wrapper (Navigate to `/Login`)                                                                     |

### Auth API (`src/api/authApi.ts`, 51 lines)

| Method | Endpoint            | Purpose                                 |
| ------ | ------------------- | --------------------------------------- |
| POST   | `/v1/auth/register` | Signup                                  |
| POST   | `/v1/auth/login`    | Login (form-urlencoded)                 |
| GET    | `/v1/auth/me`       | Fetch current user                      |
| —      | —                   | `logout()` — client-only (localStorage) |

**Shared axios instance:** `api` with baseURL `http://localhost:8000`, Bearer token interceptor, exported for use by all other API modules.

---

## 4. Routes & Pages

Routes are defined in `src/main.tsx` using `createBrowserRouter`.

### Active Routes

| Path              | Element                 | Layout                    | Notes                                   |
| ----------------- | ----------------------- | ------------------------- | --------------------------------------- |
| `/Login`          | `<LoginForm />`         | None                      | Public                                  |
| `/Signup`         | `<SignupForm />`        | None                      | Public                                  |
| `/`               | `<App />`               | Protected (`RequireAuth`) | Root layout — sidebar + header + outlet |
| `/` (index)       | `<Dashboard />`         | App                       | Dashboard cards + chart                 |
| `/chat`           | `<ChatPage />`          | App                       | New chat                                |
| `/chat/:chatId`   | `<ChatPage />`          | App                       | Existing chat                           |
| `/data-library`   | `<DataLibrary />`       | App                       | Document management                     |
| `/vector-store`   | `<VectorStorePage />`   | App                       | Embedding sync                          |
| `/word-assistant` | `<WordAssistant />`     | App                       | Placeholder                             |
| `/help`           | `<Help />`              | App                       | Placeholder                             |
| `/search`         | `<SearchPage />`        | App                       | Placeholder                             |
| `/settings`       | `<Settings />`          | App                       | Placeholder                             |
| `/reports`        | `<Reports />`           | App                       | Placeholder                             |
| `/p/:projectId`   | `<ProjectDetailPage />` | App                       | Project detail with tabs                |
| `/projects`       | `<Projects />`          | App                       | Project list + create                   |

### Commented-out Routes (in main.tsx)

- `/analytics` → `<Analytics />`
- `/team` → `<Team />`
- `/capture` → `<Capture />`
- `/proposal` → `<Proposal />`
- `/prompts` → `<Prompts />`

### Root Layout (`App.tsx`, 116 lines)

- `SidebarProvider` → `AppSidebar` + `SidebarInset`
- Dynamic breadcrumb: fetches project name for `/p/:projectId` via `projectApi.getOne()`
- `routeToHeader` Record maps paths to display titles
- Chat routes get `overflow-hidden` container; all others get `<ScrollArea>`

### Page Details

| Page           | File                                                                                         | Lines      | Description                                                                                                                                                             |
| -------------- | -------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dashboard      | `src/pages/dashboard.tsx` → `dashboard.tsx`                                                  | 12         | Composes `SectionCards` + `ChartAreaInteractive`                                                                                                                        |
| Data Library   | `src/pages/data-library.tsx`                                                                 | 479        | Full document CRUD — grid/table toggle, upload (drag-drop + file picker), download (blob), delete with confirmation, search filtering, duplicate detection via filename |
| Vector Store   | `src/pages/vector-store.tsx`                                                                 | 304        | Embedding sync management — 3 stat cards (total/embedded/pending), sync button with 3s polling, `sessionStorage` for cross-navigation sync state persistence            |
| Chat           | `src/components/features/chat/chat-page.tsx`                                                 | 660        | Main chat — see [Chat Components](#chat) below                                                                                                                          |
| Projects       | `src/components/features/projects/projects.tsx`                                              | 466        | Project cards grid, search, create dialog, delete, navigation                                                                                                           |
| Project Detail | `ProjectDetailPage.tsx` + `ProjectDetail.tsx`                                                | 95 + 162   | Tabbed view: Documents / Generate / Review                                                                                                                              |
| Placeholders   | analytics, capture, help, prompts, proposal, reports, search, settings, team, word-assistant | 10-20 each | "Coming soon" stubs                                                                                                                                                     |

---

## 5. API Layer

All API modules are in `src/api/`. They import the shared `api` axios instance from `authApi.ts`.

### Endpoints by Module

#### chatApi.ts (479 lines)

| Method | Endpoint                              | Function                                    | Notes                                     |
| ------ | ------------------------------------- | ------------------------------------------- | ----------------------------------------- |
| POST   | `/v1/chats/`                          | `create(data)`                              | Create chat                               |
| GET    | `/v1/chats/`                          | `list()`                                    | List all chats                            |
| GET    | `/v1/chats/{id}`                      | `getById(id)`                               | Get single chat                           |
| PATCH  | `/v1/chats/{id}`                      | `update(id, data)`                          | Update chat metadata                      |
| DELETE | `/v1/chats/{id}`                      | `deleteChat(id)`                            | Delete chat                               |
| POST   | `/v1/chats/{id}/messages`             | `addMessage(chatId, data)`                  | Add message                               |
| GET    | `/v1/chats/{id}/messages`             | `getMessages(chatId)`                       | List messages                             |
| PATCH  | `/v1/chats/{id}/messages/{id}`        | `updateMessage(chatId, msgId, data)`        | Edit message                              |
| DELETE | `/v1/chats/{id}/messages/{id}`        | `deleteMessage(chatId, msgId)`              | Delete message                            |
| GET    | `/v1/chats/{id}/messages/{id}/events` | `replayEventsSSE(chatId, msgId, callbacks)` | Replay persisted events (SSE or JSON)     |
| POST   | `/v1/chats/{id}/invoke`               | `stream(chatId, body, callbacks)`           | Live chat invoke (SSE via native `fetch`) |

**SSE parsing**: Uses native `fetch` + `ReadableStream` with manual line-based SSE parsing. `replayEventsSSE()` auto-detects JSON array vs SSE content-type.

**Types exported**: `ChatResponse`, `ChatCreate`, `ChatUpdate`, `ChatMessageResponse`, `ChatMessageCreate`, `ChatMessageUpdate`, `ChatInvokeEvent` (discriminated union: `started | token | done | error | thinking | reasoning_token`)

#### docApi.ts (127 lines)

| Method | Endpoint                              | Function                                     | Notes                   |
| ------ | ------------------------------------- | -------------------------------------------- | ----------------------- |
| GET    | `/v1/documents/`                      | `getUserDocuments()`                         | User-level docs         |
| POST   | `/v1/documents/`                      | `uploadDocument(file)`                       | Upload (multipart)      |
| GET    | `/v1/documents/{id}`                  | `getDocument(id)`                            | Single doc              |
| GET    | `/v1/documents/{id}/download`         | `downloadDocument(id)`                       | Blob                    |
| GET    | `/v1/documents/{id}/thumbnail`        | `getThumbnail(id)`                           | Blob                    |
| GET    | `/v1/project/{id}/documents/`         | `getProjectDocuments(projectId)`             | Project docs            |
| POST   | `/v1/project/{id}/documents/`         | `uploadDocumentToProject(projectId, file)`   | Upload to project       |
| GET    | `/v1/project/{id}/documents/{id}`     | `getProjectDocument(projectId, docId)`       | —                       |
| DELETE | `/v1/project/{id}/documents/`         | `deleteDocumentsFromProject(projectId, ids)` | Batch delete            |
| GET    | `/v1/project/{id}/documents/download` | `downloadProjectDocument(projectId, docId)`  | Blob                    |
| POST   | `/v1/project/{id}/documents/link`     | `linkDocumentsToProject(projectId, ids)`     | Link existing docs      |
| DELETE | `/v1/documents/`                      | `deleteDocuments(ids)`                       | User-level batch delete |

#### embeddingsApi.ts (50 lines)

| Method | Endpoint                | Function            |
| ------ | ----------------------- | ------------------- |
| POST   | `/v1/embeddings/sync`   | `syncEmbeddings()`  |
| GET    | `/v1/embeddings/status` | `getStatus()`       |
| POST   | `/v1/embeddings/clear`  | `clearEmbeddings()` |

**Types**: `VectorstoreStatus`, `SyncResponse`, `EmbeddingVersion`

#### agentApi.ts (230 lines)

| Method | Endpoint                      | Function                                    | Notes                                          |
| ------ | ----------------------------- | ------------------------------------------- | ---------------------------------------------- |
| POST   | `/v1/graph/start`             | `startGraph(request, callbacks)`            | SSE stream; thread ID via `X-Thread-ID` header |
| POST   | `/v1/graph/resume/{threadId}` | `resumeGraph(threadId, request, callbacks)` | SSE stream to resume                           |

**Types**: `Concept`, `Overview`, `AgentEvent`, `StartGraphRequest`, `ResumeRequest`

#### mcqApi.ts (53 lines)

| Method | Endpoint                 | Function       | Notes                           |
| ------ | ------------------------ | -------------- | ------------------------------- |
| GET    | `/v1/mcqs/`              | `getAll()`     | Try-catch fallback pattern      |
| GET    | `/v1/mcqs/{id}`          | `getById(id)`  | Falls back to `/mcqs/`          |
| GET    | `/v1/mcqs/download/{id}` | `download(id)` | Falls back to `/mcqs/download/` |

#### projectApi.ts (50 lines)

| Method | Endpoint            | Function       |
| ------ | ------------------- | -------------- |
| GET    | `/v1/projects/`     | `getAll()`     |
| POST   | `/v1/projects/`     | `create(data)` |
| GET    | `/v1/projects/{id}` | `getOne(id)`   |
| DELETE | `/v1/projects/{id}` | `remove(id)`   |

**Types**: `ProjectInput`, `ProjectResponse`

#### queryKeys.ts (17 lines)

Centralized TanStack Query key factory:

```ts
queryKeys.documents.all; // ["documents"]
queryKeys.documents.detail(id); // ["documents", id]
queryKeys.chat.all; // ["chats"]
queryKeys.chat.detail(id); // ["chats", id]
queryKeys.chat.messages(id); // ["chats", id, "messages"]
queryKeys.chat.attachments(id); // ["chats", id, "attachments"]
```

---

## 6. Hooks

### Application Hooks (`src/hooks/`)

| Hook                   | File                      | Lines | Purpose                                                                                                                                                      |
| ---------------------- | ------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `useAgentStream`       | `useAgentStream.ts`       | 181   | State machine for agent graph streaming. Phases: `idle → extracting → selecting → processing → complete \| error`. Manages thread ID, overviews, abort refs. |
| `useDocuments`         | `useDocuments.ts`         | 32    | TanStack Query for user doc library. staleTime: 5min, gcTime: 10min. Shared across mentions, data library, attachments.                                      |
| `useUploadDocument`    | `useUploadDocument.ts`    | 35    | TanStack mutation — uploads doc, optimistically prepends to cache.                                                                                           |
| `useDeleteDocuments`   | `useDeleteDocuments.ts`   | 40    | TanStack mutation — deletes docs, optimistically removes from cache.                                                                                         |
| `useDocumentSelection` | `useDocumentSelection.ts` | 37    | Multi-project document selection state. Shape: `{ [projectId]: string[] }`.                                                                                  |
| `useThumbnail`         | `useThumbnail.ts`         | 78    | Fetches thumbnails with global `Map<string, string>` cache. Creates blob URLs.                                                                               |
| `useIsMobile`          | `use-mobile.ts`           | 19    | Responsive breakpoint (768px).                                                                                                                               |

### Mention System Hooks

| Hook                 | File                      | Lines | Purpose                                                                                                                                                                                                                                             |
| -------------------- | ------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `useMentionPicker`   | `use-mention-picker.ts`   | 681   | Complex reducer-based state machine for `@mention` system. Manages trigger detection, dropdown open/close, keyboard navigation, item selection, token rebuild. Supports both `<textarea>` and `contentEditable` via configurable adapter functions. |
| `useEditableHistory` | `use-editable-history.ts` | 140   | Undo/redo stack with coalescing for contentEditable. Captures snapshots of `{ value, selection }`.                                                                                                                                                  |

---

## 7. Type Definitions & Interfaces

### Chat Types (`src/lib/chat-types.ts`)

```ts
interface Citation {
  docId: string;
  docName: string;
  pageNumbers: number[];
  snippet: string;
}
interface ThinkingStep {
  title: string;
  content: string;
  status: "thinking" | "done" | "error";
}
interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  thinkingSteps?: ThinkingStep[];
  timestamp: Date;
}
interface ChatConversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}
```

### API Response Types (from API modules)

```ts
// chatApi.ts
ChatResponse { chat_id, user_id, title, created_at, updated_at }
ChatMessageResponse { message_id, chat_id, role, content, sources?, created_at, updated_at }
ChatMessageEventResponse { event_id, message_id, event_type, payload, ts }
ChatInvokeEvent = { type: "started"|"token"|"done"|"error"|"thinking"|"reasoning_token", ... }

// docApi.ts — uses generic response shape from backend

// embeddingsApi.ts
VectorstoreStatus { status, total_documents, embedded_documents, pending_documents }
EmbeddingVersion { version_id, version_name, project_id, collection_id, version_number, is_active, desc, doc_count, created_at }

// agentApi.ts
Concept { concept_name, concept_description, document_source? }
Overview { doc_id, filename, overview, concepts }
AgentEvent { type, data }
StartGraphRequest { project_id, doc_ids }
ResumeRequest { project_id, selected_concepts, approval }

// projectApi.ts
ProjectInput { project_name, project_desc? }
ProjectResponse { project_id, user_id, project_name, project_desc, created_at, updated_at }
```

### Mention System Types (`mention-types.ts`)

```ts
type Token = TextToken | MentionToken
TextToken { type: "text"; value: string }
MentionToken { type: "mention"; id: string; label: string; triggerChar: string }
MentionItem { id: string; label: string; icon?: ReactNode; description?: string; disabled?: boolean; data?: Record<string, unknown> }
TriggerConfig { char: string; type: string; items?: MentionItem[] }
ActiveTrigger { config: TriggerConfig; query: string; triggerStart: number }
CaretCoords { x: number; y: number; lineHeight: number }
MentionPayload { text: string; mentions: Array<{ id: string; label: string; trigger: string }> }
MentionStatus = "idle" | "loading" | "error"
```

### Prompt Input Types (`prompt-input.tsx`)

```ts
type ChatStatus = "submitted" | "streaming" | "ready" | "error"
type SourceDocumentUIPart { type: "source_document"; sourceDocument: {...} }
type FileUIPart { type: "file"; filename: string; mediaType: string; url: string }
type PromptInputError { code: "accept" | "max_file_size" | "max_files"; message: string }
```

### Embedding Table Schema (`shared/data-table.tsx`)

```ts
// Zod schema
z.object({
  version_id,
  version_name,
  project_id,
  collection_id,
  version_number,
  is_active,
  desc,
  doc_count,
  created_at,
});
```

---

## 8. State Management

### Pattern Summary

| Pattern                           | Where Used                                                                                                                                                                       |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **TanStack Query** (server state) | Documents (useDocuments, useUploadDocument, useDeleteDocuments), chat list (nav-main), project name (App.tsx breadcrumb), MCQ stats (section-cards)                              |
| **React Context**                 | Auth (`AuthProvider`), Theme (`ThemeProvider`), Sidebar (`SidebarProvider`), MentionPicker (`MentionProvider`), PromptInput (attachments + referenced sources contexts)          |
| **useReducer**                    | Mention picker state machine (use-mention-picker.ts)                                                                                                                             |
| **useState (local)**              | Chat page (messages, streaming state, thinking steps), Projects page (project list, search), Data Library (view mode, search, selected), Vector Store (status, syncing, polling) |
| **sessionStorage**                | Vector Store sync state persistence across navigation                                                                                                                            |
| **localStorage**                  | Auth token (`access_token`)                                                                                                                                                      |
| **Global module-level**           | Thumbnail cache (`Map<string, string>` in useThumbnail.ts)                                                                                                                       |

### Data Flow Patterns

1. **Chat page**: Creates chat via `chatApi.create()` on first message → persists messages → SSE stream for AI response → rebuilds thinking steps from replay events on page load
2. **Document upload**: `useUploadDocument` mutation → optimistic cache update → backend processes
3. **Mention system**: ContentEditable input → trigger detection → dropdown → token insertion → `serialize()` for wire format `[mention:@:Label:id]` → `toApiPayload()` for structured JSON
4. **Agent graph**: `useAgentStream` → SSE stream → phase transitions (extracting → selecting → processing → complete) → concepts extracted from documents

---

## 9. Component Inventory

### Layout Components

| Component       | File                         | Lines | Used By                                                                                     |
| --------------- | ---------------------------- | ----- | ------------------------------------------------------------------------------------------- |
| `AppSidebar`    | `layouts/app-sidebar.tsx`    | 161   | `App.tsx` — main sidebar with nav sections, logo, user footer                               |
| `NavMain`       | `layouts/nav-main.tsx`       | 139   | `AppSidebar` — main nav items + "New Chat" button + recent chats (fetches `chatApi.list()`) |
| `NavDocuments`  | `layouts/nav-documents.tsx`  | 100   | `AppSidebar` — document nav (non-functional dropdown actions)                               |
| `NavUser`       | `layouts/nav-user.tsx`       | 156   | `AppSidebar` — user dropdown with logout confirmation                                       |
| `NavSecondary`  | `layouts/nav-secondary.tsx`  | 60    | `AppSidebar` — secondary nav (settings, help) with active-route detection                   |
| `SiteHeader`    | `layouts/site-header.tsx`    | 55    | `App.tsx` — dynamic breadcrumb + sidebar trigger                                            |
| `ThemeProvider` | `layouts/theme-provider.tsx` | 13    | `main.tsx` — wraps `next-themes/ThemeProvider`                                              |

### Chat Components {#chat}

| Component     | File                    | Lines | Purpose                                                                                                                                                                                                                              |
| ------------- | ----------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ChatPage`    | `chat/chat-page.tsx`    | 660   | Main chat interface. Creates chats on first send, loads history with thinking step reconstruction, SSE streaming, mention system integration, drag-drop file upload. Core fn: `eventsToThinkingSteps()`.                             |
| `ChatMessage` | `chat/chat-message.tsx` | 400   | Renders user/assistant messages. Custom markdown renderer (headings, code blocks w/ copy button, lists, bold, inline code). Citation rendering via `InlineCitation`. `ChainOfThought` collapsible. Mention chip rendering via regex. |

### AI Element Components

| Component                           | File                               | Lines | Purpose                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ----------------------------------- | ---------------------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PromptInput` (+ 25 sub-components) | `ai-elements/prompt-input.tsx`     | 1342  | Complex chat input with provider pattern. Manages file attachments (upload/drag-drop/paste), referenced sources, blob→dataURL conversion. Exports: `PromptInput`, `PromptInputBody`, `PromptInputTextarea`, `PromptInputHeader`, `PromptInputFooter`, `PromptInputTools`, `PromptInputButton`, `PromptInputSubmit`, `PromptInputActionMenu*`, `PromptInputSelect*`, `PromptInputHoverCard*`, `PromptInputCommand*`, `PromptInputTab*`. |
| `Conversation`                      | `ai-elements/conversation.tsx`     | 160   | Auto-scroll container via `use-stick-to-bottom`. Empty state, scroll-to-bottom button, download-as-markdown.                                                                                                                                                                                                                                                                                                                           |
| `ChainOfThought`                    | `ai-elements/chain-of-thought.tsx` | 250   | Collapsible thinking steps with animated status icons (thinking spinner, done check, error X).                                                                                                                                                                                                                                                                                                                                         |
| `InlineCitation`                    | `ai-elements/inline-citation.tsx`  | 290   | Hover card + embla-carousel citation system for showing source document snippets inline.                                                                                                                                                                                                                                                                                                                                               |

### Mention System (11 files, ~2500 lines total)

| Component/Module             | File      | Lines | Purpose                                                                                                                                                                                                     |
| ---------------------------- | --------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `mention-types.ts`           | Types     | 60    | Token, MentionItem, TriggerConfig, ActiveTrigger, CaretCoords, MentionPayload, MentionStatus                                                                                                                |
| `mention-utils.ts`           | Utilities | 436   | Wire format `[mention:@:Label:id]`, parse/serialize, trigger detection, caret coordinate calculation (mirror-div technique for textarea, Range API for contentEditable), token insertion/rebuild helpers    |
| `use-mention-picker.ts`      | Hook      | 681   | Reducer-based state machine. Actions: INPUT_CHANGE, INSERT_MENTION, CLOSE_DROPDOWN, MOVE_INDEX, SET_TOKENS, SET_ACTIVE_INDEX. Supports textarea and contentEditable via adapter functions.                  |
| `mention-picker.tsx`         | Provider  | 87    | Context provider wrapping `useMentionPicker`. Supports external picker mode (lifting state to parent).                                                                                                      |
| `mention-dropdown.tsx`       | UI        | 175   | Portal-based floating dropdown positioned above input using caret coords. Keyboard navigation integrated.                                                                                                   |
| `mention-input-editable.tsx` | Input     | 471   | ContentEditable-based rich input. Renders `MentionChip` React components inside editable div using `createRoot()`. Undo/redo via `useEditableHistory`. Handles paste (plain text), cut, composition events. |
| `mention-input.tsx`          | Input     | 93    | Standard textarea-based mention input (alternative to editable).                                                                                                                                            |
| `mention-chip.tsx`           | UI        | 87    | Badge-styled mention chip. Remove button commented out.                                                                                                                                                     |
| `mention-item.tsx`           | UI        | 57    | Memoized dropdown row.                                                                                                                                                                                      |
| `use-editable-history.ts`    | Hook      | 140   | Undo/redo stack with coalescing for contentEditable.                                                                                                                                                        |
| `index.ts`                   | Barrel    | —     | Public re-exports.                                                                                                                                                                                          |

### Project Components

| Component             | File                               | Lines | Purpose                                                                                              |
| --------------------- | ---------------------------------- | ----- | ---------------------------------------------------------------------------------------------------- |
| `Projects`            | `projects/projects.tsx`            | 466   | Project list with card grid, search, create/delete. Uses `projectApi` directly (not TanStack Query). |
| `ProjectDetailPage`   | `projects/ProjectDetailPage.tsx`   | 95    | Route wrapper — fetches project by ID, loading/error states.                                         |
| `ProjectDetail`       | `projects/ProjectDetail.tsx`       | 162   | Tabbed project view: Documents / Generate / Review. Tab navigation buttons.                          |
| `CreateProjectDialog` | `projects/CreateProjectDialog.tsx` | 191   | Zod-validated dialog for project creation. Uses react-hook-form.                                     |

### Document Components

| Component            | File                                    | Lines | Purpose                                                                                                                                |
| -------------------- | --------------------------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `DocumentsTab`       | `documents/DocumentsTab.tsx`            | 778   | Project-level document management — upload, delete, link-from-library dialog, download, grid/list views. Duplicates DataLibrary logic. |
| `DocumentGrid`       | `documents/document-grid.tsx`           | 131   | Grid view with thumbnails, context menus, checkboxes.                                                                                  |
| `columns`            | `documents/documents-table-columns.tsx` | 175   | TanStack Table column definitions.                                                                                                     |
| `DocumentsDataTable` | `documents/documents-data-table.tsx`    | 200   | Generic data table for documents.                                                                                                      |
| `DocumentPreview`    | `documents/DocumentPreview.tsx`         | 45    | Badge display of selected documents.                                                                                                   |
| `ThumbnailImage`     | `documents/ThumbnailImage.tsx`          | 67    | Memoized thumbnail using `useThumbnail`.                                                                                               |
| `ScrollingFileName`  | `documents/ScrollingFileName.tsx`       | 65    | Marquee on hover for long filenames.                                                                                                   |

### Generation Components

| Component         | File                             | Lines | Purpose                                                                                                      |
| ----------------- | -------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------ |
| `GenerateTab`     | `generation/GenerateTab.tsx`     | 300   | MCQ generation workflow using `useAgentStream`. Phases: idle→extracting→selecting→processing→complete→error. |
| `ConceptSelector` | `generation/ConceptSelector.tsx` | 155   | Toggle-button concept selection grouped by document. Select all / clear.                                     |
| `ReviewTab`       | `generation/ReviewTab.tsx`       | 12    | Placeholder.                                                                                                 |

### Dashboard Components

| Component              | File                                   | Lines | Purpose                                                                       |
| ---------------------- | -------------------------------------- | ----- | ----------------------------------------------------------------------------- |
| `Dashboard`            | `dashboard/dashboard.tsx`              | 12    | Composes `SectionCards` + `ChartAreaInteractive`.                             |
| `SectionCards`         | `dashboard/section-cards.tsx`          | 201   | 4 MCQ stat cards. Fetches from `mcqApi.getAll()`.                             |
| `ChartAreaInteractive` | `dashboard/chart-area-interactive.tsx` | 300   | Recharts area chart with date filter tabs. Hardcoded demo data.               |
| `DataCard`             | `dashboard/data-card.tsx`              | 83    | Reusable stat card with status variants (idle/syncing/success/error/warning). |

### Embeddings Components

| Component         | File                              | Lines | Purpose                                            |
| ----------------- | --------------------------------- | ----- | -------------------------------------------------- |
| `columns`         | `embeddings/columns.tsx`          | 140   | TanStack Table column defs for embedding versions. |
| `EmbeddingsTable` | `embeddings/embeddings-table.tsx` | 0     | **EMPTY FILE**                                     |

### Shared Components

| Component         | File                      | Lines | Purpose                                                                                                                                                                 |
| ----------------- | ------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DataTable`       | `shared/data-table.tsx`   | 726   | Full-featured data table with drag-and-drop reordering (dnd-kit), row selection, column visibility toggle, pagination, sorting. Hardcoded to `EmbeddingVersion` schema. |
| `AlertDialogComp` | `shared/alert-dialog.tsx` | 40    | Generic confirmation dialog wrapper. Hardcoded "delete account" text.                                                                                                   |

### Example Components

| Component       | File                                     | Purpose                                      |
| --------------- | ---------------------------------------- | -------------------------------------------- |
| Password Toggle | `examples/input/types/input-types-2.tsx` | Demo component — password visibility toggle. |

### Other

| File                                    | Purpose                                                              |
| --------------------------------------- | -------------------------------------------------------------------- |
| `src/app/dashboard/data.json`           | Static JSON data file (likely chart data)                            |
| `src/lib/mock-chat-data.ts` (125 lines) | Mock conversations/responses — **dead code** (real API is connected) |

---

## 10. Tech Debt & Recommendations

### Critical

| #   | Issue                                                                                                                | File(s)                                  | Impact                                                  |
| --- | -------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------- |
| 1   | **DocumentsTab duplicates DataLibrary** — 778 lines of near-identical logic without TanStack Query hooks             | `DocumentsTab.tsx` vs `data-library.tsx` | Maintenance burden, inconsistent behavior               |
| 2   | **Projects page uses `useEffect` for data fetching** instead of TanStack Query                                       | `projects.tsx`                           | No caching, no optimistic updates, no automatic refetch |
| 3   | **Global thumbnail cache never cleared** — module-level `Map<string, string>` persists across user sessions          | `useThumbnail.ts`                        | Memory leak, potential data leakage between users       |
| 4   | **SSE stream abort controllers** — chat page stores abort ref but cleanup on unmount may race with in-flight streams | `chat-page.tsx`                          | Potential orphaned connections                          |

### Moderate

| #   | Issue                                                                                                                        | File(s)                                                                                                           | Recommendation                                    |
| --- | ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| 5   | `import { User } from "lucide-react"` collides with local `User` type                                                        | `authContext.tsx`                                                                                                 | Remove unused Lucide import                       |
| 6   | `"use client"` directives throughout (Next.js artifact in Vite app)                                                          | `section-cards.tsx`, `chart-area-interactive.tsx`, `nav-secondary.tsx`, `theme-provider.tsx`, `input-types-2.tsx` | Remove — does nothing in Vite                     |
| 7   | `mcqApi` uses try-catch URL fallback pattern (`/v1/mcqs/` → `/mcqs/`)                                                        | `mcqApi.ts`                                                                                                       | Standardize API prefix                            |
| 8   | `docApi` has duplicate `deleteDocuments()` and `deleteDocumentsFromProject()`                                                | `docApi.ts`                                                                                                       | Consolidate                                       |
| 9   | `embeddings-table.tsx` is an empty file                                                                                      | `embeddings-table.tsx`                                                                                            | Remove or implement                               |
| 10  | `shared/data-table.tsx` is hardcoded to `EmbeddingVersion` schema                                                            | `data-table.tsx`                                                                                                  | Genericize with type parameter                    |
| 11  | `shared/alert-dialog.tsx` has hardcoded "delete account" copy                                                                | `alert-dialog.tsx`                                                                                                | Make configurable                                 |
| 12  | `App.css` is unused Vite template CSS                                                                                        | `App.css`                                                                                                         | Delete                                            |
| 13  | `mock-chat-data.ts` is dead code                                                                                             | `mock-chat-data.ts`                                                                                               | Delete                                            |
| 14  | Google login button is non-functional                                                                                        | `login-form.tsx`                                                                                                  | Implement or remove                               |
| 15  | Sidebar nav actions (Open/Share/Delete on documents) are non-functional                                                      | `nav-documents.tsx`                                                                                               | Implement or remove                               |
| 16  | `CreateProjectDialog` has `Form` imported from `react-router-dom` in import block but actually uses react-hook-form's `Form` | `projects.tsx` + `CreateProjectDialog.tsx`                                                                        | Clean up imports                                  |
| 17  | `MentionChip` `onRemove` click handler is commented out                                                                      | `mention-chip.tsx`                                                                                                | Implement or remove prop                          |
| 18  | Several commented-out routes in `main.tsx`                                                                                   | `main.tsx`                                                                                                        | Clean up or add feature flags                     |
| 19  | `chart-area-interactive.tsx` uses hardcoded demo data                                                                        | `chart-area-interactive.tsx`                                                                                      | Connect to real analytics API                     |
| 20  | `nav-main.tsx` fetches `chatApi.list()` on every route change via `useEffect` on `location`                                  | `nav-main.tsx`                                                                                                    | Use TanStack Query with proper cache invalidation |
| 21  | No error boundary components                                                                                                 | —                                                                                                                 | Add React error boundaries                        |
| 22  | No loading skeletons for most data-fetching pages                                                                            | —                                                                                                                 | Add skeleton states                               |
| 23  | Axios base URL hardcoded to `http://localhost:8000`                                                                          | `authApi.ts`                                                                                                      | Use environment variable                          |

### Architecture Observations

- **Inconsistent data fetching**: Some features use TanStack Query (documents, chat messages), others use raw `useEffect` + `useState` (projects, vector store, nav chats). Should standardize on TanStack Query throughout.
- **No global error handling**: API errors are caught locally per component with `toast.error()`. No centralized error boundary or interceptor-level error handling.
- **Mention system is the most complex feature** (~2,500 lines across 11 files) with its own state machine, token serialization format, contentEditable management, and history system. Well-architected but would benefit from unit tests.
- **File sizes**: Several files exceed 400 lines (`chat-page.tsx`: 660, `DocumentsTab.tsx`: 778, `prompt-input.tsx`: 1342, `use-mention-picker.ts`: 681, `data-library.tsx`: 479). Consider decomposing.
- **No test files** anywhere in the frontend. No test configuration, no test dependencies in package.json.
