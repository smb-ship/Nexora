"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { TicketStatus, TicketPriority } from "@/types/ticket";

interface TicketFiltersProps {
  status: TicketStatus | "all";
  priority: TicketPriority | "all";
  onStatusChange: (value: TicketStatus | "all") => void;
  onPriorityChange: (value: TicketPriority | "all") => void;
}

export function TicketFilters({ status, priority, onStatusChange, onPriorityChange }: TicketFiltersProps) {
  return (
    <div className="flex gap-3">
      <Select value={status} onValueChange={(v) => onStatusChange(v as TicketStatus | "all")}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Statuses</SelectItem>
          <SelectItem value="open">Open</SelectItem>
          <SelectItem value="pending">Pending</SelectItem>
          <SelectItem value="on_hold">On Hold</SelectItem>
          <SelectItem value="resolved">Resolved</SelectItem>
          <SelectItem value="closed">Closed</SelectItem>
        </SelectContent>
      </Select>

      <Select value={priority} onValueChange={(v) => onPriorityChange(v as TicketPriority | "all")}>
        <SelectTrigger className="w-40">
          <SelectValue placeholder="Priority" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Priorities</SelectItem>
          <SelectItem value="low">Low</SelectItem>
          <SelectItem value="medium">Medium</SelectItem>
          <SelectItem value="high">High</SelectItem>
          <SelectItem value="urgent">Urgent</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}