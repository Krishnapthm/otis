import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { LucideIcon } from "lucide-react";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface DataCardProps {
  title: string;
  value: number | string;
  description: string;
  icon?: LucideIcon;
  isPositive?: boolean;
  variant?: "default" | "positive" | "warning";
  status?: "idle" | "syncing" | "error" | "success";
}

export function DataCard({
  title,
  value,
  description,
  icon: Icon,
  isPositive = false,
  variant = "default",
  status = "idle",
}: DataCardProps) {
  // Backward compatibility for isPositive
  if (isPositive) variant = "positive";

  // Determine icon based on status
  let StatusIcon = Icon;
  let iconColor = "";
  let textColor = "";
  let valueColor = "";

  if (
    status === "success" ||
    (status === "idle" && value === 0 && variant === "warning")
  ) {
    StatusIcon = CheckCircle2;
    iconColor = "text-green-600";
    textColor = "text-green-600";
    valueColor = "text-green-600";
  } else if (status === "syncing") {
    StatusIcon = Loader2;
    iconColor = "text-yellow-500 animate-spin";
    textColor = "text-yellow-500";
    valueColor = "text-yellow-500";
  } else if (status === "error") {
    StatusIcon = AlertCircle;
    iconColor = "text-destructive";
    textColor = "text-destructive";
    valueColor = "text-destructive";
  } else if (variant === "warning" && value !== 0) {
    StatusIcon = Icon || AlertCircle;
    iconColor = "text-yellow-500";
    valueColor = "text-yellow-500";
    textColor = "text-yellow-500";
  } else if (variant === "positive" || isPositive) {
    iconColor = "text-green-600";
    textColor = "text-green-600";
    valueColor = "text-green-600";
  }

  return (
    <Card>
      <CardHeader className="">
        <CardTitle
          className={cn(
            "text-l font-medium flex items-center gap-2",
            textColor,
          )}
        >
          {StatusIcon && <StatusIcon className={cn("h-4 w-4", iconColor)} />}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={cn("text-4xl font-bold", valueColor)}>{value}</div>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </CardContent>
    </Card>
  );
}
