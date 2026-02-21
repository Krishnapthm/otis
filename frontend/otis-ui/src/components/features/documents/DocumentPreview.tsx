import { Badge } from "@/components/ui/badge";
import { FileText } from "lucide-react";
import type { Document } from "@/api/docApi";

interface DocumentPreviewProps {
  documents: Document[];
  className?: string;
}

/**
 * Displays selected documents as badges for preview
 */
export function DocumentPreview({
  documents,
  className,
}: DocumentPreviewProps) {
  if (documents.length === 0) {
    return (
      <div className="text-muted-foreground text-sm">No documents selected</div>
    );
  }

  return (
    <div className={className}>
      <div className="flex items-center gap-2 mb-3">
        <FileText className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm font-medium">
          {documents.length} document{documents.length !== 1 ? "s" : ""}{" "}
          selected
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {documents.map((doc) => (
          <Badge
            key={doc.doc_id}
            variant="secondary"
            className="max-w-[200px] truncate"
            title={doc.filename}
          >
            {doc.filename}
          </Badge>
        ))}
      </div>
    </div>
  );
}
