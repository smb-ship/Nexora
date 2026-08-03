"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/api";

const DEMO_EMAIL = "test@nexora.com";
const DEMO_PASSWORD = "Nexora123!";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isDemoLoading, setIsDemoLoading] = useState(false);

  async function performLogin(loginEmail: string, loginPassword: string) {
    setError(null);
    try {
      await login(loginEmail, loginPassword);
      router.push("/dashboard");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email || !password) {
      setError("Please enter both email and password.");
      return;
    }
    setIsSubmitting(true);
    await performLogin(email, password);
    setIsSubmitting(false);
  }

  async function handleDemoLogin() {
    setEmail(DEMO_EMAIL);
    setPassword(DEMO_PASSWORD);
    setIsDemoLoading(true);
    await performLogin(DEMO_EMAIL, DEMO_PASSWORD);
    setIsDemoLoading(false);
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 text-center">
        <h1 className="text-xl font-semibold text-foreground tracking-tight">
          Sign in to Nexora
        </h1>
        <p className="text-sm text-foreground-muted">
          Welcome back. Enter your details below.
        </p>
      </div>

      <button
        type="button"
        onClick={handleDemoLogin}
        disabled={isDemoLoading || isSubmitting}
        className="group flex items-center justify-between rounded-lg border border-border bg-surface-elevated px-4 py-3 text-left shadow-sm transition-colors hover:border-primary disabled:opacity-60"
      >
        <div>
          <p className="text-sm font-medium text-foreground">Try the live demo</p>
          <p className="mt-0.5 text-xs text-foreground-muted">
            Explore Nexora instantly with a pre-loaded Owner account — no signup required.
          </p>
        </div>
        <span className="ml-4 shrink-0 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-opacity group-hover:opacity-90">
          {isDemoLoading ? "Signing in..." : "Demo login"}
        </span>
      </button>

      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-border" />
        <span className="text-xs text-foreground-subtle">or sign in manually</span>
        <div className="h-px flex-1 bg-border" />
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor="email" className="text-sm text-foreground-muted">
            Email
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-primary"
            placeholder="you@company.com"
            autoComplete="email"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="password" className="text-sm text-foreground-muted">
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-primary"
            placeholder="••••••••"
            autoComplete="current-password"
          />
        </div>

        {error && (
          <p className="text-sm text-destructive" role="alert">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting || isDemoLoading}
          className="mt-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-sm transition-opacity hover:opacity-90 disabled:opacity-60"
        >
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>

      <p className="text-center text-sm text-foreground-muted">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="text-primary hover:underline">
          Sign up
        </Link>
      </p>
    </div>
  );
}