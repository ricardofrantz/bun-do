from __future__ import annotations

from collections import Counter, defaultdict
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
        items = json.load(f)

    normalized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized.append(
            {
                "id": item.get("id") or str(uuid4()),
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


def sorted_tasks(tasks: list[dict]) -> list[dict]:
    return sorted(
        tasks,
        key=lambda t: (iso_to_date(t["date"]), PRIORITY_ORDER.get(t.get("priority", "P2"), 99), t["title"].lower()),
    )


def rollover_unfinished(tasks: list[dict], today: date) -> int:
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


def month_key(task: dict) -> str:
    return iso_to_date(task["date"]).strftime("%Y-%m")


def day_key(task: dict) -> str:
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


def render_task(task: dict) -> None:
    cols = st.columns([0.52, 1.35, 0.6, 0.42], vertical_alignment="center")
    d = iso_to_date(task["date"])
    checked = cols[0].checkbox(
        label="",
        value=task["done"],
        key=f"done_{task['id']}",
        on_change=toggle_done,
        args=(task["id"],),
        label_visibility="collapsed",
    )
    cols[1].markdown(f"**{d.isoformat()}**  ·  **{task['title']}**")
    cols[2].write(task["priority"])
    cols[3].button("🗑", key=f"delete_{task['id']}", on_click=delete_task, args=(task["id"],))
    if task["notes"]:
        st.caption(task["notes"])


def render_year_view(selected_year: int, tasks: list[dict], include_done: bool) -> None:
    year_tasks = [t for t in tasks if iso_to_date(t["date"]).year == selected_year]
    if not include_done:
        year_tasks = [t for t in year_tasks if not t["done"]]
    year_tasks = sorted_tasks(year_tasks)

    if not year_tasks:
        st.info("No tasks for this year.")
        return

    grouped = defaultdict(list)
    for task in year_tasks:
        grouped[month_key(task)].append(task)

    for m in [f"{selected_year}-{mm:02d}" for mm in range(1, 13)]:
        month_tasks = grouped.get(m, [])
        done_count = sum(1 for t in month_tasks if t["done"])
        with st.expander(f"{month_abbr[int(m[-2:])]} {m} · {len(month_tasks)} tasks ({done_count} done)", expanded=False):
            if not month_tasks:
                st.caption("No tasks")
                continue

            day_groups = defaultdict(list)
            for task in month_tasks:
                day_groups[day_key(task)].append(task)

            for day in sorted(day_groups):
                tasks_day = day_groups[day]
                done_day = sum(1 for t in tasks_day if t["done"])
                with st.expander(f"{day} · {len(tasks_day)} ({done_day} done)", expanded=False):
                    for task in tasks_day:
                        render_task(task)


def render_month_view(selected_year: int, selected_month: int, tasks: list[dict], include_done: bool) -> None:
    month_tasks = [t for t in tasks if iso_to_date(t["date"]).year == selected_year and iso_to_date(t["date"]).month == selected_month]
    if not include_done:
        month_tasks = [t for t in month_tasks if not t["done"]]
    month_tasks = sorted_tasks(month_tasks)

    if not month_tasks:
        st.info("No tasks for this month.")
        return

    day_groups = defaultdict(list)
    for task in month_tasks:
        day_groups[day_key(task)].append(task)

    for day in sorted(day_groups):
        with st.expander(day, expanded=True):
            for task in day_groups[day]:
                render_task(task)


def render_day_view(selected_day: date, tasks: list[dict], include_done: bool) -> None:
    day_tasks = [t for t in tasks if iso_to_date(t["date"]) == selected_day]
    if not include_done:
        day_tasks = [t for t in day_tasks if not t["done"]]
    day_tasks = sorted_tasks(day_tasks)

    if not day_tasks:
        st.info("No tasks for this day.")
        return

    for task in day_tasks:
        render_task(task)


# App setup
st.set_page_config(page_title="Todo Calendar", layout="wide")
st.title("Todo Calendar")

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

today = date.today()
rollover_count = rollover_unfinished(st.session_state.tasks, today)
if rollover_count:
    st.caption(f"Carried forward {rollover_count} unfinished task(s) to {today}")

# Sidebar controls
st.sidebar.header("Controls")
years = sorted({iso_to_date(t["date"]).year for t in st.session_state.tasks} | {today.year})
selected_year = st.sidebar.selectbox("Year", years, index=years.index(today.year) if today.year in years else 0)
st.session_state.setdefault("view", "Year")
view = st.sidebar.radio("Depth", ["Year", "Month", "Day"], index=["Year", "Month", "Day"].index(st.session_state.view))
st.session_state.view = view
show_done = st.sidebar.toggle("Show done", value=False)

st.sidebar.markdown("---")
st.sidebar.subheader("Add")
with st.sidebar.form("add_task"):
    title = st.text_input("Title")
    due = st.date_input("Date", value=today)
    priority = st.selectbox("Priority", options=PRIORITY_LABELS, index=2)
    notes = st.text_area("Notes", value="", height=72)
    submit = st.form_submit_button("Add")

if submit and title.strip():
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

# Content
all_tasks = sorted_tasks(st.session_state.tasks)
if not all_tasks:
    st.info("No entries yet.")
else:
    if view == "Year":
        render_year_view(selected_year, all_tasks, show_done)
    elif view == "Month":
        selected_month = st.sidebar.selectbox(
            "Month",
            range(1, 13),
            index=today.month - 1,
            format_func=lambda m: month_abbr[m],
        )
        render_month_view(selected_year, selected_month, all_tasks, show_done)
    else:
        selected_day = st.sidebar.date_input(
            "Day",
            value=date(selected_year, today.month, min(today.day, 28)),
            min_value=date(selected_year, 1, 1),
            max_value=date(selected_year, 12, 31),
        )
        if selected_day.year != selected_year:
            selected_day = selected_day.replace(year=selected_year)
        render_day_view(selected_day, all_tasks, show_done)

total = len(all_tasks)
done = sum(1 for t in all_tasks if t["done"])
st.caption(f"Total: {total} | Done: {done} | Remaining: {total - done}")
