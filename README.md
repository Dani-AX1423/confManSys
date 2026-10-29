<div align="center">

# 🏛️ ConfMan - Conference Management System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-SQLite3-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-67%20Passed-brightgreen.svg)](#testing--quality-assurance)
[![Vercel](https://img.shields.io/badge/Deployed-Vercel-black.svg?logo=vercel&logoColor=white)](https://conference-management-system-liard.vercel.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**A full-stack, production-grade academic Conference Management System built in Python, Flask, and SQLite.**  
ConfMan coordinates the entire conference lifecycle from call-for-papers to the final published schedule.

[Live Demo](https://conference-management-system-liard.vercel.app/) • [Features](#features) • [Quick Start](#quick-start) • [Demo Logins](#demo-accounts) • [Documentation](#documentation--reports)

---

</div>

## 📸 Interface Preview

<div align="center">

| Public Landing & Login | Program Chair Dashboard |
|:---:|:---:|
| <img src="ConfMan/docs/screenshots/Figure_D1_Dashboard_Home_and_Login.png" width="450" alt="Home and Login"> | <img src="ConfMan/docs/screenshots/Figure_D2_Chair_Dashboard.png" width="450" alt="Chair Dashboard"> |

| Paper Review & Decision Stepper | Payment Checkout & Confirmation |
|:---:|:---:|
| <img src="ConfMan/docs/screenshots/Figure_D3_Paper_Detail_Review_Panel.png" width="450" alt="Paper Detail View"> | <img src="ConfMan/docs/screenshots/Figure_D4_Payment_Checkout_and_Confirmation.png" width="450" alt="Payment Confirmation"> |

</div>

---

## Table of Contents

- [Key Features](#features)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Demo Accounts](#demo-accounts)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Vercel Deployment](#vercel-deployment)
- [Environment Variables](#environment-variables)
- [Repository Structure](#repository-structure)
- [Documentation & Reports](#documentation--reports)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **🔐 5-Role Access Control (RBAC)**: Dedicated interfaces, permissions, and dashboards for **Admin**, **Chair**, **Reviewer**, **Author**, and **Attendee**.
- **📄 Complete Submission Lifecycle**: Authors submit manuscripts (PDF format validation, abstract, keywords, track routing) with multi-step status stepper.
- **👥 Intelligent Reviewer Assignment**:
  - Manual assignment by Program Chair with automatic Conflict of Interest (COI) prevention.
  - Reviewer volunteering for unassigned papers matching their declared research expertise.
  - Keyword-based automated reviewer assignment algorithm.
- **⚖️ Double-Blind Peer Review**: Anonymized author information, 1–10 scoring rubric, confidential remarks, and algorithmic decision recommendations (Accept, Reject, Revision Required).
- **💳 Registration & Mock Payments**: Category pricing (Student, Academic, Industry), dynamic early-bird discount calculation, Luhn card validation, and receipt generation.
- **📅 Session Scheduling**: Room allocation (Hall A, Hall B), clash detection, room capacity limits, and interactive public programme schedule.
- **📊 Admin Console & Analytics**: Platform KPIs, acceptance rate metrics, user activation toggle, role management, and audit activity log.
- **🎨 Modern Responsive UI**: Teal design system with custom CSS Grid/Flexbox layouts, SVG charts, and instant light/dark theme toggle. Zero bulky frontend frameworks.

---

## System Architecture

ConfMan follows a clean **Three-Layer Architecture** strictly separating presentation, domain business logic, and data persistence:

```
┌─────────────────────────────────────────────────────────────┐
│                 PRESENTATION LAYER (Flask)                  │
│   • 26 HTTP Controllers (`cms_app/__init__.py`)             │
│   • Jinja2 Component Templates (`cms_app/templates/`)       │
│   • Custom Design System CSS (`cms_app/static/style.css`)   │
│   • Session Authentication & CSRF Protection                │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    BUSINESS LOGIC LAYER                     │
│   • Domain Services (`cms_app/services.py`)                 │
│   • Analytical Read Models (`cms_app/insights.py`)          │
│   • Validation, Deadlines, COI Checks, Luhn Algorithm       │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                     DATA ACCESS LAYER                       │
│   • Connection Pool (`cms_app/db.py`)                       │
│   • Relational Schema (`cms_app/schema.sql` - 13 Tables)    │
│   • SQLite3 with Foreign Key Enforcement (`PRAGMA`)         │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.10+, Flask 3.x WSGI, Werkzeug |
| **Database** | SQLite3 (13 normalized relational tables with foreign key triggers) |
| **Frontend** | Jinja2 Templates, HTML5, CSS3 Grid/Flexbox, Vanilla JS |
| **Deployment** | Vercel Serverless Functions (`@vercel/python` WSGI runtime) |
| **Testing** | Python standard library `unittest` (67 automated tests) |

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/Dani-AX1423/confManSys.git
cd confManSys/ConfMan
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the application
```bash
python run.py
```
*The application will automatically initialize the SQLite database and seed 3 conferences, 30 papers, 25 users, and demo reviews on first start.*

Open your browser at **[http://127.0.0.1:5000](http://127.0.0.1:5000)**.

To reset the database back to clean demo data at any time:
```bash
python seed.py --reset
```

---

## Demo Accounts

All pre-configured accounts share the password: **`Demo@1234`**

| Role | Email | Capabilities & Views |
|---|---|---|
| **Admin** | `admin@demo.org` | User management, role elevation, account status toggle, audit log, platform KPIs |
| **Chair** | `chair@demo.org` | Conference setup, reviewer assignments, paper decisions, session scheduling |
| **Reviewer** | `reviewer1@demo.org` | Scoring rubric, assigned papers, "Open for review" paper volunteering |
| **Author** | `author@demo.org` | Paper submission, status timeline, anonymous reviewer critiques |
| **Attendee** | `attendee@demo.org` | Conference registration, early-bird checkout, confirmed receipts |

> **Tip**: The login page has **one-click demo buttons** to instantly fill credentials.  
> **Test Payment Card**: `4242 4242 4242 4242` succeeds; a Luhn-valid card ending in `0002` simulates a declined transaction.

---

## Testing & Quality Assurance

ConfMan includes **67 automated unit and integration tests** validating business logic, role boundaries, COI rules, Luhn algorithms, and web flows.

```bash
# Run the complete test suite
python -m unittest discover -s ConfMan/tests -v

# Run the deployment and serverless verification suite
python ConfMan/scripts/verify_deployment.py
```

---

## Vercel Deployment

ConfMan is configured for one-click deployment on [Vercel](https://vercel.com/) via Vercel Serverless Functions:

1. Import this repository in the **Vercel Dashboard**.
2. Framework Preset: **Other**.
3. Root Directory: `./` (or `ConfMan`).
4. Set Environment Variables:
   - `CMS_SECRET`: Set to a strong random token (`python3 -c "import secrets; print(secrets.token_hex(32))"`).
   - `CMS_AUTO_SEED`: `true` (enables ready-to-use demo data).
5. Click **Deploy**.

*ConfMan automatically directs ephemeral SQLite storage to `/tmp` in serverless environments, providing a live preview without any external database provisioning.*

---

## Environment Variables

Copy `.env.example` to `.env` to customize settings:

| Variable | Default | Purpose |
|---|---|---|
| `CMS_SECRET` | `dev-only-change-me` | Secret key for session cookies and CSRF tokens |
| `CMS_DATABASE` | `instance/cms.sqlite` | SQLite database file location |
| `CMS_UPLOAD_FOLDER` | `instance/uploads` | Uploaded paper PDF directory |
| `CMS_AUTO_SEED` | `false` (local) / `true` (Vercel) | Auto-populate rich demo data if database is empty |
| `CMS_CSRF_ENABLED` | `true` | Enforce CSRF token validation on POST requests |

---

## Repository Structure

```text
.
├── README.md                   # Main GitHub overview & documentation (you are here)
├── LICENSE                     # MIT Open Source License
├── CONTRIBUTING.md             # Developer contribution guidelines
├── SECURITY.md                 # Security policies and reporting
├── vercel.json                 # Vercel Serverless deployment rewrite rules
├── requirements.txt            # Python dependencies (Flask>=3.0)
├── api/index.py                # Serverless WSGI entrypoint for Vercel
├── app.py                      # Root WSGI application entrypoint
│
├── ConfMan/                    # Core project codebase
│   ├── run.py                  # Local development server entrypoint
│   ├── seed.py                 # CLI database seeding & reset tool
│   ├── demo.py                 # Demo dataset generator (3 confs, 30 papers, 25 users)
│   │
│   ├── cms_app/                # Flask application package
│   │   ├── __init__.py         # App factory, routes, CSRF, auth, template filters
│   │   ├── db.py               # SQLite connection pool & initialization
│   │   ├── schema.sql          # DDL relational database schema (13 tables)
│   │   ├── services.py         # Transactional domain services & business logic
│   │   ├── insights.py         # Analytical read models for manager dashboards
│   │   ├── static/             # Vanilla CSS design system (style.css)
│   │   └── templates/          # Jinja2 templates & reusable UI macros
│   │
│   ├── tests/                  # 67 Automated tests
│   │   ├── test_cms.py         # Unit tests for domain services and routes
│   │   └── test_v13.py         # Tests for v1.3 role dashboards and auto-assignment
│   │
│   ├── scripts/                # Development and verification utilities
│   │   ├── capture_screenshots.py  # Headless browser screenshot generator
│   │   ├── seed.py                 # Database reset utility
│   │   └── verify_deployment.py    # Local & Vercel deployment verification
│   │
│   └── docs/                   # Documentation and project deliverables
│       ├── project_report.md   # Comprehensive technical report (Markdown)
│       ├── screenshots/        # High-resolution application figures
│       ├── reports/            # Formatted academic reports (.docx and .pdf)
│       └── reference/          # Reference specifications
```

---

## Documentation & Reports

Detailed technical documentation and project reports are preserved in [`ConfMan/docs/`](ConfMan/docs/):

- 📖 [Technical Project Report](ConfMan/docs/project_report.md) — Comprehensive design, schema, and implementation report.
- 🖼️ [Screenshots Gallery](ConfMan/docs/screenshots/) — High-resolution interface figures across all 5 roles.
- 📑 [Academic Reports (Word & PDF)](ConfMan/docs/reports/) — Formatted reports with embedded interface figures.

---

## Contributing

Contributions, feature requests, and bug reports are welcome!  
Please review [CONTRIBUTING.md](CONTRIBUTING.md) for details on code standards and the testing workflow.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
