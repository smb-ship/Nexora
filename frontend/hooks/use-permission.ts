"use client";

import { useAuth } from "@/lib/auth-context"; // adjust to match your actual hook export
import { hasPermission, type Permission } from "@/lib/permissions";

export function usePermission(permission: Permission): boolean {
  const { user } = useAuth();
  return hasPermission(user?.role, permission);
}