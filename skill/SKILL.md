---
name: bun-do-api
description: >
  Manage bun-do tasks and projects — add tasks, edit tasks, delete tasks,
  toggle done, manage subtasks, and log project progress entries. Use when the
  user says "add a todo", "update task", "remove task", "mark done", "add
  subtask", "log progress", "update project", or any variant of managing
  tasks/projects. Also use when an agent finishes work and needs to record
  progress.
---

# bun-do API

REST API running at `http://localhost:8000`. The server must be running.

**Start**: `bun-do start` (installed globally via `npm install -g bun-do`)
**Data dir**: `~/.bun-do/` (override with `BUNDO_DATA_DIR`)
**Port**: default 8000, override with `--port=PORT`

All mutations persist immediately to JSON files on disk.

## Quick Reference

| Action | Method | Endpoint |
|--------|--------|----------|
| List tasks | GET | `/api/tasks` |
| Add task | POST | `/api/tasks` |
| Edit task | PUT | `/api/tasks/{id}` |
| Delete task | DELETE | `/api/tasks/{id}` |
| Toggle done | PUT | `/api/tasks/{id}` with `{"done": true/false}` |
| Add subtask | POST | `/api/tasks/{id}/subtasks` |
| Toggle subtask | PUT | `/api/tasks/{id}/subtasks/{sub_id}` |
| Delete subtask | DELETE | `/api/tasks/{id}/subtasks/{sub_id}` |
| Reorder backlog | POST | `/api/tasks/reorder` |
| List projects | GET | `/api/projects` |
| Add project | POST | `/api/projects` |
| Edit project | PUT | `/api/projects/{id}` |
| Delete project | DELETE | `/api/projects/{id}` |
| Add entry | POST | `/api/projects/{id}/entries` |
| Delete entry | DELETE | `/api/projects/{id}/entries/{eid}` |

## Task Fields

```json
{
  "title": "string (required)",
  "date": "YYYY-MM-DD (default: today)",
  "priority": "P0 | P1 | P2 | P3 (default: P2)",
  "notes": "string (default: empty)",
  "type": "task | deadline | reminder | payment (default: task)",
  "recurrence": null | {"type": "weekly", "dow": 0-6} | {"type": "monthly", "day": 1-31} | {"type": "yearly", "month": 1-12, "day": 1-31}
}
```

**Types**: `task` = regular actionable, `deadline` = hard deadline, `reminder` = informational only, `payment` = bill tracker.

**Backlog**: Tasks with `type=task` + `priority=P3` appear in a persistent backlog panel (not calendar).

## Instructions

### Before any operation

Check the server is running:
```bash
curl -sf http://localhost:8000/api/tasks > /dev/null && echo "OK" || echo "Server not running — run: bun-do start"
```

### Add a task

```bash
curl -s -X POST http://localhost:8000/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Buy milk", "date": "2026-03-01", "priority": "P2", "type": "task"}'
```

### Add a recurring task

```bash
curl -s -X POST http://localhost:8000/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Pay rent", "date": "2026-02-28", "priority": "P1", "type": "payment", "recurrence": {"type": "monthly", "day": 28}}'
```

### Find a task by title (to get its ID)

```bash
curl -s http://localhost:8000/api/tasks | python3 -c "
import sys, json
for t in json.load(sys.stdin)['tasks']:
    if 'SEARCH_TERM' in t['title'].lower():
        print(t['id'], t['title'])
"
```

### Edit a task

Only send the fields you want to change:
```bash
curl -s -X PUT http://localhost:8000/api/tasks/TASK_ID \
  -H 'Content-Type: application/json' \
  -d '{"title": "New title", "priority": "P1"}'
```

### Mark done

```bash
curl -s -X PUT http://localhost:8000/api/tasks/TASK_ID \
  -H 'Content-Type: application/json' \
  -d '{"done": true}'
```

### Delete a task

```bash
curl -s -X DELETE http://localhost:8000/api/tasks/TASK_ID
```

### Add a subtask

```bash
curl -s -X POST http://localhost:8000/api/tasks/TASK_ID/subtasks \
  -H 'Content-Type: application/json' \
  -d '{"title": "Step one"}'
```

### Log project progress

```bash
# Find project ID
curl -s http://localhost:8000/api/projects | python3 -c "
import sys, json
for p in json.load(sys.stdin)['projects']:
    if 'PROJECT_NAME' in p['name'].lower():
        print(p['id'], p['name'])
"

# Add progress entry
curl -s -X POST http://localhost:8000/api/projects/PROJECT_ID/entries \
  -H 'Content-Type: application/json' \
  -d '{"summary": "Finished figures 1-3, updated results section"}'
```

### Create a project

```bash
curl -s -X POST http://localhost:8000/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"name": "my-project", "repo": "https://github.com/user/repo", "description": "Project description"}'
```

## Agent Workflow: Record Progress

When an agent finishes a coding session:

1. **Check server**: verify it's running
2. **Find the project** by name (or create it if new)
3. **Add an entry** summarizing what was accomplished
4. **Optionally update tasks**: mark done, add new tasks discovered during the session

## Tips

- Dates are ISO format: `YYYY-MM-DD`. Omit for today's date.
- The API returns the created/updated object on success.
- `GET /api/tasks` also runs carry-over (moves overdue non-recurring tasks to today).
- All IDs are UUIDs — always search by title first, never guess IDs.
