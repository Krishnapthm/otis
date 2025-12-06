import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
  FormDescription,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import {
  Plus,
  Search,
  Calendar,
  User,
  MoreVertical,
  Edit,
  Trash2,
  Share2,
  FolderPlus,
  Command,
  Loader2,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { projectApi, type ProjectResponse } from "../api/projectApi"; // Make sure path is correct
// import { fetchMe } from "./authapi"; // Optional: To compare created_by with current user

export default function Projects() {
  const navigate = useNavigate();

  // State
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filteredProjects, setFilteredProjects] = useState<ProjectResponse[]>(
    []
  );
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  // 1. Fetch Projects on Mount
  useEffect(() => {
    const loadProjects = async () => {
      try {
        setIsLoading(true);
        const data = await projectApi.getAll();
        setProjects(data);
      } catch (error) {
        console.error("Failed to fetch projects:", error);
        // Add toast notification here for error
      } finally {
        setIsLoading(false);
      }
    };
    loadProjects();
  }, []);

  // 2. Search Filtering Logic
  useEffect(() => {
    const filtered = projects.filter(
      (project) =>
        project.project_name
          .toLowerCase()
          .includes(searchQuery.toLowerCase()) ||
        (project.project_desc || "")
          .toLowerCase()
          .includes(searchQuery.toLowerCase())
    );
    setFilteredProjects(filtered);
  }, [searchQuery, projects]);

  // Keyboard Shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        document.getElementById("project-search")?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const formatDate = (dateString: string): string => {
    if (!dateString) return "N/A";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const handleProjectClick = (projectId: string): void => {
    navigate(`/p/${projectId}`);
  };

  // --- API Action Handlers ---

  const handleCreateProjectSubmit = async (values: {
    project_name: string;
    project_desc?: string;
  }) => {
    // API Call
    const newProject = await projectApi.create({
      project_name: values.project_name,
      project_desc: values.project_desc || "",
    });

    // Update State (Prepend new project)
    setProjects((prev) => [newProject, ...prev]);
    setIsCreateDialogOpen(false);
    console.log("Created:", newProject);
  };

  const handleDelete = async (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    // Add a confirmation dialog here in a real app
    if (!confirm("Are you sure you want to delete this project?")) return;

    try {
      await projectApi.delete(projectId);
      setProjects((prev) => prev.filter((p) => p.project_id !== projectId));
    } catch (error) {
      console.error("Failed to delete project:", error);
    }
  };

  // Placeholders for actions not yet in backend
  const handleEdit = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    console.log("Edit not implemented yet", projectId);
  };
  const handleShare = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    console.log("Share not implemented yet", projectId);
  };
  const handleCreateFolder = (e: React.MouseEvent, projectId: string) => {
    e.stopPropagation();
    console.log("Folder not implemented yet", projectId);
  };

  if (isLoading) {
    return (
      <div className="flex h-[50vh] w-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 py-4 md:gap-8 md:py-6 px-4 md:px-6 w-full">
      {/* Search Bar */}
      <div className="flex justify-center w-full">
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            id="project-search"
            type="search"
            placeholder="Search projects..."
            className="pl-10 pr-12"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <kbd className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
            <Command className="h-3 w-3" />
            <span className="text-xs">K</span>
          </kbd>
        </div>
      </div>

      {/* Projects Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full auto-rows-fr">
        {/* Create Project Card */}
        <Card
          className="border-2 border-dashed hover:border-primary transition-colors cursor-pointer group flex flex-col h-full"
          onClick={() => setIsCreateDialogOpen(true)}
        >
          <CardContent className="flex flex-col items-center justify-center flex-1 p-6 min-h-30">
            <div className="rounded-full bg-muted p-4 mb-4 group-hover:bg-primary/10 transition-colors">
              <Plus className="h-8 w-8 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Create New Project</h3>
            <p className="text-sm text-muted-foreground text-center">
              Start a new project and collaborate with your team
            </p>
          </CardContent>
        </Card>

        {/* Existing Project Cards */}
        {filteredProjects.map((project) => (
          <Card
            key={project.project_id}
            className="hover:shadow-lg transition-shadow cursor-pointer flex flex-col h-full"
            onClick={() => {
              handleProjectClick(project.project_id);
            }}
          >
            <CardHeader className="flex-none">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <CardTitle className="line-clamp-1">
                    {project.project_name}
                  </CardTitle>
                  <CardDescription className="line-clamp-2 mt-1.5">
                    {project.project_desc || "No description"}
                  </CardDescription>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger
                    asChild
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 flex-none"
                    >
                      <MoreVertical className="h-4 w-4" />
                      <span className="sr-only">Open menu</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={(e) => handleEdit(e, project.project_id)}
                    >
                      <Edit className="mr-2 h-4 w-4" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={(e) => handleShare(e, project.project_id)}
                    >
                      <Share2 className="mr-2 h-4 w-4" />
                      Share
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={(e) => handleCreateFolder(e, project.project_id)}
                    >
                      <FolderPlus className="mr-2 h-4 w-4" />
                      Create Folder
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={(e) => handleDelete(e, project.project_id)}
                      className="text-destructive focus:text-destructive"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>
            <CardContent className="flex-1">
              <div className="flex flex-col gap-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 flex-none" />
                  <span>Created {formatDate(project.created_at)}</span>
                </div>
                {/* Note: Backend currently returns UUID for created_by. 
                  In a real app, you might want to fetch the User profile or 
                  check if created_by === currentUser.id 
                */}
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 flex-none" />
                  <span
                    className="truncate max-w-[150px]"
                    title={String(project.created_by)}
                  >
                    By {String(project.created_by).slice(0, 8)}...
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* No Results Message */}
      {!isLoading && filteredProjects.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-lg font-medium text-muted-foreground">
            No projects found
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Try adjusting your search or create a new project
          </p>
        </div>
      )}

      {/* Create Project Dialog */}
      <CreateProjectDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        existingProjects={projects}
        onSubmit={handleCreateProjectSubmit}
      />
    </div>
  );
}

// -----------------------------------------------------------------------------
// COMPONENT: CreateProjectDialog
// -----------------------------------------------------------------------------

interface CreateProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  existingProjects: ProjectResponse[];
  onSubmit: (values: {
    project_name: string;
    project_desc?: string;
  }) => Promise<void>;
}

export function CreateProjectDialog({
  open,
  onOpenChange,
  existingProjects,
  onSubmit,
}: CreateProjectDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const formSchema = z.object({
    project_name: z
      .string()
      .min(3, { message: "Project name must be at least 3 characters." })
      .max(50, { message: "Project name cannot exceed 50 characters." })
      .refine(
        (name) =>
          !existingProjects.some(
            (p) => p.project_name.toLowerCase() === name.toLowerCase()
          ),
        {
          message: "A project with this name already exists.",
        }
      ),
    project_desc: z
      .string()
      .max(300, { message: "Description cannot exceed 300 characters." })
      .optional(),
  });

  type FormValues = z.infer<typeof formSchema>;

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      project_name: "",
      project_desc: "",
    },
  });

  useEffect(() => {
    if (open) {
      form.reset();
    }
  }, [open, form]);

  const handleSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } catch (error) {
      console.error("Failed to create project", error);
      // You could set a form error here if the backend returns validation errors
      form.setError("root", {
        message: "Something went wrong. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
          <DialogDescription>
            Enter the details for your new project. Click create when you're
            done.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit(handleSubmit)}
            className="space-y-6"
          >
            <FormField
              control={form.control}
              name="project_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Project Name</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="e.g. Q1 Marketing Campaign"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    This will be the unique display name of your project.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="project_desc"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description (Optional)</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Briefly describe the goals of this project..."
                      className="resize-none h-24"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription className="flex justify-between">
                    <span>Helps your team identify the project purpose.</span>
                    <span
                      className={
                        field.value?.length && field.value.length > 300
                          ? "text-destructive"
                          : ""
                      }
                    >
                      {field.value?.length || 0}/300
                    </span>
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            {form.formState.errors.root && (
              <p className="text-sm font-medium text-destructive">
                {form.formState.errors.root.message}
              </p>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                Create Project
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
