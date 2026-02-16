# Session Ledger — bun-do

## Goal

Complete rewrite of todo app from Streamlit to Bun + Alpine.js, then iterative feature additions, security hardening, and polish.

## Completed

### Rewrite & Core Features
- Full migration: Streamlit → Bun `server.ts` + Alpine.js `static/index.html`
- Views: All / Year / Month / Day / Backlog / Payments / Projects
- Task types: task, deadline, reminder, payment
- Recurring tasks: weekly, monthly, yearly with auto-creation on completion
- Subtasks with drag-and-drop reorder (SortableJS)
- Projects with timestamped progress log entries
- Inline click-to-edit for titles, notes, subtask names

### UX Polish (Phase 3-4)
- Keyboard shortcuts: `n` new, `1`–`5` views, `/` search, `Esc` dismiss
- Live search across titles and notes
- Error toasts via `apiFetch()` wrapper (all fetch calls routed through it)
- Undo delete with 10-second soft-delete window
- Overdue count badge on All tab
- Eisenhower matrix toggle (P0–P3 ↔ Do/Plan/Defer/Later)
- Adjustable font size (A-/A+) with localStorage persistence
- Recurrence toggle: click ↻ to cycle None→Weekly→Monthly→Yearly
- Color-coded recurrence: weekly=green, monthly=blue, yearly=purple
- Light / dark theme

### Payments Section
- New "payment" task type with optional amount field
- Payments filtered out of normal views (All, Day, Month, Year, calendar dots, overdueCount)
- Payments keep original due date (excluded from carryOver)
- Dedicated Payments view tab with monthly grouping and per-month $ subtotals
- Persistent collapsible Payments panel on task views
- Backend: amount field in Task interface, create/update/recurring handlers

### Code Quality
- Code simplifier pass: unified CSS (`.collapsible-*`), extracted `isRegularTask()`, `isListView()`, `LIST_VIEWS` constant, fixed stale amount in `openAddModal()`
- Security audit: sanitized recurrence objects, validated ids arrays, allowlisted project status
- Steinberger analysis: routed all raw `fetch()` through `apiFetch()`, deleted 295 MB `.venv/`

### Repo & Publishing
- Renamed to **bun-do** (title, navbar, bin script, server log, README, GitHub repo)
- `cli.ts` entry point for `bunx bun-do`
- `package.json` with bin, files, keywords for npm/bun publish
- Purged `todo_data.json` from git history (`git-filter-repo`), backed up to `~/autobkp/`
- Removed old Streamlit files (app.py, requirements.txt, .streamlit/)
- Symlink `~/autobkp/bin/bun-do` → `bin/bun-do` (with `readlink -f` fix)
- GitHub repo renamed, topics and description set

## Key Files

| File | Lines | Role |
|------|------:|------|
| `static/index.html` | 2618 | CSS + HTML + Alpine.js SPA |
| `server.ts` | 694 | Bun HTTP backend + JSON persistence |
| `bin/bun-do` | 101 | Service manager (start/stop/restart/status) |
| `cli.ts` | 3 | npm/bun entry shim |
| `package.json` | 47 | Package manifest |
| `data/tasks.example.json` | — | Seed data |

## Pending

- **npm publish**: Ready (`bun publish`), user said "not yet"
- **Task-row deduplication**: 8 copies of task-row HTML across views — accepted tradeoff for "no build step" constraint; revisit if Alpine components become viable
- **SRI hashes**: CDN scripts (Alpine.js, SortableJS) lack integrity attributes (low priority)

## Latest Commit

```
7140392 fix: route all fetch calls through apiFetch error handler
```
