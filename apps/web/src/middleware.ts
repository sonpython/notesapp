/**
 * Middleware for route protection based on session cookie.
 * No token decoding - just checks if session cookie exists.
 * Real auth validation happens when API calls are made.
 */

import { NextResponse, type NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const hasSession = request.cookies.has('session')
  const { pathname } = request.nextUrl

  // Redirect unauthenticated users to login (except auth pages and landing)
  if (
    !hasSession &&
    !pathname.startsWith('/login') &&
    !pathname.startsWith('/signup') &&
    pathname !== '/'
  ) {
    const url = request.nextUrl.clone()
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  // Redirect authenticated users away from auth pages
  if (
    hasSession &&
    (pathname.startsWith('/login') || pathname.startsWith('/signup'))
  ) {
    const url = request.nextUrl.clone()
    url.pathname = '/notes'
    return NextResponse.redirect(url)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api|sw\\.js|icons).*)'],
}
