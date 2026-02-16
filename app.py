from __future__ import annotations

from collections import defaultdict
from calendar import month_abbr
from datetime import date
from pathlib import Path
import json
from uuid import uuid4

import streamlit as st


DATA_PATH = Path(__file__).resolve().parent / "todo_data.json"
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
PRIORITY_LABELS = list(PRIORITY_ORDER)


def iso_to_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return date.fromisoformat(value)
    except ValueError:
        return date.today()


def load_tasks() -> list[dict]:
    if not DATA_PATH.exists():
        return []

    with DATA_PATH.open("r", encoding="utf-8") as f:
        try:
            raw_tasks = json.load(f)
        except json.JSONDecodeError:
            return []

    tasks: list[dict] = []
    for item in raw_tasks:
        if not isinstance(item, dict):
            continue
        tasks.append(
            {
                "id": item.get("id") or str(uuid4()),
                "title": str(item.get("title", "")).strip() or "Untitled task",
                "date": iso_to_date(item.get("date", date.today().isoformat())).isoformat(),
                "priority": item.get("priority", "P2") if item.get("priority", "P2") in PRIORITY_LABELS else "P2",
                "notes": str(item.get("notes", "")).strip(),
                "done": bool(item.get("done", False)),
            }
        )
    return tasks


def save_tasks(tasks: list[dict]) -> None:
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


def carry_over_unfinished(tasks: list[dict], today: date) -> int:
    moved = 0
    for task in tasks:
        if task["done"]:
            continue
        if iso_to_date(task["date"]) < today:
            task["date"] = today.isoformat()
            moved += 1
    if moved:
        save_tasks(tasks)
    return moved


def sort_tasks(tasks: list[dict]) -> list[dict]:
    return sorted(
        tasks,
        key=lambda t: (iso_to_date(t["date"]), PRIORITY_ORDER.get(t.get("priority", "P2"), 99), t.get("title", "").lower()),
    )


def toggle_done(task_id: str) -> None:
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["done"] = bool(st.session_state[f"done_{task_id}"])
            break
    save_tasks(st.session_state.tasks)


def delete_task(task_id: str) -> None:
    st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_id]
    save_tasks(st.session_state.tasks)


def month_key(task: dict) -> str:
    due = iso_to_date(task["date"])
    return f"{due.year}-{due.month:02d}"


def day_key(task: dict) -> str:
    return iso_to_date(task["date"]).strftime("%Y-%m-%d")


def render_task_row(task: dict, show_done: bool) -> None:
    if task["done"] and not show_done:
        return

    cols = st.columns([0.07, 0.18, 0.10, 0.60, 0.05], gap="small")
    checked = cols[0].checkbox(
        label="",
        value=task["done"],
        key=f"done_{task['id']}",
        on_change=toggle_done,
        args=(task["id"],),
        label_visibility="collapsed",
    )

    due = iso_to_date(task["date"]).strftime("%m-%d")
    text = f"{task['title']}"
    if task["done"]:
        text = f"~~{text}~~"

    cols[1].markdown(due)
    cols[2].markdown(task["priority"])
    cols[3].markdown(text)
    cols[4].button("✕", key=f"delete_{task['id']}", on_click=delete_task, args=(task["id"],), use_container_width=True)

    if checked:
        return


def render_year(tasks: list[dict], year: int, show_done: bool) -> None:
    visible = [t for t in tasks if iso_to_date(t["date"]).year == year]
    grouped_months = defaultdict(list)
    for task in visible:
        grouped_months[month_key(task)].append(task)

    for m in range(1, 13):
        key = f"{year}-{m:02d}"
        month_tasks = grouped_months.get(key, [])
        if not month_tasks:
            continue

        done_count = sum(1 for t in month_tasks if t["done"])
        st.markdown(f"## {month_abbr[m]} · {len(month_tasks)}")
        if done_count and not show_done:
            st.caption(f"{len(month_tasks)-done_count} remaining")

        by_day = defaultdict(list)
        for task in month_tasks:
            by_day[day_key(task)].append(task)

        for day in sorted(by_day):
            st.markdown(f"**{day}**")
            for task in sorted(by_day[day], key=lambda t: (PRIORITY_ORDER.get(t["priority"], 99), t["title"].lower())):
                render_task_row(task, show_done)


def render_month(tasks: list[dict], year: int, month: int, show_done: bool) -> None:
    grouped = [t for t in tasks if iso_to_date(t["date"]).year == year and iso_to_date(t["date"]).month == month]
    by_day = defaultdict(list)
    for task in grouped:
        by_day[day_key(task)].append(task)

    if not by_day:
        st.info("No tasks this month.")
        return

    for day in sorted(by_day):
        st.markdown(f"**{day}**")
        for task in sorted(by_day[day], key=lambda t: (PRIORITY_ORDER.get(t["priority"], 99), t["title"].lower())):
            render_task_row(task, show_done)


def render_day(tasks: list[dict], selected_day: date, show_done: bool) -> None:
    day_tasks = [
        t for t in tasks
        if iso_to_date(t["date"]) == selected_day and (show_done or not t["done"])
    ]
    if not day_tasks:
        st.info("No tasks for this day.")
        return

    for task in sorted(day_tasks, key=lambda t: (PRIORITY_ORDER.get(t["priority"], 99), t["title"].lower())):
        render_task_row(task, show_done=True)


# ---------- UI ----------
st.set_page_config(page_title="Todo Calendar", page_icon="🗓", layout="centered")
st.title("Todo Calendar")

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

today = date.today()
moved = carry_over_unfinished(st.session_state.tasks, today)
if moved:
    st.caption(f"{moved} unfinished item(s) moved to {today}")

st.session_state.tasks = sort_tasks(st.session_state.tasks)

# Sidebar
st.sidebar.subheader("Controls")
years = sorted({iso_to_date(t["date"]).year for t in st.session_state.tasks} | {today.year})
selected_year = st.sidebar.selectbox("Year", years, index=years.index(today.year))
view = st.sidebar.radio("View", ["Year", "Month", "Day"], index=0)
show_done = st.sidebar.toggle("Show done", value=False)
if st.sidebar.button("Reload from disk", help="Re-read todo_data.json from disk"):
    st.session_state.tasks = load_tasks()
    st.rerun()

st.sidebar.subheader("Add task")
with st.sidebar.form("add_task", clear_on_submit=True):
    title = st.text_input("Title", placeholder="Task")
    due = st.date_input("Date", value=today)
    priority = st.selectbox("Priority", options=PRIORITY_LABELS, index=2)
    notes = st.text_input("Notes (optional)")
    add = st.form_submit_button("Add")

if add and title.strip():
    st.session_state.tasks.append(
        {
            "id": str(uuid4()),
            "title": title.strip(),
            "date": due.isoformat(),
            "priority": priority,
            "notes": notes.strip(),
            "done": False,
        }
    )
    save_tasks(st.session_state.tasks)
    st.rerun()

# Main content
if not st.session_state.tasks:
    st.info("No tasks yet.")
else:
    if view == "Year":
        render_year(st.session_state.tasks, selected_year, show_done)
    elif view == "Month":
        month = st.sidebar.slider("Month", 1, 12, today.month, format="%02d")
        render_month(st.session_state.tasks, selected_year, month, show_done)
    else:
        selected_day = st.sidebar.date_input("Day", value=today, min_value=date(selected_year, 1, 1), max_value=date(selected_year, 12, 31))
        render_day(st.session_state.tasks, selected_day, show_done)

all_tasks = len(st.session_state.tasks)
done = sum(1 for t in st.session_state.tasks if t["done"])
st.caption(f"Total: {all_tasks} | Done: {done} | Remaining: {all_tasks-done}")
