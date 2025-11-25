from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from flask import Flask, redirect, render_template, request, url_for

DATA_FILE = Path("data_store.json")
DATE_FMT = "%Y-%m-%d"

app = Flask(__name__)


def _default_data() -> Dict:
    return {
        "study_sessions": [
            {"subject": "Math", "hours": 1.5, "date": datetime.utcnow().strftime(DATE_FMT)},
            {"subject": "Science", "hours": 2.0, "date": (datetime.utcnow() - timedelta(days=1)).strftime(DATE_FMT)},
        ],
        "grades": [
            {"course": "Math", "score": 92},
            {"course": "Science", "score": 84},
        ],
        "chores": [
            {"task": "Clean desk", "done": False},
            {"task": "Take out trash", "done": True},
        ],
        "thresholds": {
            "weekly_study_goal": 14,
            "grade_goal": 85,
            "pending_chore_warning": 3,
            "pending_chore_critical": 5,
        },
    }


def load_data() -> Dict:
    if not DATA_FILE.exists():
        data = _default_data()
        save_data(data)
        return data

    try:
        return json.loads(DATA_FILE.read_text())
    except json.JSONDecodeError:
        return _default_data()


def save_data(data: Dict) -> None:
    DATA_FILE.write_text(json.dumps(data, indent=2))


def _get_recent_hours(study_sessions: List[Dict], days: int = 7) -> float:
    cutoff = datetime.utcnow().date() - timedelta(days=days - 1)
    return sum(
        session["hours"]
        for session in study_sessions
        if datetime.strptime(session["date"], DATE_FMT).date() >= cutoff
    )


def _average_grade(grades: List[Dict]) -> float:
    return sum(g["score"] for g in grades) / len(grades) if grades else 0.0


def _pending_chores(chores: List[Dict]) -> int:
    return sum(1 for chore in chores if not chore.get("done"))


def build_notifications(data: Dict) -> List[Dict]:
    thresholds = data.get("thresholds", {})
    weekly_goal = thresholds.get("weekly_study_goal", 14)
    grade_goal = thresholds.get("grade_goal", 85)
    warning_pending = thresholds.get("pending_chore_warning", 3)
    critical_pending = thresholds.get("pending_chore_critical", 5)

    hours = _get_recent_hours(data.get("study_sessions", []))
    avg_grade = _average_grade(data.get("grades", []))
    pending = _pending_chores(data.get("chores", []))

    notifications = []

    study_ratio = hours / weekly_goal if weekly_goal else 1
    if study_ratio < 0.5:
        notifications.append(
            {
                "level": "critical",
                "message": f"Study time dangerously low: {hours:.1f} / {weekly_goal} hrs this week.",
            }
        )
    elif study_ratio < 1:
        notifications.append(
            {
                "level": "warning",
                "message": f"Study time below goal: {hours:.1f} / {weekly_goal} hrs this week.",
            }
        )

    if avg_grade < grade_goal * 0.85:
        notifications.append(
            {
                "level": "critical",
                "message": f"Grades slipping: avg {avg_grade:.1f} below recovery threshold {grade_goal * 0.85:.0f}.",
            }
        )
    elif avg_grade < grade_goal:
        notifications.append(
            {
                "level": "warning",
                "message": f"Average grade {avg_grade:.1f} is below goal of {grade_goal}.",
            }
        )

    if pending >= critical_pending:
        notifications.append(
            {
                "level": "critical",
                "message": f"{pending} chores pending — handle immediately to avoid escalation.",
            }
        )
    elif pending >= warning_pending:
        notifications.append(
            {"level": "warning", "message": f"{pending} chores still pending — clear them soon."}
        )

    if not notifications:
        notifications.append(
            {
                "level": "success",
                "message": "All systems nominal — keep up the momentum!",
            }
        )

    return notifications


@app.route("/")
def index():
    data = load_data()
    hours = _get_recent_hours(data.get("study_sessions", []))
    avg_grade = _average_grade(data.get("grades", []))
    pending = _pending_chores(data.get("chores", []))
    notifications = build_notifications(data)

    return render_template(
        "index.html",
        study_sessions=data.get("study_sessions", []),
        grades=data.get("grades", []),
        chores=data.get("chores", []),
        hours=hours,
        avg_grade=avg_grade,
        pending=pending,
        thresholds=data.get("thresholds", {}),
        notifications=notifications,
        now=datetime.utcnow(),
    )


@app.route("/add-study", methods=["POST"])
def add_study():
    data = load_data()
    subject = request.form.get("subject", "General").strip() or "General"
    try:
        hours = float(request.form.get("hours", "0"))
    except ValueError:
        hours = 0.0
    date_str = request.form.get("date") or datetime.utcnow().strftime(DATE_FMT)

    data.setdefault("study_sessions", []).append(
        {"subject": subject, "hours": max(hours, 0.0), "date": date_str}
    )
    save_data(data)
    return redirect(url_for("index"))


@app.route("/add-grade", methods=["POST"])
def add_grade():
    data = load_data()
    course = request.form.get("course", "Course").strip() or "Course"
    try:
        score = float(request.form.get("score", "0"))
    except ValueError:
        score = 0.0

    data.setdefault("grades", []).append({"course": course, "score": max(min(score, 100.0), 0.0)})
    save_data(data)
    return redirect(url_for("index"))


@app.route("/add-chore", methods=["POST"])
def add_chore():
    data = load_data()
    task = request.form.get("task", "New chore").strip() or "New chore"
    data.setdefault("chores", []).append({"task": task, "done": False})
    save_data(data)
    return redirect(url_for("index"))


@app.route("/toggle-chore/<int:index>")
def toggle_chore(index: int):
    data = load_data()
    chores = data.setdefault("chores", [])
    if 0 <= index < len(chores):
        chores[index]["done"] = not chores[index].get("done", False)
        save_data(data)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
