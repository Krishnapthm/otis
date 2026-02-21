import { useParams, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { projectApi, type ProjectResponse } from "@/api/projectApi";
import ProjectDetail from "@/components/features/projects/ProjectDetail";

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [project, setProject] = useState<ProjectResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProject = async () => {
      if (!projectId) {
        navigate("/projects");
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        const data = await projectApi.getOne(projectId);
        setProject(data);
      } catch (err: any) {
        console.error("Failed to fetch project:", err);

        // Handle different error types
        if (err.response?.status === 404) {
          setError("Project not found");
        } else if (err.response?.status === 403) {
          setError("You don't have permission to view this project");
        } else {
          setError("Failed to load project. Please try again.");
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadProject();
  }, [projectId, navigate]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading project...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !project) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="flex flex-col items-center gap-4 max-w-md text-center">
          <div className="rounded-full bg-destructive/10 p-4">
            <AlertCircle className="h-8 w-8 text-destructive" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl font-semibold">
              {error || "Project not found"}
            </h2>
            <p className="text-sm text-muted-foreground">
              The project you're looking for doesn't exist or you don't have
              access to it.
            </p>
          </div>
          <Button onClick={() => navigate("/projects")} className="mt-4">
            Back to Projects
          </Button>
        </div>
      </div>
    );
  }

  // Success state - render the project detail
  return (
    <div className="flex flex-col h-screen w-full overflow-hidden">
      <ProjectDetail
        projectId={project.project_id}
        projectName={project.project_name}
      />
    </div>
  );
}
