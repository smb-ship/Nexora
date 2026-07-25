"use client";

import { useState } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetFooter } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Check, Copy } from "lucide-react";
import { createInvitation } from "@/lib/api/team";
import type { UserRole, Invitation } from "@/types/team";

interface InviteSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onInvited: (invitation: Invitation) => void;
}

export function InviteSheet({ open, onOpenChange, onInvited }: InviteSheetProps) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<UserRole>("agent");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [link, setLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleSubmit() {
    if (!email.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const invitation = await createInvitation({ email, role });
      setLink(`${window.location.origin}/accept-invite?token=${invitation.token}`);
      onInvited(invitation);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create invitation");
    } finally {
      setSubmitting(false);
    }
  }

  function handleCopy() {
    if (!link) return;
    navigator.clipboard.writeText(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleClose(next: boolean) {
    if (!next) {
      setEmail(""); setRole("agent"); setLink(null); setError(null);
    }
    onOpenChange(next);
  }

  return (
    <Sheet open={open} onOpenChange={handleClose}>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Invite a team member</SheetTitle>
          <SheetDescription>Email delivery isn't set up yet — you'll get a link to share manually.</SheetDescription>
        </SheetHeader>

        <div className="space-y-4 px-4">
          {!link ? (
            <>
              <div>
                <label className="mb-1 block text-sm font-medium">Email</label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="teammate@company.com" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Role</label>
                <Select value={role} onValueChange={(v) => setRole(v as UserRole)}>
                  <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">Admin</SelectItem>
                    <SelectItem value="manager">Manager</SelectItem>
                    <SelectItem value="agent">Agent</SelectItem>
                    <SelectItem value="viewer">Viewer</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {error && <p className="text-sm text-red-400">{error}</p>}
            </>
          ) : (
            <div className="space-y-2 rounded-lg border border-border bg-muted/30 p-3">
              <p className="text-sm text-muted-foreground">Share this link with {email}:</p>
              <div className="flex items-center gap-2">
                <Input readOnly value={link} className="text-xs" />
                <Button size="icon-sm" variant="outline" onClick={handleCopy}>
                  {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">Expires in 7 days.</p>
            </div>
          )}
        </div>

        <SheetFooter>
          {!link ? (
            <Button onClick={handleSubmit} disabled={submitting || !email.trim()}>
              {submitting ? "Creating…" : "Create invite link"}
            </Button>
          ) : (
            <Button variant="outline" onClick={() => handleClose(false)}>Done</Button>
          )}
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}