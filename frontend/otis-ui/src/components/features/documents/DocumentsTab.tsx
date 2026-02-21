import { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { ItemGroup, Item, ItemMedia } from "@/components/ui/item";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import { Empty } from "@/components/ui/empty";
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import {
  Upload,
  Grid3x3,
  List,
  File,
  CheckCircle2,
  Clock,
  Link2,
  Loader2,
} from "lucide-react";
import {
  uploadDocuments,
  getAllDocuments,
  getAllUserDocuments,
  linkDocumentToProject,
  deleteDocumentsFromProject,
  downloadDocuments,
  downloadDocument,
  type Document,
} from "@/api/docApi";
import { toast } from "sonner";
import { Separator } from "@/components/ui/separator";
import ScrollingFilename from "@/components/features/documents/ScrollingFileName";
import { ThumbnailImage } from "@/components/features/documents/ThumbnailImage";
import { DocumentGrid } from "@/components/features/documents/document-grid";
import { DownloadButton } from "@/components/ui/download-button";

interface DocumentsTabProps {
  projectId: string;
  onDocumentsChange?: (hasDocuments: boolean) => void;
  onDocumentsLoaded?: (documents: Document[]) => void;
  onSelectionChange?: (hasSelection: string[]) => void;
  selectedDocIds?: string[]; // Receive selection from parent
}

export function DocumentsTab({
  projectId,
  onDocumentsChange,
  onDocumentsLoaded,
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

  // Link from Library Dialog State
  const [linkDialogOpen, setLinkDialogOpen] = useState(false);
  const [userDocuments, setUserDocuments] = useState<Document[]>([]);
  const [selectedLinkedDocs, setSelectedLinkedDocs] = useState<Set<string>>(
    new Set(),
  );
  const [isLoadingUserDocs, setIsLoadingUserDocs] = useState(false);
  const [isLinking, setIsLinking] = useState(false);

  // Ref for the hidden file input
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Effects ---
  useEffect(() => {
    loadDocuments();
  }, [projectId]);

  useEffect(() => {
    onDocumentsChange?.(documents.length > 0);
    onDocumentsLoaded?.(documents);
  }, [documents, onDocumentsChange, onDocumentsLoaded]);

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
    [projectId],
  );

  const isAllSelected =
    documents.length > 0 && selectedDocs.size === documents.length;

  const isSomeSelected =
    selectedDocs.size > 0 && selectedDocs.size < documents.length;

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
          prev.filter((doc) => !docIds.includes(doc.doc_id)),
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

  // --- Link from Library Logic ---
  const openLinkDialog = async () => {
    setLinkDialogOpen(true);
    setIsLoadingUserDocs(true);
    try {
      const allDocs = await getAllUserDocuments();
      // Filter out documents already in this project
      const projectDocIds = new Set(documents.map((d) => d.doc_id));
      const availableDocs = allDocs.filter((d) => !projectDocIds.has(d.doc_id));
      setUserDocuments(availableDocs);
    } catch (error) {
      toast.error("Failed to load documents from library");
    } finally {
      setIsLoadingUserDocs(false);
    }
  };

  const handleLinkedDocSelect = (docId: string, checked: boolean) => {
    const newSelection = new Set(selectedLinkedDocs);
    if (checked) {
      newSelection.add(docId);
    } else {
      newSelection.delete(docId);
    }
    setSelectedLinkedDocs(newSelection);
  };

  const executeLinkDocuments = async () => {
    if (selectedLinkedDocs.size === 0) return;

    setIsLinking(true);
    const docIds = Array.from(selectedLinkedDocs);

    try {
      // Link documents one by one
      for (const docId of docIds) {
        await linkDocumentToProject(projectId, docId);
      }

      toast.success(`Linked ${docIds.length} document(s) to project`);
      setLinkDialogOpen(false);
      setSelectedLinkedDocs(new Set());
      loadDocuments(); // Refresh the documents list
    } catch (error) {
      toast.error("Failed to link documents");
    } finally {
      setIsLinking(false);
    }
  };

  // --- Download Logic ---
  const handleDownloadSelected = async () => {
    if (selectedDocs.size === 0) return;

    setIsDownloading(true);

    try {
      if (selectedDocs.size === documents.length) {
        // Download all as zip
        const blob = await downloadDocuments(projectId);
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `project-${projectId}-documents.zip`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        toast.success("Documents downloaded successfully");
      } else {
        // Download selected individually
        const docsToDownload = documents.filter((d) =>
          selectedDocs.has(d.doc_id),
        );
        for (const doc of docsToDownload) {
          const blob = await downloadDocument(doc.doc_id);
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = doc.filename;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
        }
        toast.success(`Downloaded ${docsToDownload.length} document(s)`);
      }
    } catch (error) {
      toast.error("Failed to download documents");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDownloadSingle = async (doc: Document) => {
    try {
      const blob = await downloadDocument(doc.doc_id);
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
                checked={
                  isAllSelected
                    ? true
                    : isSomeSelected
                      ? "indeterminate"
                      : false
                }
                onCheckedChange={(checked) => handleSelectAll(checked === true)}
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
                      selectedDocs.has(d.doc_id),
                    );
                    confirmDelete(docsToDel);
                  }}
                >
                  Delete ({selectedDocs.size})
                </Button>
                <DownloadButton
                  selectedCount={selectedDocs.size}
                  totalCount={documents.length}
                  isDownloading={isDownloading}
                  onDownload={handleDownloadSelected}
                />
              </>
            )}

            <Button
              variant="default"
              size="default"
              onClick={triggerFileUpload}
              disabled={isUploading}
            >
              <Upload className="h-4 w-4 mr-2" />
              {isUploading ? "Uploading..." : "Upload"}
            </Button>

            <Button variant="outline" size="default" onClick={openLinkDialog}>
              <Link2 className="h-4 w-4 mr-2" />
              Link from Library
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
                  <div className="items-center justify-center aspect-square min-w-40 pt-8">
                    <Skeleton className="h-12 w-12 rounded" />
                  </div>
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
          <Empty
            icon={Upload}
            title="No documents yet"
            description="Upload your first document to get started. Supports PDF, DOCX, TXT, MD."
            action={
              <Button onClick={triggerFileUpload} disabled={isUploading}>
                <Upload className="h-4 w-4 mr-2" />
                {isUploading ? "Uploading..." : "Choose Files"}
              </Button>
            }
          />
        ) : viewMode === "grid" ? (
          // Grid View - Using reusable component
          <DocumentGrid
            documents={documents}
            selectedDocs={selectedDocs}
            onSelect={handleSelect}
            onDownload={handleDownloadSingle}
            onDelete={(doc) => confirmDelete([doc])}
          />
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
                      <ThumbnailImage
                        docId={doc.doc_id}
                        filename={doc.filename}
                        fileType={doc.file_type}
                        className="max-w-8"
                      />
                    </ItemMedia>

                    <p
                      className="font-medium text-sm flex-1 truncate"
                      title={doc.filename}
                    >
                      {doc.filename}
                    </p>

                    <div className="shrink-0">
                      {doc.is_embedded ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <Clock className="h-4 w-4 text-orange-500" />
                      )}
                    </div>

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

      {/* Link from Library Dialog */}
      <Dialog open={linkDialogOpen} onOpenChange={setLinkDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Link Documents from Library</DialogTitle>
            <DialogDescription>
              Select documents from your library to link to this project.
            </DialogDescription>
          </DialogHeader>

          {isLoadingUserDocs ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : userDocuments.length === 0 ? (
            <Empty
              icon={File}
              title="No documents available"
              description="All your documents are already linked to this project, or you have no documents in your library."
            />
          ) : (
            <ScrollArea className="h-[300px] w-full rounded-md border p-2">
              <div className="space-y-2 p-2">
                {userDocuments.map((doc) => (
                  <div
                    key={doc.doc_id}
                    className={`flex items-center gap-3 p-2 rounded-md cursor-pointer transition-colors ${
                      selectedLinkedDocs.has(doc.doc_id)
                        ? "bg-primary/10 border border-primary/20"
                        : "hover:bg-muted/50"
                    }`}
                    onClick={() =>
                      handleLinkedDocSelect(
                        doc.doc_id,
                        !selectedLinkedDocs.has(doc.doc_id),
                      )
                    }
                  >
                    <Checkbox
                      checked={selectedLinkedDocs.has(doc.doc_id)}
                      onCheckedChange={(checked) =>
                        handleLinkedDocSelect(doc.doc_id, checked as boolean)
                      }
                    />
                    <ThumbnailImage
                      docId={doc.doc_id}
                      filename={doc.filename}
                      fileType={doc.file_type}
                      className="w-8 h-8 object-cover rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">
                        {doc.filename}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatFileSize(doc.file_size)}
                      </p>
                    </div>
                    <div className="shrink-0">
                      {doc.is_embedded ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <Clock className="h-4 w-4 text-orange-500" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setLinkDialogOpen(false);
                setSelectedLinkedDocs(new Set());
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={executeLinkDocuments}
              disabled={selectedLinkedDocs.size === 0 || isLinking}
            >
              {isLinking ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Linking...
                </>
              ) : (
                `Link ${selectedLinkedDocs.size} Document${selectedLinkedDocs.size !== 1 ? "s" : ""}`
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
