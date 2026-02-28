import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layouts/app-sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { SiteHeader } from "@/components/layouts/site-header";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import type React from "react";
import { Outlet, useLocation, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { projectApi } from "@/api/projectApi";
import { Loader2 } from "lucide-react";
import { Toaster } from "sonner";
import ChatsPage from "@/pages/chats";

function App() {
  const location = useLocation();
  const params = useParams();
  const [projectName, setProjectName] = useState<string | null>(null);
  const [isLoadingProject, setIsLoadingProject] = useState(false);
  const [isChatsOverlayOpen, setIsChatsOverlayOpen] = useState(false);

  useEffect(() => {
    const { projectId } = params;

    if (projectId) {
      setIsLoadingProject(true);
      projectApi
        .getOne(projectId)
        .then((project) => {
          setProjectName(project.project_name);
        })
        .catch((error) => {
          console.error("Failed to fetch project for header:", error);
          setProjectName("Project");
        })
        .finally(() => {
          setIsLoadingProject(false);
        });
    } else {
      setProjectName(null);
    }
  }, [params.projectId]);

  const getHeaderData = () => {
    const { projectId } = params;

    // Project page → dynamic title
    if (projectId) {
      if (isLoadingProject) {
        return {
          title: "Loading",
          icon: <Loader2 className="h-4 w-4 animate-spin" />,
        };
      }

      return {
        title: projectName || "Project",
        icon: undefined,
      };
    }

    // Normal pages
    const routeToHeader: Record<string, string> = {
      "/": "Chat",
      "/dashboard": "Dashboard",
      "/chats": "Chats",
      "/projects": "Projects",
      "/data-library": "Data Library",
      "/mcqs": "MCQs",
      "/vector-store": "Vector Store",
      "/reports": "Reports",
      "/word-assistant": "Word Assistant",
      "/settings": "Settings",
      "/help": "Get Help",
      "/search": "Search",
    };

    // Handle chat routes like /c/:chatId
    if (location.pathname.startsWith("/c/")) {
      return { title: "Chat", icon: undefined };
    }

    return {
      title: routeToHeader[location.pathname.toLowerCase()] ?? "Chat",
      icon: undefined,
    };
  };

  const { title, icon } = getHeaderData();
  const isChatRoute =
    location.pathname === "/" || location.pathname.startsWith("/c/");

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar
        variant="inset"
        isChatsOverlayOpen={isChatsOverlayOpen}
        onOpenChatsOverlay={() => setIsChatsOverlayOpen(true)}
      />

      <SidebarInset className="flex flex-col max-h-screen overflow-hidden">
        <SiteHeader title={title} icon={icon} />
        {isChatRoute ? (
          <div className="flex-1 overflow-hidden">
            <Outlet />
          </div>
        ) : (
          <ScrollArea className="flex-1">
            <Outlet />
          </ScrollArea>
        )}
        <Toaster />
      </SidebarInset>

      <Dialog
        open={isChatsOverlayOpen}
        onOpenChange={(open) => {
          if (!open) {
            setIsChatsOverlayOpen(false);
          }
        }}
      >
        <DialogContent
          className="max-w-3xl border-none bg-transparent p-0 shadow-none"
          overlayClassName="bg-transparent"
          showCloseButton={false}
        >
          <ChatsPage embedded />
        </DialogContent>
      </Dialog>
    </SidebarProvider>
  );
}

export default App;
