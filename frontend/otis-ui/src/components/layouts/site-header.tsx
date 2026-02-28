import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import { chatApi } from "@/api/chatApi";
import { useCallback, useEffect, useRef, useState, type JSX } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";

interface SiteHeaderProps {
  title: string; // breadcrumb-capable
  icon?: JSX.Element; // loader, spinner, etc.
}

export function SiteHeader({ title, icon }: SiteHeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { chatId } = useParams<{ chatId?: string }>();
  const chatTitleRef = useRef<HTMLHeadingElement>(null);
  const [chatTitle, setChatTitle] = useState<string>("Chat");
  const [savedChatTitle, setSavedChatTitle] = useState<string>("Chat");
  const [isLoadingChatTitle, setIsLoadingChatTitle] = useState(false);
  const [isSavingChatTitle, setIsSavingChatTitle] = useState(false);

  const isChatDetailRoute =
    Boolean(chatId) && location.pathname.startsWith("/c/");

  useEffect(() => {
    if (!isChatDetailRoute || !chatId) {
      setChatTitle("Chat");
      setSavedChatTitle("Chat");
      return;
    }

    let mounted = true;
    setIsLoadingChatTitle(true);

    chatApi
      .get(chatId)
      .then((chat) => {
        if (!mounted) return;
        const resolvedTitle = chat.title?.trim() || "Untitled chat";
        setChatTitle(resolvedTitle);
        setSavedChatTitle(resolvedTitle);
      })
      .catch((error) => {
        if (!mounted) return;
        console.error("Failed to load chat title:", error);
        setChatTitle("Chat");
        setSavedChatTitle("Chat");
      })
      .finally(() => {
        if (mounted) {
          setIsLoadingChatTitle(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [chatId, isChatDetailRoute]);

  const handleChatTitleBlur = useCallback(async () => {
    if (!chatId || !isChatDetailRoute || !chatTitleRef.current) {
      return;
    }

    const nextTitle = chatTitleRef.current.textContent?.trim() || "";
    const fallbackTitle = savedChatTitle || "Untitled chat";

    if (!nextTitle) {
      chatTitleRef.current.textContent = fallbackTitle;
      return;
    }

    if (nextTitle === savedChatTitle) {
      return;
    }

    setIsSavingChatTitle(true);
    try {
      const updated = await chatApi.update(chatId, { title: nextTitle });
      const resolvedTitle = updated.title?.trim() || nextTitle;
      setSavedChatTitle(resolvedTitle);
      setChatTitle(resolvedTitle);
      chatTitleRef.current.textContent = resolvedTitle;
    } catch (error) {
      console.error("Failed to update chat title:", error);
      chatTitleRef.current.textContent = fallbackTitle;
      toast.error("Unable to update chat title");
    } finally {
      setIsSavingChatTitle(false);
    }
  }, [chatId, isChatDetailRoute, savedChatTitle]);

  const isBreadcrumb = title.includes(" / ");
  const [parentPath, currentPage] = isBreadcrumb
    ? title.split(" / ")
    : [null, title];

  return (
    <header className="flex h-(--header-height) shrink-0 items-center gap-2 bg-blend-saturation transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1" />

        <Separator
          orientation="vertical"
          className="mx-2 data-[orientation=vertical]:h-4"
        />

        {/* If icon exists, it takes priority */}
        {icon ? (
          <div className="flex items-center gap-2">{icon}</div>
        ) : isBreadcrumb ? (
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate("/projects")}
              className="text-base font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              {parentPath}
            </button>

            <span className="text-muted-foreground">/</span>

            <h1 className="text-base font-medium">{currentPage}</h1>
          </div>
        ) : isChatDetailRoute ? (
          <h1
            ref={chatTitleRef}
            key={chatId}
            contentEditable={!isLoadingChatTitle && !isSavingChatTitle}
            suppressContentEditableWarning
            role="textbox"
            aria-label="Chat title"
            spellCheck={false}
            onBlur={handleChatTitleBlur}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                event.currentTarget.blur();
              }
            }}
            className={cn(
              "text-base font-medium rounded-[8px] bg-transparent -mx-2 -my-1 px-2 py-1 outline-none transition-colors",
              "hover:bg-background/75 focus-visible:ring-2 focus-visible:ring-ring/75",
              isSavingChatTitle ? "opacity-80" : "",
            )}
          >
            {chatTitle}
          </h1>
        ) : (
          <h1 className="text-base font-medium">{title}</h1>
        )}
      </div>
    </header>
  );
}
