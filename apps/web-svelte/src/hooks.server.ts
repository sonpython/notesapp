/**
 * Server hooks for route protection based on session cookie.
 * No token decoding - just checks if session cookie exists.
 * Real auth validation happens when API calls are made.
 */

import { redirect, type Handle } from '@sveltejs/kit';

export const handle: Handle = async ({ event, resolve }) => {
	const hasSession = event.cookies.get('session');
	const { pathname } = event.url;

	// Skip static assets and API routes
	if (
		pathname.startsWith('/_app') ||
		pathname.startsWith('/favicon') ||
		pathname.startsWith('/icons') ||
		pathname.startsWith('/sw.js')
	) {
		return resolve(event);
	}

	// Redirect unauthenticated users to login (except auth pages, landing, and public routes)
	if (
		!hasSession &&
		!pathname.startsWith('/login') &&
		!pathname.startsWith('/signup') &&
		!pathname.startsWith('/offline') &&
		!pathname.startsWith('/pub') &&
		pathname !== '/'
	) {
		throw redirect(303, '/login');
	}

	// Redirect authenticated users away from auth pages
	if (hasSession && (pathname.startsWith('/login') || pathname.startsWith('/signup'))) {
		throw redirect(303, '/notes');
	}

	return resolve(event);
};
