/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

import { build, files, version } from '$service-worker';

const sw = self as unknown as ServiceWorkerGlobalScope;
// Force cache invalidation on deploy - change this value to bust cache
const CACHE_VERSION = '7';
const CACHE_NAME = `notesapp-${version}-v${CACHE_VERSION}`;

// Assets to cache on install
const ASSETS = [...build, ...files];

sw.addEventListener('install', (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)).then(() => sw.skipWaiting())
	);
});

sw.addEventListener('activate', (event) => {
	event.waitUntil(
		caches.keys().then((keys) =>
			Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
		).then(() => sw.clients.claim())
	);
});

sw.addEventListener('fetch', (event) => {
	if (event.request.method !== 'GET') return;

	const url = new URL(event.request.url);

	// Skip API calls - network only
	if (url.pathname.startsWith('/api')) return;

	event.respondWith(
		caches.match(event.request).then((cached) => {
			// Cache first for static assets
			if (cached) return cached;

			// Network fallback
			return fetch(event.request).then((response) => {
				if (response.ok && url.origin === location.origin) {
					const clone = response.clone();
					caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
				}
				return response;
			}).catch(() => {
				// Offline fallback for navigation
				if (event.request.mode === 'navigate') {
					return caches.match('/offline') || new Response('Offline', { status: 503 });
				}
				return new Response('Offline', { status: 503 });
			});
		})
	);
});
