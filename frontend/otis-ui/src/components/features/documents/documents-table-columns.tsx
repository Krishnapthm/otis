import type { ColumnDef } from "@tanstack/react-table";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  CircleCheck,
  Clock,
  MoreVertical,
  Download,
  Trash2,
  ArrowUpDown,
} from "lucide-react";
import { ThumbnailImage } from "@/components/features/documents/ThumbnailImage";
import type { Document } from "@/api/docApi";

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

export const createColumns = (
  onDownload: (doc: Document) => void,
  onDelete: (doc: Document) => void,
): ColumnDef<Document>[] => [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && "indeterminate")
        }
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "preview",
    header: "Preview",
    cell: ({ row }) => (
      <ThumbnailImage
        docId={row.original.doc_id}
        filename={row.original.filename}
        fileType={row.original.file_type}
        className="w-10 h-10 rounded object-cover"
      />
    ),
    enableSorting: false,
  },
  {
    accessorKey: "filename",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="-ml-4"
        >
          Filename
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => (
      <div
        className="max-w-md truncate font-medium"
        title={row.original.filename}
      >
        {row.original.filename}
      </div>
    ),
  },
  {
    accessorKey: "file_size",
    header: "Size",
    cell: ({ row }) => (
      <div className="text-muted-foreground text-sm">
        {formatFileSize(row.original.file_size)}
      </div>
    ),
    enableSorting: false,
  },
  {
    accessorKey: "is_embedded",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="-ml-4"
        >
          Status
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) =>
      row.original.is_embedded ? (
        <Badge className="text-xs bg-green-600 ">Synced</Badge>
      ) : (
        <Badge className="text-xs bg-yellow-600 ">Not Synced</Badge>
      ),
  },
  {
    accessorKey: "created_at",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          className="-ml-4"
        >
          Uploaded On
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      );
    },
    cell: ({ row }) => {
      const date = row.original.created_at
        ? new Date(row.original.created_at)
        : null;
      return (
        <div className="text-muted-foreground text-sm">
          {date
            ? date.toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })
            : "N/A"}
        </div>
      );
    },
  },
  {
    id: "actions",
    cell: ({ row }) => (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <MoreVertical className="h-4 w-4" />
            <span className="sr-only">Open menu</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => onDownload(row.original)}>
            <Download className="h-4 w-4 mr-2" />
            Download
          </DropdownMenuItem>
          <DropdownMenuItem
            onClick={() => onDelete(row.original)}
            className="text-destructive"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
    enableSorting: false,
    enableHiding: false,
  },
];
