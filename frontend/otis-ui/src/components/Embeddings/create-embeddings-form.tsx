import { useState, useEffect } from "react";
import { X, FileText, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import { createEmbedding } from "@/api/embeddingsApi";
import { getDocument, type Document } from "@/api/docApi";

interface CreateEmbeddingsFormProps {
  projectId: string;
  selectedDocIds: string[];
  onSuccess?: () => void;
  onDocRemove?: (docId: string) => void;
  onCreateStart?: () => void;
  isCreating?: boolean;
}

export function CreateEmbeddingsForm({
  projectId,
  selectedDocIds,
  onSuccess,
  onDocRemove,
  onCreateStart,
  isCreating = false,
}: CreateEmbeddingsFormProps) {
  const [versionName, setVersionName] = useState("");
  const [documents, setDocuments] = useState<Map<string, Document>>(new Map());
  const [loadingDocs, setLoadingDocs] = useState(false);

  // Fetch document details for selected IDs
  useEffect(() => {
    const fetchDocuments = async () => {
      if (selectedDocIds.length === 0) {
        setDocuments(new Map());
        setLoadingDocs(false);
        return;
      }

      setLoadingDocs(true);
      const docMap = new Map<string, Document>();

      try {
        const results = await Promise.allSettled(
          selectedDocIds.map((docId) => getDocument(projectId, docId))
        );

        results.forEach((result, index) => {
          if (result.status === "fulfilled") {
            docMap.set(selectedDocIds[index], result.value);
          } else {
            console.error(
              `Failed to fetch document ${selectedDocIds[index]}:`,
              result.reason
            );
          }
        });

        setDocuments(docMap);
      } catch (error) {
        console.error("Error fetching documents:", error);
        toast.error("Failed to load document details");
      } finally {
        setLoadingDocs(false);
      }
    };

    fetchDocuments();
  }, [selectedDocIds, projectId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!versionName.trim()) {
      toast.error("Please enter a version name");
      return;
    }

    if (selectedDocIds.length === 0) {
      toast.error("Please select at least one document");
      return;
    }

    // Notify parent that we're starting creation
    onCreateStart?.();

    try {
      await createEmbedding(projectId, {
        version_name: versionName.trim(),
        project_id: projectId,
        doc_id: selectedDocIds,
      });

      toast.success(
        `Successfully created embeddings for ${selectedDocIds.length} document${
          selectedDocIds.length > 1 ? "s" : ""
        }`
      );

      setVersionName("");
      onSuccess?.();
    } catch (error: any) {
      toast.error(
        error?.response?.data?.message || "Failed to create embeddings"
      );
      // If creation fails, we need to reset the creating state
      // The parent should handle this via onSuccess with error handling
    }
  };

  const handleRemoveDoc = (docId: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    onDocRemove?.(docId);
  };

  if (isCreating) {
    return (
      <div className="flex flex-col items-center justify-center py-12 space-y-4">
        <div className="relative">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <div className="absolute inset-0 animate-ping">
            <div className="h-12 w-12 rounded-full bg-primary/20" />
          </div>
        </div>
        <div className="text-center space-y-1">
          <p className="text-sm font-medium">Creating embeddings...</p>
          <p className="text-xs text-muted-foreground">
            Processing {selectedDocIds.length} document
            {selectedDocIds.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 justify-center max-w-md">
          {selectedDocIds.map((docId) => {
            const doc = documents.get(docId);
            const displayName =
              doc?.filename || `Document ${docId.slice(0, 8)}`;

            return (
              <Badge
                key={docId}
                variant="outline"
                className="px-2 py-1 text-xs"
              >
                <FileText className="h-3 w-3 mr-1" />
                <span className="max-w-[150px] truncate">{displayName}</span>
              </Badge>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Version Name Input */}
      <div className="space-y-2">
        <Label htmlFor="version-name" className="text-sm font-medium">
          Version Name
        </Label>
        <Input
          id="version-name"
          placeholder="e.g., v1.0, Initial embeddings"
          value={versionName}
          onChange={(e) => setVersionName(e.target.value)}
          className="h-10"
        />
        <p className="text-xs text-muted-foreground">
          A descriptive name for this embedding version
        </p>
      </div>

      {/* Selected Documents */}
      <div className="space-y-2">
        <Label className="text-sm font-medium">
          Selected Documents ({selectedDocIds.length})
        </Label>

        {loadingDocs ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground p-4 border border-dashed rounded-lg">
            <Loader2 className="h-4 w-4 animate-spin" />
            Loading documents...
          </div>
        ) : selectedDocIds.length === 0 ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground p-4 border border-dashed rounded-lg">
            <FileText className="h-4 w-4" />
            No documents selected. Please select documents from the Documents
            tab.
          </div>
        ) : (
          <TooltipProvider>
            <div className="flex flex-wrap gap-2 p-4 border rounded-lg bg-muted/30">
              {selectedDocIds.map((docId) => {
                const doc = documents.get(docId);
                const displayName =
                  doc?.filename || `Document ${docId.slice(0, 8)}`;

                return (
                  <Tooltip key={docId}>
                    <TooltipTrigger asChild>
                      <Badge
                        variant="secondary"
                        className="px-3 py-1.5 text-sm font-normal gap-2 hover:bg-secondary max-w-[200px]"
                      >
                        <FileText className="h-3.5 w-3.5 shrink-0" />
                        <span className="truncate">{displayName}</span>
                        <button
                          type="button"
                          onClick={(e) => handleRemoveDoc(docId, e)}
                          className="ml-1 hover:bg-destructive/10 hover:text-destructive rounded-full p-0.5 transition-colors shrink-0"
                          aria-label={`Remove ${displayName}`}
                        >
                          <X className="h-3.5 w-3.5" />
                        </button>
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent side="top" className="max-w-xs">
                      <p className="font-medium">{displayName}</p>
                      {doc && (
                        <p className="text-xs text-muted-foreground mt-1">
                          {doc.file_type} • {(doc.file_size / 1024).toFixed(1)}{" "}
                          KB
                        </p>
                      )}
                    </TooltipContent>
                  </Tooltip>
                );
              })}
            </div>
          </TooltipProvider>
        )}
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        disabled={selectedDocIds.length === 0 || !versionName.trim()}
        className="w-full h-10"
      >
        <Sparkles className="mr-2 h-4 w-4" />
        Create Embeddings
      </Button>
    </form>
  );
}
