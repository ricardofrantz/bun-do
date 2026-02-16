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


def set_notice(message: str, level: str = "info") -> None:
    st.session_state["_todo_notice"] = {"message": message, "level": level}


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


def section(title: str, subtitle: str = "", motion_index: int = 0) -> None:
    delay = min(motion_index * 0.06, 0.7)
    heading = (
        "<div class='section-title task-enter' "
        f"style='animation-delay: {delay:.2f}s'>{title}</div>"
    )
    if subtitle:
        heading += (
            "<div class='section-subtitle task-enter' "
            f"style='animation-delay: {min(delay + 0.05, 0.7):.2f}s'>{subtitle}</div>"
        )
    st.markdown(heading, unsafe_allow_html=True)


def render_task_row(task: dict, show_done: bool, motion_index: int = 0) -> None:
    if task["done"] and not show_done:
        return

    due = iso_to_date(task["date"])
    delay = min(motion_index * 0.04, 0.5)
    delay_style = f"animation-delay: {delay:.2f}s"
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

        col_title.markdown(
            f"<div class='task-title task-enter' style='{delay_style}'>{title}</div>",
            unsafe_allow_html=True,
        )
        if task.get("notes"):
            col_title.caption(task["notes"])

        col_priority.markdown(priority_chip(task["priority"]), unsafe_allow_html=True)
        if col_delete.button(
            "🗑",
            key=f"delete_{task['id']}",
            use_container_width=True,
            help="Delete task",
        ):
            delete_task(task["id"])
            st.rerun()

        st.markdown(
            f"<div class='row-divider {row_cls} task-enter' style='{delay_style}'></div>",
            unsafe_allow_html=True,
        )


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
            section(
                f"{month_abbr[month]}",
                f"{len(month_tasks)} tasks · {remaining} remaining",
                motion_index=month,
            )

            by_day = defaultdict(list)
            for task in month_tasks:
                by_day[day_key(task)].append(task)

            for day_idx, day in enumerate(sorted(by_day), start=1):
                day_dt = iso_to_date(day)
                st.markdown(
                    (
                        "<div class='day-header task-enter' "
                        f"style='animation-delay: {min(day_idx * 0.05, 0.6):.2f}s'>"
                        f"{day_dt.strftime('%a %m/%d')}</div>"
                    ),
                    unsafe_allow_html=True,
                )
                for task_idx, task in enumerate(
                    sorted(
                        by_day[day],
                        key=lambda t: (PRIORITY_ORDER.get(t["priority"], 99), t["title"].lower()),
                    ),
                    start=1,
                ):
                    render_task_row(task, show_done, motion_index=((day_idx - 1) * 20) + task_idx)


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

    section(f"{month_abbr[month]} {year}", f"{len(grouped)} items", motion_index=month)
    for day in sorted(by_day):
        day_dt = iso_to_date(day)
        st.markdown(
            f"<div class='day-header'>{day_dt.strftime('%A, %b %d')}</div>",
            unsafe_allow_html=True,
        )
        for i, task in enumerate(sorted(by_day[day], key=lambda t: (PRIORITY_ORDER.get(t["priority"], 99), t["title"].lower()), start=1):
            render_task_row(task, show_done, i)


def render_day(tasks: list[dict], selected_day: date, show_done: bool) -> None:
    day_tasks = [
        t for t in tasks
        if iso_to_date(t["date"]) == selected_day and (show_done or not t["done"])
    ]
    if not day_tasks:
        st.info("No tasks for this day.")
        return

    section(selected_day.strftime("%A, %b %d"), f"{len(day_tasks)} tasks", motion_index=1)
    for i, task in enumerate(sorted(day_tasks, key=lambda t: (PRIORITY_ORDER.get(t["priority"], 99), t["title"].lower()), start=1):
        render_task_row(task, show_done=show_done, motion_index=i)


st.set_page_config(page_title="Todo Calendar", page_icon="🗓", layout="wide")

st.markdown(
    """
    <style>
        :root {
            --bg-start: #19131d;
            --bg-end: #2d2028;
            --panel: rgba(255, 255, 255, 0.08);
            --panel-border: rgba(255, 255, 255, 0.22);
            --muted: rgba(241, 221, 198, 0.72);
            --text: #f5f2ef;
            --text-soft: #d8c7b8;
            --accent: rgba(255, 178, 112, 0.95);
            --accent-soft: rgba(255, 211, 158, 0.16);
        }

        .stApp {
            background: radial-gradient(circle at 20% 20%, #3a2536 0%, var(--bg-start) 40%, var(--bg-end) 100%);
        }

        .block-container {
            padding-top: 1rem;
        }

        .main .block-container {
            max-width: 980px;
        }

        h1, h2, h3 {
            font-family: "SF Pro Display", "Inter", "Avenir Next", "Segoe UI", sans-serif;
            color: var(--text);
        }

        .title-row {
            margin-bottom: 0.55rem;
            padding: 0.85rem 1rem;
            border-radius: 16px;
            background: var(--panel);
            border: 1px solid var(--panel-border);
            backdrop-filter: blur(12px);
            box-shadow: inset 0 1px 0 var(--accent-soft);
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
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.02em;
            color: var(--text);
            margin-bottom: 0.2rem;
        }

        .section-subtitle {
            color: var(--text-soft);
            margin-bottom: 0.42rem;
            font-size: 0.86rem;
        }

        .task-enter {
            opacity: 0;
            transform: translateY(8px);
            animation: taskFadeIn 380ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
            animation-delay: var(--delay, 0s);
        }

        @keyframes taskFadeIn {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .day-header {
            color: var(--text-soft);
            margin: 0.48rem 0 0.12rem;
            font-weight: 600;
            font-size: 0.82rem;
        }

        .task-title {
            color: var(--text);
            font-size: 0.9rem;
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

        .todo-toast-wrap {
            position: fixed;
            top: 14px;
            right: 14px;
            z-index: 1000;
            pointer-events: none;
        }

        .todo-toast {
            padding: 0.52rem 0.78rem;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.25);
            background: rgba(14, 16, 24, 0.82);
            color: var(--text);
            font-size: 0.82rem;
            backdrop-filter: blur(8px);
            animation: toastIn 220ms ease, toastOut 220ms ease 1.35s forwards;
            pointer-events: auto;
        }

        .todo-toast--success {
            border-color: rgba(130, 255, 196, 0.35);
            box-shadow: 0 6px 18px rgba(130, 255, 196, 0.18);
        }

        .todo-toast--info {
            border-color: rgba(173, 216, 255, 0.35);
            box-shadow: 0 6px 18px rgba(173, 216, 255, 0.18);
        }

        @keyframes toastIn {
            from {
                transform: translateX(8px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes toastOut {
            from {
                opacity: 1;
            }
            to {
                opacity: 0;
            }
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
            backdrop-filter: blur(6px);
            transition: all 150ms ease;
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        .stFormSubmitButton > button:hover {
            border-color: var(--accent);
            transform: translateY(-1px);
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

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stDateInput"] input:focus,
        div[data-testid="stSelectbox"] > div:focus-within,
        div[data-testid="stTextArea"] textarea:focus,
        button:focus-visible {
            outline: 1px solid rgba(64, 156, 255, 0.9);
            outline-offset: 0;
            box-shadow: 0 0 0 3px rgba(64, 156, 255, 0.24);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

st.session_state.setdefault("view", "Year")
notice = st.session_state.pop("_todo_notice", None)
if notice and notice.get("message"):
    level = notice.get("level", "info")
    if level not in {"success", "info"}:
        level = "info"
    st.markdown(
        "<div class='todo-toast-wrap'>"
        f"<div class='todo-toast todo-toast--{level}'>"
        f"{notice['message']}"
        "</div></div>",
        unsafe_allow_html=True,
    )

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
          <div class="title-sub">Keyboard: Tab/Enter in forms, Space checks, Esc dismisses modal prompts.</div>
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

if st.sidebar.button("Today", help="Jump to today"):
    st.session_state.view = "Day"
    st.session_state.year_selector = today.year
    st.session_state.month_selector = today.month
    st.session_state.day_selector = today
    set_notice("Jumped to today", "success")
    st.rerun()

icon_bar = st.sidebar.container()
with icon_bar:
    c1, c2 = st.columns(2)
    if c1.button("⟳", help="Reload data from disk"):
        st.session_state.tasks = load_tasks()
        set_notice("Reloaded from disk", "success")
        st.rerun()
    if c2.button("🧹", help="Clear completed tasks"):
        st.session_state.tasks = [t for t in st.session_state.tasks if not t["done"]]
        save_tasks(st.session_state.tasks)
        set_notice("Cleared completed tasks", "success")
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
    set_notice("Task added", "success")
    st.rerun()

# Extra controls for non-year views
if view == "Month":
    selected_month = st.sidebar.slider("Month", 1, 12, today.month, key="month_selector")
else:
    selected_month = today.month

if view == "Day":
    selected_day = st.sidebar.date_input(
        "Day",
        value=today,
        key="day_selector",
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
