import { useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { GlobeIcon, MessageSquareIcon, PaperclipIcon } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "@/lib/chat-types";
import {
    generateMockResponse,
    getMockConversation,
    generateChatTitle,
    MOCK_CONVERSATIONS,
} from "@/lib/mock-chat-data";
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
    PromptInputTextarea,
    PromptInputTools,
    PromptInputButton,
    PromptInputActionMenu,
    PromptInputActionMenuTrigger,
    PromptInputActionMenuContent,
    PromptInputActionAddAttachments,
} from "@/components/ai-elements/prompt-input";
import { ChatMessage } from "@/components/features/chat/chat-message";
import {
    MentionPicker,
    MentionDropdown,
    MOCK_DOCUMENTS,
    useMentionPicker,
} from "@/components/features/mention";

// ============================================================================
// Chat Page
// ============================================================================

const MENTION_TRIGGERS = [
    { char: "@", type: "document", items: MOCK_DOCUMENTS },
];

export default function ChatPage() {
    const { chatId } = useParams<{ chatId?: string }>();
    const navigate = useNavigate();

    const existingConversation = chatId ? getMockConversation(chatId) : undefined;

    const [messages, setMessages] = useState<ChatMessageType[]>(
        existingConversation?.messages ?? []
    );
    const [isStreaming, setIsStreaming] = useState(false);
    const [useWebSearch, setUseWebSearch] = useState(false);

    const picker = useMentionPicker({ triggers: MENTION_TRIGGERS });

    const handleSubmit = useCallback(
        (message: PromptInputMessage) => {
            const text = message.text?.trim();
            if (!text) return;

            const userMessage: ChatMessageType = {
                id: `msg-user-${Date.now()}`,
                role: "user",
                content: text,
                createdAt: new Date().toISOString(),
            };

            setMessages((prev) => [...prev, userMessage]);
            picker.reset();
            setIsStreaming(true);

            if (!chatId) {
                const newId = `conv-${Date.now()}`;
                const title = generateChatTitle(text);
                MOCK_CONVERSATIONS.unshift({
                    id: newId,
                    title,
                    updatedAt: new Date().toISOString(),
                    messages: [userMessage],
                });
                navigate(`/c/${newId}`, { replace: true });
            }

            setTimeout(() => {
                const response = generateMockResponse(text);
                setMessages((prev) => [...prev, response]);
                setIsStreaming(false);
            }, 1200);
        },
        [chatId, navigate, picker]
    );

    return (
        <div className="flex flex-col h-full">
            <Conversation className="flex-1">
                <ConversationContent className="mx-auto w-full max-w-2xl">
                    {messages.length === 0 ? (
                        <ConversationEmptyState
                            title="What can I help you with?"
                            description="Ask me anything about your projects, documents, or data."
                            icon={
                                <MessageSquareIcon className="size-10 text-muted-foreground/40" />
                            }
                        />
                    ) : (
                        messages.map((msg) => (
                            <ChatMessage key={msg.id} message={msg} />
                        ))
                    )}
                </ConversationContent>
                <ConversationScrollButton />
            </Conversation>

            {/* Input area */}
            <div className="px-3 py-2">
                <div className="mx-auto w-full max-w-2xl">
                    <MentionPicker externalPicker={picker}>
                        <MentionDropdown />
                        <PromptInput onSubmit={handleSubmit}>
                            <PromptInputBody>
                                <PromptInputTextarea
                                    ref={picker.textareaRef}
                                    value={picker.displayValue}
                                    onChange={picker.handleChange}
                                    onKeyDown={picker.handleKeyDown}
                                    onClick={picker.handleClick}
                                    placeholder="Message Otis… type @ to mention a document"
                                    className="min-h-[2.25rem] text-sm"
                                />
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

                                <PromptInputSubmit
                                    disabled={!picker.displayValue.trim() && !isStreaming}
                                />
                            </PromptInputFooter>
                        </PromptInput>
                    </MentionPicker>
                    <p className="mt-1.5 text-center text-[11px] text-muted-foreground">
                        Otis may produce inaccurate information. Verify important details.
                    </p>
                </div>
            </div>
        </div>
    );
}
