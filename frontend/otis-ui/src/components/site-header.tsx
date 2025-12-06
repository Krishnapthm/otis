import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import type { JSX } from "react";
import { useNavigate } from "react-router-dom";

interface SiteHeaderProps {
  title: string; // breadcrumb-capable
  icon?: JSX.Element; // loader, spinner, etc.
}

export function SiteHeader({ title, icon }: SiteHeaderProps) {
  const navigate = useNavigate();

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
        ) : (
          <h1 className="text-base font-medium">{title}</h1>
        )}
      </div>
    </header>
  );
}
