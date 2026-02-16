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

PRIORITY_STYLE = {
    "P0": {"bg": "#ff5f57", "fg": "#fff"},
    "P1": {"bg": "#ffbd2e", "fg": "#fff"},
    "P2": {"bg": "#5ac8fa", "fg": "#fff"},
    "P3": {"bg": "#8e8e93", "fg": "#fff"},
}


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
        key=lambda t: (
            iso_to_date(t["date"]),
            PRIORITY_ORDER.get(t.get("priority", "P2"), 99),
            t.get("title", "").lower(),
        ),
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


def priority_chip(priority: str) -> str:
    style = PRIORITY_STYLE.get(priority, PRIORITY_STYLE["P3"])
    return f"<span class='priority-chip' style='background:{style['bg']};color:{style['fg']};'>{priority}</span>"


def section(title: str, subtitle: str = "") -> None:
    heading = f"<div class='section-title'>{title}</div>"
    if subtitle:
        heading += f"<div class='section-subtitle'>{subtitle}</div>"
    st.markdown(heading, unsafe_allow_html=True)


def render_task_row(task: dict, show_done: bool) -> None:
    if task["done"] and not show_done:
        return

    due = iso_to_date(task["date"])
    row_cls = "done" if task["done"] else "active"
    container = st.container(border=True)
    with container:
        col_done, col_time, col_title, col_priority, col_delete = st.columns(
            [0.55, 1.1, 3.4, 0.9, 0.6],
            gap="small",
        )

        col_done.checkbox(
            label="",
            value=task["done"],
            key=f"done_{task['id']}",
            on_change=toggle_done,
            args=(task["id"],),
            label_visibility="collapsed",
        )
        col_time.caption(due.strftime("%m/%d"))

        title = task["title"]
        if task["done"]:
            title = f"<span class='task-done'>{title}</span>"
        else:
            title = f"<span class='{row_cls}'>{title}</span>"

        col_title.markdown(f"<div class='task-title'>{title}</div>", unsafe_allow_html=True)
        if task.get("notes"):
            col_title.caption(task["notes"])

        col_priority.markdown(priority_chip(task["priority"]), unsafe_allow_html=True)
        if col_delete.button("×", key=f"delete_{task['id']}", use_container_width=True):
            delete_task(task["id"])
            st.rerun()

        st.markdown(f"<div class='row-divider {row_cls}'></div>", unsafe_allow_html=True)


def render_year(tasks: list[dict], year: int, show_done: bool) -> None:
    visible = [t for t in tasks if iso_to_date(t["date"]).year == year]
    if not visible:
        st.info("No tasks for this year.")
        return

    grouped_months = defaultdict(list)
    for task in visible:
        grouped_months[month_key(task)].append(task)

    for month in range(1, 13):
        key = f"{year}-{month:02d}"
        month_tasks = grouped_months.get(key, [])
        if not month_tasks:
            continue

        remaining = len([t for t in month_tasks if not t["done"]])
        mbox = st.container(border=True)
        with mbox:
            section(f"{month_abbr[month]}", f"{len(month_tasks)} tasks · {remaining} remaining")

            by_day = defaultdict(list)
            for task in month_tasks:
                by_day[day_key(task)].append(task)

            for day in sorted(by_day):
                day_dt = iso_to_date(day)
                st.markdown(
                    f"<div class='day-header'>{day_dt.strftime('%a %m/%d')}</div>",
                    unsafe_allow_html=True,
                )
                for task in sorted(by_day[day], key=lambda t: (PRIORITY_ORDER.get(t["priority"], 99), t["title"].lower())):
                    render_task_row(task, show_done)


def render_month(tasks: list[dict], year: int, month: int, show_done: bool) -> None:
    grouped = [
        t for t in tasks
        if iso_to_date(t["date"]).year == year and iso_to_date(t["date"]).month == month
    ]
    if not grouped:
        st.info("No tasks for this month.")
        return

    by_day = defaultdict(list)
    for task in grouped:
        by_day[day_key(task)].append(task)

    section(f"{month_abbr[month]} {year}", f"{len(grouped)} items")
    for day in sorted(by_day):
        day_dt = iso_to_date(day)
        st.markdown(f"<div class='day-header'>{day_dt.strftime('%A, %b %d')}</div>", unsafe_allow_html=True)
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

    section(selected_day.strftime("%A, %b %d"), f"{len(day_tasks)} tasks")
    for task in sorted(day_tasks, key=lambda t: (PRIORITY_ORDER.get(t["priority"], 99), t["title"].lower())):
        render_task_row(task, show_done=True)


st.set_page_config(page_title="Todo Calendar", page_icon="🗓", layout="wide")

st.markdown(
    """
    <style>
        :root {
            --bg-start: #0f1320;
            --bg-end: #1b2338;
            --panel: rgba(255, 255, 255, 0.10);
            --panel-border: rgba(255, 255, 255, 0.18);
            --muted: rgba(235, 235, 245, 0.72);
            --text: #f5f5f7;
            --text-soft: #c8c9cc;
        }

        .stApp {
            background: radial-gradient(circle at 20% 20%, #2d334a 0%, var(--bg-start) 40%, var(--bg-end) 100%);
        }

        .block-container {
            padding-top: 1.4rem;
        }

        .main .block-container {
            max-width: 1100px;
        }

        h1, h2, h3 {
            font-family: "SF Pro Display", "Inter", "Avenir Next", "Segoe UI", sans-serif;
            color: var(--text);
        }

        .title-row {
            margin-bottom: 0.75rem;
            padding: 1rem 1.2rem;
            border-radius: 20px;
            background: var(--panel);
            border: 1px solid var(--panel-border);
            backdrop-filter: blur(12px);
        }

        .title-row h1 {
            margin: 0;
        }

        .title-sub {
            margin-top: 0.25rem;
            color: var(--muted);
            font-size: 0.95rem;
        }

        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            color: var(--text);
            margin-bottom: 0.2rem;
        }

        .section-subtitle {
            color: var(--text-soft);
            margin-bottom: 0.6rem;
            font-size: 0.86rem;
        }

        .day-header {
            color: var(--text-soft);
            margin: 0.6rem 0 0.15rem;
            font-weight: 600;
            font-size: 0.88rem;
        }

        .task-title {
            color: var(--text);
            font-size: 0.95rem;
            font-weight: 600;
        }

        .task-done {
            color: rgba(220, 220, 224, 0.65);
            text-decoration: line-through;
        }

        .priority-chip {
            display: inline-flex;
            border-radius: 999px;
            padding: 0.25rem 0.62rem;
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .row-divider {
            margin-top: 0.35rem;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            opacity: 0.65;
        }

        .row-divider.done {
            opacity: 0.3;
        }

        .stButton > button,
        .stDownloadButton > button,
        .stFormSubmitButton > button {
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.15);
            color: #ffffff;
        }

        div[data-testid="stSidebar"] {
            background: rgba(13, 16, 27, 0.85);
        }

        div[data-testid="stSidebar"] .stMarkdown,
        div[data-testid="stSidebar"] label,
        div[data-testid="stSidebar"] p {
            color: #ffffff;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stDateInput"] input,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] {
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

st.session_state.setdefault("view", "Year")

# Header
today = date.today()
moved = carry_over_unfinished(st.session_state.tasks, today)
if moved:
    st.caption(f"{moved} unfinished item(s) moved to {today}")

st.session_state.tasks = sort_tasks(st.session_state.tasks)

header = st.container()
with header:
    st.markdown(
        """
        <div class="title-row">
          <h1>Todo + Calendar</h1>
          <div class="title-sub">Human-friendly planning interface with AI-safe plain JSON storage.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Sidebar controls
years = sorted({iso_to_date(task["date"]).year for task in st.session_state.tasks} | {today.year})
st.sidebar.selectbox("Year", years, index=years.index(today.year), key="year_selector")
selected_year = st.session_state.year_selector
view = st.sidebar.radio("Mode", ["Year", "Month", "Day"], index=["Year", "Month", "Day"].index(st.session_state.view))
st.session_state.view = view
show_done = st.sidebar.toggle("Show completed", value=False)

if st.sidebar.button("Reload from disk", help="Re-read todo_data.json and refresh view"):
    st.session_state.tasks = load_tasks()
    st.rerun()

st.sidebar.markdown("—")
st.sidebar.subheader("Add task")
with st.sidebar.form("add_task", clear_on_submit=True):
    title = st.text_input("Title", placeholder="Task title")
    due = st.date_input("Date", value=today)
    priority = st.selectbox("Priority", options=PRIORITY_LABELS, index=2)
    notes = st.text_input("Notes", placeholder="optional")
    add = st.form_submit_button("Add task")

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

# Extra controls for non-year views
if view == "Month":
    selected_month = st.sidebar.slider("Month", 1, 12, today.month)
else:
    selected_month = today.month

if view == "Day":
    selected_day = st.sidebar.date_input(
        "Day",
        value=today,
        min_value=date(selected_year, 1, 1),
        max_value=date(selected_year, 12, 31),
    )
else:
    selected_day = today

# Main content
if not st.session_state.tasks:
    st.info("No tasks yet.")
else:
    if view == "Year":
        render_year(st.session_state.tasks, selected_year, show_done)
    elif view == "Month":
        render_month(st.session_state.tasks, selected_year, selected_month, show_done)
    else:
        render_day(st.session_state.tasks, selected_day, show_done)

all_tasks = len(st.session_state.tasks)
done = sum(1 for task in st.session_state.tasks if task["done"])
remaining = all_tasks - done

summary = st.container()
with summary:
    st.markdown(
        f"<div style='color: var(--text-soft); margin-top: 1rem; font-size: 0.88rem;'>"
        f"Total: {all_tasks} · Done: {done} · Remaining: {remaining}"
        "</div>",
        unsafe_allow_html=True,
    )
