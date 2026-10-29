# ConfMan - Conference Management System

A production-ready, full-featured Conference Management System (CMS) built in Python with Flask and SQLite. ConfMan orchestrates the complete academic conference lifecycle: multi-role authentication (Admin, Chair, Reviewer, Author, Attendee), conference and track administration, paper submissions with PDF uploads, automated and volunteered peer-review workflows, blind review evaluations, editorial decisions, early-bird registration with mock payment processing, session scheduling, analytics, and public programme generation.

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Architecture & Directory Structure](#project-architecture--directory-structure)
- [Prerequisites](#prerequisites)
- [Local Installation & Development](#local-installation--development)
- [Environment Variables](#environment-variables)
- [Demo Credentials](#demo-credentials)
- [Testing & Quality Assurance](#testing--quality-assurance)
- [Vercel Deployment Guide](#vercel-deployment-guide)
- [Database & Persistent Storage Considerations](#database--persistent-storage-considerations)
- [Documentation & Deliverables](#documentation--deliverables)

---

## Features

- **Multi-Role Access Control**: 5 distinct roles (Admin, Chair, Reviewer, Author, Attendee) with strict role-based decorators and session protections.
- **Conference & Track Management**: Multiple tracks, configurable submission deadlines, early-bird pricing dates, and chair delegation.
- **Paper Submissions**: Authors upload papers (PDF validation, abstract, metadata keywords) with real-time tracking from submission to scheduling.
- **Flexible Reviewer Assignment**:
  - Chair manual assignment with Conflict of Interest (COI) prevention and workload balancing.
  - Reviewer volunteering for papers open for review matching expertise.
  - Heuristic auto-assignment based on expertise keyword matching.
- **Blind Peer Review & Suggestions**: Structured scoring, confidential remarks, chair suggestion heuristics (Accept/Reject/Revision), and author notifications.
- **Registrations & Payments**: Tiered registration fees (Early Bird vs. Regular, Student vs. Academic vs. Industry), Luhn-validated credit card processing, and receipt generation.
- **Session Scheduling**: Room allocation, clash detection, capacity verification, and interactive public programme schedule view.
- **Analytics & Admin Console**: Platform KPIs, acceptance rate metrics, user role management, account activation toggle, and audit activity logging.

---

## Technology Stack

- **Backend**: Python 3.10+ (tested through 3.14)
- **Web Framework**: Flask 3.x (WSGI)
- **Database**: SQLite3 (`schema.sql` data definition with foreign key enforcement)
- **Frontend**: Server-rendered Jinja2 templates, modern CSS3 (responsive flex/grid, light & dark themes), vanilla JavaScript
- **Deployment Platform**: Vercel Serverless Functions (`@vercel/python` WSGI runtime via `api/index.py`)
- **Testing**: Python standard library `unittest` (67 automated tests)

---

## Project Architecture & Directory Structure

```text
ConfMan/
│
├── README.md                   # Primary developer guide and deployment manual
├── .gitignore                  # Git ignore rules for Python, virtualenvs, secrets, caches
├── .env.example                # Safe environment variable template
├── vercel.json                 # Vercel deployment and URL routing configuration
├── requirements.txt            # Python dependencies
├── run.py                      # Local development server entry point
├── seed.py                     # Demo data loader and database reset CLI
├── demo.py                     # Rich seed dataset generator (3 conferences, 30 papers, 25 users)
│
├── api/                        # Serverless function entry points
│   └── index.py                # WSGI entry point for Vercel Serverless deployment
│
├── cms_app/                    # Core application package (3-layer architecture)
│   ├── __init__.py             # Presentation Layer: Flask app factory, routing, CSRF, auth
│   ├── db.py                   # Data Access Layer: SQLite connection and initialization
│   ├── schema.sql              # Relational schema (tables, constraints, triggers)
│   ├── services.py             # Business Logic Layer: validation, COI, assignment, payment rules
│   ├── insights.py             # Analytics & Read-models for manager dashboards
│   ├── static/                 # Static assets (style.css, design system)
│   └── templates/              # Jinja2 presentation templates and macro components
│
├── tests/                      # Automated test suite
│   ├── test_cms.py             # Core unit tests (auth, papers, reviews, payments, scheduling)
│   └── test_v13.py             # Features v1.3 tests (admin console, dashboards, auto-assignment)
│
├── scripts/                    # Development, maintenance, and deployment utilities
│   ├── seed.py                 # CLI database seeding utility
│   └── verify_deployment.py    # Automated local and Vercel compatibility verification suite
│
└── docs/                       # Project documentation and non-executable deliverables
    ├── project_report.md       # Comprehensive markdown technical report
    ├── reports/                # Formatted project reports (.docx and .pdf)
    │   ├── confman_report.docx
    │   ├── confman_report.pdf
    │   ├── confman_report_refined.docx
    │   └── confman_report_refined.pdf
    └── reference/              # Project reference documentation
        └── docustream_report.pdf
```

---

## Prerequisites

- **Python**: Version 3.10 or higher.
- **Pip**: Latest Python package manager.
- **Git**: Version control.

---

## Local Installation & Development

1. **Clone repository**:
   ```bash
   git clone https://github.com/prasinna/ConfMan.git
   cd ConfMan
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate    # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables (optional for local)**:
   ```bash
   cp .env.example .env
   ```

5. **Run the local development server**:
   ```bash
   python run.py
   ```
   *Note: On first startup, `run.py` automatically initializes SQLite and loads the rich demo dataset into `instance/cms.sqlite`.*

6. **Access the application**:
   Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser.

7. **Reset database to fresh state**:
   ```bash
   python seed.py --reset
   ```

---

## Environment Variables

ConfMan reads configuration from the environment, with safe defaults for local development:

| Variable | Description | Local Default | Production / Vercel Default |
|---|---|---|---|
| `CMS_SECRET` | Cryptographic secret for session cookie signing & CSRF | `dev-only-change-me` | **Set to a strong random token** |
| `CMS_DATABASE` | Filesystem path to SQLite database | `instance/cms.sqlite` | `/tmp/confman_instance/cms.sqlite` |
| `CMS_UPLOAD_FOLDER` | Filesystem path for uploaded paper PDFs | `instance/uploads` | `/tmp/confman_instance/uploads` |
| `CMS_AUTO_SEED` | Auto-seed demo dataset on boot if empty | `false` (handled by `run.py`) | `true` (enables live preview out-of-the-box) |
| `CMS_CSRF_ENABLED` | Enforce CSRF tokens on POST requests | `true` | `true` |
| `PORT` | Local HTTP port | `5000` | Assigned dynamically by hosting platform |

To generate a secure production secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Demo Credentials

All demo accounts share the password: `Demo@1234`

| Role | Email | Capabilities & Views |
|---|---|---|
| **Admin** | `admin@demo.org` | User administration, role changes, account toggle, platform KPIs, audit log |
| **Chair** | `chair@demo.org` *(also `chair2`, `chair3`)* | Conference dashboard, track management, reviewer assignment, decisions, scheduling |
| **Reviewer** | `reviewer1@demo.org` *(through `reviewer6`)* | Assigned papers, scoring rubric, "Open for review" paper volunteering |
| **Author** | `author@demo.org` *(through `author10`)* | Paper submission, status timeline, anonymous reviewer comments |
| **Attendee** | `attendee@demo.org` *(through `attendee4`)* | Conference registration, early-bird fee calculation, receipt view |

*Quick test card for payment gateway*: `4242 4242 4242 4242` succeeds; any Luhn-valid card ending in `0002` simulates a declined transaction.

---

## Testing & Quality Assurance

ConfMan includes 67 comprehensive automated tests covering unit logic, service validation, role security, Luhn algorithms, auto-assign algorithms, and end-to-end web workflows.

### Run Full Test Suite
```bash
python -m unittest discover -s tests -v
```

### Run Deployment Verification Suite
A specialized verification utility is provided to simulate the Vercel serverless environment:
```bash
python scripts/verify_deployment.py
```
This script validates:
- Standard initialization
- Vercel serverless mode (`VERCEL=1`) with `/tmp` filesystem redirection
- Static asset delivery
- Core web endpoints (`/`, `/login`, `/register`, `/conferences`, `/conferences/1/program`)
- Database seeding integrity

---

## Vercel Deployment Guide

ConfMan is configured for direct deployment on Vercel using Vercel Serverless Functions (`@vercel/python` runtime).

### Option 1: Deploy with Vercel CLI

1. **Install Vercel CLI**:
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Deploy from project root**:
   ```bash
   vercel
   ```
   For production deployment:
   ```bash
   vercel --prod
   ```

### Option 2: Deploy via GitHub / GitLab

1. Push your repository to GitHub.
2. In the Vercel Dashboard, click **Add New...** > **Project**.
3. Import your `ConfMan` repository.
4. Framework Preset: Leave as **Other**.
5. Root Directory: `./`
6. Under **Environment Variables**, add:
   - `CMS_SECRET`: *(A random 64-character hexadecimal string)*
   - `CMS_AUTO_SEED`: `true` *(optional, enabled by default on Vercel)*
7. Click **Deploy**.

---

## Database & Persistent Storage Considerations

> [!IMPORTANT]
> **Understanding Vercel Serverless Execution & Ephemeral Storage:**
>
> 1. **Serverless Filesystem**: Vercel functions execute in stateless, ephemeral micro-containers. The project root is read-only. ConfMan automatically directs the SQLite database (`CMS_DATABASE`) and uploads (`CMS_UPLOAD_FOLDER`) to the `/tmp` directory when running on Vercel.
> 2. **Lifespan of Data in `/tmp`**: Data written to `/tmp` is temporary and resets when serverless containers cold-start or scale down. Furthermore, separate concurrent serverless instances do not share the `/tmp` filesystem.
> 3. **Production Recommendations**:
>    - **For Interactive Demos & Previews**: The built-in `/tmp` storage with `CMS_AUTO_SEED=true` works immediately out-of-the-box with zero extra configuration.
>    - **For Permanent Multi-Tenant Production**:
>      - **Database**: Use a hosted serverless database such as **Turso (libSQL)** which provides SQLite API compatibility over HTTP/WebSocket, or migrate queries to **PostgreSQL (Neon / Supabase)**.
>      - **File Storage**: Replace local disk storage with cloud object storage such as **AWS S3**, **Cloudflare R2**, or **Vercel Blob** for PDF submissions.
>      - **Alternative Hosting**: If local SQLite file persistence without cloud adapters is strictly desired, deploy using container hosting with persistent volumes (e.g. **Railway**, **Render**, **Fly.io**, or **Docker/VPS**).

---

## Documentation & Deliverables

All academic deliverables, project reports, and reference specifications are preserved and cleanly organized under the [`docs/`](docs/) directory:

- [docs/project_report.md](docs/project_report.md): Comprehensive Markdown technical report covering requirements, architecture, design patterns, testing, and implementation details.
- [docs/reports/](docs/reports/): Academic reports and project submissions in DOCX and PDF formats:
  - `confman_report.docx` / `confman_report.pdf`
  - `confman_report_refined.docx` / `confman_report_refined.pdf`
- [docs/reference/](docs/reference/): Reference project specifications:
  - `docustream_report.pdf`
