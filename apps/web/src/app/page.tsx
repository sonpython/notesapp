import { redirect } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase-server";

export default async function HomePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (user) {
    redirect("/notes");
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-6">
      <div className="max-w-md text-center">
        <h1 className="text-4xl font-bold tracking-tight text-foreground">
          NotesApp
        </h1>
        <p className="mt-4 text-lg text-muted">
          A simple, fast way to capture your thoughts and stay organized.
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link
            href="/signup"
            className="inline-flex h-11 items-center justify-center rounded-lg bg-accent px-6 text-sm font-semibold text-black transition-opacity hover:opacity-90"
          >
            Get Started
          </Link>
          <Link
            href="/login"
            className="inline-flex h-11 items-center justify-center rounded-lg border border-border px-6 text-sm font-medium text-foreground transition-colors hover:bg-sidebar"
          >
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
