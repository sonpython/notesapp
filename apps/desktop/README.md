# NotesApp Desktop (macOS)

Tauri v2 desktop wrapper for NotesApp.

## Prerequisites

- macOS 12.0+ (Monterey or later)
- Rust toolchain (`rustup`)
- Node.js 22+, pnpm 10.29+

## Development

```bash
# From repo root -- starts Next.js dev + Tauri window
pnpm dev:desktop
```

## Build DMG

```bash
cd apps/desktop
pnpm tauri build
# Output: src-tauri/target/release/bundle/dmg/NotesApp_*.dmg
```

## Install

1. Open the DMG file
2. Drag NotesApp.app to Applications
3. First launch: right-click > Open (macOS Gatekeeper bypass)

## Usage (MVP)

The desktop app connects to a running Next.js server.
Start the server before launching:

```bash
pnpm dev:web    # development
# or
pnpm build:web && pnpm --filter @notesapp/web start  # production
```

## Gatekeeper Bypass

For unsigned apps on macOS:
```bash
# Option 1: Right-click > Open (recommended)
# Option 2: System Settings > Privacy & Security > Open Anyway
# Option 3: Remove quarantine attribute
xattr -d com.apple.quarantine /Applications/NotesApp.app
```

## Architecture

- Tauri v2 WebView shell (WebKit)
- Loads Next.js from http://localhost:3000
- Offline: IndexedDB + Service Worker (inherited from PWA)
- Native: macOS menu bar, window state persistence

## Menu Shortcuts

| Shortcut | Action |
|----------|--------|
| Cmd+, | Settings |
| Cmd+R | Reload |
| Cmd+Q | Quit |
| Cmd+M | Minimize |
| Cmd+C/V/X/Z/A | Copy/Paste/Cut/Undo/Select All |

## Future Enhancements

- Standalone sidecar: Bundle Next.js server inside the app
- Auto-update: Tauri updater plugin
- Universal binary: aarch64 + x86_64
- Code signing: Apple Developer account
