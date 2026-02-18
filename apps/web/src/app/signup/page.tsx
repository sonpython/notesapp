"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Fingerprint } from "lucide-react";
import { registerPasskey, isPasskeySupported } from "@/lib/auth-api";

export default function SignupPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const trimmedName = displayName.trim();
    if (!trimmedName) {
      setError("Please enter your name.");
      return;
    }

    if (!isPasskeySupported()) {
      setError("Your browser does not support passkeys. Please use a modern browser.");
      return;
    }

    setLoading(true);
    try {
      await registerPasskey(trimmedName);
      router.push("/notes");
    } catch (err) {
      if (err instanceof Error) {
        // Handle user cancellation gracefully
        if (err.name === "NotAllowedError") {
          setError("Passkey creation was cancelled. Please try again.");
        } else {
          setError(err.message);
        }
      } else {
        setError("Registration failed. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        {/* Header */}
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-bold text-foreground">
            Create your account
          </h1>
          <p className="mt-2 text-sm text-muted">
            Set up a passkey to secure your account.
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Signup form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="displayName"
              className="mb-1.5 block text-sm font-medium text-foreground"
            >
              Your name
            </label>
            <input
              id="displayName"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
              autoComplete="name"
              placeholder="Enter your name"
              className="h-10 w-full rounded-lg border border-border bg-background px-3 text-sm text-foreground placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex h-12 w-full items-center justify-center gap-3 rounded-lg bg-accent text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            <Fingerprint className="h-5 w-5" />
            {loading ? "Creating account..." : "Create account with passkey"}
          </button>
        </form>

        {/* Info text */}
        <p className="mt-4 text-center text-xs text-muted">
          Your device will create a secure passkey using Face ID, Touch ID, or your device PIN.
        </p>

        {/* Footer link */}
        <p className="mt-6 text-center text-sm text-muted">
          Already have an account?{" "}
          <Link
            href="/login"
            className="font-medium text-accent hover:underline"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
