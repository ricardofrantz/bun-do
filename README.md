# Todo + Calendar (Hybrid Human + AI Agenda)

This repository stores a combined planning system: a personal visual agenda and a structured task list that can be edited by humans and automation (Claude/Codex).

## Overview

- `app.py` → Streamlit app with year/month/day views.
- `todo_data.json` → source-of-truth task data.
- `requirements.txt` → Python dependency list (`streamlit`).
- `autobkp/bin/todo` → launcher script to start the UI quickly (outside this repo).

The model is a hybrid:

- **Calendar mode:** each item has a date and is shown chronologically by month/day.
- **Todo mode:** each item has `priority`, optional notes, and a completion state.
- **AI-friendly:** tasks are plain JSON records that can be updated by code/CLI.

## Data format

Each row in `todo_data.json` follows:

```json
{
  "id": "uuid4",
  "title": "task title",
  "date": "YYYY-MM-DD",
  "priority": "P0|P1|P2|P3",
  "notes": "extra details (including time)",
  "done": false
}
```

Notes:

- Date is the anchor used by the calendar.
- Priority is sorted as `P0` (highest) to `P3` (lowest).
- You can encode extra time in `notes` (for example `13:15`, `afternoon`).
- `done` is used by the UI to mark completion and for filtering.

## Local usage

Run locally from repo root:

```bash
uv run streamlit run app.py
```

Or via helper launcher:

```bash
todo
```

You can override host and port:

```bash
TODO_HOST=0.0.0.0 TODO_PORT=8600 todo
```

The app applies a rollover rule: unfinished items from past dates are moved to today on each run.

## Human workflow

1. Open the Streamlit interface.
2. Add or update items with date, title, priority, and notes.
3. Check boxes to mark completion.
4. Use year/month/day drill-down to keep context and detail separate.

## AI/Codex workflow

1. Use the same JSON structure to add/update tasks in `todo_data.json`.
2. Commit edits as semantic, small changes.
3. Use clear titles and notes so the UI remains readable.

## GitHub backup workflow

This repo is tracked with GitHub and serves as backup/version history.

```bash
git status
git add todo_data.json app.py README.md
git commit -m "chore: update agenda"
git push
```

If you only modify data while talking to AI, keep the workflow narrow:

```bash
git add todo_data.json
git commit -m "data: add/update agenda items"
git push
```

## Repository intent

- Keep `todo_data.json` as the canonical schedule source.
- Keep `app.py` as the canonical visual layer.
- Use concise commits for traceability (especially when AI updates tasks).
