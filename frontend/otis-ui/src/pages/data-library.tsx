import { useState, useCallback, useRef, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Empty } from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
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
import { Upload, Grid3x3, List } from "lucide-react";
import {
  downloadDocument,
  type Document,
} from "@/api/docApi";
import { toast } from "sonner";
import { DocumentsDataTable } from "@/components/features/documents/documents-data-table";
import { createColumns } from "@/components/features/documents/documents-table-columns";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { DocumentGrid } from "@/components/features/documents/document-grid";
import { SearchInput } from "@/components/ui/search-input";
import { DownloadButton } from "@/components/ui/download-button";
import ScrollingFilename from "@/components/features/documents/ScrollingFileName";
import { useDocuments } from "@/hooks/useDocuments";
import { useUploadDocument } from "@/hooks/useUploadDocument";
import { useDeleteDocuments } from "@/hooks/useDeleteDocuments";

export default function DataLibrary() {
  // Server State (TanStack Query)
  const { documents, isLoading } = useDocuments();
  const { uploadDocuments, isUploading } = useUploadDocument();
  const { deleteDocuments, isDeleting } = useDeleteDocuments();

  // UI State
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [isDragging, setIsDragging] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  // Delete Dialog State
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [docsToDelete, setDocsToDelete] = useState<Document[]>([]);

  // Duplicate Alert State
  const [duplicateFiles, setDuplicateFiles] = useState<string[]>([]);
  const [showDuplicateAlert, setShowDuplicateAlert] = useState(false);

  // Ref for the hidden file input
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- Filtered Documents ---
  const filteredDocuments = documents.filter((doc) =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  // --- Selection Logic ---
  const handleSelect = (docId: string, checked: boolean) => {
    const newSelection = new Set(selectedDocs);
    if (checked) {
      newSelection.add(docId);
    } else {
      newSelection.delete(docId);
    }
    setSelectedDocs(newSelection);
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      const allIds = new Set(filteredDocuments.map((d) => d.doc_id));
      setSelectedDocs(allIds);
    } else {
      setSelectedDocs(new Set());
    }
  };

  // Handle selection change from table
  const handleTableSelectionChange = (docIds: string[]) => {
    setSelectedDocs(new Set(docIds));
  };

  const isAllSelected =
    filteredDocuments.length > 0 &&
    selectedDocs.size === filteredDocuments.length;

  const isSomeSelected =
    selectedDocs.size > 0 && selectedDocs.size < filteredDocuments.length;

  // --- Upload Logic ---
  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async (files: File[]) => {
    if (files.length === 0) return;

    try {
      const uploadedDocs = await uploadDocuments(files);
      toast.success(`Uploaded ${uploadedDocs.length} file(s) successfully`);

      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error: any) {
      console.error("Upload error:", error);

      // Check if it's a duplicate error (409 Conflict)
      if (error?.response?.status === 409) {
        const detail = error?.response?.data?.detail;
        const duplicates = detail?.duplicates || [];
        setDuplicateFiles(duplicates);
        setShowDuplicateAlert(true);
      } else {
        toast.error("Failed to upload documents", {
          description: error?.response?.data?.detail || "An error occurred",
        });
      }
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

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleUpload(files);
  }, []);

  // --- Delete Logic ---
  const confirmDelete = (docs: Document[]) => {
    setDocsToDelete(docs);
    setDeleteDialogOpen(true);
  };

  const executeDelete = async () => {
    const docIds = docsToDelete.map((d) => d.doc_id);

    try {
      await deleteDocuments({
        projectId: docsToDelete[0].project_id,
        docIds,
      });

      setSelectedDocs((prev) => {
        const newSet = new Set(prev);
        docIds.forEach((id) => newSet.delete(id));
        return newSet;
      });

      setDeleteDialogOpen(false);
      setDocsToDelete([]);
      toast.success(`${docIds.length} document(s) deleted successfully`);
    } catch (error) {
      toast.error("Failed to delete documents");
    }
  };

  // --- Download Logic ---
  const handleDownloadSingle = useCallback(async (doc: Document) => {
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
  }, []);

  const handleDownloadSelected = async () => {
    if (selectedDocs.size === 0) return;

    setIsDownloading(true);
    const docsToDownload = documents.filter((d) => selectedDocs.has(d.doc_id));

    try {
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
    } catch (error) {
      toast.error("Failed to download documents");
    } finally {
      setIsDownloading(false);
    }
  };

  // --- Delete from table ---
  const handleDeleteSingle = useCallback((doc: Document) => {
    confirmDelete([doc]);
  }, []);

  // Create columns with callbacks - memoized to prevent unnecessary re-renders
  const columns = useMemo(
    () => createColumns(handleDownloadSingle, handleDeleteSingle),
    [handleDownloadSingle, handleDeleteSingle],
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-200px)]">
        <Skeleton className="h-8 w-full max-w-md" />
      </div>
    );
  }

  return (
    <div
      className="relative h-full flex flex-col gap-4 py-4 md:gap-6 md:py-6 px-4 md:px-6"
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
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-bold">Data Library</h1>
        <p className="text-muted-foreground">
          Manage all your documents in one place. Upload files here and link
          them to projects.
        </p>
      </div>

      {documents.length === 0 ? (
        <Empty
          icon={Upload}
          title="No documents yet"
          description="Upload your first document to get started. Drag and drop files here or click the button below."
          action={
            <Button onClick={triggerFileUpload} disabled={isUploading}>
              <Upload className="h-4 w-4 mr-2" />
              {isUploading ? "Uploading..." : "Upload Documents"}
            </Button>
          }
        />
      ) : (
        <>
          {/* Toolbar */}
          <div className="flex justify-between items-center gap-4">
            <SearchInput
              value={searchQuery}
              onValueChange={setSearchQuery}
              placeholder="Search documents..."
              className="max-w-md"
            />

            <div className="flex gap-4 items-center">
              <p className="text-sm text-muted-foreground whitespace-nowrap">
                {filteredDocuments.length} document(s)
                {selectedDocs.size > 0 && ` • ${selectedDocs.size} selected`}
              </p>

              {filteredDocuments.length > 0 && (
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
                    onCheckedChange={(checked) =>
                      handleSelectAll(checked === true)
                    }
                  />
                  <Label
                    htmlFor="select-all"
                    className="text-sm cursor-pointer"
                  >
                    Select All
                  </Label>
                </div>
              )}

              <div className="flex gap-2 items-center">
                <DownloadButton
                  selectedCount={selectedDocs.size}
                  totalCount={filteredDocuments.length}
                  isDownloading={isDownloading}
                  onDownload={handleDownloadSelected}
                />

                {selectedDocs.size > 0 && (
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
                    value && setViewMode(value as "grid" | "table")
                  }
                  variant="outline"
                  size="default"
                >
                  <ToggleGroupItem value="grid" aria-label="Grid view">
                    <Grid3x3 className="h-4 w-4" />
                  </ToggleGroupItem>
                  <ToggleGroupItem value="table" aria-label="Table view">
                    <List className="h-4 w-4" />
                  </ToggleGroupItem>
                </ToggleGroup>
              </div>
            </div>
          </div>

          {/* Documents Grid/Table */}
          {viewMode === "grid" ? (
            <DocumentGrid
              documents={filteredDocuments}
              selectedDocs={selectedDocs}
              onSelect={handleSelect}
              onDownload={handleDownloadSingle}
              onDelete={(doc) => confirmDelete([doc])}
            />
          ) : (
            <DocumentsDataTable
              columns={columns}
              data={filteredDocuments}
              selectedDocIds={Array.from(selectedDocs)}
              onSelectionChange={handleTableSelectionChange}
            />
          )}
        </>
      )}

      {/* Drag Overlay */}
      {isDragging && (
        <div className="absolute inset-0 bg-primary/10 border-4 border-dashed border-primary pointer-events-none flex items-center justify-center z-[100]">
          <div className="bg-background p-8 rounded-lg shadow-lg">
            <Upload className="h-16 w-16 text-primary mx-auto mb-4" />
            <p className="text-xl font-semibold">Drop files to upload</p>
          </div>
        </div>
      )}

      {/* Duplicate Alert */}
      {showDuplicateAlert && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Duplicate Documents Detected</AlertTitle>
          <AlertDescription>
            The following files already exist in your library:
            <ul className="list-disc list-inside mt-2">
              {duplicateFiles.map((filename, idx) => (
                <li key={idx} className="text-sm">
                  {filename}
                </li>
              ))}
            </ul>
            <Button
              variant="outline"
              size="sm"
              className="mt-3"
              onClick={() => setShowDuplicateAlert(false)}
            >
              Dismiss
            </Button>
          </AlertDescription>
        </Alert>
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
              from your library.
            </AlertDialogDescription>
          </AlertDialogHeader>

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
