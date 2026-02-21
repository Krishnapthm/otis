import { Download, Loader2 } from "lucide-react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DownloadButtonProps extends Omit<ButtonProps, "children"> {
  selectedCount: number;
  totalCount: number;
  isDownloading?: boolean;
  onDownload: () => void;
}

export function DownloadButton({
  selectedCount,
  totalCount,
  isDownloading = false,
  onDownload,
  className,
  variant = "outline",
  size = "default",
  ...props
}: DownloadButtonProps) {
  // Determine button text based on selection
  const getButtonText = () => {
    if (isDownloading) return "Downloading...";
    if (selectedCount === 0) return "Download";
    if (selectedCount === totalCount && totalCount > 1) return "Download All";
    if (selectedCount === 1) return "Download";
    return "Download Selected";
  };

  return (
    <Button
      variant={variant}
      size={size}
      onClick={onDownload}
      disabled={isDownloading || selectedCount === 0}
      className={cn(className)}
      {...props}
    >
      {isDownloading ? (
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
      ) : (
        <Download className="h-4 w-4 mr-2" />
      )}
      {getButtonText()}
      {selectedCount > 0 && !isDownloading && selectedCount < totalCount && (
        <span className="ml-1">({selectedCount})</span>
      )}
    </Button>
  );
}
