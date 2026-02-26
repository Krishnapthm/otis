import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  GlobeIcon,
  MessageSquareIcon,
  PaperclipIcon,
  Upload,
} from "lucide-react";
import type {
  ChatMessage as ChatMessageType,
  ThinkingStep,
} from "@/lib/chat-types";
import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  type PromptInputMessage,
  PromptInputSubmit,
  PromptInputTools,
  PromptInputButton,
  PromptInputActionMenu,
  PromptInputActionMenuTrigger,
  PromptInputActionMenuContent,
  PromptInputActionAddAttachments,
} from "@/components/ai-elements/prompt-input";
import { DropdownMenuItem } from "@/components/ui/dropdown-menu";
import { ChatMessage } from "@/components/features/chat/chat-message";
import {
  MentionPicker,
  MentionDropdown,
  MentionInputEditable,
  useMentionPicker,
} from "@/components/features/mention";
import type { Token, TriggerConfig } from "@/components/features/mention";
import { chatApi } from "@/api/chatApi";
import type { ChatMessageEventResponse } from "@/api/chatApi";
import { getAllUserDocuments, type Document } from "@/api/docApi";
import { queryKeys } from "@/api/queryKeys";
import { useDocuments } from "@/hooks/useDocuments";
import { useUploadDocument } from "@/hooks/useUploadDocument";
import { toast } from "sonner";

// ============================================================================
// Helpers
// ============================================================================

/**
 * Reconstruct ThinkingStep[] from persisted events.
 *
 * Replays `thinking` and `reasoning_token` events in seq order to rebuild
 * the same step structure the live SSE stream produces.
 */
function eventsToThinkingSteps(
  events: ChatMessageEventResponse[],
): ThinkingStep[] | undefined {
  const steps: ThinkingStep[] = [];
  const stepByNode = new Map<string, number>(); // node → index in steps[]

  for (const ev of events) {
    if (ev.event_type === "thinking") {
      const meta = (ev.metadata ?? {}) as Record<string, string>;
      const node = meta.node ?? "";
      const evStatus = meta.status ?? "";

      if (evStatus === "started") {
        // Mark all prior active steps as complete
        for (const s of steps) {
          if (s.status === "active") s.status = "complete";
        }
        const idx = steps.length;
        steps.push({
          node,
          label: ev.content ?? "",
          status: "active",
        });
        stepByNode.set(node, idx);
      } else if (evStatus === "completed") {
        const idx = stepByNode.get(node);
        if (idx !== undefined && steps[idx]) {
          steps[idx].status = "complete";
          if (meta.detail) steps[idx].description = meta.detail;
        }
      }
    } else if (ev.event_type === "reasoning_token" && ev.content) {
      const meta = (ev.metadata ?? {}) as Record<string, string>;
      const node = meta.node;
      let targetIdx = -1;
      if (node) {
        targetIdx = stepByNode.get(node) ?? -1;
      }
      if (targetIdx === -1) {
        // Fall back to last active step
        for (let i = steps.length - 1; i >= 0; i--) {
          if (steps[i].status === "active") {
            targetIdx = i;
            break;
          }
        }
      }
      if (targetIdx >= 0) {
        steps[targetIdx].reasoningText =
          (steps[targetIdx].reasoningText ?? "") + ev.content;
      }
    }
  }

  // Mark any remaining active steps as complete (message is done)
  for (const s of steps) {
    if (s.status === "active") s.status = "complete";
  }

  return steps.length > 0 ? steps : undefined;
}

function apiMessageToLocal(msg: {
  message_id: string;
  role: string;
  content: string | null;
  created_at: string;
}): ChatMessageType {
  return {
    id: msg.message_id,
    role: msg.role as "user" | "assistant",
    content: msg.content ?? "",
    createdAt: msg.created_at,
  };
}

function buildTokenizedMentionMessage(
  tokens: Token[],
  fallbackText: string,
): string {
  if (tokens.length === 0) {
    return fallbackText;
  }

  return tokens
    .map((token) =>
      token.type === "mention" ? `[mention: ${token.label}]` : token.value,
    )
    .join("");
}

function resolveDocIdsFromNames(
  mentionNames: string[],
  documents: Document[],
): { docIds: string[]; unresolvedNames: string[] } {
  const byFilename = new Map<string, string>();

  for (const document of documents) {
    const normalized = document.filename.trim().toLowerCase();
    if (!byFilename.has(normalized)) {
      byFilename.set(normalized, document.doc_id);
    }
  }

  const dedupedNames = [...new Set(mentionNames.map((name) => name.trim()))];
  const docIds = new Set<string>();
  const unresolvedNames: string[] = [];

  for (const name of dedupedNames) {
    const resolved = byFilename.get(name.toLowerCase());
    if (resolved) {
      docIds.add(resolved);
    } else {
      unresolvedNames.push(name);
    }
  }

  return {
    docIds: [...docIds],
    unresolvedNames,
  };
}

// ============================================================================
// Chat Page
// ============================================================================

export default function ChatPage() {
  const { chatId } = useParams<{ chatId?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  // Track which chatId we last loaded so we don't double-fetch on re-renders
  const loadedChatId = useRef<string | undefined>(undefined);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Documents from TanStack Query cache — shared with data library
  const { documents } = useDocuments();
  const { uploadDocuments, isUploading } = useUploadDocument();

  // Build mention triggers from cached documents
  const mentionTriggers: TriggerConfig[] = useMemo(
    () => [
      {
        char: "@",
        type: "document",
        items: documents.map((doc) => ({
          id: doc.doc_id,
          label: doc.filename,
        })),
      },
    ],
    [documents],
  );

  const picker = useMentionPicker({ triggers: mentionTriggers });

  // --- Document Upload (to backend library) ---
  const handleDocUpload = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;
      try {
        const uploaded = await uploadDocuments(files);
        toast.success(`Uploaded ${uploaded.length} document(s) to library`);
      } catch (error: any) {
        if (error?.response?.status === 409) {
          toast.error("Duplicate document(s) detected");
        } else {
          toast.error("Failed to upload document");
        }
      }
    },
    [uploadDocuments],
  );

  const handleDocFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        handleDocUpload(Array.from(e.target.files));
        e.target.value = "";
      }
    },
    [handleDocUpload],
  );

  // --- Drag and Drop ---
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files);
      handleDocUpload(files);
    },
    [handleDocUpload],
  );

  // Load messages whenever chatId changes
  useEffect(() => {
    if (!chatId) {
      setMessages([]);
      loadedChatId.current = undefined;
      return;
    }

    if (loadedChatId.current === chatId) return;
    loadedChatId.current = chatId;

    setIsLoadingMessages(true);
    chatApi.messages
      .list(chatId, { limit: 200 })
      .then(async (apiMessages) => {
        const localMessages = apiMessages.map(apiMessageToLocal);

        // Fetch events for completed assistant messages to restore thinking blocks
        const assistantMsgs = apiMessages.filter(
          (m) => m.role === "assistant" && m.status === "completed",
        );

        if (assistantMsgs.length > 0) {
          const eventResults = await Promise.allSettled(
            assistantMsgs.map((m) =>
              chatApi.messages.replayEvents(chatId, m.message_id),
            ),
          );

          const thinkingByMsgId = new Map<string, ThinkingStep[]>();

          for (let i = 0; i < assistantMsgs.length; i++) {
            const result = eventResults[i];
            if (
              result.status === "fulfilled" &&
              result.value.events.length > 0
            ) {
              const steps = eventsToThinkingSteps(result.value.events);
              if (steps) {
                thinkingByMsgId.set(assistantMsgs[i].message_id, steps);
              }
            }
          }

          // Attach thinking steps to the corresponding messages
          if (thinkingByMsgId.size > 0) {
            for (const msg of localMessages) {
              const steps = thinkingByMsgId.get(msg.id);
              if (steps) {
                msg.thinking = steps;
              }
            }
          }
        }

        setMessages(localMessages);
      })
      .catch((err) => {
        console.error("Failed to load chat messages:", err);
      })
      .finally(() => {
        setIsLoadingMessages(false);
      });
  }, [chatId]);

  const handleSubmit = useCallback(
    async (message: PromptInputMessage) => {
      const text = message.text ?? "";
      if (!text.trim()) return;

      let resolvedChatId = chatId;
      if (!resolvedChatId) {
        const created = await chatApi.create({
          title: text.slice(0, 80),
        });
        resolvedChatId = created.chat_id;
        loadedChatId.current = resolvedChatId;
        navigate(`/c/${resolvedChatId}`);
      }

      const mentionPayload = picker.getApiPayload();
      const mentionIds = mentionPayload.mentions
        .map((mention) => mention.id?.trim())
        .filter((value): value is string => Boolean(value));
      const mentionNames = mentionPayload.mentions.map(
        (mention) => mention.label,
      );
      const tokenizedText = buildTokenizedMentionMessage(picker.tokens, text);

      let docsForResolution =
        queryClient.getQueryData<Document[]>(queryKeys.documents.all) ??
        documents;

      let docIds = [...new Set(mentionIds)];
      let unresolvedNames: string[] = [];

      if (docIds.length === 0 && mentionNames.length > 0) {
        ({ docIds, unresolvedNames } = resolveDocIdsFromNames(
          mentionNames,
          docsForResolution,
        ));
      }

      if (docIds.length === 0 && unresolvedNames.length > 0) {
        docsForResolution = await queryClient.fetchQuery({
          queryKey: queryKeys.documents.all,
          queryFn: getAllUserDocuments,
          staleTime: 5 * 60 * 1000,
        });

        ({ docIds, unresolvedNames } = resolveDocIdsFromNames(
          mentionNames,
          docsForResolution,
        ));
      }

      if (unresolvedNames.length > 0) {
        console.warn("Unresolved mention names", unresolvedNames);
      }

      const payload = {
        message: tokenizedText,
        doc_ids: docIds,
        mentions: mentionPayload.mentions,
      };

      console.log("Resolved chat payload", payload);

      // Optimistically show the user message
      const optimisticUserMsg: ChatMessageType = {
        id: `optimistic-user-${Date.now()}`,
        role: "user",
        content: tokenizedText,
        createdAt: new Date().toISOString(),
      };
      const optimisticAssistantId = `optimistic-assistant-${Date.now()}`;
      const optimisticAssistantMsg: ChatMessageType = {
        id: optimisticAssistantId,
        role: "assistant",
        content: "",
        createdAt: new Date().toISOString(),
        isStreaming: true,
        thinking: [],
      };

      setMessages((prev) => [
        ...prev,
        optimisticUserMsg,
        optimisticAssistantMsg,
      ]);
      picker.reset();

      try {
        await chatApi.messages.stream(
          resolvedChatId,
          payload.message,
          {
            onThinking: (event) => {
              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.id !== optimisticAssistantId) return msg;
                  const steps = [...(msg.thinking ?? [])];

                  if (event.status === "started") {
                    // Mark all prior steps as complete
                    const updated = steps.map((s) =>
                      s.status === "active"
                        ? { ...s, status: "complete" as const }
                        : s,
                    );
                    // Add the new active step
                    updated.push({
                      node: event.node,
                      label: event.label,
                      status: "active" as const,
                    });
                    return { ...msg, thinking: updated };
                  }

                  if (event.status === "completed") {
                    const updated = steps.map((s) =>
                      s.node === event.node
                        ? {
                            ...s,
                            status: "complete" as const,
                            description: event.detail ?? s.description,
                          }
                        : s,
                    );
                    return { ...msg, thinking: updated };
                  }

                  return msg;
                }),
              );
            },
            onReasoningToken: (event) => {
              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.id !== optimisticAssistantId) return msg;
                  const steps = [...(msg.thinking ?? [])];
                  // Find the matching active step, or the last active step
                  let targetIdx = -1;
                  if (event.node) {
                    targetIdx = steps.findIndex(
                      (s) => s.node === event.node && s.status === "active",
                    );
                  } else {
                    for (let i = steps.length - 1; i >= 0; i--) {
                      if (steps[i].status === "active") {
                        targetIdx = i;
                        break;
                      }
                    }
                  }

                  if (targetIdx === -1) return msg;

                  const updated = [...steps];
                  updated[targetIdx] = {
                    ...updated[targetIdx],
                    reasoningText:
                      (updated[targetIdx].reasoningText ?? "") + event.content,
                  };
                  return { ...msg, thinking: updated };
                }),
              );
            },
            onToken: (chunk) => {
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === optimisticAssistantId
                    ? { ...msg, content: `${msg.content}${chunk}` }
                    : msg,
                ),
              );
            },
            onDone: (assistantMessage) => {
              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.id !== optimisticAssistantId) return msg;
                  const finalMsg = apiMessageToLocal(assistantMessage);
                  // Preserve thinking steps, mark all complete
                  const completedSteps = (msg.thinking ?? []).map((s) => ({
                    ...s,
                    status: "complete" as const,
                  }));
                  return {
                    ...finalMsg,
                    thinking:
                      completedSteps.length > 0 ? completedSteps : undefined,
                    isStreaming: false,
                  };
                }),
              );
            },
            onError: (error) => {
              toast.error(error || "Chat stream failed");
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === optimisticAssistantId
                    ? { ...msg, isStreaming: false }
                    : msg,
                ),
              );
            },
          },
          payload.doc_ids,
          payload.mentions,
        );
      } catch (error) {
        toast.error(
          error instanceof Error ? error.message : "Chat invoke failed",
        );
        setMessages((prev) =>
          prev.filter((msg) => msg.id !== optimisticAssistantId),
        );
      }
    },
    [chatId, documents, navigate, picker, queryClient],
  );

  return (
    <div
      className="flex flex-col h-full relative"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Hidden file input for document upload */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleDocFileInput}
        accept=".pdf,.txt,.doc,.docx,.md"
      />

      <Conversation className="flex-1">
        <ConversationContent className="mx-auto w-full max-w-2xl">
          {isLoadingMessages ? (
            <ConversationEmptyState
              title="Loading conversation…"
              description=""
            />
          ) : messages.length === 0 ? (
            <ConversationEmptyState
              title="What can I help you with?"
              description="Ask me anything about your projects, documents, or data."
              icon={
                <MessageSquareIcon className="size-10 text-muted-foreground/40" />
              }
            />
          ) : (
            messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      {/* Input area */}
      <div className="px-3 py-2">
        <div className="mx-auto w-full max-w-2xl">
          <MentionPicker externalPicker={picker}>
            <MentionDropdown />
            <PromptInput onSubmit={handleSubmit} className="px-4">
              <PromptInputBody className="">
                <MentionInputEditable className="px-4 min-h-9 text-sm " />
              </PromptInputBody>

              <PromptInputFooter>
                <PromptInputTools>
                  <PromptInputActionMenu>
                    <PromptInputActionMenuTrigger
                      tooltip={{ content: "Attach files" }}
                    >
                      <PaperclipIcon className="size-4" />
                    </PromptInputActionMenuTrigger>
                    <PromptInputActionMenuContent>
                      <PromptInputActionAddAttachments />
                      <DropdownMenuItem
                        onSelect={(e) => {
                          e.preventDefault();
                          fileInputRef.current?.click();
                        }}
                        disabled={isUploading}
                      >
                        <Upload className="mr-2 size-4" />
                        {isUploading ? "Uploading…" : "Upload to library"}
                      </DropdownMenuItem>
                    </PromptInputActionMenuContent>
                  </PromptInputActionMenu>

                  <PromptInputButton
                    onClick={() => setUseWebSearch(!useWebSearch)}
                    tooltip={{ content: "Search the web" }}
                    variant={useWebSearch ? "default" : "ghost"}
                  >
                    <GlobeIcon className="size-4" />
                    <span>Search</span>
                  </PromptInputButton>
                </PromptInputTools>

                <PromptInputSubmit disabled={!picker.displayValue.trim()} />
              </PromptInputFooter>
            </PromptInput>
          </MentionPicker>
          <p className="mt-1.5 text-center text-[11px] text-muted-foreground">
            Otis may produce inaccurate information. Verify important details.
          </p>
        </div>
      </div>

      {/* Drag overlay for document upload */}
      {isDragging && (
        <div className="absolute inset-0 z-100 flex items-center justify-center border-4 border-dashed border-primary bg-primary/10 pointer-events-none">
          <div className="bg-background p-8 rounded-lg shadow-lg">
            <Upload className="h-16 w-16 text-primary mx-auto mb-4" />
            <p className="text-xl font-semibold">Drop files to upload</p>
          </div>
        </div>
      )}
    </div>
  );
}
