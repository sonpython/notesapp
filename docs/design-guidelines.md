# Design Guidelines

## Design Philosophy

NotesApp emphasizes **clarity, simplicity, and speed**. Every interface element should get out of the user's way while providing necessary context and controls. Design decisions prioritize:

1. **Minimal cognitive load** - Familiar patterns, clear hierarchy
2. **Fast task completion** - Quick capture, editing, task management
3. **Dark theme by default** - Reduced eye strain, modern aesthetic
4. **Responsive design** - Mobile-first, works across devices
5. **Keyboard accessibility** - Power users can work without mouse

## Visual Design System

### Color Palette

**Base Colors** (TailwindCSS v4 theme)
```css
--color-slate-50: #f8fafc
--color-slate-100: #f1f5f9
--color-slate-200: #e2e8f0
--color-slate-300: #cbd5e1
--color-slate-400: #94a3b8
--color-slate-500: #64748b
--color-slate-600: #475569
--color-slate-700: #334155
--color-slate-800: #1e293b
--color-slate-900: #0f172a
--color-slate-950: #020617
```

**Semantic Colors**
- **Primary**: Slate-500 (text), Slate-600 (hover)
- **Background**: Slate-950 (dark mode default)
- **Surface**: Slate-900 (cards, modals)
- **Border**: Slate-700 (subtle dividers)
- **Text**: Slate-100 (primary text)
- **Muted**: Slate-400 (secondary text, placeholders)

**Functional Colors**
- **Success**: Green-500 (#22c55e) - Completed todos, save confirmation
- **Warning**: Amber-500 (#f59e0b) - Pending reminders, alerts
- **Error**: Red-500 (#ef4444) - Errors, delete confirmation
- **Info**: Blue-500 (#3b82f6) - Info messages, selected state

### Typography

**Font Stack**
```css
font-family: "Geist", system-ui, -apple-system, sans-serif;
font-mono: "Geist Mono", monospace;
```

**Scale**
- **xs**: 12px (captions, hints)
- **sm**: 14px (labels, secondary text)
- **base**: 16px (body text, form inputs)
- **lg**: 18px (section headings)
- **xl**: 20px (subsection headings)
- **2xl**: 24px (page headings)

**Weight**
- **Regular (400)**: Body text, UI labels
- **Medium (500)**: Emphasis, section headings
- **Semibold (600)**: Page headings, important labels
- **Bold (700)**: Avoid unless critical

### Spacing & Layout

**Base Unit**: 4px

**Scale**
- xs: 4px (internal component spacing)
- sm: 8px (padding, margins)
- md: 12px (standard component gap)
- lg: 16px (section spacing)
- xl: 24px (major sections)
- 2xl: 32px (page padding)

**Layout Grid**
- Desktop: 1024px max-width with 32px margins
- Tablet: Full width with 16px margins
- Mobile: Full width with 8px margins
- Gap between sections: 24px

### Shadows & Elevation

```css
/* Level 1: Subtle, cards */
box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);

/* Level 2: Modals, dropdowns */
box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

/* Level 3: Tooltips, popovers */
box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
```

### Border Radius

- **Buttons, inputs**: 6px (subtle roundness)
- **Cards, panels**: 8px (softer look)
- **Modals**: 12px (prominent)
- **Inline icons**: 4px (minimal)

### Icons

**Library**: Lucide React
**Size Scale**:
- sm: 16px (inline text, labels)
- base: 20px (buttons, list items)
- lg: 24px (page headers, important actions)

**Style**:
- Stroke width: 2
- All icons: outlined style (not filled)
- Color: Inherit from text color, with opacity for disabled state

## Component Design Patterns

### Buttons

**Primary Button**
```tsx
<button className="px-4 py-2 bg-slate-600 text-white rounded-md
                   hover:bg-slate-700 active:bg-slate-800
                   focus:outline-none focus:ring-2 focus:ring-slate-500
                   disabled:opacity-50 disabled:cursor-not-allowed">
  Primary Action
</button>
```

**Sizes**:
- sm: 8px vertical, 12px horizontal, 14px text
- base: 10px vertical, 16px horizontal, 16px text
- lg: 12px vertical, 20px horizontal, 18px text

**States**:
- Default: Slate-600
- Hover: Slate-700
- Active: Slate-800
- Disabled: opacity-50 with cursor-not-allowed
- Loading: spinner inside button

**Variants**:
- Primary (filled): bg-slate-600
- Secondary (outline): border-slate-400 text-slate-400
- Tertiary (ghost): transparent, hover:bg-slate-800
- Danger: bg-red-600 hover:bg-red-700

### Form Inputs

**Text Input**
```tsx
<input
  className="w-full px-3 py-2 bg-slate-800 border border-slate-700
             text-slate-100 placeholder-slate-400 rounded-md
             focus:border-slate-600 focus:outline-none focus:ring-2
             focus:ring-slate-500 focus:ring-offset-0"
  placeholder="Enter text..."
/>
```

**Principles**:
- Minimum 44px touch height (mobile)
- Clear focus state (ring + border change)
- Placeholder text: Slate-400
- Error state: border-red-500, focus:ring-red-500
- Success state: border-green-500, focus:ring-green-500

### Cards

**Structure**
```tsx
<div className="bg-slate-900 border border-slate-700 rounded-lg
                p-4 hover:border-slate-600 transition-colors">
  <h3 className="text-base font-medium text-slate-100 mb-2">Title</h3>
  <p className="text-sm text-slate-400">Description</p>
</div>
```

**Features**:
- Border: slate-700 by default, hover:slate-600
- Padding: 16px standard, 12px compact
- Hover: Border color change, subtle scale (transform scale-101)
- No shadow by default (borderless minimalism)

### Modals & Dialogs

**Design**:
- Semi-transparent backdrop (bg-black/50)
- Center on screen (fixed, flex center)
- Max-width: 480px (narrow, readable)
- Close button: top-right corner
- Click outside to close (recommended)

**Content**:
- Header: 24px bold heading
- Body: 16px text, max-width 65 chars per line
- Footer: Action buttons (primary + secondary)

**Cascade Delete Dialog** (NEW):
```svelte
<ConfirmDialog
  title="Delete Folder"
  message="Are you sure? This cannot be undone."
  primaryAction="Delete"
  secondaryAction="Cancel"
  onConfirm={() => deleteFolder(folderId, cascadeDelete)}
>
  <label className="flex items-center space-x-2 my-4">
    <input
      type="checkbox"
      bind:checked={cascadeDelete}
      className="w-4 h-4 rounded"
    />
    <span className="text-sm text-slate-300">
      Also delete all notes/todos in this folder
    </span>
  </label>
</ConfirmDialog>
```

**Cascade Delete UX**:
- Default checkbox: unchecked (preserve items)
- Warning icon next to checkbox (optional)
- Clarify scope: "all notes" vs "all todos" based on context
- Disable delete button until user confirms (optional safeguard)
- Spacing: 24px between sections

### Lists & Tables

**Note List**
```tsx
<div className="grid grid-cols-1 md:grid-cols-2 gap-4">
  {/* Note cards */}
</div>
```

**Todo List**
```tsx
<ul className="space-y-2">
  {/* Todo items with checkboxes */}
</ul>
```

**Features**:
- Responsive grid (mobile: 1 col, desktop: 2 cols)
- Consistent spacing between items
- Hover states for interactivity
- Selection highlight on focus

### Navigation

**Sidebar**
- Fixed width: 250px (desktop), collapsed on mobile
- Hamburger toggle on mobile (< 768px)
- Active state: Slate-600 background
- Items: Flex layout, 40px height
- Icon + text: 8px gap

**Breadcrumbs**
- "/" separator between levels
- Clickable ancestors
- Current page: bold, no link
- Spacing: 8px around separator

## Page Layouts

### Protected App Layout

```
┌────────────────────────────────────────┐
│        Header (sticky top)             │
│  Logo / Breadcrumb     Search  Profile  │
├──────────┬──────────────────────────────┤
│          │                              │
│ Sidebar  │   Main Content               │
│ (nav,    │   - Page title               │
│  folders)│   - Filters/controls         │
│          │   - Content grid/list        │
│          │                              │
│          │                              │
└──────────┴──────────────────────────────┘
```

**Notes Page Layout**
- Top bar: Filters (folder, archive status, sort)
- Left column: Pinned notes (20% width)
- Right column: Regular notes (80% width)
- Editor: Overlay or split view (responsive)

**Todos Page Layout**
- Top bar: Filters (status, priority, deadline)
- Main area: Todo list (full width)
- Create form: Sticky bottom or inline

**Settings Page Layout**
- Left sidebar: Settings sections (Profile, Telegram, etc.)
- Right panel: Section content
- Actions: Save/cancel buttons at bottom

### Landing Page

- Hero section: Title + CTA button
- Features section: 3 columns (notes, todos, telegram)
- Call-to-action: Sign up button
- Footer: Links, copyright

## Animation & Transitions

**Principles**:
- All animations: 200-300ms (feel responsive)
- Easing: ease-in-out (smooth, natural)
- Avoid flashy effects (minimize motion preference respected)

**Common Animations**
```css
/* Fade in */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Slide up */
@keyframes slideUp {
  from { transform: translateY(10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

/* Scale hover */
transition: transform 200ms ease-in-out;
hover:scale-102 (2% increase)
```

**Usage**:
- Modal open: fadeIn + slideUp
- Toast notification: slideUp from bottom
- Page navigation: fadeIn content
- Hover effects: 200ms color/scale transition
- Loading: Subtle spinner animation (200ms rotate loop)

## Responsive Design

**Breakpoints** (TailwindCSS)
- sm: 640px
- md: 768px
- lg: 1024px
- xl: 1280px

**Mobile-First Approach**
```tsx
{/* Mobile: single column */}
<div className="grid grid-cols-1
                md:grid-cols-2
                lg:grid-cols-3">
  {/* Responsive grid */}
</div>
```

**Key Changes**
- Mobile: Hamburger menu, full-width components
- Tablet (md): 2-column layouts, sidebar visible
- Desktop: Full sidebar, multi-column grids

## Dark Theme Implementation

**CSS Variables** (globals.css)
```css
:root {
  --background: 15 23 42;  /* slate-900 */
  --surface: 15 23 42;     /* slate-900 */
  --text: 241 245 249;     /* slate-100 */
  --text-muted: 148 163 184; /* slate-400 */
  --border: 51 65 85;      /* slate-700 */
}
```

**No Light Mode**
- Default: Dark theme always
- Future: Allow user toggle (planned)
- All colors tested for dark theme contrast

## Accessibility (WCAG AA)

### Color Contrast
- Text on background: 4.5:1 minimum
- UI components: 3:1 minimum
- Tested with aXe accessibility checker

### Keyboard Navigation
- Tab order: Logical, top-to-bottom
- Focus visible: 2px ring on all interactive elements
- Escape key: Close modals, dialogs
- Enter key: Submit forms

### Semantic HTML
- Use `<button>` for actions (not `<div>`)
- Use `<label>` for form inputs
- Use `<nav>` for navigation
- Use proper heading hierarchy (h1 → h2 → h3)

### ARIA Labels
```tsx
<button aria-label="Close modal" className="...">
  <X size={20} />
</button>

<input aria-describedby="email-help" type="email" />
<p id="email-help">We'll never share your email.</p>
```

### Motion & Animation
- Respect `prefers-reduced-motion`
- No auto-playing videos
- Animations can be disabled in settings (future)

## Component Best Practices

### Performance
- Lazy load components (React.lazy for routes)
- Memo expensive components
- Virtual lists for long lists (1000+ items)

### Maintainability
- Single responsibility (one component = one purpose)
- Props documentation
- Consistent naming (use `isLoading`, not `loading`)
- Story examples for UI components

### Reusability
- Extract button variants to constant
- Create composable icon components
- Use CSS classes over inline styles
- Define color palette in one place

## Error & Loading States

### Loading State
```tsx
<div className="flex items-center justify-center p-8">
  <div className="animate-spin w-5 h-5 border-2 border-slate-600
                  border-t-slate-300 rounded-full" />
</div>
```

### Empty State
```tsx
<div className="text-center py-12">
  <FileText className="w-12 h-12 text-slate-600 mx-auto mb-4" />
  <p className="text-slate-400">No notes yet</p>
  <p className="text-sm text-slate-500 mb-4">Create your first note to get started</p>
  <button>Create Note</button>
</div>
```

### Error State
```tsx
<div className="bg-red-500/10 border border-red-500/30 rounded-md p-4">
  <div className="flex items-start">
    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 mr-3" />
    <div>
      <h3 className="font-medium text-red-500">Error</h3>
      <p className="text-sm text-red-400 mt-1">Failed to load notes</p>
    </div>
  </div>
</div>
```

## Notifications & Toast Messages

**Toast Types**:
- Success: Green, checkmark icon, auto-dismiss 3s
- Error: Red, X icon, user dismissible
- Info: Blue, info icon, user dismissible
- Warning: Amber, alert icon, user dismissible

**Position**:
- Bottom-right corner (desktop)
- Bottom-center (mobile, full-width)
- Stacked if multiple notifications

## Future Design Considerations

- [ ] Light theme toggle
- [ ] Custom color scheme
- [ ] Font size adjustment
- [ ] Layout preferences (compact vs spacious)
- [ ] High contrast mode
- [ ] Custom keyboard shortcuts settings

## References

- TailwindCSS: https://tailwindcss.com
- Lucide Icons: https://lucide.dev
- WCAG Accessibility: https://www.w3.org/WAI/WCAG21/quickref/
- React Patterns: https://react.dev/reference/react
