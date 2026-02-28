import { useState } from "react";
import {
  ArrowLeftIcon,
  BrainIcon,
  DownloadIcon,
  FileTextIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import mcqApi, { type MCQExportFormat, type MCQExportMode } from "@/api/mcqApi";

interface MCQExportButtonProps {
  mcqId: string | null | undefined;
  showLabel?: boolean;
  align?: "start" | "end";
  className?: string;
}

const EXPORT_FORMAT_OPTIONS: Array<{
  value: MCQExportFormat;
  label: string;
  icon: typeof FileTextIcon;
}> = [
  { value: "md", label: "MD", icon: FileTextIcon },
  { value: "pdf", label: "PDF", icon: FileTextIcon },
  { value: "json", label: "JSON", icon: BrainIcon },
  { value: "docx", label: "DOCX", icon: FileTextIcon },
];

function getFilenameFromContentDisposition(
  contentDisposition: string | undefined,
): string | null {
  if (!contentDisposition) return null;
  const match = contentDisposition.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? null;
}

export function MCQExportButton({
  mcqId,
  showLabel = true,
  align = "end",
  className,
}: MCQExportButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [step, setStep] = useState<"mode" | "format">("mode");
  const [mode, setMode] = useState<MCQExportMode | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  const reset = () => {
    setStep("mode");
    setMode(null);
  };

  const handleExport = async (format: MCQExportFormat) => {
    if (!mcqId || !mode) return;

    setIsExporting(true);
    try {
      const response = await mcqApi.exportMcq(mcqId, mode, format);
      const blob = response.data as Blob;
      const contentDisposition = response.headers["content-disposition"] as
        | string
        | undefined;
      const filename =
        getFilenameFromContentDisposition(contentDisposition) ??
        `mcq_${mode}.${format}`;

      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = filename;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);

      setIsOpen(false);
      reset();
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <DropdownMenu
      open={isOpen}
      onOpenChange={(open) => {
        setIsOpen(open);
        if (!open) {
          reset();
        }
      }}
    >
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="sm"
          className={className ?? "h-8 gap-1.5 px-2"}
          aria-label="Export MCQ"
          disabled={!mcqId}
        >
          <DownloadIcon className="h-4 w-4" />
          {showLabel && <span>Export</span>}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align} className="w-48">
        {step === "mode" ? (
          <>
            <DropdownMenuItem
              onSelect={(event) => {
                event.preventDefault();
                setMode("raw");
                setStep("format");
              }}
            >
              Raw
            </DropdownMenuItem>
            <DropdownMenuItem
              onSelect={(event) => {
                event.preventDefault();
                setMode("test");
                setStep("format");
              }}
            >
              Test
            </DropdownMenuItem>
          </>
        ) : (
          <>
            <DropdownMenuItem
              onSelect={(event) => {
                event.preventDefault();
                setStep("mode");
                setMode(null);
              }}
            >
              <ArrowLeftIcon className="h-4 w-4" />
              Back
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            {EXPORT_FORMAT_OPTIONS.map((item) => {
              const Icon = item.icon;
              return (
                <DropdownMenuItem
                  key={item.value}
                  disabled={isExporting}
                  onSelect={() => {
                    void handleExport(item.value);
                  }}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </DropdownMenuItem>
              );
            })}
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
