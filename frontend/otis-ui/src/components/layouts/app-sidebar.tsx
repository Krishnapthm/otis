import * as React from "react";
import {
  IconCamera,
  IconChartBar,
  IconDashboard,
  IconDatabase,
  IconFileAi,
  IconFileDescription,
  IconFileWord,
  IconHelp,
  IconInnerShadowTop,
  IconListDetails,
  IconMessage,
  IconReport,
  IconSearch,
  IconSettings,
  IconUsers,
  IconCloudDataConnection,
} from "@tabler/icons-react";

import { NavDocuments } from "@/components/layouts/nav-documents";
import { NavMain } from "@/components/layouts/nav-main";
import { NavSecondary } from "@/components/layouts/nav-secondary";
import { NavUser } from "@/components/layouts/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
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
      title: "Chat",
      url: "/",
      icon: IconMessage,
    },
    {
      title: "Dashboard",
      url: "/dashboard",
      icon: IconDashboard,
    },
    {
      title: "Projects",
      url: "/projects",
      icon: IconListDetails,
    },
    {
      title: "Analytics",
      url: "/analytics",
      icon: IconChartBar,
    },
    {
      title: "Team",
      url: "/team",
      icon: IconUsers,
    },
  ],
  navClouds: [
    {
      title: "Capture",
      icon: IconCamera,
      url: "/capture",
    },
    {
      title: "Proposal",
      icon: IconFileDescription,
      url: "/proposal",
    },
    {
      title: "Prompts",
      icon: IconFileAi,
      url: "/prompts",
    },
  ],
  navSecondary: [
    {
      title: "Vector Store",
      url: "/vector-store",
      icon: IconCloudDataConnection,
    },
    {
      title: "Settings",
      url: "/settings",
      icon: IconSettings,
    },
    {
      title: "Get Help",
      url: "/help",
      icon: IconHelp,
    },
    {
      title: "Search",
      url: "/search",
      icon: IconSearch,
    },
  ],
  documents: [
    {
      name: "Data Library",
      url: "/data-library",
      icon: IconDatabase,
    },
    {
      name: "Reports",
      url: "/reports",
      icon: IconReport,
    },
    {
      name: "Word Assistant",
      url: "/word-assistant",
      icon: IconFileWord,
    },
  ],
};
type AppSidebarProps = React.ComponentProps<typeof Sidebar> & {};

export function AppSidebar({ ...props }: AppSidebarProps) {
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
        <ScrollArea className="h-full">
          <div className="flex flex-col gap-2 pr-3">
            <NavMain items={data.navMain} />
            <NavSecondary items={data.navClouds} />
            <NavDocuments items={data.documents} />
            <NavSecondary items={data.navSecondary} className="mt-auto" />
          </div>
        </ScrollArea>
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={user!} />
      </SidebarFooter>
    </Sidebar>
  );
}
