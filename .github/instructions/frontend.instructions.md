---
applyTo: "frontend/**"
---

# Frontend (Vite + React) — canonical patterns

> These rules apply to every file under `frontend/`. They complement the
> cross-cutting rules in `.github/copilot-instructions.md`.

## File naming

| Location                                                | Convention       | Example            |
| ------------------------------------------------------- | ---------------- | ------------------ |
| `components/ui/` (shadcn-installed)                     | `kebab-case.tsx` | `alert-dialog.tsx` |
| `components/features/`, `components/layouts/`, `pages/` | `PascalCase.tsx` | `ChatPage.tsx`     |
| `hooks/`                                                | `camelCase.ts`   | `useDocuments.ts`  |
| `api/`                                                  | `camelCase.ts`   | `chatApi.ts`       |
| `lib/`                                                  | `camelCase.ts`   | `utils.ts`         |

Do not mix conventions within a directory.

## Component exports

Use **named exports** for all components — no default exports.

```tsx
// ✅ correct
export function ChatPage() { ... }

// ❌ wrong
export default function ChatPage() { ... }
```

## Separation of concerns

| Responsibility                    | Location                                            |
| --------------------------------- | --------------------------------------------------- |
| Rendering + local UI state        | Component file                                      |
| Server data fetching & caching    | Custom hook in `src/hooks/` wrapping TanStack Query |
| API calls (HTTP)                  | `src/api/` module                                   |
| Reusable pure functions           | `src/lib/`                                          |
| Cross-cutting state (auth, theme) | React Context in `src/` root                        |

**Never fetch data with `useEffect` + `useState`.** All server state goes
through TanStack Query.

```tsx
// ✅ correct — server state via TanStack Query hook
const { data: chats, isLoading } = useChats();

// ❌ wrong — manual fetch
const [chats, setChats] = useState([]);
useEffect(() => {
  api.get("/chats").then((r) => setChats(r.data));
}, []);
```

## Dependency injection

- **Context** for cross-cutting concerns (auth → `useAuth`, theme)
- **Props** for component-specific dependencies
- Never import a singleton or make an API call directly inside a component —
  always go through a custom hook

## API modules — standalone exports

Each resource has its own module in `src/api/`. All functions are **individually
exported async functions** sharing the single `api` axios instance from
`authApi.ts`. No object-literal namespaces.

```typescript
// ✅ correct — standalone exports in chatApi.ts
import api from "@/api/authApi";

export async function createChat(payload: ChatCreate): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>("/v1/chats/", payload);
  return data;
}

// ❌ wrong — object-literal namespace
export const chatApi = {
  create: async (payload) => api.post("/v1/chats/", payload),
};
```

Query keys must be declared in `src/api/queryKeys.ts` — not inlined in
`useQuery` calls.

## Helpers & utils — DRY

| What                                    | Where                               |
| --------------------------------------- | ----------------------------------- |
| Tailwind class merging                  | `cn()` from `src/lib/utils.ts`      |
| Formatting, validation, data transforms | `src/lib/` module                   |
| Component-specific helpers              | Co-located `ComponentName.utils.ts` |
| Shared custom hooks                     | `src/hooks/`                        |

Never duplicate a pure function across components — extract to `src/lib/`.

## Type safety — zero `any`

- `any` is forbidden. Use `unknown` in catch blocks and narrow before use.
- All API response shapes must have a matching TypeScript interface in the
  API module file.
- Use `import type` for type-only imports (`verbatimModuleSyntax` is enabled).

```typescript
// ✅ correct
} catch (error: unknown) {
  const message = error instanceof Error ? error.message : "Unknown error"
  console.error(message)
}

// ❌ wrong
} catch (error: any) {
  console.error(error.message)
}
```

## Styling

- Tailwind CSS classes only — no CSS modules, no inline `style` objects
- Use `cn()` for conditional / merged class strings
- CVA (`class-variance-authority`) for variant-driven components
- Radix UI primitives + shadcn/ui for all standard UI elements

## Console usage

Only `console.error()` inside catch blocks. Remove all other console calls
before committing.

```typescript
// ✅ allowed
} catch (err: unknown) { console.error("Upload failed:", err) }

// ❌ remove before commit
console.log("Created:", project)
console.warn("Unresolved mention names")
console.debug("debug logger")
```

## On-touch cleanup checklist

When you edit **any** file under `frontend/`, also fix these in that same file:

- [ ] Replace `catch (error: any)` → `catch (error: unknown)` with proper narrowing
      (known instances: `chat-page.tsx` L231, `ProjectDetailPage.tsx` L28,
      `section-cards.tsx` L20, `data-library.tsx` L113, `vector-store.tsx` L121)
- [ ] Remove `"use client"` directives — they are Next.js-only and no-ops in Vite
- [ ] Remove `console.log` / `console.warn` / `console.debug` statements
- [ ] `src/authContext.tsx`: remove dead `import { User } from "lucide-react"`;
      fix typo `"withing"` → `"within"`
- [ ] If converting a page from `useEffect` fetch to TanStack Query, add its query
      key to `src/api/queryKeys.ts` first
- [ ] `src/api/docApi.ts`: delete duplicate `deleteDocumentsFromProject` (identical
      to `deleteDocuments`)
- [ ] If touching an API module that uses object-literal namespace style
      (`chatApi = { ... }`, `mcqApi = { ... }`), convert touched functions to
      standalone exported functions
- [ ] Fix default exports → named exports on any touched component
- [ ] Add JSDoc `/** */` to any touched exported component or hook
