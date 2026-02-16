from __future__ import annotations

from collections import defaultdict
from datetime import date
from calendar import month_abbr
from collections import Counter
from pathlib import Path
import json
import uuid

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
        tasks = json.load(f)

    normalized: list[dict] = []
    for item in tasks:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "id": item.get("id") or str(uuid.uuid4()),
                "title": str(item.get("title", "")).strip() or "Untitled task",
                "date": iso_to_date(item.get("date", date.today().isoformat())).isoformat(),
                "priority": item.get("priority", "P2") if item.get("priority", "P2") in PRIORITY_LABELS else "P2",
                "notes": str(item.get("notes", "")).strip(),
                "done": bool(item.get("done", False)),
            }
        )
    return normalized


def save_tasks(tasks: list[dict]) -> None:
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


def advance_unfinished_tasks(tasks: list[dict], today: date) -> int:
    moved = 0
    for task in tasks:
        if task["done"]:
            continue
        due = iso_to_date(task["date"])
        if due < today:
            task["date"] = today.isoformat()
            moved += 1
    if moved:
        save_tasks(tasks)
    return moved


def sort_tasks(tasks: list[dict]) -> list[dict]:
    return sorted(
        tasks,
        key=lambda task: (
            iso_to_date(task["date"]),
            PRIORITY_ORDER.get(task.get("priority", "P2"), 99),
            task.get("title", "").lower(),
        ),
    )


def task_month_key(task: dict) -> str:
    return iso_to_date(task["date"]).strftime("%Y-%m")


def task_day_key(task: dict) -> str:
    return iso_to_date(task["date"]).strftime("%Y-%m-%d")


def toggle_done(task_id: str) -> None:
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["done"] = bool(st.session_state[f"done_{task_id}"])
            break
    save_tasks(st.session_state.tasks)


def delete_task(task_id: str) -> None:
    st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_id]
    save_tasks(st.session_state.tasks)


def render_task_row(task: dict, show_notes: bool) -> None:
    cols = st.columns([0.55, 1, 0.9, 0.9, 4, 1])
    done_key = f"done_{task['id']}"
    cols[0].checkbox(
        label="Done",
        value=task["done"],
        key=done_key,
        on_change=toggle_done,
        args=(task["id"],),
        label_visibility="collapsed",
    )
    cols[1].caption(iso_to_date(task["date"]).strftime("%Y-%m-%d"))
    cols[2].caption(task["priority"])
    cols[3].caption(f"{'✅' if task['done'] else '◯'}")
    cols[4].markdown(f"**{task['title']}**")
    cols[5].button("Delete", key=f"delete_{task['id']}", on_click=delete_task, args=(task["id"],))

    if show_notes:
        st.write(task["notes"] or "—")


def render_month_summary(year: int, tasks: list[dict], include_done: bool, detail_mode: str) -> None:
    year_tasks = [t for t in tasks if iso_to_date(t["date"]).year == year]
    if not include_done:
        year_tasks = [t for t in year_tasks if not t["done"]]
    year_tasks = sort_tasks(year_tasks)

    if not year_tasks:
        st.info("No tasks in the selected year with current filters.")
        return

    total_counts = Counter(t["priority"] for t in year_tasks)
    done_count = sum(1 for t in year_tasks if t["done"])

    st.metric("Tasks in year", len(year_tasks))
    st.metric("Done", done_count)
    st.write(
        f"Priority mix: P0={total_counts['P0']} | P1={total_counts['P1']} | "
        f"P2={total_counts['P2']} | P3={total_counts['P3']}"
    )
    st.divider()

    grouped = defaultdict(list)
    for task in year_tasks:
        grouped[task_month_key(task)].append(task)

    for month in [f"{year}-{m:02d}" for m in range(1, 13)]:
        month_tasks = grouped.get(month, [])
        month_name = month_abbr[int(month[-2:])]
        completed = sum(1 for t in month_tasks if t["done"])
        with st.expander(f"{month_name} {month} — {len(month_tasks)} tasks ({completed} done)", expanded=False):
            if not month_tasks:
                st.caption("No tasks.")
                continue
            for task in month_tasks:
                render_task_row(task, show_notes=(detail_mode == "Detailed"))
            if st.button("Open this month in detail", key=f"open_{month}"):
                st.session_state.current_view = "Month agenda"
                st.session_state.current_month = int(month[-2:])
                st.rerun()


def render_month_view(year: int, month: int, tasks: list[dict], include_done: bool, detail_mode: str) -> None:
    month_tasks = [
        t for t in tasks if iso_to_date(t["date"]).year == year and iso_to_date(t["date"]).month == month
    ]
    if not include_done:
        month_tasks = [t for t in month_tasks if not t["done"]]
    month_tasks = sort_tasks(month_tasks)

    st.subheader(f"{month_abbr[month]} {year}")
    if not month_tasks:
        st.info("No tasks for this month with current filters.")
        return

    grouped = defaultdict(list)
    for task in month_tasks:
        grouped[task_day_key(task)].append(task)

    for day_key in sorted(grouped.keys()):
        day_tasks = grouped[day_key]
        done_day = sum(1 for t in day_tasks if t["done"])
        with st.expander(f"{day_key} — {len(day_tasks)} tasks ({done_day} done)", expanded=False):
            for task in day_tasks:
                render_task_row(task, show_notes=(detail_mode == "Detailed"))


def render_day_view(year: int, selected_day: date, tasks: list[dict], include_done: bool, detail_mode: str) -> None:
    day_tasks = [t for t in tasks if iso_to_date(t["date"]) == selected_day]
    if not include_done:
        day_tasks = [t for t in day_tasks if not t["done"]]
    day_tasks = sort_tasks(day_tasks)

    st.subheader(f"{selected_day.isoformat()} task detail")
    if not day_tasks:
        st.info("No tasks for the selected day with current filters.")
        return

    for task in day_tasks:
        with st.expander(f"{task['priority']} | {task['title']}", expanded=True):
            render_task_row(task, show_notes=(detail_mode == "Detailed"))


def sync_to_current_date(today: date) -> None:
    last_sync = st.session_state.get("agenda_last_sync")
    if last_sync == today.isoformat():
        return

    st.session_state.agenda_last_sync = today.isoformat()
    st.session_state.current_year = today.year
    st.session_state.current_month = today.month
    st.session_state.current_day = today


# ---- App state ----
st.set_page_config(page_title="Year Todo Agenda", page_icon="🗓", layout="wide")
st.title("Year Todo Agenda")

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

today = date.today()
rolled_count = advance_unfinished_tasks(st.session_state.tasks, today)
if rolled_count:
    st.caption(f"Carried forward {rolled_count} unfinished task(s) to today ({today}).")
sync_to_current_date(today)

st.sidebar.header("Controls")
default_year = today.year
years = sorted({iso_to_date(task["date"]).year for task in st.session_state.tasks} | {default_year})
st.session_state.setdefault("current_year", default_year)
selected_year = st.sidebar.selectbox(
    "Year",
    years,
    index=years.index(st.session_state.current_year) if st.session_state.current_year in years else years.index(default_year),
    key="year_selector",
)
st.session_state.current_year = selected_year

st.session_state.setdefault("current_view", "Year overview")
st.session_state.setdefault("current_month", today.month)
st.session_state.setdefault("current_day", today)
view = st.sidebar.radio(
    "Agenda depth",
    ["Year overview", "Month agenda", "Day agenda"],
    index=["Year overview", "Month agenda", "Day agenda"].index(st.session_state.current_view)
)
st.session_state.current_view = view

detail_mode = st.sidebar.radio("Task detail", ["Compact", "Detailed"], index=0)
include_done = st.sidebar.toggle("Show completed", value=False)

st.sidebar.markdown("---")
st.subheader("Add task")
with st.sidebar.form("new_task", clear_on_submit=True):
    title = st.text_input("Task", placeholder="Draft monthly architecture review")
    due = st.date_input("Due date", value=today)
    priority = st.selectbox("Priority", options=PRIORITY_LABELS, index=2)
    notes = st.text_area("Notes", placeholder="Optional context", height=72)
    submitted = st.form_submit_button("Add task")

if submitted:
    if title.strip():
        st.session_state.tasks.append(
            {
                "id": str(uuid.uuid4()),
                "title": title.strip(),
                "date": due.isoformat(),
                "priority": priority,
                "notes": notes.strip(),
                "done": False,
            }
        )
        save_tasks(st.session_state.tasks)
        st.rerun()

st.divider()

all_tasks = sort_tasks(st.session_state.tasks)

if not all_tasks:
    st.info("No tasks yet. Add your first task to start building your yearly agenda.")
else:
    if view == "Year overview":
        render_month_summary(selected_year, all_tasks, include_done, detail_mode)
    elif view == "Month agenda":
        selected_month = st.sidebar.selectbox(
            "Month",
            list(range(1, 13)),
            index=st.session_state.current_month - 1,
            format_func=lambda m: month_abbr[m],
            key="month_selector",
        )
        st.session_state.current_month = selected_month
        render_month_view(selected_year, selected_month, all_tasks, include_done, detail_mode)
    else:
        default_day = st.session_state.current_day
        if isinstance(default_day, str):
            default_day = iso_to_date(default_day)
        selected_day = st.sidebar.date_input(
            "Day",
            value=default_day,
            min_value=date(selected_year, 1, 1),
            max_value=date(selected_year, 12, 31),
            key="day_selector",
        )
        st.session_state.current_day = selected_day
        if selected_day.year != selected_year:
            selected_day = selected_day.replace(year=selected_year)
        render_day_view(selected_day.year, selected_day, all_tasks, include_done, detail_mode)

total_tasks = len(all_tasks)
done_tasks = sum(1 for t in all_tasks if t["done"])
remaining = total_tasks - done_tasks
st.caption(f"Total: {total_tasks} | Done: {done_tasks} | Remaining: {remaining}")
