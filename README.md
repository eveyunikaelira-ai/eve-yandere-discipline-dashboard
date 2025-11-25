# eve-yandere-discipline-dashboard

A Flask dashboard that tracks study time, grades, chores, and triggers escalating notifications based on thresholds.

## Features
- Weekly study hour tracking with customizable goals.
- Grade logging with average tracking against target scores.
- Chore list with quick toggle between pending/done.
- Escalating notifications (success, warning, critical) when thresholds are missed.
- Simple JSON persistence for quick demos.

## Getting started
1. Install dependencies:
   ```bash
   pip install flask
   ```
2. Run the development server:
   ```bash
   FLASK_APP=app.py flask run --host 0.0.0.0 --port 5000
   ```
3. Open the dashboard at http://localhost:5000.

Data is stored in `data_store.json`; you can edit thresholds there to tune notification sensitivity.
