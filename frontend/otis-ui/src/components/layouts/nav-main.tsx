"use client";

import { IconCirclePlus, IconTrash, type Icon } from "@tabler/icons-react";

import { useLocation, Link } from "react-router-dom";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import { useEffect, useState, useCallback } from "react";
import { chatApi, type ChatResponse } from "@/api/chatApi";
import { Kbd } from "../ui/kbd";

type NavItem = {
  title: string;
  url: string;
  icon?: Icon;
};

type NavMainProps = {
  items: NavItem[];
  isChatsOverlayOpen?: boolean;
  onOpenChatsOverlay?: () => void;
};

export function NavMain({
  items,
  isChatsOverlayOpen = false,
  onOpenChatsOverlay,
}: NavMainProps) {
  const location = useLocation();

  // Check if we're on a chat page (/ or /c/:id)
  const isChatPage =
    location.pathname === "/" || location.pathname.startsWith("/c/");

  return (
    <SidebarGroup>
      <SidebarGroupContent className="flex flex-col gap-2">
        <SidebarMenu>
          <SidebarMenuItem className="flex items-center gap-2">
            <SidebarMenuButton
              asChild
              variant="outline"
              tooltip="New Chat"
              className="squircle rounded-lg min-w-8"
            >
              <Link to="/" className="flex w-full items-center justify-between">
                <div className="flex flex-row gap-2 items-center">
                  <IconCirclePlus size={16} />
                  <span>New Chat</span>
                </div>
                <Kbd>Ctrl + O</Kbd>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        <SidebarMenu>
          {items.map((item) => {
            const isChatsItem = item.url === "/chats";
            const isActive = isChatsItem
              ? isChatsOverlayOpen ||
                location.pathname === item.url ||
                location.pathname.startsWith(item.url + "/")
              : item.url === "/"
                ? isChatPage
                : location.pathname === item.url ||
                  location.pathname.startsWith(item.url + "/");

            return (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton
                  asChild={!isChatsItem}
                  tooltip={item.title}
                  isActive={isActive}
                  onClick={isChatsItem ? onOpenChatsOverlay : undefined}
                >
                  {isChatsItem ? (
                    <>
                      {item.icon && <item.icon />}
                      <span>{item.title}</span>
                    </>
                  ) : (
                    <Link to={item.url}>
                      {item.icon && <item.icon />}
                      <span>{item.title}</span>
                    </Link>
                  )}
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}

export function RecentChatsSection({
  onOpenChatsOverlay,
}: {
  onOpenChatsOverlay?: () => void;
}) {
  const location = useLocation();
  const [chats, setChats] = useState<ChatResponse[]>([]);

  const loadChats = useCallback(async () => {
    try {
      const data = await chatApi.list({ limit: 20, status: "active" });
      setChats(data);
    } catch (err) {
      console.error("Failed to load chats:", err);
    }
  }, []);

  useEffect(() => {
    loadChats();
  }, [loadChats, location.pathname]);

  const handleDeleteChat = async (e: React.MouseEvent, chatId: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await chatApi.delete(chatId);
      setChats((prev) => prev.filter((c) => c.chat_id !== chatId));
    } catch (err) {
      console.error("Failed to delete chat:", err);
    }
  };

  const visibleChats = chats.slice(0, 10);
  const hasMoreChats = chats.length > 10;

  return (
    <SidebarGroup>
      <SidebarGroupContent className="flex flex-col gap-2">
        <SidebarMenu>
          <SidebarGroupLabel>Recent Chats</SidebarGroupLabel>
          {visibleChats.map((chat) => {
            const isActive = location.pathname === `/c/${chat.chat_id}`;
            const label = chat.title ?? "Untitled chat";

            return (
              <SidebarMenuItem key={chat.chat_id}>
                <SidebarMenuButton asChild tooltip={label} isActive={isActive}>
                  <Link
                    to={`/c/${chat.chat_id}`}
                    className={cn(
                      "truncate text-sm",
                      isActive ? "font-medium" : "",
                    )}
                  >
                    <span className="truncate">{label}</span>
                  </Link>
                </SidebarMenuButton>
                <SidebarMenuAction
                  showOnHover
                  className="data-[state=open]:bg-accent rounded-sm"
                  onClick={(e) => handleDeleteChat(e, chat.chat_id)}
                  title="Delete chat"
                >
                  <IconTrash className="size-3.5" />
                  <span className="sr-only">Delete</span>
                </SidebarMenuAction>
              </SidebarMenuItem>
            );
          })}
          {hasMoreChats ? (
            <SidebarMenuItem>
              <button
                type="button"
                onClick={onOpenChatsOverlay}
                className="text-muted-foreground hover:text-foreground block w-full px-2 py-1 text-center text-sm"
              >
                See more
              </button>
            </SidebarMenuItem>
          ) : null}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
