"use client";

import { useEffect, useState } from "react";
import { Search } from "lucide-react";

export function TicketSearchInput({
  onSearch,
  placeholder = "Search tickets...",
}: {
  onSearch: (value: string) => void;
  placeholder?: string;
}) {
  const [value, setValue] = useState("");

  useEffect(() => {
    const handle = setTimeout(() => onSearch(value), 300);
    return () => clearTimeout(handle);
  }, [value, onSearch]);

  return (
    <div className="relative">
      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-border bg-transparent py-2 pl-9 pr-3 text-sm outline-none focus:border-primary"
      />
    </div>
  );
}