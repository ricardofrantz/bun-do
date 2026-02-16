from __future__ import annotations

from collections import defaultdict
from datetime import date
from pathlib import Path
import json
import uuid

import streamlit as st


DATA_PATH = Path(__file__).resolve().parent / "todo_data.json"

PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
PRIORITY_LABELS = list(PRIORITY_ORDER)


def load_tasks() -> list[dict]:
    if not DATA_PATH.exists():
        return []

    with DATA_PATH.open("r", encoding="utf-8") as f:
        tasks = json.load(f)

    # Ensure all rows have expected fields for UI compatibility.
    for item in tasks:
        item.setdefault("notes", "")
        item.setdefault("done", False)
    return tasks


def save_tasks(tasks: list[dict]) -> None:
    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)


def iso_to_date(value: str) -> date:
    return date.fromisoformat(value)


def sort_tasks(tasks: list[dict]) -> list[dict]:
    return sorted(
        tasks,
        key=lambda t: (
            iso_to_date(t["date"]),
            PRIORITY_ORDER.get(t["priority"], 99),
            t["title"].lower(),
        ),
    )


def toggle_done(task_id: str) -> None:
    for task in st.session_state.tasks:
        if task["id"] == task_id:
            task["done"] = st.session_state[f"done_{task_id}"]
            break
    save_tasks(st.session_state.tasks)


def delete_task(task_id: str) -> None:
    st.session_state.tasks = [t for t in st.session_state.tasks if t["id"] != task_id]
    save_tasks(st.session_state.tasks)


def month_key(task: dict) -> str:
    return iso_to_date(task["date"]).strftime("%Y-%m")


# ---- App state ----
st.set_page_config(page_title="Todo Timeline", page_icon="🗓", layout="wide")
st.title("Todo Timeline")
st.caption("Chronological planning with priority lanes (P0 highest, P3 lowest).")

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

# ---- Add task ----
with st.form("new_task", clear_on_submit=True):
    st.subheader("Add a task")
    c1, c2 = st.columns([2, 1])
    title = c1.text_input("Task", placeholder="Draft monthly architecture review")
    due = c2.date_input("Due date", value=date.today())
    c3, c4 = st.columns([1, 2])
    priority = c3.selectbox("Priority", options=PRIORITY_LABELS, index=1)
    notes = c4.text_area("Notes", placeholder="Optional context", height=85)

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

# ---- View ----
st.divider()

tasks = sort_tasks(st.session_state.tasks)
if not tasks:
    st.info("No tasks yet. Add your first item above to build the timeline.")
else:
    grouped = defaultdict(list)
    for task in tasks:
        grouped[month_key(task)].append(task)

    for month in sorted(grouped):
        st.subheader(month)
        for task in grouped[month]:
            row = task
            cols = st.columns([0.7, 1, 1, 4, 4, 1])
            done_key = f"done_{row['id']}"

            cols[0].checkbox(
                label="Done",
                value=row["done"],
                key=done_key,
                on_change=toggle_done,
                args=(row["id"],),
                label_visibility="collapsed",
            )

            cols[1].write(f"{row['date']}")
            cols[2].write(f"{row['priority']}")
            cols[3].write(f"**{row['title']}**")
            cols[4].write(row["notes"] or "—")

            if cols[5].button("Delete", key=f"delete_{row['id']}"):
                delete_task(row["id"])
                st.rerun()

            if row["done"]:
                for c in cols[:5]:
                    c.caption("")
                cols[0].success("✓")

    st.caption(f"Total tasks: {len(tasks)} | Done: {sum(1 for t in tasks if t['done'])} | Remaining: {sum(1 for t in tasks if not t['done'])}")
