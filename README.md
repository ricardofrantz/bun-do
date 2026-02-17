# bun-do

A fast, local-first todo app built on [Bun](https://bun.sh). One TypeScript file, one HTML file, zero dependencies.

![Bun](https://img.shields.io/badge/runtime-Bun-f9f1e1?logo=bun)
![TypeScript](https://img.shields.io/badge/lang-TypeScript-3178c6?logo=typescript&logoColor=white)
![Alpine.js](https://img.shields.io/badge/frontend-Alpine.js-77c1d2?logo=alpine.js&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-blue)

## Why bun-do?

Most todo apps want you to sign up, sync to the cloud, or install an Electron app. **bun-do** is different:

- **Single-file server** — `server.ts` serves both the API and frontend
- **JSON storage** — tasks and projects live in plain `.json` files you can version, grep, or edit by hand
- **No build step** — Alpine.js + SortableJS loaded from CDN, no bundler needed
- **Self-hosted** — runs on `localhost`, your data never leaves your machine

## Features

**Views** — All / Year / Month / Day / Backlog / Payments / Projects

**Tasks**
- Priorities P0 (critical) through P3 (backlog), with optional Eisenhower matrix labels
- Types: task, deadline, reminder, payment
- Recurring: weekly, monthly, yearly with auto-creation on completion
- Overdue tasks auto-carry to today (payments keep their original due date)
- Inline click-to-edit for titles, notes, and subtask names
- Undo delete with 10-second recovery window

**Payments** — Dedicated bill/payment tracker with optional amounts, grouped by month with per-month subtotals

**Subtasks** — Per-task checklists with drag-and-drop reorder

**Projects** — Lightweight project tracker with timestamped progress log entries

**UX**
- Keyboard shortcuts: `n` new task, `1`–`5` switch views, `/` search, `Esc` dismiss
- Live search across task titles and notes
- Overdue count badge
- Adjustable font size (A-/A+)
- Error toasts on failed API calls
- Light / dark theme

## Quick start

```bash
git clone https://github.com/ricardofrantz/bun-do.git
cd bun-do
bun install
bun run dev     # hot reload on :8000
```

Or without hot reload:

```bash
bun run start   # plain server on :8000
```

### Background service

```bash
./bin/bun-do              # start
./bin/bun-do status       # check
./bin/bun-do stop         # stop
./bin/bun-do restart      # restart
./bin/bun-do restart --example  # restart and reload data/tasks.example.json
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `TODO_PORT` | `8000` | Server port |
| `TODO_DATA_DIR` | `./data` | Directory for JSON data files |

For this environment, keep a fixed default in `~/.bashrc`:

```bash
export TODO_DATA_DIR=\${HOME}/.bun-do
```

```bash
TODO_PORT=9000 TODO_DATA_DIR=~/my-tasks bun run start
```

## Data

All data is plain JSON in `TODO_DATA_DIR`:

```
data/
  tasks.json            # your tasks
  projects.json         # your projects
  tasks.example.json    # seed data (committed to repo)
```

On first run, `tasks.example.json` seeds `tasks.json` if it doesn't exist.

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/tasks` | List tasks (auto-carries overdue to today) |
| `POST` | `/api/tasks` | Create task |
| `PUT` | `/api/tasks/:id` | Update task |
| `DELETE` | `/api/tasks/:id` | Delete task |
| `POST` | `/api/tasks/reorder` | Persist backlog order |
| `POST` | `/api/tasks/clear-done` | Remove completed tasks |
| `POST` | `/api/tasks/:id/subtasks` | Add subtask |
| `PUT` | `/api/tasks/:id/subtasks/:sid` | Update subtask |
| `DELETE` | `/api/tasks/:id/subtasks/:sid` | Delete subtask |
| `POST` | `/api/tasks/:id/subtasks/reorder` | Reorder subtasks |
| `GET` | `/api/projects` | List projects |
| `POST` | `/api/projects` | Create project |
| `PUT` | `/api/projects/:id` | Update project |
| `DELETE` | `/api/projects/:id` | Delete project |
| `POST` | `/api/projects/:id/entries` | Add log entry |
| `DELETE` | `/api/projects/:id/entries/:eid` | Delete log entry |

## Stack

| Layer | Tech |
|---|---|
| Runtime | [Bun](https://bun.sh) |
| Server | `Bun.serve()` — zero-dependency HTTP |
| Frontend | [Alpine.js](https://alpinejs.dev) + [SortableJS](https://sortablejs.github.io/Sortable/) (CDN) |
| Storage | Flat JSON files |

## License

MIT
