import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'
import { ResizableAppLayout } from '@/components/layout/resizable-app-layout'
import { InstallBanner } from '@/components/pwa/install-banner'

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
  const cookieStore = await cookies()
  const hasSession = cookieStore.has('session')

  if (!hasSession) {
    redirect('/login')
  }

  return (
    <>
      <ResizableAppLayout>{children}</ResizableAppLayout>
      <InstallBanner />
    </>
  )
}
