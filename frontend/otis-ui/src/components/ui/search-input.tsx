import * as React from "react";
import { Search, Command } from "lucide-react";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

interface SearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  value: string;
  onValueChange: (value: string) => void;
  showKbd?: boolean;
}

export function SearchInput({
  value,
  onValueChange,
  showKbd = true,
  placeholder = "Search...",
  className,
  id,
  ...props
}: SearchInputProps) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const inputId = id || "search-input";

  // Keyboard shortcut (Ctrl/Cmd + K)
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent): void => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className={cn("relative flex-1", className)}>
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        ref={inputRef}
        id={inputId}
        type="search"
        placeholder={placeholder}
        className="pl-10 pr-12"
        value={value}
        onChange={(e) => onValueChange(e.target.value)}
        {...props}
      />
      {showKbd && (
        <kbd className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
          <Command className="h-3 w-3" />
          <span className="text-xs">K</span>
        </kbd>
      )}
    </div>
  );
}
