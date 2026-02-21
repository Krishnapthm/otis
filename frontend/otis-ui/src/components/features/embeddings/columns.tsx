import type { ColumnDef } from "@tanstack/react-table";
import {
  MoreHorizontal,
  Trash2,
  CheckCircle2,
  XCircle,
  Copy,
} from "lucide-react";
import { format } from "date-fns";

import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import type { EmbeddingVersion } from "@/api/embeddingsApi";

interface ColumnProps {
  onDelete: (id: string) => void;
}

export const getColumns = ({
  onDelete,
}: ColumnProps): ColumnDef<EmbeddingVersion>[] => [
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
    accessorKey: "version_number",
    header: "Ver.",
    cell: ({ row }) => (
      <span className="font-mono text-muted-foreground">
        v{row.getValue("version_number")}
      </span>
    ),
  },
  {
    accessorKey: "version_name",
    header: "Version Name",
    cell: ({ row }) => (
      <span className="font-medium text-foreground">
        {row.getValue("version_name")}
      </span>
    ),
  },
  {
    accessorKey: "doc_count",
    header: "Docs",
    cell: ({ row }) => (
      <Badge variant="outline" className="font-mono">
        {row.getValue("doc_count")}
      </Badge>
    ),
  },
  {
    accessorKey: "is_active",
    header: "Status",
    cell: ({ row }) => {
      const isActive = row.getValue("is_active");
      return (
        <div
          className={`flex items-center gap-2 ${
            isActive ? "text-green-600" : "text-muted-foreground"
          }`}
        >
          {isActive ? (
            <CheckCircle2 className="h-4 w-4" />
          ) : (
            <XCircle className="h-4 w-4" />
          )}
          <span className="text-sm font-medium">
            {isActive ? "Active" : "Inactive"}
          </span>
        </div>
      );
    },
  },
  {
    accessorKey: "created_at",
    header: "Created At",
    cell: ({ row }) => {
      try {
        const date = new Date(row.getValue("created_at"));
        return (
          <span className="text-muted-foreground text-sm whitespace-nowrap">
            {format(date, "MMM d, yyyy HH:mm")}
          </span>
        );
      } catch (e) {
        return <span className="text-muted-foreground text-sm">-</span>;
      }
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const version = row.original;

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem
              onClick={() => navigator.clipboard.writeText(version.version_id)}
            >
              <Copy className="mr-2 h-4 w-4" /> Copy ID
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => onDelete(version.version_id)}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete Version
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
