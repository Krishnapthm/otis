import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Item, ItemGroup, ItemHeader, ItemMedia } from "@/components/ui/item";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Upload, Grid3x3, List, FileText, File, Download } from "lucide-react";
import {
  uploadDocuments,
  getAllDocuments,
  deleteDocumentsFromProject,
  downloadDocuments,
  type Document,
} from "@/api/docApi";
import { toast } from "sonner";
import { Separator } from "./ui/separator";
import ScrollingFilename from "./ScrollingFileName";

interface DocumentsTabProps {
  projectId: string;
  onDocumentsChange?: (hasDocuments: boolean) => void;
  onSelectionChange?: (hasSelection: string[]) => void;
  selectedDocIds?: string[]; // ADD THIS - receive selection from parent
}

export function DocumentsTab({
  projectId,
  onDocumentsChange,
  onSelectionChange,
  selectedDocIds = [],
}: DocumentsTabProps) {
  // Data State
  const [documents, setDocuments] = useState<Document[]>([]);
  const selectedDocs = useMemo(() => new Set(selectedDocIds), [selectedDocIds]);

  // UI State
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Delete Dialog State
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [docsToDelete, setDocsToDelete] = useState<Document[]>([]);
  const [isDeleting, setIsDeleting] = useState(false);

  // Ref for the hidden file input
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Effects ---
  useEffect(() => {
    loadDocuments();
  }, [projectId]);

  useEffect(() => {
    onDocumentsChange?.(documents.length > 0);
  }, [documents, onDocumentsChange]);

  // useEffect(() => {
  //   onSelectionChange?.(Array.from(selectedDocs));
  // }, [selectedDocs, onSelectionChange]);

  // --- Data Loading ---
  const loadDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await getAllDocuments(projectId);
      setDocuments(docs);
    } catch (error) {
      toast.error("Failed to load documents");
    } finally {
      setIsLoading(false);
    }
  };

  // --- Selection Logic ---
  const handleSelect = (docId: string, checked: boolean) => {
    const currentSelection = new Set(selectedDocIds);
    if (checked) {
      currentSelection.add(docId);
    } else {
      currentSelection.delete(docId);
    }
    onSelectionChange?.(Array.from(currentSelection));
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = documents.map((d) => d.doc_id);
      onSelectionChange?.(allIds);
    } else {
      onSelectionChange?.([]);
    }
  };

  // const isAllSelected =
  //   documents.length > 0 && selectedDocs.size === documents.length;

  // --- Upload Logic ---
  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async (files: File[]) => {
    if (files.length === 0) return;

    setIsUploading(true);

    const uploadPromise = uploadDocuments(projectId, files);

    toast.promise(uploadPromise, {
      loading: "Uploading documents...",
      success: (uploaded) => {
        setDocuments((prev) => [...prev, ...uploaded]);
        if (fileInputRef.current) fileInputRef.current.value = "";
        return `${files.length} file(s) uploaded successfully`;
      },
      error: "Failed to upload documents",
    });

    try {
      await uploadPromise;
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      handleUpload(files);
    }
  };

  // --- Drag and Drop ---
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files);
      handleUpload(files);
    },
    [projectId]
  );

  const isAllSelected =
    documents.length > 0 && selectedDocs.size === documents.length;

  // --- Delete Logic ---
  const confirmDelete = (docs: Document[]) => {
    setDocsToDelete(docs);
    setDeleteDialogOpen(true);
  };

  const executeDelete = async () => {
    setIsDeleting(true);
    const docIds = docsToDelete.map((d) => d.doc_id);

    const deletePromise = deleteDocumentsFromProject(projectId, docIds);

    toast.promise(deletePromise, {
      loading: "Deleting documents...",
      success: () => {
        // Update documents list
        setDocuments((prev) =>
          prev.filter((doc) => !docIds.includes(doc.doc_id))
        );

        // Update selection through parent - FIXED
        const currentSelection = new Set(selectedDocIds);
        docIds.forEach((id) => currentSelection.delete(id));
        onSelectionChange?.(Array.from(currentSelection));

        setDeleteDialogOpen(false);
        setDocsToDelete([]);
        return `${docIds.length} document(s) deleted successfully`;
      },
      error: "Failed to delete documents",
    });

    try {
      await deletePromise;
    } catch (error) {
      console.error(error);
    } finally {
      setIsDeleting(false);
    }
  };

  // --- Download Logic ---
  const handleDownloadAll = async () => {
    setIsDownloading(true);
    const downloadPromise = downloadDocuments(projectId);

    toast.promise(downloadPromise, {
      loading: "Preparing download...",
      success: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `project-${projectId}-documents.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        return "Documents downloaded successfully";
      },
      error: "Failed to download documents",
    });

    try {
      await downloadPromise;
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDownloadSingle = async (doc: Document) => {
    try {
      const response = await fetch(doc.file_path);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success("Downloaded", {
        description: (
          <ScrollingFilename
            text={doc.filename}
            className="max-w-[260px] text-sm"
          />
        ),
      });
    } catch (error) {
      toast.error("Failed to download document");
    }
  };

  // --- Helpers ---
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (fileType: string, small = false) => {
    const className = small ? "h-5 w-5" : "h-12 w-12";
    if (fileType.includes("pdf")) return <FileText className={className} />;
    return <File className={className} />;
  };

  return (
    <div
      className="h-full flex flex-col"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {/* Hidden Input for Uploads */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={handleFileInput}
        accept=".pdf,.txt,.doc,.docx,.md"
      />

      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <div>
          <h2 className="text-2xl font-semibold">Documents</h2>
          <p className="text-sm text-muted-foreground">
            {documents.length} document(s) uploaded
            {selectedDocs.size > 0 && ` • ${selectedDocs.size} selected`}
          </p>
        </div>

        <div className="flex gap-4 items-center">
          {documents.length > 0 && (
            <div className="flex items-center space-x-2 mr-2">
              <Checkbox
                id="select-all"
                checked={isAllSelected}
                onCheckedChange={(checked) =>
                  handleSelectAll(checked as boolean)
                }
              />
              <Label htmlFor="select-all" className="text-sm cursor-pointer">
                Select All
              </Label>
            </div>
          )}

          <div className="flex gap-2 items-center">
            {selectedDocs.size > 0 && (
              <>
                <Button
                  variant="destructive"
                  size="default"
                  onClick={() => {
                    const docsToDel = documents.filter((d) =>
                      selectedDocs.has(d.doc_id)
                    );
                    confirmDelete(docsToDel);
                  }}
                >
                  Delete ({selectedDocs.size})
                </Button>
                <Button
                  variant="outline"
                  size="default"
                  onClick={handleDownloadAll}
                  disabled={isDownloading}
                >
                  <Download className="h-4 w-4 mr-2" />
                  {isDownloading ? "Downloading..." : "Download Selected"}
                </Button>
              </>
            )}

            <Button
              variant="default"
              size="default"
              onClick={triggerFileUpload}
              disabled={isUploading}
            >
              <Upload className="h-4 w-4 mr-2" />
              {isUploading ? "Uploading..." : "Upload Documents"}
            </Button>

            <ToggleGroup
              type="single"
              value={viewMode}
              onValueChange={(value) =>
                value && setViewMode(value as "grid" | "list")
              }
              variant="outline"
              size="default"
            >
              <ToggleGroupItem value="grid" aria-label="Grid view">
                <Grid3x3 className="h-4 w-4" />
              </ToggleGroupItem>
              <ToggleGroupItem value="list" aria-label="List view">
                <List className="h-4 w-4" />
              </ToggleGroupItem>
            </ToggleGroup>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 mt-4 pb-20">
        {isLoading ? (
          // Skeleton Loading State
          viewMode === "grid" ? (
            <ItemGroup className="grid grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <Item key={i} variant="outline" className="cursor-default">
                  <ItemHeader className="items-center justify-center aspect-square min-w-40 pt-8">
                    <Skeleton className="h-12 w-12 rounded" />
                  </ItemHeader>
                  <div className="flex flex-col gap-3 p-4">
                    <div className="w-full space-y-2">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-3 w-16" />
                    </div>
                  </div>
                </Item>
              ))}
            </ItemGroup>
          ) : (
            <ItemGroup className="flex flex-col gap-1">
              {Array.from({ length: 10 }).map((_, i) => (
                <Item
                  key={i}
                  variant="outline"
                  className="flex-row items-center gap-4 p-3 cursor-default"
                >
                  <Skeleton className="h-4 w-4 rounded shrink-0" />
                  <Skeleton className="h-5 w-5 rounded shrink-0" />
                  <Skeleton className="h-4 flex-1" />
                  <Skeleton className="h-3 w-16 shrink-0" />
                </Item>
              ))}
            </ItemGroup>
          )
        ) : documents.length === 0 ? (
          <div
            className={`flex flex-col items-center justify-center mx-auto mt-16 h-[300px] w-[70%] rounded-lg transition-colors ${
              isDragging
                ? "border-primary bg-primary/5"
                : "border-muted-foreground/25"
            }`}
          >
            <Upload className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">
              Drop files here or click Upload above
            </p>
            <p className="text-sm text-muted-foreground mb-4">
              Supports PDF, DOCX, TXT, MD
            </p>
            <Button
              variant="outline"
              onClick={triggerFileUpload}
              disabled={isUploading}
            >
              Choose Files
            </Button>
          </div>
        ) : viewMode === "grid" ? (
          // Grid View
          <ItemGroup className="grid grid-cols-4 gap-4 ">
            {documents.map((doc) => (
              <ContextMenu key={doc.doc_id}>
                <ContextMenuTrigger>
                  <div className="relative group ">
                    <Item
                      className={`cursor-pointer transition-all  ${
                        selectedDocs.has(doc.doc_id)
                          ? "ring-2 ring-primary bg-primary/5"
                          : "hover:bg-muted/50"
                      }`}
                      variant="outline"
                      onClick={() =>
                        handleSelect(doc.doc_id, !selectedDocs.has(doc.doc_id))
                      }
                    >
                      <div
                        className="absolute top-3 left-3 z-10"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Checkbox
                          checked={selectedDocs.has(doc.doc_id)}
                          onCheckedChange={(checked) =>
                            handleSelect(doc.doc_id, checked as boolean)
                          }
                        />
                      </div>
                      <ItemHeader className="items-center justify-center aspect-square min-w-40 p-0">
                        <ItemMedia className="w-full h-full p-0 m-0">
                          <img
                            src={`http://localhost:8000/v1/project/${projectId}/documents/thumbnail/${doc.doc_id}`}
                            alt={doc.filename}
                            className="w-full h-full object-cover m-0 p-0"
                          />
                        </ItemMedia>
                      </ItemHeader>

                      <div className="flex flex-col gap-3 p-4 min-w-0">
                        <div className="w-full space-y-1">
                          <ScrollingFilename
                            text={doc.filename}
                            className="font-medium text-sm"
                          />
                          <p className="text-xs text-muted-foreground">
                            {formatFileSize(doc.file_size)}
                          </p>
                        </div>
                      </div>
                    </Item>
                  </div>
                </ContextMenuTrigger>
                <ContextMenuContent>
                  <ContextMenuItem
                    onClick={() =>
                      handleSelect(doc.doc_id, !selectedDocs.has(doc.doc_id))
                    }
                  >
                    {selectedDocs.has(doc.doc_id) ? "Deselect" : "Select"}
                  </ContextMenuItem>
                  <ContextMenuItem onClick={() => handleDownloadSingle(doc)}>
                    Download
                  </ContextMenuItem>
                  <ContextMenuItem
                    onClick={() => confirmDelete([doc])}
                    variant="destructive"
                  >
                    Delete
                  </ContextMenuItem>
                </ContextMenuContent>
              </ContextMenu>
            ))}
          </ItemGroup>
        ) : (
          // List View - Sleek and thin like Google Drive
          <ItemGroup className="flex flex-col gap-1">
            {documents.map((doc) => (
              <ContextMenu key={doc.doc_id}>
                <ContextMenuTrigger>
                  <Separator className="mb-1" />
                  <Item
                    className={`flex-row items-center  gap-4 border p-2.5 cursor-pointer transition-all hover:bg-muted/50 ${
                      selectedDocs.has(doc.doc_id)
                        ? "bg-primary/5 border-primary/20"
                        : ""
                    }`}
                    onClick={() =>
                      handleSelect(doc.doc_id, !selectedDocs.has(doc.doc_id))
                    }
                  >
                    <div onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selectedDocs.has(doc.doc_id)}
                        onCheckedChange={(checked) =>
                          handleSelect(doc.doc_id, checked as boolean)
                        }
                        className="shrink-0"
                      />
                    </div>

                    <ItemMedia>
                      <img
                        src={`http://localhost:8000/v1/project/${projectId}/documents/thumbnail/${doc.doc_id}`}
                        alt={`${doc.filename}`}
                        className="max-w-8"
                      />
                    </ItemMedia>
                    {/* <div>{getFileIcon(doc.file_type)}</div> */}

                    <p
                      className="font-medium text-sm flex-1 truncate"
                      title={doc.filename}
                    >
                      {doc.filename}
                    </p>

                    <p className="text-xs text-muted-foreground shrink-0 min-w-[60px] text-right">
                      {formatFileSize(doc.file_size)}
                    </p>
                  </Item>
                </ContextMenuTrigger>
                <ContextMenuContent>
                  <ContextMenuItem
                    onClick={() =>
                      handleSelect(doc.doc_id, !selectedDocs.has(doc.doc_id))
                    }
                  >
                    {selectedDocs.has(doc.doc_id) ? "Deselect" : "Select"}
                  </ContextMenuItem>
                  <ContextMenuItem onClick={() => handleDownloadSingle(doc)}>
                    Download
                  </ContextMenuItem>
                  <ContextMenuItem
                    onClick={() => confirmDelete([doc])}
                    variant="destructive"
                  >
                    Delete
                  </ContextMenuItem>
                </ContextMenuContent>
              </ContextMenu>
            ))}
          </ItemGroup>
        )}
      </div>

      {/* Drag Overlay */}
      {isDragging && (
        <div className="fixed inset-0 bg-primary/10 border-4 border-dashed border-primary pointer-events-none flex items-center justify-center z-[100]">
          <div className="bg-background p-8 rounded-lg shadow-lg">
            <Upload className="h-16 w-16 text-primary mx-auto mb-4" />
            <p className="text-xl font-semibold">Drop files to upload</p>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete the
              following
              <span className="font-medium text-foreground">
                {" "}
                {docsToDelete.length} document(s)
              </span>{" "}
              from this project.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <ScrollArea className="h-[200px] w-full rounded-md border p-2 bg-muted/50">
            <ul className="text-sm space-y-2 p-2">
              {docsToDelete.map((doc) => (
                <li
                  key={doc.doc_id}
                  className="flex items-center gap-2 text-muted-foreground"
                >
                  <File className="h-4 w-4 shrink-0" />
                  <span className="truncate break-all">{doc.filename}</span>
                </li>
              ))}
            </ul>
          </ScrollArea>

          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault();
                executeDelete();
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={isDeleting}
            >
              {isDeleting ? "Deleting..." : "Delete Documents"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
