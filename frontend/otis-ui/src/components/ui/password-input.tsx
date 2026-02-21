"use client";

import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface PasswordInputProps extends Omit<
  React.ComponentProps<typeof Input>,
  "type"
> {
  showToggle?: boolean;
}

function PasswordInput({
  className,
  showToggle = true,
  ...props
}: PasswordInputProps) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="relative">
      <Input
        className={cn("pr-10", className)}
        type={showPassword ? "text" : "password"}
        {...props}
      />
      {showToggle && (
        <Button
          className="absolute top-0 right-0 h-full px-3 hover:bg-transparent bg-transparent "
          onClick={() => setShowPassword(!showPassword)}
          size="icon"
          type="button"
          variant="default"
        >
          {showPassword ? (
            <EyeOff className="h-4 w-4 text-muted-foreground" />
          ) : (
            <Eye className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="sr-only">
            {showPassword ? "Hide password" : "Show password"}
          </span>
        </Button>
      )}
    </div>
  );
}

export { PasswordInput };
