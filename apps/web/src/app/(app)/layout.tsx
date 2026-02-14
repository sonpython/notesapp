import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'
import { ResizableAppLayout } from '@/components/layout/resizable-app-layout'

/**
 * Authenticated app layout with 3-column structure:
 * Sidebar (folders/nav) | Note list | Editor/content.
 * Redirects to /login if user is not authenticated.
 * Sidebar and note list panels are resizable.
 */
export default async function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const supabase = await createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  return <ResizableAppLayout>{children}</ResizableAppLayout>
}
