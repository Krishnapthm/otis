import type { ChatMessage as ChatMessageType } from "@/lib/chat-types";
import { cn } from "@/lib/utils";
import {
  BrainIcon,
  FileTextIcon,
  SearchIcon,
  ShieldCheckIcon,
  SparklesIcon,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  ChainOfThought,
  ChainOfThoughtContent,
  ChainOfThoughtHeader,
  ChainOfThoughtStep,
} from "@/components/ai-elements/chain-of-thought";
import {
  InlineCitation,
  InlineCitationCard,
  InlineCitationCardBody,
  InlineCitationCardTrigger,
  InlineCitationCarousel,
  InlineCitationCarouselContent,
  InlineCitationCarouselHeader,
  InlineCitationCarouselIndex,
  InlineCitationCarouselItem,
  InlineCitationCarouselNext,
  InlineCitationCarouselPrev,
  InlineCitationQuote,
  InlineCitationSource,
} from "@/components/ai-elements/inline-citation";
import { MentionChip } from "@/components/features/mention/mention-chip";

// ============================================================================
// Citation Renderer
// ============================================================================

function renderContentWithCitations(message: ChatMessageType) {
  const { content, citations } = message;
  if (!citations?.length) {
    return <MessageMarkdown content={content} />;
  }

  // Split on citation markers like [1], [2], etc.
  const parts = content.split(/(\[\d+\])/);

  return (
    <div className="leading-relaxed">
      {parts.map((part, index) => {
        const match = part.match(/\[(\d+)\]/);
        if (match) {
          const citationNumber = match[1];
          const citation = citations.find((c) => c.number === citationNumber);
          if (citation) {
            return (
              <InlineCitation key={index}>
                <InlineCitationCard>
                  <InlineCitationCardTrigger sources={[citation.url]} />
                  <InlineCitationCardBody>
                    <InlineCitationCarousel>
                      <InlineCitationCarouselHeader>
                        <InlineCitationCarouselPrev />
                        <InlineCitationCarouselNext />
                        <InlineCitationCarouselIndex />
                      </InlineCitationCarouselHeader>
                      <InlineCitationCarouselContent>
                        <InlineCitationCarouselItem>
                          <InlineCitationSource
                            title={citation.title}
                            url={citation.url}
                            description={citation.description}
                          />
                          {citation.quote && (
                            <InlineCitationQuote>
                              {citation.quote}
                            </InlineCitationQuote>
                          )}
                        </InlineCitationCarouselItem>
                      </InlineCitationCarouselContent>
                    </InlineCitationCarousel>
                  </InlineCitationCardBody>
                </InlineCitationCard>
              </InlineCitation>
            );
          }
        }
        // Render plain text with basic markdown support
        return <MessageMarkdown key={index} content={part} />;
      })}
    </div>
  );
}

// ============================================================================
// Basic Markdown Renderer
// ============================================================================

function MessageMarkdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let inCodeBlock = false;
  let codeContent: string[] = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block toggle
    if (line.startsWith("```")) {
      if (inCodeBlock) {
        elements.push(
          <pre
            key={`code-${i}`}
            className="my-2 overflow-x-auto rounded-lg bg-muted p-3 text-sm"
          >
            <code className="text-foreground">{codeContent.join("\n")}</code>
          </pre>,
        );
        codeContent = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeContent.push(line);
      continue;
    }

    // Headings
    if (line.startsWith("### ")) {
      elements.push(
        <h3 key={i} className="mt-3 mb-1 text-sm font-semibold">
          {line.slice(4)}
        </h3>,
      );
      continue;
    }
    if (line.startsWith("## ")) {
      elements.push(
        <h2 key={i} className="mt-3 mb-1 text-base font-semibold">
          {line.slice(3)}
        </h2>,
      );
      continue;
    }

    // List items
    if (/^(\d+\.\s|- )/.test(line)) {
      elements.push(
        <div key={i} className="ml-4 flex gap-2 text-sm">
          <span className="shrink-0 text-muted-foreground">
            {line.match(/^(\d+\.|- )/)?.[0]}
          </span>
          <span>
            {renderInlineFormatting(line.replace(/^(\d+\.\s|- )/, ""))}
          </span>
        </div>,
      );
      continue;
    }

    // Empty line
    if (line.trim() === "") {
      elements.push(<div key={i} className="h-2" />);
      continue;
    }

    // Normal paragraph
    elements.push(
      <p key={i} className="text-sm">
        {renderInlineFormatting(line)}
      </p>,
    );
  }

  return <>{elements}</>;
}

/** Handles **bold** and `code` inline */
function renderInlineFormatting(text: string): React.ReactNode {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={i}
          className="rounded bg-muted px-1 py-0.5 text-xs font-mono"
        >
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

// ============================================================================
// Chat Message Component
// ============================================================================

const MESSAGE_MENTION_REGEX = /\[mention:\s*([^\]]+?)\]/g;

function renderMessageMentions(content: string): React.ReactNode {
  const parts: React.ReactNode[] = [];
  let lastIndex = 0;

  for (const match of content.matchAll(MESSAGE_MENTION_REGEX)) {
    const fullMatch = match[0];
    const label = (match[1] ?? "").trim();
    const start = match.index ?? 0;

    if (start > lastIndex) {
      parts.push(content.slice(lastIndex, start));
    }

    parts.push(
      <MentionChip
        key={`mention-${start}-${label}`}
        label={label}
        className="mx-0.5 align-middle"
        variant="chat"
      />,
    );

    lastIndex = start + fullMatch.length;
  }

  if (lastIndex < content.length) {
    parts.push(content.slice(lastIndex));
  }

  if (parts.length === 0) {
    return content;
  }

  return parts;
}

interface ChatMessageProps {
  message: ChatMessageType;
}

/** Map step labels to contextual icons for the ChainOfThought UI. */
function getStepIcon(label: string): LucideIcon | undefined {
  const l = label.toLowerCase();
  if (l.includes("search") || l.includes("retriev")) return SearchIcon;
  if (l.includes("read") || l.includes("fetch") || l.includes("document"))
    return FileTextIcon;
  if (l.includes("draft") || l.includes("generat") || l.includes("think"))
    return SparklesIcon;
  if (l.includes("check") || l.includes("guard")) return ShieldCheckIcon;
  if (l.includes("figur") || l.includes("quer") || l.includes("build"))
    return BrainIcon;
  return undefined;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const hasThinking =
    !isUser && message.thinking && message.thinking.length > 0;
  const isStreaming = message.isStreaming ?? false;
  const hideMessageBubble = isStreaming && !message.content;

  return (
    <div
      className={cn(
        "flex gap-3 max-w-3xl w-full",
        isUser ? "ml-auto flex-row-reverse" : "",
      )}
    >
      {/* Content */}
      <div
        className={cn(
          "flex-1 space-y-2 overflow-hidden",
          isUser ? "text-right" : "",
        )}
      >
        {/* Chain of Thought for assistant */}
        {hasThinking && (
          <ChainOfThought
            defaultOpen={true}
            open={isStreaming ? true : undefined}
          >
            <ChainOfThoughtHeader>
              {isStreaming ? "Working on it\u2026" : "Thoughts"}
            </ChainOfThoughtHeader>
            <ChainOfThoughtContent>
              {message.thinking!.map((step, idx) => (
                <ChainOfThoughtStep
                  key={step.node ?? idx}
                  label={step.label}
                  description={step.description}
                  status={step.status}
                  icon={getStepIcon(step.label)}
                >
                  {step.reasoningText && (
                    <details className="mt-1">
                      <summary className="text-xs text-muted-foreground cursor-pointer select-none">
                        Show reasoning
                      </summary>
                      <pre className="text-xs text-muted-foreground whitespace-pre-wrap mt-1 max-h-40 overflow-y-auto font-mono">
                        {step.reasoningText}
                      </pre>
                    </details>
                  )}
                </ChainOfThoughtStep>
              ))}
            </ChainOfThoughtContent>
          </ChainOfThought>
        )}

        {/* Message content */}
        {!hideMessageBubble && (
          <div
            className={cn(
              "rounded-2xl px-3 py-2 text-sm",
              isUser ? "inline-block bg-primary text-primary-foreground" : "",
            )}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap wrap-break-word">
                {renderMessageMentions(message.content)}
              </p>
            ) : (
              renderContentWithCitations(message)
            )}
          </div>
        )}
      </div>
    </div>
  );
}
