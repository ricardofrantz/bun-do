# Changelog

## [v1.4.0] — 2026-02-18

### Added
- **Native macOS app** — `bun-do app` opens a lightweight WKWebView window (no Electron). Compiles Swift source on first run and caches the binary in `~/.bun-do/app/`.
- Screenshot in README

### Changed
- **SKILL.md rewrite** — natural language mapping table, proactive patterns (morning briefing, weekly review), payment tracking examples
- npm package only ships `bin/bun-do-webview.swift` instead of entire `bin/` directory

### Fixed
- **First-run empty tasks** — `tasks.example.json` wraps tasks in `{ "tasks": [...] }` but `parseTasks` expected a bare array, causing blank task list on first boot
- Recurrence validation bypass — `parseTasks` now routes through `sanitizeRecurrence()` instead of raw cast
- `child.pid` undefined guard when spawning background server
- Removed stale `macapp` script referencing deleted `bin/bun-do.app`

---

## [v1.3.0] — 2026-02-18

### Added
- **MCP server** (`bun-do-mcp`) — stdio JSON-RPC 2.0 server exposing 6 tools: `list_tasks`, `add_task`, `update_task`, `delete_task`, `list_projects`, `add_project_entry`. Works with Claude Desktop, opencode, and any MCP client.
- **Installable skill** — Markdown skill for Claude Code and OpenClaw (`bun-do install-skill` / `bun-do install-skill --openclaw`)
- **OpenClaw integration** — bun-do positioned as the task layer for [OpenClaw](https://github.com/openclaw/openclaw); route tasks from WhatsApp, Telegram, Slack via your local AI assistant
- `AGENTS.md` — machine-readable orientation guide for AI agents

### Fixed
- CLI: replaced HTTP `fetch()` health check in `waitForReady()` with TCP socket connect — removes unnecessary network access during startup
- MCP: guard `params` destructuring against malformed `tools/call` requests
- MCP: added `ping` handler required by MCP spec

---

## [v1.2.1] — 2026-02-17

### Added
- Vendored **Alpine.js 3.15.8** and **SortableJS 1.15.7** — no CDN dependency, fully offline-capable
- `.gitattributes` marks vendored minified files as binary/linguist-generated

### Changed
- Removed Google Fonts CDN link

### Fixed
- CLI: `--serve` flag fallthrough into service manager switch

---

## [v1.2.0] — 2026-02-16

### Changed
- Server refactor: in-memory store with atomic JSON writes — eliminates read/write races
- Union types for task and project shapes — stricter TypeScript throughout
- `findById` helpers — cleaner route handlers

---

## [v1.1.3] — 2026-02-15

### Added
- GitHub Actions workflow to publish to npm on version tag push (`NPM_TOKEN` secret)

---

## [v1.1.2] — 2026-02-14

### Added
- `bun-do --version` flag
- Version printed on server start and restart

---

## [v1.1.1] — 2026-02-13

### Added
- **CLI service manager** (`cli.ts`): `start`, `stop`, `restart`, `status`, `open` commands
- Background server with PID file tracking and log output
- `bun-do open` starts the server and opens the browser automatically

---

## [v1.1.0] — 2026-02-12

Initial public release.

### Features
- Year / month / day agenda calendar views with auto-sync to current date
- Task rollover: overdue tasks carry to today automatically (payments keep original date)
- Priorities P0–P3 (critical → backlog) with optional Eisenhower matrix labels
- Task types: task, deadline, reminder, payment
- Recurring tasks: weekly, monthly, yearly with auto-creation on completion
- Subtasks with drag-and-drop reorder
- Projects tracker with timestamped progress log entries
- Payments view grouped by month with per-month subtotals
- Live search across titles and notes
- Keyboard shortcuts: `n` new task, `1`–`5` views, `/` search, `Esc` dismiss
- Light / dark theme, adjustable font size
- Undo delete with 10-second recovery window
- REST API via `Bun.serve()` — zero runtime dependencies
- Alpine.js + SortableJS frontend, no build step, works offline
