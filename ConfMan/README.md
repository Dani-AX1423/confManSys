# ConfMan - Conference Management System

A working conference management system: accounts with five roles (admin, chair, author, reviewer,
attendee), conference and track set-up, paper submission, reviewer assignment (chair picks, auto-assign,
or reviewers volunteer), blind reviews, decisions, registration with early-bird pricing, a mock payment
gateway, session scheduling, a public programme, analytics and an admin console.

Stack: Python 3.10+, Flask, SQLite (nothing else to install).

## Run it (PowerShell or any terminal)
    cd ConfMan
    pip install -r requirements.txt
    python run.py            # first start loads the demo data automatically
    # open http://127.0.0.1:5000

To start again from scratch: delete the `instance` folder (or run `python seed.py --reset`), then `python run.py`.

## Demo logins (password for all: Demo@1234)
| Role | Email | What you see |
|---|---|---|
| Admin | admin@demo.org | users, roles, activity log, platform KPIs, every conference |
| Chair | chair@demo.org (also chair2, chair3) | papers needing reviewers, auto-assign, decisions, scheduling |
| Reviewer | reviewer1@demo.org ... reviewer3@demo.org | assigned papers, "Open for review" tab, volunteer |
| Author | author@demo.org | own papers, progress, anonymous reviews after decision |
| Attendee | attendee@demo.org | registration, payment, receipt, accepted papers |

The login page has one-click demo buttons. A brand-new reviewer (register with role Reviewer) sees every
paper that still needs reviewers under **Open for review** and can click **Review this**.
Payment card: `4242 4242 4242 4242` succeeds; a Luhn-valid number ending `0002` is declined.

## Tests
    python -m unittest discover -s tests -v      # 67 tests

## Layout (3-layer architecture)
| Path | Layer | Purpose |
|---|---|---|
| `cms_app/__init__.py` | Presentation | routes, sessions, CSRF, role checks |
| `cms_app/templates/`, `static/` | Presentation | full-width teal UI: sidebar shell, KPI cards, charts, dark mode |
| `cms_app/services.py` | Business logic | all rules (deadlines, COI, reviewer limits, fees, scheduling, admin) |
| `cms_app/insights.py` | Business logic | read-models behind dashboards and charts |
| `cms_app/db.py`, `schema.sql` | Data access | SQLite connection and schema |
| `demo.py`, `seed.py` | Demo data | 3 conferences, 30 papers, 25 users |
| `tests/` | Tests | unit and end-to-end tests |
