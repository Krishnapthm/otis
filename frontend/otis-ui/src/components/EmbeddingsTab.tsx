import { useState, useEffect } from "react";
import { ChevronDown, Loader2, Plus } from "lucide-react";
import type { EmbeddingVersion } from "@/api/embeddingsApi";
import { DataTable } from "./data-table";
import { listEmbeddings, deleteEmbeddings } from "@/api/embeddingsApi";
import { CreateEmbeddingsForm } from "./Embeddings/create-embeddings-form";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface EmbeddingsTabProps {
  selectedDocIds: string[];
  projectId: string;
  onDocIdsChange?: (docIds: string[]) => void;
}

export function EmbeddingsTab({
  selectedDocIds = [],
  projectId,
  onDocIdsChange,
}: EmbeddingsTabProps) {
  const [embeddings, setEmbeddings] = useState<EmbeddingVersion[]>([]);
  const [isOpen, setIsOpen] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    listEmbeddings(projectId).then(setEmbeddings);
  }, [projectId]);

  const handleDelete = async (versionIds: string[]) => {
    await deleteEmbeddings(projectId, versionIds);
    const updated = await listEmbeddings(projectId);
    setEmbeddings(updated);
  };

  const handleCreateStart = () => {
    setIsCreating(true);
    // Auto-collapse to show loading animation
    setIsOpen(true);
  };

  const handleCreateSuccess = async () => {
    setIsCreating(false);

    // Refresh embeddings list
    const updated = await listEmbeddings(projectId);
    setEmbeddings(updated);

    // Clear selected documents if parent provides the handler
    onDocIdsChange?.([]);

    // Keep the form open so user can see the success state
    setIsOpen(true);
  };

  const handleRemoveDoc = (docId: string) => {
    const updated = selectedDocIds.filter((id) => id !== docId);
    onDocIdsChange?.(updated);
  };

  return (
    <div className="space-y-6">
      {/* Create Embeddings Card */}
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <CardTitle className="text-lg flex items-center gap-2">
                  {isCreating ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      Creating Embeddings
                    </>
                  ) : (
                    <>
                      <Plus className="h-5 w-5" />
                      Create New Embeddings
                    </>
                  )}
                </CardTitle>
                <CardDescription>
                  {isCreating
                    ? `Processing ${selectedDocIds.length} document${
                        selectedDocIds.length !== 1 ? "s" : ""
                      }...`
                    : "Generate vector embeddings for your selected documents"}
                </CardDescription>
              </div>
              <CollapsibleTrigger asChild>
                <Button variant="ghost" size="sm" className="w-9 p-0">
                  <ChevronDown
                    className={cn(
                      "h-4 w-4 transition-transform duration-200",
                      !isOpen && "-rotate-90"
                    )}
                  />
                  <span className="sr-only">Toggle</span>
                </Button>
              </CollapsibleTrigger>
            </div>
          </CardHeader>

          <CollapsibleContent>
            <CardContent>
              <CreateEmbeddingsForm
                projectId={projectId}
                selectedDocIds={selectedDocIds}
                onSuccess={handleCreateSuccess}
                onDocRemove={handleRemoveDoc}
                onCreateStart={handleCreateStart}
                isCreating={isCreating}
              />
            </CardContent>
          </CollapsibleContent>
        </Card>
      </Collapsible>

      {/* Embeddings Table */}
      <Card>
        <CardHeader>
          <CardTitle>Embedding Versions</CardTitle>
          <CardDescription>
            Manage and view all embedding versions for this project
          </CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable data={embeddings} onDelete={handleDelete} />
        </CardContent>
      </Card>
    </div>
  );
}
