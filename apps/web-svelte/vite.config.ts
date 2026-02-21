import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		port: 3000,
		host: true,
		hmr: {
			// In Docker, client connects from browser (localhost), not container
			clientPort: 3000
		},
		proxy: {
			'/api': {
				target: process.env.BACKEND_URL || 'http://localhost:8001',
				changeOrigin: true
			}
		}
	}
});
