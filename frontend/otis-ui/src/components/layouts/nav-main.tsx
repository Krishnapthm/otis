"use client";

import { IconCirclePlusFilled, type Icon } from "@tabler/icons-react";

import { useLocation, Link } from "react-router-dom";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { MOCK_CONVERSATIONS } from "@/lib/mock-chat-data";
import { cn } from "@/lib/utils";

type NavItem = {
  title: string;
  url: string;
  icon?: Icon;
};

type NavMainProps = {
  items: NavItem[];
};

export function NavMain({ items }: NavMainProps) {
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
              <Link to="/">
                <IconCirclePlusFilled />
                <span>New Chat</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        <SidebarMenu>
          {items.map((item) => {
            const isActive =
              item.url === "/"
                ? isChatPage
                : location.pathname === item.url ||
                location.pathname.startsWith(item.url + "/");

            return (
              <SidebarMenuItem key={item.title}>
                <SidebarMenuButton
                  asChild
                  tooltip={item.title}
                  isActive={isActive}
                >
                  <Link to={item.url}>
                    {item.icon && <item.icon />}
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>

        {/* Recent Conversations */}
        <SidebarMenu>
          <SidebarGroupLabel>Recent Chats</SidebarGroupLabel>
          {MOCK_CONVERSATIONS.slice(0, 5).map((conv) => {
            const isActive = location.pathname === `/c/${conv.id}`;
            return (
              <SidebarMenuItem key={conv.id}>
                <SidebarMenuButton
                  asChild
                  tooltip={conv.title}
                  isActive={isActive}
                >
                  <Link
                    to={`/c/${conv.id}`}
                    className={cn(
                      "truncate text-sm",
                      isActive ? "font-medium" : ""
                    )}
                  >
                    <span className="truncate">{conv.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
