import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import type React from "react";
import { Outlet, useLocation, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { projectApi } from "./api/projectApi";
import { Loader2 } from "lucide-react";
import { Toaster } from "sonner";

function App() {
  const location = useLocation();
  const params = useParams();
  const [projectName, setProjectName] = useState<string | null>(null);
  const [isLoadingProject, setIsLoadingProject] = useState(false);

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
      "/": "Dashboard",
      "/projects": "Projects",
      "/analytics": "Analytics",
    };

    return {
      title: routeToHeader[location.pathname.toLowerCase()] ?? "Dashboard",
      icon: undefined,
    };
  };

  const { title, icon } = getHeaderData();

  return (
    <SidebarProvider
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 72)",
          "--header-height": "calc(var(--spacing) * 12)",
        } as React.CSSProperties
      }
    >
      <AppSidebar variant="inset" />

      <SidebarInset>
        <SiteHeader title={title} icon={icon} />
        <div className="flex flex-1 flex-col min-h-0 ">
          <Outlet />
        </div>
        <Toaster /> /
      </SidebarInset>
    </SidebarProvider>
  );
}

export default App;
