import { Checkbox } from "@/components/ui/checkbox";
import { Item, ItemGroup, ItemHeader, ItemMedia } from "@/components/ui/item";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import { CheckCircle2, Clock } from "lucide-react";
import ScrollingFilename from "@/components/features/documents/ScrollingFileName";
import { ThumbnailImage } from "@/components/features/documents/ThumbnailImage";
import type { Document } from "@/api/docApi";
import { cn } from "@/lib/utils";

interface DocumentGridProps {
  documents: Document[];
  selectedDocs: Set<string>;
  onSelect: (docId: string, checked: boolean) => void;
  onDownload?: (doc: Document) => void;
  onDelete?: (doc: Document) => void;
  className?: string;
}

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export function DocumentGrid({
  documents,
  selectedDocs,
  onSelect,
  onDownload,
  onDelete,
  className,
}: DocumentGridProps) {
  return (
    <ItemGroup className={cn("grid grid-cols-4 gap-4", className)}>
      {documents.map((doc) => (
        <ContextMenu key={doc.doc_id}>
          <ContextMenuTrigger>
            <div className="relative group">
              <Item
                className={`cursor-pointer transition-all ${
                  selectedDocs.has(doc.doc_id)
                    ? "ring-2 ring-primary g-primary/5"
                    : "hover:bg-muted/50"
                }`}
                variant="outline"
                onClick={() =>
                  onSelect(doc.doc_id, !selectedDocs.has(doc.doc_id))
                }
              >
                <div
                  className="absolute  top-3 left-3 z-10"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Checkbox
                    checked={selectedDocs.has(doc.doc_id)}
                    onCheckedChange={(checked) =>
                      onSelect(doc.doc_id, checked as boolean)
                    }
                  />
                </div>

                <div className="absolute top-3 right-3 z-10">
                  {doc.is_embedded ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <Clock className="h-5 w-5 text-orange-500" />
                  )}
                </div>

                <ItemHeader className="items-center justify-center aspect-square min-w-40 p-0">
                  <ItemMedia className="w-full h-full p-0 m-0">
                    <ThumbnailImage
                      docId={doc.doc_id}
                      filename={doc.filename}
                      fileType={doc.file_type}
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
                onSelect(doc.doc_id, !selectedDocs.has(doc.doc_id))
              }
            >
              {selectedDocs.has(doc.doc_id) ? "Deselect" : "Select"}
            </ContextMenuItem>
            {onDownload && (
              <ContextMenuItem onClick={() => onDownload(doc)}>
                Download
              </ContextMenuItem>
            )}
            {onDelete && (
              <ContextMenuItem
                onClick={() => onDelete(doc)}
                variant="destructive"
              >
                Delete
              </ContextMenuItem>
            )}
          </ContextMenuContent>
        </ContextMenu>
      ))}
    </ItemGroup>
  );
}
