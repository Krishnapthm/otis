import * as React from "react";
import {
  IconDatabase,
  IconFileDescription,
  IconListDetails,
  IconMessage,
  IconSettings,
  IconCloudDataConnection,
} from "@tabler/icons-react";

import { NavMain, RecentChatsSection } from "@/components/layouts/nav-main";
import { NavUser } from "@/components/layouts/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarSeparator,
} from "@/components/ui/sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Link } from "react-router-dom";
import { useAuth } from "@/authContext";

const data = {
  user: {
    name: "shadcn",
    email: "m@example.com",
    avatar: "/avatars/shadcn.jpg",
  },
  navMain: [
    {
      title: "Chats",
      url: "/chats",
      icon: IconMessage,
    },
    {
      title: "Data Library",
      url: "/data-library",
      icon: IconDatabase,
    },
    {
      title: "Projects",
      url: "/projects",
      icon: IconListDetails,
    },
    {
      title: "MCQs",
      url: "/mcqs",
      icon: IconFileDescription,
    },
    {
      title: "Vector Store",
      url: "/vector-store",
      icon: IconCloudDataConnection,
    },
  ],
};
type AppSidebarProps = React.ComponentProps<typeof Sidebar> & {};

export function AppSidebar({
  isChatsOverlayOpen = false,
  onOpenChatsOverlay,
  ...props
}: AppSidebarProps & {
  isChatsOverlayOpen?: boolean;
  onOpenChatsOverlay?: () => void;
}) {
  const { user } = useAuth();
  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="w-24 hover:bg-transparent data-[state=open]:bg-transparent active:bg-transparent"
            >
              <Link to="/">
                <img
                  src="/otis-light.svg"
                  alt="Otis"
                  className="block h-6 w-auto dark:hidden"
                />
                <img
                  src="/otis-dark.svg"
                  alt="Otis"
                  className="hidden h-6 w-auto dark:block"
                />
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="pr-3">
            <NavMain
              items={data.navMain}
              isChatsOverlayOpen={isChatsOverlayOpen}
              onOpenChatsOverlay={onOpenChatsOverlay}
            />
          </div>

          <ScrollArea className="min-h-0 flex-1">
            <div className="pr-3">
              <RecentChatsSection onOpenChatsOverlay={onOpenChatsOverlay} />
            </div>
          </ScrollArea>
        </div>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <Link to="/settings">
                <IconSettings />
                <span>Settings</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        <SidebarSeparator />
        <NavUser user={user!} />
      </SidebarFooter>
    </Sidebar>
  );
}
