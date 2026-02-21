import { memo } from "react";
import { useThumbnail } from "@/hooks/useThumbnail";
import { FileText, File, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface ThumbnailImageProps {
  docId: string;
  filename: string;
  fileType?: string;
  className?: string;
}

function ThumbnailImageComponent({
  docId,
  filename,
  fileType = "",
  className,
}: ThumbnailImageProps) {
  const { thumbnailUrl, isLoading, error } = useThumbnail(docId);

  if (isLoading) {
    return (
      <div
        className={cn("flex items-center justify-center bg-muted", className)}
      >
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !thumbnailUrl) {
    // Fallback to icon if thumbnail fails to load
    const Icon = fileType.includes("pdf") ? FileText : File;
    return (
      <div
        className={cn("flex items-center justify-center bg-muted", className)}
      >
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
    );
  }

  return (
    <img
      src={thumbnailUrl}
      alt={filename}
      className={className}
      onError={(e) => {
        // Fallback if image fails to render
        const target = e.target as HTMLImageElement;
        target.style.display = "none";
      }}
    />
  );
}

// Memoize the component to prevent re-renders when only parent state changes
// This prevents unnecessary API calls when selection state changes
export const ThumbnailImage = memo(
  ThumbnailImageComponent,
  (prevProps, nextProps) => {
    // Only re-render if docId, filename, fileType, or className changes
    return (
      prevProps.docId === nextProps.docId &&
      prevProps.filename === nextProps.filename &&
      prevProps.fileType === nextProps.fileType &&
      prevProps.className === nextProps.className
    );
  },
);
