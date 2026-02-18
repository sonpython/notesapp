"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Fingerprint } from "lucide-react";
import { loginPasskey, isPasskeySupported } from "@/lib/auth-api";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    setError(null);

    if (!isPasskeySupported()) {
      setError("Your browser does not support passkeys. Please use a modern browser.");
      return;
    }

    setLoading(true);
    try {
      await loginPasskey();
      router.push("/notes");
    } catch (err) {
      if (err instanceof Error) {
        // Handle user cancellation gracefully
        if (err.name === "NotAllowedError") {
          setError("Authentication was cancelled. Please try again.");
        } else {
          setError(err.message);
        }
      } else {
        setError("Authentication failed. Please try again.");
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
            Sign in to NotesApp
          </h1>
          <p className="mt-2 text-sm text-muted">
            Use your passkey to sign in securely.
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Passkey sign-in button */}
        <button
          onClick={handleLogin}
          disabled={loading}
          className="flex h-12 w-full items-center justify-center gap-3 rounded-lg bg-accent text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          <Fingerprint className="h-5 w-5" />
          {loading ? "Authenticating..." : "Sign in with passkey"}
        </button>

        {/* Info text */}
        <p className="mt-4 text-center text-xs text-muted">
          Your device will prompt you to use Face ID, Touch ID, or your device PIN.
        </p>

        {/* Footer link */}
        <p className="mt-6 text-center text-sm text-muted">
          Don&apos;t have an account?{" "}
          <Link
            href="/signup"
            className="font-medium text-accent hover:underline"
          >
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
