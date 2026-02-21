import type { ProjectResponse } from "@/api/projectApi";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@radix-ui/react-dialog";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Form } from "react-router-dom";
import z from "zod";
import { Button } from "@/components/ui/button";
import { DialogHeader, DialogFooter } from "@/components/ui/dialog";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormDescription,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

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
            (p) => p.project_name.toLowerCase() === name.toLowerCase(),
          ),
        {
          message: "A project with this name already exists.",
        },
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
