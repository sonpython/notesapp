import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase-server'
import { AppSidebar } from '@/components/layout/app-sidebar'
import { AppHeader } from '@/components/layout/app-header'

/**
 * Authenticated app layout with 3-column structure:
 * Sidebar (folders/nav) | Note list | Editor/content.
 * Redirects to /login if user is not authenticated.
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

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Mobile header with menu toggle */}
      <AppHeader />

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar - hidden on mobile */}
        <div className="hidden lg:block">
          <AppSidebar />
        </div>

        {/* Main content area: note list + editor panes rendered by children */}
        <main className="flex flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}
