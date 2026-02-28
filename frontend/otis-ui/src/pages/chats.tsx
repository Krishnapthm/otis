import { chatApi, type ChatResponse } from "@/api/chatApi";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { IconArrowRight, IconSearch } from "@tabler/icons-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

type ChatsPageProps = {
  embedded?: boolean;
};

export default function ChatsPage({ embedded = false }: ChatsPageProps) {
  const [chats, setChats] = useState<ChatResponse[]>([]);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    chatApi
      .list({ limit: 100, status: "active" })
      .then((data) => {
        if (mounted) {
          setChats(data);
        }
      })
      .catch((error) => {
        console.error("Failed to load chats:", error);
      })
      .finally(() => {
        if (mounted) {
          setIsLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, []);

  const filteredChats = useMemo(() => {
    const search = query.trim().toLowerCase();
    if (!search) return chats;

    return chats.filter((chat) =>
      (chat.title ?? "Untitled chat").toLowerCase().includes(search),
    );
  }, [chats, query]);

  return (
    <div className={embedded ? " backdrop-blur-sm" : "p-4 md:p-6"}>
      <Card className="mx-auto bg-background/75 backdrop-blur-sm w-full max-w-3xl rounded-2xl p-0 ring ring-ring/50 shadow-sm">
        <CardContent className="p-0">
          <div className="p-3 border-b">
            <div className="relative">
              <IconSearch className="text-muted-foreground pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2" />
              <Input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search chats..."
                className="h-9 rounded-lg pl-9"
              />
            </div>
          </div>

          <ScrollArea className="h-80 rounded-b-2xl">
            <div className="p-3">
              {isLoading ? (
                <div className="space-y-2">
                  {Array.from({ length: 8 }).map((_, idx) => (
                    <div
                      key={`chat-skeleton-${idx}`}
                      className="flex items-center justify-between rounded-md border p-3"
                    >
                      <div className="space-y-2">
                        <Skeleton className="h-4 w-48" />
                        <Skeleton className="h-3 w-28" />
                      </div>
                      <Skeleton className="size-4 rounded-sm" />
                    </div>
                  ))}
                </div>
              ) : filteredChats.length ? (
                <div className="space-y-1">
                  {filteredChats.map((chat) => {
                    const title = chat.title ?? "Untitled chat";
                    return (
                      <Link
                        key={chat.chat_id}
                        to={`/c/${chat.chat_id}`}
                        className="hover:bg-accent/60 flex items-center justify-between rounded-md px-3 py-2 transition-colors"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">
                            {title}
                          </p>
                          <p className="text-muted-foreground text-xs">
                            {new Date(chat.updated_at).toLocaleString()}
                          </p>
                        </div>
                        <IconArrowRight className="text-muted-foreground size-4" />
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <div className="text-muted-foreground py-12 text-center text-sm">
                  No chats found.
                </div>
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
