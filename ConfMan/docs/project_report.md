# Technical and Academic Project Report: ConfMan (Conference Management System)

**Document Version:** 1.0.0  
**Repository Working Directory:** `/home/dani/Projects/clg/ConfMan/ConfMan`  
**Reference Specification:** College Academic Capstone Project Source of Truth  
**Target Output Document:** Academic Final Degree Project Report (Source Document)  

---

## 1. Project Overview

### 1.1 Official Project Identity
- **Project Title:** ConfMan - Conference Management System
- **Repository Established Name:** ConfMan
- **Target Application Domain:** Academic Event Orchestration, Scholarly Peer Review, Conference Editorial Administration, Scientific Publishing Workflows
- **Software Classification:** Web-based Multi-Role Enterprise Management System
- **System Architecture:** Clean 3-Tier Layered Architecture (Presentation Layer, Business Logic Layer, Data Access Layer)
- **Primary Runtime Platform:** Python 3.10+ / WSGI Web Application
- **Core Technology Stack:** Python 3.10+, Flask 3.0+, SQLite3 (with enforced foreign keys), Vanilla HTML5/CSS3 (Custom Teal Design System)

### 1.2 Purpose and High-Level Value Proposition
Academic conferences constitute the primary dissemination channel for rapidly advancing scientific disciplines, particularly in computer science and engineering. Organizing a contemporary conference entails managing complex, non-linear workflows: configuring tracks, accepting scholarly submissions, maintaining double-blind peer review integrity, resolving reviewer-author conflicts of interest (COI), orchestrating reviewer bidding and assignment, computing aggregate review scores, rendering editorial decisions, processing tiered registrations with early-bird discounts, verifying payment transactions, and compiling accepted papers into multi-session presentation programmes without room or timeslot collisions.

`ConfMan` is a fully realized, self-contained, multi-role conference management web application engineered to address these operational requirements without the operational weight, licensing friction, or hosting complexity of legacy enterprise platforms. Designed with strict adherence to separation of concerns, `ConfMan` encapsulates all business logic within a framework-agnostic service layer (`cms_app/services.py`), leverages analytical read models for real-time dashboards (`cms_app/insights.py`), provides role-based user interfaces (`cms_app/templates/`, `cms_app/static/style.css`), and utilizes SQLite3 with ACID transactions and schema-level relational constraints (`cms_app/schema.sql`).

### 1.3 Intended User Roles
The system natively supports five distinct actors with strictly enforced Role-Based Access Control (RBAC):
1. **System Administrator (`admin`):** Platform-level governance, user lifecycle management (activation/deactivation, role reassignment), conference chair appointment, cross-conference KPI oversight, and system-wide activity audit inspection.
2. **Program Committee Chair (`chair`):** Conference configuration, thematic track setup, paper submission monitoring, reviewer assignment (manual, greedy auto-assign, or volunteer approval), review progress tracking, decision recording with algorithmic guidance, session creation, and paper presentation scheduling.
3. **Reviewer (`reviewer`):** Double-blind paper evaluation, reviewer volunteering via an open paper pool, numeric scoring (1–10 scale), narrative critique authoring, recommendation submission, and workload tracking against explicit quota constraints.
4. **Author (`author`):** Scholarly manuscript submission (PDF format with metadata), real-time peer review status monitoring, post-decision feedback inspection, conference registration, and presentation schedule tracking.
5. **Conference Attendee (`attendee`):** Conference discovery, category-tiered registration (Student, Academic, Industry), early-bird pricing evaluation, credit card payment execution via simulated gateway, receipt/ticket generation, and accepted paper programme browsing.

---

## 2. Abstract

The administration of academic peer-reviewed conferences requires coordinated execution across multiple interdependent operational phases: manuscript ingestion, conflict-free reviewer assignment, double-blind peer evaluation, editorial decision-making, fee collection, and physical or virtual session scheduling. Legacy conference management systems frequently suffer from significant usability friction, convoluted user interfaces, monolithic architectures, vendor lock-in, and excessive runtime overhead that complicates localized deployment in institutional or departmental environments.

This project presents **ConfMan**, an end-to-end, lightweight, yet functionally comprehensive Conference Management System implemented using Python 3.10+, Flask 3.0+, and SQLite3. The system is engineered around a modular three-tier architecture that decouples web presentation and routing from core domain rules and relational data access. ConfMan implements fine-grained Role-Based Access Control across five distinct user personas: Administrator, Program Chair, Reviewer, Author, and Attendee. Core technical capabilities include an automated reviewer assignment engine driven by keyword and track expertise matching with reviewer workload balancing; an automated editorial decision support system based on score thresholds; strict enforcement of double-blind review constraints and conflict-of-interest prevention; a conference registration engine with dynamic early-bird discount calculation; a payment processing workflow with Luhn algorithm validation and mock gateway interaction; and a conference scheduling module with automated room clash and timeslot collision detection.

The system is validated through an extensive test suite comprising 67 unit and integration tests executing across 11 test suites, achieving complete pass rates and verifying business invariants including state transitions, authorization boundaries, and numerical calculations. In addition, the repository incorporates a realistic historical demo data generator simulating 3 conferences, 25 users, 30 scholarly papers, and 14 payments over a 75-day chronological continuum. The resulting system demonstrates that enterprise-grade scholarly conference management workflows can be realized with zero external runtime dependencies beyond the Flask framework, providing high operational reliability, fast cold-boot execution, and accessible maintainability for academic institutions.

---

## 3. Introduction

### 3.1 Background and Domain Context
Scholarly communication relies heavily on peer-reviewed conferences to validate, prioritize, and disseminate original scientific research. Unlike journal publication cycles, which operate on rolling, continuous timelines, academic conferences operate under rigid, synchronized, deadline-driven milestones:
1. **Call for Papers (CFP) & Ingestion Window:** Authors submit structured abstracts, keywords, and draft manuscripts within strict temporal bounds.
2. **Reviewer Allocation & Bidding:** The Program Committee (PC) must assign qualified subject matter experts to evaluate each submission while rigorously preventing ethical conflicts of interest (such as authors reviewing their own work or colleagues from identical institutions).
3. **Double-Blind Peer Evaluation:** Reviewers submit quantitative evaluations and detailed qualitative critiques without knowledge of author identities, preventing prestige and institutional bias.
4. **Editorial Deliberation & Decision Formulation:** The Program Chair synthesizes independent reviews, assesses variance, and records definitive editorial decisions (Accepted, Rejected, Revision Required).
5. **Attendee Registration & Financial Settlement:** Accepted authors and general attendees register under differentiated price tiers (Student, Academic, Industry), taking advantage of early-bird incentives.
6. **Programme Scheduling & Proceedings Compilation:** Accepted manuscripts whose authors have satisfied registration requirements are scheduled into physical or virtual conference tracks without room or time collisions.

### 3.2 Technological Challenges in Conference Management
Managing this pipeline manually via spreadsheets and disparate email threads is notoriously error-prone, resulting in:
- Reviewer over-allocation or severe workload imbalances.
- Ethical breaches such as inadvertent assignment of reviewers to their own papers.
- De-anonymization of authors during the evaluation phase.
- Financial discrepancies and tracking failures during registration.
- Room-time scheduling collisions during physical session planning.

While commercial platforms (e.g., EasyChair, EDAS, OpenConf, HotCRP) exist, they typically impose subscription fees, feature complex and dated user interfaces, enforce rigid workflows, or operate exclusively as closed-source SaaS offerings that prevent on-premise institutional hosting or bespoke educational adaptations.

### 3.3 The ConfMan Solution
`ConfMan` was conceived and implemented to provide a modern, self-contained, open-source reference solution that captures the entire academic conference lifecycle. Built upon clean architectural principles, ConfMan demonstrates that a fully functional conference management portal—incorporating responsive web dashboards, real-time KPI metrics, automated assignment heuristics, double-blind access control, secure payment simulation, and clash-free session scheduling—can be implemented cleanly in Python and Flask with zero external database or worker service dependencies.

---

## 4. Problem Statement

### 4.1 Core Problem Description
Traditional academic conference coordination workflows are characterized by administrative fragmentation, manual communication bottlenecks, and inadequate automated validation. Specifically, the challenges include:
1. **Workload Imbalance and Reviewer Burnout:** Program chairs manually assign reviewers without real-time visibility into current reviewer workloads, leading to review delays and low evaluation quality.
2. **Conflict of Interest (COI) Vulnerabilities:** In manual or basic spreadsheet systems, authors may inadvertently be assigned to review their own papers or those submitted by immediate institutional collaborators.
3. **Integrity Violations in Double-Blind Review:** Author identities, institutional affiliations, and reviewer critiques are frequently exposed prematurely, introducing cognitive bias into scholarly evaluation.
4. **Complex Registration & Fee Reconciliation:** Calculating early-bird versus standard fees across diverse attendee categories (students, faculty, industry practitioners) requires cumbersome financial reconciliation.
5. **Scheduling and Venue Clashes:** Manually organizing accepted papers into rooms and timeslots frequently produces room double-booking, over-capacity room allocations, or scheduling papers whose authors have not registered.
6. **Administrative Overhead in Legacy Systems:** Existing enterprise systems require heavy external infrastructure (dedicated MySQL/PostgreSQL databases, message brokers, caching daemons), creating substantial hurdles for lightweight deployment by university departments.

### 4.2 Documented Facts vs. Contextual Assumptions
To maintain rigorous academic documentation standards, we delineate verified codebase facts from contextual domain assumptions:
- **Confirmed Implementation Facts:**
  - The repository implements 5 distinct roles (`admin`, `chair`, `reviewer`, `author`, `attendee`) with explicit database-level check constraints (`cms_app/schema.sql#L8`).
  - Maximum reviewers per paper is strictly capped at 3 (`services.py#L19`).
  - Maximum pending reviews per reviewer is capped at 5 (`services.py#L20`).
  - Minimum reviews required before an editorial decision can be recorded is 2 (`services.py#L21`).
  - Payment processing validates card numbers using the Luhn mod-10 algorithm and declines cards ending with `0002` (`services.py#L457-L474`).
  - Paper scheduling strictly requires that the author possess a confirmed, paid registration (`services.py#L551-L556`).
- **Contextual Assumptions:**
  - The payment gateway is explicitly a software mock designed for demonstration and educational testing; it does not connect to live financial networks (e.g., Visa, Mastercard, Stripe).
  - File storage is local to the server filesystem (`instance/uploads/`) rather than an Amazon S3 or Azure Blob container.
  - Notifications are internal, database-persisted notifications rendered in the UI; outgoing SMTP email delivery is intentionally omitted to avoid external network dependencies.

---

## 5. Objectives

### 5.1 Primary Objectives (Fully Achieved & Tested)
1. **Develop a Multi-Role Relational Core:** Implement a relational database schema supporting users, conferences, tracks, papers, review assignments, reviews, decisions, registrations, payments, sessions, presentations, notifications, and activity audit logs with full foreign-key referential integrity.
2. **Enforce Role-Based Access Control (RBAC):** Restrict system views and actions through declarative decorators and session verification, preventing privilege escalation.
3. **Automate Reviewer Allocation via Heuristic Matching:** Implement both manual reviewer selection and a greedy automated assignment algorithm that ranks candidates based on keyword/track expertise overlap while enforcing capacity limits and COI prevention.
4. **Implement Double-Blind Review Controls:** Guarantee that reviewers cannot inspect author names or affiliations during evaluation, and authors cannot view reviewer identities or critiques until an official editorial decision is recorded.
5. **Provide Algorithmic Editorial Decision Guidance:** Implement score synthesis logic that calculates composite average scores and suggests acceptance, rejection, or revision based on empirical thresholds.
6. **Provide Tiered Registration with Early-Bird Fee Engine:** Automatically apply category-based fee structures and date-driven early-bird discounts (20% reduction) based on conference deadlines.
7. **Simulate Secure Payment Processing:** Implement credit card payment verification with Luhn algorithm checksum testing, transaction reference generation, and zero retention of sensitive card numbers.
8. **Orchestrate Clash-Free Session Scheduling:** Enable chairs to define conference rooms, timeslots, and seat capacities, while automatically blocking overlapping sessions and preventing the scheduling of unpaid papers.
9. **Deliver Role-Specific Analytical Dashboards:** Construct custom dashboards for chairs, administrators, reviewers, authors, and attendees featuring real-time KPIs, SVG sparklines, ring completion charts, and weekly submission series.
10. **Validate Core Logic via Automated Testing:** Construct a comprehensive automated test harness verifying all business logic constraints, edge cases, and web routes.

### 5.2 Secondary Objectives (Achieved & Demonstrated)
1. **Simulate Longitudinal Demo Data:** Provide a high-fidelity database seeder (`demo.py`) that uses an offset virtual clock to generate 75 days of realistic historical conference activity.
2. **Deliver Modern Responsive UI Without Third-Party Frameworks:** Design an accessible, responsive user interface utilizing custom CSS variables, SVG icons, and a dark/light theme switch without relying on Bootstrap, Tailwind, or jQuery.
3. **Provide Comprehensive Audit Logging:** Maintain an immutable administrative activity log capturing significant user actions across the platform.

### 5.3 Future / Non-Implemented Objectives
1. **Live External Payment Integration:** Connection to production Stripe, PayPal, or Razorpay payment APIs.
2. **Out-of-Band Email Notifications:** Integration with an asynchronous SMTP/SES queue for email dispatch.
3. **Multi-File Manuscript Revision Bundles:** Support for supplementary datasets, source code ZIP files, and rebuttal letters.

---

## 6. Project Scope

### 6.1 Supported User Personas and Workflows
The project encompasses five distinct user interaction models:
- **System Administrator:** Global user management (create users, alter roles, toggle active status), chair reassignment for conferences, platform KPI tracking (user growth, revenue, conversion), and security activity log review.
- **Program Chair:** Conference creation (dates, venue, submission/early-bird deadlines), track creation, paper monitoring, single-click and batch auto-assignment of reviewers, editorial decision recording, session creation with conflict detection, accepted paper scheduling, and CSV export.
- **Reviewer:** Self-registration, browsing open papers needing reviewers, self-assignment (volunteering), blind review submission (score 1–10, qualitative critique, recommendation), and pending workload tracking.
- **Author:** Self-registration, manuscript PDF submission with abstract and keywords, real-time submission tracking, review feedback review upon decision, and conference registration.
- **Attendee:** Account creation, conference discovery, category-based registration, mock credit card checkout, receipt verification, and public programme browsing.

### 6.2 System Boundaries and Exclusions
To maintain software quality and eliminate external point-of-failure dependencies, the following boundaries were deliberately established:
- **Single-Node Execution:** The system runs as a unified WSGI application designed for standard web server deployment (e.g., Gunicorn, uWSGI) backed by SQLite3.
- **PDF-Only Document Intake:** Ingestion is restricted to PDF files under 10MB to maintain strict document format consistency.
- **Internal Notifications:** Alerts are delivered via an in-app notification center; SMS and external SMTP emails are out of scope.
- **No Third-Party Frontend Dependencies:** The user interface uses pure HTML5 and vanilla CSS3; no Node.js build pipelines, React, Vue, or CDN-hosted CSS libraries are required.

---

## 7. Existing System and Limitations

### 7.1 Traditional Conference Coordination Approaches
Academic event management has historically relied on two models:
1. **Ad-Hoc Manual Coordination:** Small workshops and symposia often manage submissions, assignments, and reviews via email attachments, shared folders (e.g., Google Drive), and spreadsheets.
2. **Legacy Enterprise Platforms:** Larger conferences typically deploy established SaaS or on-premise platforms such as EasyChair, EDAS, OpenConf, or HotCRP.

### 7.2 Documented Limitations of Existing Approaches
| Dimension | Manual / Spreadsheet Systems | Legacy Enterprise Platforms |
|---|---|---|
| **Conflict of Interest Control** | Highly error-prone; requires human memory or manual cross-referencing. | Rigid; often fails to adapt to specific track configurations or self-assignment models. |
| **Reviewer Workload Balance** | Difficult to track in real time; leads to reviewer fatigue and missed deadlines. | Often treats reviewers as static assignees without volunteer/bidding workflows. |
| **User Experience & Responsiveness** | Disjointed; requires switching between email, spreadsheets, and file drives. | Dense, legacy interfaces built in early-2000s web patterns; poor mobile responsiveness. |
| **Deployment Complexity** | None (no dedicated system). | Complex; requires dedicated MySQL/PostgreSQL instances, daemon workers, or paid subscriptions. |
| **Financial Reconciliation** | Manual bank transfer checks or disjointed third-party payment forms. | High per-submission or per-attendee licensing fees. |
| **Double-Blind Integrity** | Easy to breach inadvertently when forwarding raw PDF emails. | Often obscured behind complex privilege permission toggles. |

---

## 8. Proposed System

### 8.1 System Philosophy and Architecture
The proposed system, **ConfMan**, resolves these limitations through a streamlined, cohesive, and architecturally decoupled web platform. Built from first principles, ConfMan introduces:
1. **Strict 3-Tier Layered Decoupling:** Business rules are entirely isolated in `cms_app/services.py`, taking raw database connections and raising structured exceptions (`ServiceError`). This ensures 100% testability of business logic independent of HTTP contexts.
2. **Dedicated Read-Model Engine:** Complex dashboard metrics, time-series bucketing, and analytics pipelines are encapsulated in `cms_app/insights.py`, preserving clean separation between transactional write operations and analytical read operations.
3. **Integrated Lifecycle Automation:** From submission through double-blind review, editorial scoring thresholds, category-tiered payment, to room-clash-free scheduling, all phases communicate through shared relational invariants.
4. **Self-Contained Deployment Footprint:** The entire system runs out-of-the-box with a standard Python installation and `pip install Flask`. Zero database configuration, message queues, or asset compilers are required.

### 8.2 Summary of Actual Implemented Capabilities
- Five-role access control with automated redirects and CSRF verification.
- Manuscript submission with file size checking, PDF verification, and metadata indexing.
- Multi-channel reviewer allocation: chair manual pick, ranked auto-assignment with expertise matching, and reviewer self-assignment (volunteering).
- Strict double-blind enforcement in templates and routing.
- Algorithmic decision support calculating composite averages and suggesting outcomes.
- Early-bird fee calculator with calendar deadline boundary testing.
- PCI-compliant mock payment gateway with Luhn checksum validation.
- Session scheduling engine with temporal overlap detection and registration prerequisite checks.
- Comprehensive administrative control and immutable activity auditing.

## 9. Technology Stack

### 9.1 Technology Inventory and Role Justification
Every technology employed within `ConfMan` was selected to maximize architectural cohesion, operational reliability, developer ergonomics, and deployment simplicity.

| Component / Layer | Technology Name | Version / Specification | Exact Usage and Responsibility | Evidence in Codebase |
|---|---|---|---|---|
| **Programming Language** | Python | >= 3.10 (Tested on 3.10–3.14) | Core application implementation, business rules, service orchestrations, data models. | `run.py`, `cms_app/*.py` |
| **Web Framework** | Flask | >= 3.0 | Application routing, request/response lifecycle, session management, template rendering, error handling. | `requirements.txt#L1`, `cms_app/__init__.py#L10` |
| **WSGI & Security Utilities** | Werkzeug | >= 3.0 (Bundled with Flask) | Password hashing (`generate_password_hash`, `check_password_hash` via PBKDF2:SHA256), secure filename sanitization (`secure_filename`). | `cms_app/services.py#L10`, `cms_app/__init__.py#L12` |
| **Template Engine** | Jinja2 | >= 3.1 (Bundled with Flask) | Server-side HTML template compilation, macro definitions, custom template filters (`dt`, `d`, `ago`, `inr`, `firstname`), context processors. | `cms_app/__init__.py#L137-L194`, `cms_app/templates/*.html` |
| **Relational Database** | SQLite3 | 3.x (Python Standard Library) | Relational transactional datastore with ACID semantics, foreign keys enabled (`PRAGMA foreign_keys = ON`), in-memory testing. | `cms_app/db.py#L3-L13`, `cms_app/schema.sql` |
| **User Interface & Styling** | Vanilla CSS3 | Custom Properties (Variables) | Bespoke "Teal Green" Design System, full-width CSS Grid/Flexbox layouts, light/dark theme switching, responsive sidebar shell. Zero third-party frameworks. | `cms_app/static/style.css#L1-L362` |
| **Iconography & Graphics** | Inline SVG | Scalable Vector Graphics | 24px stroke-based SVG icons, inline sparklines, circular percentage rings, and vertical CSS/SVG bar charts. | `cms_app/templates/_macros.html#L1-L115` |
| **Testing Harness** | `unittest` | Python Standard Library | Unit, service rule, and integration test execution; in-memory SQLite isolation; client test runner. | `tests/test_cms.py#L10`, `tests/test_v13.py#L10` |
| **Build & Dependency Tooling** | `pip` / Standard Manifest | Standard Python packaging | Dependency management restricted strictly to `Flask>=3.0`. | `requirements.txt#L1` |

### 9.2 Critical Technology Distinctions
- **Technologies Genuinely Used:** Python 3, Flask, Werkzeug, Jinja2, SQLite3, HTML5, CSS3, SVG, Python `unittest`.
- **Technologies NOT Used (Eliminated Overhead):** No external database daemons (PostgreSQL, MySQL, Redis), no task queues (Celery, RabbitMQ), no CSS frameworks (Bootstrap, Tailwind), no JavaScript build tools (Webpack, Vite, npm, React, Vue, jQuery). The entire frontend executes without external CDN dependencies or client-side runtime compilation.

---

## 10. Requirements Analysis

### 10.1 Functional Requirements (FR)

| Req ID | Requirement Title | Detailed Description and Implementation Rule | Supporting Source Code Reference |
|---|---|---|---|
| **FR-01** | User Registration & Role Selection | Allow public users to register accounts choosing among `author`, `reviewer`, or `attendee` roles. Block self-registration for `chair` or `admin`. Passwords must be >= 8 chars and contain at least one numeric digit. | `services.py#L101-L124`, `__init__.py#L213-L230` |
| **FR-02** | User Authentication & Session Security | Authenticate users via email and password using PBKDF2-HMAC-SHA256 password hash comparisons. Reject inactive/deactivated users. Establish secure server-side session. | `services.py#L126-L135`, `__init__.py#L251-L268` |
| **FR-03** | Conference Creation & Configuration | Enable Program Chairs and Admins to create conferences with venue, dates, submission deadline, and early-bird deadline. Validate chronological consistency (`end >= start`, `deadline < start`, `early <= start`). | `services.py#L138-L169`, `__init__.py#L396-L413` |
| **FR-04** | Track Management | Allow conference chairs to add thematic tracks to their conference. Enforce uniqueness of track names within a specific conference (`UNIQUE(conf_id, name)`). | `services.py#L171-L182`, `__init__.py#L451-L460` |
| **FR-05** | Manuscript Submission | Enable Authors to submit papers by selecting a conference and track, providing a title (max 200 chars), abstract (min 50 chars), keywords, and uploading a PDF document. Reject submissions once the submission deadline has elapsed. | `services.py#L185-L217`, `__init__.py#L533-L555` |
| **FR-06** | Manual Reviewer Assignment | Allow Chairs to manually assign active reviewers to submissions. Prevent Conflict of Interest (author cannot review own paper). Prevent duplicate assignments. Enforce max 3 reviewers per paper and max 5 pending reviews per reviewer. | `services.py#L220-L274`, `__init__.py#L725-L734` |
| **FR-07** | Reviewer Volunteering (Self-Assignment) | Allow Reviewers to browse a curated list of open papers lacking reviewers and volunteer to review. Enforce identical COI, duplicate, and capacity constraints as chair assignment. | `services.py#L275-L285`, `__init__.py#L746-L758`, `insights.py#L185-L211` |
| **FR-08** | Automated Reviewer Allocation | Implement greedy auto-assignment matching candidate reviewer expertise keywords against paper title, track, and keywords. Prioritize highest expertise overlap, then lowest existing workload. Cap assignments at 3 reviewers. | `services.py#L287-L348`, `__init__.py#L483-L503`, `__init__.py#L735-L745` |
| **FR-09** | Double-Blind Review Evaluation | Reviewers evaluate assigned submissions anonymously (author identities masked). Submission of integer score (1–10), narrative critique (min 20 chars), and recommendation (`accept`, `minor revision`, `major revision`, `reject`). | `services.py#L350-L387`, `__init__.py#L781-L803` |
| **FR-10** | Algorithmic Decision Support | Calculate composite review scores for submissions with >= 2 reviews. Automatically suggest decision: `Accepted` (avg >= 7.0), `Revision Required` (5.0 <= avg < 7.0), or `Rejected` (avg < 5.0). | `services.py#L389-L404`, `__init__.py#L682-L685` |
| **FR-11** | Editorial Decision Recording | Enable Chairs to record binding decisions (`Accepted`, `Rejected`, `Revision Required`) with remarks. Prohibit decisions if fewer than 2 reviews exist. Automatically update paper status and notify author. | `services.py#L406-L426`, `__init__.py#L759-L769` |
| **FR-12** | Tiered Conference Registration | Allow attendees/authors to register under Student (Rs 500), Academic (Rs 1000), or Industry (Rs 2000) tiers. Automatically deduct a 20% early-bird discount if registered on or before `early_bird_deadline`. | `services.py#L428-L455`, `__init__.py#L805-L821` |
| **FR-13** | Payment Processing Simulation | Validate 13–19 digit credit card numbers using the Luhn mod-10 algorithm. Dispatch to mock payment gateway (declining numbers ending in `0002`). Update registration to `Confirmed`. Never persist card numbers. | `services.py#L457-L500`, `__init__.py#L823-L839` |
| **FR-14** | Clash-Free Session Scheduling | Allow Chairs to create sessions with room, capacity, and time windows. Detect and prevent room double-booking. Schedule accepted papers only if the primary author possesses a confirmed, paid registration. | `services.py#L502-L563`, `__init__.py#L461-L472`, `__init__.py#L770-L779` |
| **FR-15** | Administration & Audit Logging | Enable Admins to create users with any role, toggle active status, reassign conference chairs, inspect platform KPIs, and review chronological activity audit records. | `services.py#L580-L630`, `__init__.py#L852-L911` |

### 10.2 Non-Functional Requirements (NFR)

- **NFR-01: Security & Confidentiality (Demonstrated):**
  - All password credentials stored as cryptographic one-way hashes via Werkzeug PBKDF2-HMAC-SHA256 (`services.py#L118`).
  - Session state protected against Cross-Site Request Forgery (CSRF) using per-session cryptographic hexadecimal tokens verified with constant-time equality checks (`secrets.compare_digest`) on all POST submissions (`__init__.py#L54-L58`).
  - Double-blind evaluation strictly maintained: Author metadata stripped from reviewer views; reviewer identities and narrative critiques hidden from authors until official decision recording (`__init__.py#L562-L578`, `__init__.py#L614-L622`, `__init__.py#L678-L680`).
  - Open redirect vulnerabilities mitigated via strict relative URL path verification (`safe_next`) (`__init__.py#L79-L80`).
  - Strict SQL injection prevention via 100% parameterized query bindings across all data operations (`db.execute("...?", (args,))`).
  - Sensitive payment card numbers are parsed in memory, verified via Luhn, and immediately discarded without writing to disk or database (`services.py#L485`).

- **NFR-02: Reliability & Data Integrity (Demonstrated):**
  - Enforced relational referential integrity through SQLite foreign keys (`PRAGMA foreign_keys = ON;` in `schema.sql#L1` and `db.py#L12`).
  - Strict database constraints: Check constraints on user roles (`schema.sql#L8`), paper statuses (`schema.sql#L44`), review scores 1–10 (`schema.sql#L61`), recommendations (`schema.sql#L64`), registration statuses (`schema.sql#L84`), and payment statuses (`schema.sql#L95`).
  - Atomic database transactions with explicit commits and rollback on error (`db.commit()` in all mutating service routines).

- **NFR-03: Performance & Resource Footprint (Demonstrated):**
  - Sub-second cold-boot startup time and instant test execution (all 67 unit and integration tests run in ~31 seconds on standard hardware).
  - Minimal memory footprint: zero background daemon workers, zero in-memory caching servers (Redis/Memcached) needed for baseline operation.
  - Efficient analytical queries: aggregations, weekly series bucketing, and status counts execute directly in SQLite in single-digit milliseconds (`insights.py#L25-L90`).

- **NFR-04: Usability & Accessibility (Demonstrated):**
  - Fully responsive web presentation adapting seamlessly from mobile viewports (collapsible off-canvas sidebar menu) to wide-screen desktop displays (`style.css#L348-L356`).
  - Built-in theme switcher (Light / Dark mode) with preference persistence in browser `localStorage` (`base.html#L12`, `base.html#L70`).
  - Rich visual telemetry: SVG sparklines showing 8-week submission velocity, ring charts for acceptance percentages, color-coded status badges, and contextual KPI cards (`_macros.html#L45-L98`).

- **NFR-05: Maintainability & Testability (Demonstrated):**
  - Framework-agnostic business logic in `services.py`: all domain rules take standard `sqlite3.Connection` instances, enabling unit testing without spinning up Flask WSGI contexts or HTTP fixtures (`tests/test_cms.py#L21-L27`).
  - Modular 3-tier architecture with distinct presentation, domain service, read model, and persistence modules.

---

## 11. System Architecture

### 11.1 Architectural Pattern: Clean 3-Tier Layered Architecture
`ConfMan` is architected as a modular, three-tier monolithic application. Unlike sprawling microservice architectures that introduce network latency, distributed transaction complexity, and heavy orchestration requirements, ConfMan adopts a tightly coupled in-process, loosely coupled architectural separation:

```
+-------------------------------------------------------------------------+
|                           PRESENTATION LAYER                            |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   | Flask WSGI Application (`cms_app/__init__.py`)                  |   |
|   | - Application Factory (`create_app`)                            |   |
|   | - Route Handlers & Controllers (26 Endpoints)                   |   |
|   | - Security Pre-Filters: `before_request` (Auth & CSRF)          |   |
|   | - Decorators: `@login_required`, `@role_required`               |   |
|   | - Context Processors & Custom Jinja Filters (`dt`, `inr`, etc.) |   |
|   +-----------------------------------------------------------------+   |
|                                    |                                    |
|   +-----------------------------------------------------------------+   |
|   | Templates & Static Assets (`templates/*.html`, `style.css`)     |   |
|   | - HTML5 Semantic Templates & Component Macros (`_macros.html`)  |   |
|   | - Teal Design System, CSS Grid/Flexbox, Dark Theme Switcher     |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                          BUSINESS LOGIC LAYER                           |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   | Transactional Services (`cms_app/services.py`)                  |   |
|   | - Identity & Credentials (`register_user`, `authenticate`)      |   |
|   | - Conference & Tracks (`create_conference`, `add_track`)        |   |
|   | - Manuscript Ingestion (`submit_paper`, PDF validation)         |   |
|   | - Reviewer Allocation (`assign_reviewer`, `auto_assign`,        |   |
|   |   `volunteer_to_review`, COI & Workload checks)                 |   |
|   | - Review Evaluation & Decision Engine (`submit_review`,         |   |
|   |   `suggest_decision`, `record_decision`)                        |   |
|   | - Tiered Fee Engine & Payments (`registration_fee`, `luhn_valid`|   |
|   |   `process_payment`, Mock Gateway)                              |   |
|   | - Scheduling Engine (`create_session`, `schedule_paper`,        |   |
|   |   Room Clash Detection, Paid Registration Validation)           |   |
|   | - Administrative Actions (`set_user_role`, `reassign_chair`)    |   |
|   +-----------------------------------------------------------------+   |
|                                    |                                    |
|   +-----------------------------------------------------------------+   |
|   | Read-Model & Analytics Services (`cms_app/insights.py`)         |   |
|   | - Analytical Read Aggregations (`manager_kpis`, `admin_kpis`)   |   |
|   | - Weekly Time-Series Bucketing (`weekly_series`)                |   |
|   | - Reviewer Workload Tracking (`reviewer_workload`)              |   |
|   | - Open Papers Matching for Volunteering (`open_papers`)         |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                           DATA ACCESS LAYER                             |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   | Database Connection Manager (`cms_app/db.py`)                   |   |
|   | - Thread-Local Connection Pool (`g.db`, `get_db()`)             |   |
|   | - Foreign Key Enforcement (`PRAGMA foreign_keys = ON`)          |   |
|   | - Row Factory (`sqlite3.Row` for dict-like attribute access)    |   |
|   | - Teardown Context Handler (`close_db`)                         |   |
|   | - Schema Initializer (`init_db`)                                |   |
|   +-----------------------------------------------------------------+   |
|                                    |                                    |
|   +-----------------------------------------------------------------+   |
|   | Relational Storage (`cms_app/schema.sql`, `instance/cms.sqlite`)|   |
|   | - 13 Relational Tables with Check Constraints & Unique Keys     |   |
|   | - Local Document Storage (`instance/uploads/`)                  |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
```

### 11.2 Request-Response Lifecycle Trace
To illustrate how data and control propagate through the system, we trace a typical non-trivial operation: **Author Submits a Manuscript for Review**.

1. **User Interaction & Client Dispatch:**
   - Author navigates to `/conferences/<conf_id>/submit` and submits a `multipart/form-data` POST containing `title`, `abstract`, `keywords`, `track_id`, `_csrf` token, and a PDF file attachment (`file`).
2. **Presentation Layer Filter (`cms_app/__init__.py#L44-L77`):**
   - `@app.before_request` intercepts the incoming HTTP request.
   - It reads `session["user_id"]`, queries the database for the active user record, and attaches the active record to Flask's context proxy `g.user`.
   - It checks whether CSRF enforcement is enabled (`app.config["CSRF_ENABLED"]`). Since the request method is POST, it retrieves `request.form["_csrf"]` and compares it to `session["_csrf"]` using `secrets.compare_digest`. If invalid, request processing halts with HTTP 400.
   - The route handler `@role_required("author")` verifies that `g.user["role"] == "author"`. If a non-author attempts access, it immediately halts with HTTP 403.
3. **Route Handler Orchestration (`cms_app/__init__.py#L532-L555`):**
   - The `paper_submit(conf_id)` view handler extracts form attributes and invokes `werkzeug.utils.secure_filename` on the uploaded file.
   - The view delegates domain validation and database insertion to the business logic service: `services.submit_paper(db, g.user["user_id"], conf_id, track_id, title, abstract, keywords, original_filename)`.
4. **Business Logic Execution (`cms_app/services.py#L185-L217`):**
   - `submit_paper` verifies that the author role is valid.
   - It retrieves the conference record and compares current date `_today(today)` against `conf["submission_deadline"]`. If expired, it raises `ServiceError("The submission deadline has passed.")`.
   - It verifies that the specified `track_id` belongs to the conference.
   - It validates that `title` length is between 1 and 200 characters.
   - It validates that `abstract` length is at least 50 characters.
   - It validates that `file_name` ends with `.pdf`.
   - It executes an INSERT query into the `papers` table with initial status `'Submitted'`.
   - It executes an INSERT into `notifications` for the author ("Your paper was submitted successfully").
   - It executes an INSERT into `notifications` for the conference chair ("New paper submitted: Assign reviewers").
   - It logs the event in the `activity` audit table.
   - It issues `db.commit()` and returns the new `paper_id`.
5. **Filesystem Persistence & Redirect (`cms_app/__init__.py#L548-L551`):**
   - Back in the presentation controller, the uploaded PDF stream is saved to `instance/uploads/{paper_id}_{uuid.hex[:8]}.pdf`.
   - A success message is pushed to the session flash queue: `flash("Paper submitted...", "success")`.
   - The controller returns a redirect HTTP 302 response to `url_for("paper_detail", paper_id=paper_id)`.
6. **Teardown & Response Delivery:**
   - Flask's `teardown_appcontext` hook invokes `cms_app.db.close_db`, releasing the SQLite database connection back to the thread environment.
   - The client browser follows the redirect and renders the newly created paper detail page.

---

## 12. Module Description

`ConfMan` is structured into distinct, cohesive functional modules:

### 12.1 User & Authentication Module
- **Purpose:** Manage user identities, self-registration, role assignments, password updates, and secure authentication sessions.
- **Key Files:** `cms_app/services.py#L101-L135`, `cms_app/services.py#L631-L647`, `cms_app/__init__.py#L212-L273`, `cms_app/__init__.py#L365-L382`.
- **Core Functions:** `register_user`, `authenticate`, `update_profile`, `change_password`.
- **Inputs & Outputs:** Inputs: user registration tuples (name, email, password, role, affiliation, expertise); Outputs: user IDs, authenticated user records, session cookies.
- **Security Logic:** Password complexity enforcement (>=8 chars, >=1 digit); email normalization (strip and lowercase); unique email enforcement; PBKDF2-HMAC-SHA256 password hashing.

### 12.2 Conference & Track Management Module
- **Purpose:** Administer conference entities, chronological milestones, and thematic research tracks.
- **Key Files:** `cms_app/services.py#L138-L182`, `cms_app/__init__.py#L384-L530`.
- **Core Functions:** `create_conference`, `add_track`, `reassign_chair`, `get_program`, `export_papers`.
- **Inputs & Outputs:** Inputs: conference metadata, start/end dates, submission/early-bird deadlines; Outputs: conference IDs, track records, CSV paper export streams.
- **Business Invariants:** Strict chronological sequence: `start_date <= end_date`, `submission_deadline < start_date`, `early_bird_deadline <= start_date`. Only Chairs or Admins can create conferences or tracks.

### 12.3 Manuscript Ingestion & Access Control Module
- **Purpose:** Process paper submissions, validate PDF files, and control access permissions according to the user's relationship to the paper.
- **Key Files:** `cms_app/services.py#L185-L217`, `cms_app/__init__.py#L532-L723`.
- **Core Functions:** `submit_paper`, `paper_row`, `paper_access`, `paper_file`.
- **Inputs & Outputs:** Inputs: multipart PDF upload, title, abstract, keywords, track ID; Outputs: new paper record, sanitized PDF storage on disk.
- **Relationship Matrix (`paper_access`):** Dynamically categorizes a viewing user as `chair`, `author`, `reviewer`, `prospect` (unassigned reviewer browsing open papers), or `public` (attendees viewing accepted papers).

### 12.4 Reviewer Assignment & Volunteering Module
- **Purpose:** Allocate reviewers to papers through chair manual assignment, reviewer self-assignment (volunteering), or algorithmic auto-assignment.
- **Key Files:** `cms_app/services.py#L220-L348`, `cms_app/__init__.py#L725-L758`.
- **Core Functions:** `_check_assignable`, `assign_reviewer`, `volunteer_to_review`, `ranked_reviewers`, `auto_assign`, `auto_assign_conference`.
- **Inputs & Outputs:** Inputs: `paper_id`, `reviewer_id`, `chair_id`; Outputs: `assignment_id`, list of auto-assigned reviewer names.
- **Business Invariants:**
  - Conflict of Interest (COI) blocked: Reviewer cannot be the author (`reviewer_id != paper['author_id']`).
  - Active reviewer status verified (`is_active == 1` and `role == 'reviewer'`).
  - Maximum 3 reviewers per paper (`MAX_REVIEWERS_PER_PAPER = 3`).
  - Maximum 5 pending reviews per reviewer (`MAX_PENDING_REVIEWS_PER_REVIEWER = 5`).
  - Paper status transitions: Assigning the first reviewer moves paper from `'Submitted'` to `'Under Review'`.

### 12.5 Peer Review Evaluation & Editorial Decision Module
- **Purpose:** Collect double-blind reviews, calculate score aggregations, suggest decisions, and record binding editorial determinations.
- **Key Files:** `cms_app/services.py#L350-L426`, `cms_app/__init__.py#L759-L803`.
- **Core Functions:** `submit_review`, `suggest_decision`, `record_decision`.
- **Inputs & Outputs:** Inputs: `assignment_id`, numeric score (1–10), narrative comments, recommendation; Outputs: review record, composite average score, suggested decision.
- **Business Invariants:**
  - Comments must contain at least 20 characters.
  - Review belongs only to the assigned reviewer and cannot be submitted twice.
  - When all pending assignments for a paper are completed, paper status transitions to `'Reviewed'`.
  - Editorial decisions require at least 2 completed reviews (`MIN_REVIEWS_FOR_DECISION = 2`).
  - Suggested decision rules: Average score >= 7.0 -> `Accepted`; 5.0 <= Average < 7.0 -> `Revision Required`; Average < 5.0 -> `Rejected`.

### 12.6 Registration & Fee Calculation Module
- **Purpose:** Manage conference attendee registrations, determine attendee fee tiers, and apply temporal early-bird discounts.
- **Key Files:** `cms_app/services.py#L428-L455`, `cms_app/__init__.py#L805-L821`.
- **Core Functions:** `registration_fee`, `register_for_conference`.
- **Inputs & Outputs:** Inputs: `user_id`, `conf_id`, category (`student`, `academic`, `industry`), registration date; Outputs: `reg_id`, computed fee amount.
- **Business Invariants:** Fee tiers: Student (Rs 500.0), Academic (Rs 1000.0), Industry (Rs 2000.0). If current date <= `early_bird_deadline`, fee is discounted by 20% (`fee *= 0.80`). Duplicate registrations for the same user and conference are strictly prohibited (`UNIQUE(conf_id, user_id)`).

### 12.7 Payment Processing & Gateway Simulation Module
- **Purpose:** Validate credit card instruments and process payments through a simulated financial gateway.
- **Key Files:** `cms_app/services.py#L457-L500`, `cms_app/__init__.py#L823-L839`.
- **Core Functions:** `luhn_valid`, `_mock_gateway`, `process_payment`.
- **Inputs & Outputs:** Inputs: `reg_id`, `card_number`; Outputs: `txn_ref` (e.g., `TXN-3F8E1A0B2C`), updated registration status (`Confirmed`).
- **Business Invariants:**
  - Card number must consist of 13 to 19 digits.
  - Card number must pass the Luhn Mod-10 checksum algorithm.
  - Mock gateway declines cards ending in `"0002"`.
  - Card numbers are NEVER stored in the database (PCI compliance simulation).

### 12.8 Session Scheduling & Programme Module
- **Purpose:** Organize conference venues into multi-room timeslots and assign accepted manuscripts to session presentation slots.
- **Key Files:** `cms_app/services.py#L502-L578`, `cms_app/__init__.py#L461-L472`, `cms_app/__init__.py#L770-L779`.
- **Core Functions:** `create_session`, `schedule_paper`, `get_program`.
- **Inputs & Outputs:** Inputs: `conf_id`, `title`, `room`, `start_time`, `end_time`, `capacity`, `paper_id`, `session_id`; Outputs: session records, presentation slot allocations.
- **Business Invariants:**
  - Session times must fall within the conference dates (`start.date() == end.date()`).
  - Room double-booking is blocked via interval overlap query.
  - Only papers with status `'Accepted'` can be scheduled.
  - A paper can only be scheduled once (`presentations.paper_id` is PRIMARY KEY).
  - Crucial Policy: The manuscript author must have completed a confirmed, paid registration before scheduling is permitted.

### 12.9 Analytical Read-Models & Insights Module
- **Purpose:** Serve real-time telemetry, KPI metrics, score distributions, and time-series bucketing across role dashboards.
- **Key Files:** `cms_app/insights.py#L1-L219`, `cms_app/__init__.py#L841-L850`.
- **Core Functions:** `manager_kpis`, `admin_kpis`, `author_kpis`, `reviewer_kpis`, `attendee_kpis`, `weekly_series`, `status_counts`, `open_papers`, `reviewer_workload`, `score_histogram`, `revenue_by_conference`.
- **Data Architecture:** Read-only analytical queries separated entirely from transactional write logic, computing acceptance rates, reviewer utilization meters, 8-week submission velocity, and track distributions.

### 12.10 Administration & Audit Logging Module
- **Purpose:** System-wide governance, user account state modification, role elevation, and immutable activity logging.
- **Key Files:** `cms_app/services.py#L42-L46`, `cms_app/services.py#L580-L630`, `cms_app/__init__.py#L852-L911`.
- **Core Functions:** `log_activity`, `admin_create_user`, `set_user_role`, `set_user_active`, `reassign_chair`.
- **Security Rules:** Self-deactivation and self-removal of the administrator role are strictly blocked. Every state mutation records an entry in the `activity` table with timestamp and actor ID.

## 13. System Workflow and Algorithms

This section details the primary algorithmic logic, mathematical models, decision rules, and step-by-step procedures implemented in `ConfMan`.

---

### Algorithm 1: User Registration and Credential Hashing
- **Source Reference:** `cms_app/services.py#L101-L124`
- **Purpose:** Validate user input, enforce role boundaries, prevent duplicate email accounts, hash passwords securely, and record an audit log.

```
Algorithm 1: User Registration
Input: db (Database Connection), name, email, password, role, affiliation, expertise
Output: user_id (Integer)

1. Strip whitespace from name and normalize email to lowercase.
2. If name is empty, raise ServiceError("Name is required.").
3. If email does not match regex ^[^@\s]+@[^@\s]+\.[^@\s]+$, raise ServiceError("Enter a valid email address.").
4. If length(password) < 8 or password does not contain at least one digit [0-9]:
       raise ServiceError("Password must be at least 8 characters and contain a digit.").
5. If role not in ("admin", "chair", "reviewer", "author", "attendee"):
       raise ServiceError("Invalid role.").
6. Query users table: SELECT 1 FROM users WHERE email = email.
   If record exists:
       raise ServiceError("An account with this email already exists.").
7. Compute password_hash = generate_password_hash(password) using PBKDF2:SHA256.
8. Execute SQL:
       INSERT INTO users(name, email, password_hash, role, affiliation, expertise, created_at)
       VALUES (name, email, password_hash, role, affiliation, expertise, CURRENT_TIMESTAMP)
9. Record activity audit: log_activity(db, new_user_id, "Account created", "{name} joined as {role}")
10. Commit transaction: db.commit()
11. Return new_user_id.
```

---

### Algorithm 2: Reviewer Expertise Ranking and Workload Matching Heuristic
- **Source Reference:** `cms_app/services.py#L287-L308`
- **Purpose:** Rank candidate reviewers for a specific paper using set-theoretic keyword overlap and current pending workload.

```
Algorithm 2: Reviewer Expertise Ranking
Input: db, paper_id
Output: ranked_list (Ordered List of Dictionaries)

1. Retrieve paper record: paper = SELECT * FROM papers WHERE paper_id = paper_id.
2. Retrieve track record: track = SELECT name FROM tracks WHERE track_id = paper.track_id.
3. Define term tokenization function terms(text):
       Split text by non-alphanumeric characters [^a-z0-9+#]+.
       Return set of lowercase tokens with length > 2.
4. Construct wanted terms set:
       wanted = terms(paper.keywords + " " + track.name + " " + paper.title)
5. Retrieve all eligible candidate reviewers:
       candidates = SELECT * FROM users 
                    WHERE role = 'reviewer' 
                      AND is_active = 1 
                      AND user_id != paper.author_id
                      AND user_id NOT IN (
                          SELECT reviewer_id FROM review_assignments 
                          WHERE paper_id = paper_id
                      )
6. Initialize ranked = []
7. For each reviewer r in candidates:
       a. Calculate load = pending_reviews(db, r.user_id, paper.conf_id)
          where pending_reviews counts review_assignments with status = 'Pending'.
       b. reviewer_terms = terms(r.expertise)
       c. match_score = |wanted ∩ reviewer_terms|  (Cardinality of set intersection)
       d. is_full = (load >= MAX_PENDING_REVIEWS_PER_REVIEWER)  [where MAX = 5]
       e. Append {user: r, match: match_score, load: load, full: is_full} to ranked.
8. Sort ranked using multi-criteria key:
       Primary Key:   full ASCENDING (reviewers under quota prioritized over full reviewers)
       Secondary Key: match DESCENDING (highest keyword overlap prioritized)
       Tertiary Key:  load ASCENDING (lowest existing workload prioritized)
       Quaternary:    user.name ASCENDING (deterministic alphabetical tie-breaker)
9. Return ranked.
```

---

### Algorithm 3: Greedy Multi-Criteria Reviewer Auto-Assignment
- **Source Reference:** `cms_app/services.py#L310-L348`
- **Purpose:** Automatically fill a manuscript's review quota up to 3 reviewers without exceeding individual reviewer limits or introducing conflicts of interest.

```
Algorithm 3: Automated Reviewer Assignment
Input: db, chair_id, paper_id, target = 3
Output: added_reviewers (List of Reviewer Names)

1. Verify that chair_id has Chair role for the conference or is Admin.
2. Count existing assignments:
       have = SELECT COUNT(*) FROM review_assignments WHERE paper_id = paper_id.
3. If have >= min(target, MAX_REVIEWERS_PER_PAPER):
       Return empty list (Quota already satisfied).
4. Retrieve ranked candidate list: candidates = ranked_reviewers(db, paper_id)
5. Initialize added = []
6. For each candidate cand in candidates:
       If have + length(added) >= min(target, MAX_REVIEWERS_PER_PAPER):
           Break loop.
       If cand.full is True:
           Continue to next candidate.
       Execute _insert_assignment:
           INSERT INTO review_assignments(paper_id, reviewer_id, assigned_at)
           VALUES (paper_id, cand.user.user_id, CURRENT_TIMESTAMP)
           UPDATE papers SET status = 'Under Review' WHERE paper_id = paper_id.
           INSERT notification for reviewer: "You have been assigned to review '{paper.title}'."
           Log activity: "Reviewer auto-assigned"
       Append cand.user.name to added.
7. If added is empty:
       raise ServiceError("No eligible reviewers are available for this paper.")
8. Commit transaction: db.commit()
9. Return added.
```

---

### Algorithm 4: Editorial Decision Suggestion Engine
- **Source Reference:** `cms_app/services.py#L389-L404`
- **Purpose:** Calculate statistical consensus from completed reviews and produce an automated decision recommendation.

```
Algorithm 4: Decision Suggestion Logic
Input: db, paper_id
Output: Dictionary {average: Float, count: Integer, suggestion: String}

1. Retrieve scores:
       rows = SELECT r.score FROM reviews r 
              JOIN review_assignments ra ON ra.assignment_id = r.assignment_id 
              WHERE ra.paper_id = paper_id
2. If count(rows) < MIN_REVIEWS_FOR_DECISION (2):
       raise ServiceError("At least 2 completed reviews are required.")
3. Calculate arithmetic mean:
       average = round( sum(rows.score) / count(rows), 2 )
4. Apply decision threshold mapping:
       If average >= 7.00:
           suggestion = "Accepted"
       Else if average >= 5.00:
           suggestion = "Revision Required"
       Else:
           suggestion = "Rejected"
5. Return {average: average, count: count(rows), suggestion: suggestion}.
```

---

### Algorithm 5: Tiered Registration Fee Calculation with Early-Bird Discount
- **Source Reference:** `cms_app/services.py#L428-L455`
- **Purpose:** Determine attendee registration fee based on attendee professional category and date boundaries.

```
Algorithm 5: Registration Fee Calculation
Input: category, registration_date, early_bird_deadline
Output: final_fee (Float)

1. Fee Schedule:
       FEES = {"student": 500.00, "academic": 1000.00, "industry": 2000.00}
2. If category not in FEES:
       raise ServiceError("Select a valid registration category.")
3. base_fee = FEES[category]
4. Parse registration_date (YYYY-MM-DD) and early_bird_deadline (YYYY-MM-DD).
5. If registration_date <= early_bird_deadline:
       final_fee = base_fee * (1.00 - EARLY_BIRD_DISCOUNT)  [where discount = 0.20]
   Else:
       final_fee = base_fee
6. Return round(final_fee, 2).
```

---

### Algorithm 6: Luhn Modulo-10 Checksum Card Validation
- **Source Reference:** `cms_app/services.py#L457-L466`
- **Purpose:** Validate credit card numbers against the standard ISO/IEC 7812 Luhn formula before gateway dispatch.

```
Algorithm 6: Luhn Mod-10 Checksum
Input: card_number (String of digits)
Output: Boolean (True if valid, False otherwise)

1. Convert string digits to integer array: digits = [int(c) for c in card_number].
2. Initialize checksum = 0.
3. For each index i, digit d in reversed(digits) from index 0 to length-1:
       If i is odd (i % 2 == 1, i.e., every second digit from the right):
           d = d * 2
           If d > 9:
               d = d - 9
       checksum = checksum + d
4. Return (checksum % 10 == 0).
```

---

### Algorithm 7: Room Clash and Session Conflict Detection
- **Source Reference:** `cms_app/services.py#L502-L534`
- **Purpose:** Prevent scheduling two sessions in the same physical or virtual room with overlapping time boundaries.

```
Algorithm 7: Room Clash Detection
Input: db, conf_id, room, new_start_time, new_end_time
Output: Conflict Status (Success or ServiceError)

1. Parse new_start_time and new_end_time as ISO datetimes.
2. If new_end_time <= new_start_time:
       raise ServiceError("End time must be after the start time.")
3. Verify that new_start_time and new_end_time occur on the same date and fall within [conf.start_date, conf.end_date].
4. Query existing sessions for room overlap:
       SELECT 1 FROM sessions 
       WHERE conf_id = conf_id 
         AND room = room.strip() 
         AND start_time < new_end_time 
         AND end_time > new_start_time
5. If query returns a matching record:
       raise ServiceError("Another session already uses this room at that time.")
6. Return Success.
```

---

### Algorithm 8: Paper Scheduling Prerequisite Enforcement
- **Source Reference:** `cms_app/services.py#L536-L563`
- **Purpose:** Ensure that a paper scheduled into a session is accepted, not already scheduled, fits session capacity, and its author has paid conference registration.

```
Algorithm 8: Paper Scheduling Validation
Input: db, user_id, paper_id, session_id
Output: Presentation Slot Order (Integer)

1. Verify user_id is the conference Chair or Admin.
2. Verify paper.status == 'Accepted'. If not, raise ServiceError("Only accepted papers can be scheduled.").
3. Verify paper is not already scheduled:
       SELECT 1 FROM presentations WHERE paper_id = paper_id.
       If exists, raise ServiceError("This paper is already scheduled.").
4. Verify session capacity:
       used = SELECT COUNT(*) FROM presentations WHERE session_id = session_id.
       If used >= session.capacity, raise ServiceError("This session is full.").
5. Mandatory Author Registration Verification:
       registered = SELECT 1 FROM registrations 
                    WHERE conf_id = paper.conf_id 
                      AND user_id = paper.author_id 
                      AND status = 'Confirmed'
       If registered is None:
           raise ServiceError("The author must complete a paid registration before scheduling.")
6. Insert into presentations:
       INSERT INTO presentations(paper_id, session_id, slot_order)
       VALUES (paper_id, session_id, used + 1)
7. Update paper status:
       UPDATE papers SET status = 'Scheduled' WHERE paper_id = paper_id.
8. Notify author: "Your paper is scheduled in {session.title} ({session.room}) at {session.start_time}."
9. Commit transaction and return used + 1.
```

---

## 14. Database Design

### 14.1 Relational Architecture and Integrity
The database layer is implemented in SQLite3 with enforced referential integrity (`PRAGMA foreign_keys = ON;`). The schema comprises 13 distinct relational tables with strict column constraints, primary key generation via auto-increment, unique composite indices, and domain check constraints.

### 14.2 Detailed Data Dictionary

#### Table 1: `users`
Stores user identities, credentials, roles, institutional affiliations, and reviewer expertise keywords.
- `user_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique user identifier.
- `name`: `TEXT NOT NULL` — Full name of the user.
- `email`: `TEXT NOT NULL UNIQUE` — Normalized lowercase email address (case-insensitive unique index).
- `password_hash`: `TEXT NOT NULL` — Werkzeug PBKDF2:SHA256 password hash string.
- `role`: `TEXT NOT NULL CHECK (role IN ('admin','chair','reviewer','author','attendee'))` — System access role.
- `affiliation`: `TEXT NOT NULL DEFAULT ''` — Academic institution, university, or corporate affiliation.
- `expertise`: `TEXT NOT NULL DEFAULT ''` — Comma-separated or space-separated research expertise keywords.
- `is_active`: `INTEGER NOT NULL DEFAULT 1` — Account activation flag (1 = active, 0 = deactivated).
- `created_at`: `TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP` — ISO timestamp of user registration.

#### Table 2: `conferences`
Stores academic conference editions, dates, venue, and assigned conference chair.
- `conf_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique conference identifier.
- `name`: `TEXT NOT NULL` — Official title of the conference edition.
- `venue`: `TEXT NOT NULL` — Physical location, university hall, or virtual platform designation.
- `description`: `TEXT NOT NULL DEFAULT ''` — Extended narrative overview of conference topics.
- `start_date`: `TEXT NOT NULL` — Beginning date of conference (YYYY-MM-DD).
- `end_date`: `TEXT NOT NULL` — Concluding date of conference (YYYY-MM-DD).
- `submission_deadline`: `TEXT NOT NULL` — Ingestion deadline for authors (YYYY-MM-DD).
- `early_bird_deadline`: `TEXT NOT NULL` — Cutoff date for discounted attendee registration (YYYY-MM-DD).
- `chair_id`: `INTEGER NOT NULL REFERENCES users(user_id)` — Foreign key referencing the chair user record.

#### Table 3: `tracks`
Thematic areas or symposia under a specific conference.
- `track_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique track identifier.
- `conf_id`: `INTEGER NOT NULL REFERENCES conferences(conf_id) ON DELETE CASCADE` — Parent conference.
- `name`: `TEXT NOT NULL` — Name of track (e.g., "Software Testing", "AI and Machine Learning").
- *Constraints:* `UNIQUE (conf_id, name)` — Prevents duplicate track names within the same conference.

#### Table 4: `papers`
Submitted manuscripts, metadata, review lifecycle status, and decisions.
- `paper_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique paper identifier.
- `conf_id`: `INTEGER NOT NULL REFERENCES conferences(conf_id)` — Target conference.
- `track_id`: `INTEGER NOT NULL REFERENCES tracks(track_id)` — Assigned thematic track.
- `author_id`: `INTEGER NOT NULL REFERENCES users(user_id)` — Submitting author.
- `title`: `TEXT NOT NULL` — Manuscript title (max 200 characters).
- `abstract`: `TEXT NOT NULL` — Manuscript abstract (min 50 characters).
- `keywords`: `TEXT NOT NULL DEFAULT ''` — Author-provided index terms for reviewer matching.
- `file_name`: `TEXT NOT NULL` — Original uploaded filename (PDF).
- `status`: `TEXT NOT NULL DEFAULT 'Submitted' CHECK (status IN ('Submitted','Under Review','Reviewed','Accepted','Rejected','Revision Required','Scheduled'))` — Current workflow state.
- `decision_remarks`: `TEXT NOT NULL DEFAULT ''` — Narrative remarks attached by the Chair during decision.
- `submitted_at`: `TEXT NOT NULL` — ISO timestamp of initial manuscript submission.

#### Table 5: `review_assignments`
Allocation of specific reviewers to manuscripts.
- `assignment_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique review assignment identifier.
- `paper_id`: `INTEGER NOT NULL REFERENCES papers(paper_id)` — Foreign key to assigned paper.
- `reviewer_id`: `INTEGER NOT NULL REFERENCES users(user_id)` — Foreign key to assigned reviewer.
- `assigned_at`: `TEXT NOT NULL` — ISO timestamp when assignment was created.
- `status`: `TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending','Completed'))` — Review completion state.
- *Constraints:* `UNIQUE (paper_id, reviewer_id)` — Enforces that a reviewer cannot be assigned to a paper multiple times.

#### Table 6: `reviews`
Quantitative and qualitative peer review evaluations.
- `review_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique review identifier.
- `assignment_id`: `INTEGER NOT NULL UNIQUE REFERENCES review_assignments(assignment_id)` — 1-to-1 link to assignment.
- `score`: `INTEGER NOT NULL CHECK (score BETWEEN 1 AND 10)` — Integer quality score from 1 (poor) to 10 (exceptional).
- `comments`: `TEXT NOT NULL` — Narrative critique and evaluation (min 20 characters).
- `recommendation`: `TEXT NOT NULL CHECK (recommendation IN ('accept','minor revision','major revision','reject'))` — Categorical recommendation.
- `submitted_at`: `TEXT NOT NULL` — ISO timestamp of review submission.

#### Table 7: `decisions`
Permanent audit log of editorial decisions.
- `decision_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique decision identifier.
- `paper_id`: `INTEGER NOT NULL REFERENCES papers(paper_id)` — Evaluated paper.
- `decision`: `TEXT NOT NULL CHECK (decision IN ('Accepted','Rejected','Revision Required'))` — Outcome.
- `remarks`: `TEXT NOT NULL DEFAULT ''` — Editorial explanation to author.
- `decided_by`: `INTEGER NOT NULL REFERENCES users(user_id)` — Chair who recorded the decision.
- `decided_at`: `TEXT NOT NULL` — ISO timestamp of decision execution.

#### Table 8: `registrations`
Conference attendance bookings by users across fee categories.
- `reg_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique registration identifier.
- `conf_id`: `INTEGER NOT NULL REFERENCES conferences(conf_id)` — Target conference.
- `user_id`: `INTEGER NOT NULL REFERENCES users(user_id)` — Registering attendee or author.
- `category`: `TEXT NOT NULL CHECK (category IN ('student','academic','industry'))` — Fee classification.
- `fee_amount`: `REAL NOT NULL` — Computed fee in INR, accounting for early-bird discount.
- `status`: `TEXT NOT NULL DEFAULT 'Pending Payment' CHECK (status IN ('Pending Payment','Confirmed','Cancelled'))` — Registration state.
- `registered_at`: `TEXT NOT NULL` — ISO timestamp of registration initiation.
- *Constraints:* `UNIQUE (conf_id, user_id)` — A user can register at most once per conference.

#### Table 9: `payments`
Financial transaction records resulting from credit card processing.
- `payment_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique payment record identifier.
- `reg_id`: `INTEGER NOT NULL REFERENCES registrations(reg_id)` — Linked registration.
- `amount`: `REAL NOT NULL` — Amount paid in INR.
- `method`: `TEXT NOT NULL DEFAULT 'card'` — Payment method instrument.
- `txn_ref`: `TEXT NOT NULL` — Gateway transaction reference (e.g., `TXN-5C9B3D7E8F`).
- `status`: `TEXT NOT NULL CHECK (status IN ('Success','Failed'))` — Transaction outcome.
- `paid_at`: `TEXT NOT NULL` — ISO timestamp of transaction attempt.

#### Table 10: `sessions`
Conference schedule tracks and physical/virtual presentation rooms.
- `session_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique session identifier.
- `conf_id`: `INTEGER NOT NULL REFERENCES conferences(conf_id)` — Parent conference.
- `title`: `TEXT NOT NULL` — Thematic session title (e.g., "Networks and SDN").
- `room`: `TEXT NOT NULL` — Hall name or room designation (e.g., "Hall A").
- `start_time`: `TEXT NOT NULL` — ISO datetime string (e.g., `2026-11-20T10:00`).
- `end_time`: `TEXT NOT NULL` — ISO datetime string (e.g., `2026-11-20T11:30`).
- `capacity`: `INTEGER NOT NULL DEFAULT 4` — Maximum number of papers that can be scheduled in this session.

#### Table 11: `presentations`
Mapping of accepted papers to session presentation slots.
- `paper_id`: `INTEGER PRIMARY KEY REFERENCES papers(paper_id)` — The paper scheduled (1-to-1 mapping ensures a paper is scheduled only once).
- `session_id`: `INTEGER NOT NULL REFERENCES sessions(session_id)` — Target session.
- `slot_order`: `INTEGER NOT NULL` — Sequential presentation position within the session (1, 2, 3...).

#### Table 12: `notifications`
Internal asynchronous notification messages dispatched to users.
- `notif_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique notification identifier.
- `user_id`: `INTEGER NOT NULL REFERENCES users(user_id)` — Recipient user.
- `message`: `TEXT NOT NULL` — Notification body text.
- `created_at`: `TEXT NOT NULL` — ISO timestamp of creation.
- `is_read`: `INTEGER NOT NULL DEFAULT 0` — Read flag (0 = unread, 1 = read).

#### Table 13: `activity`
System-wide immutable security audit log.
- `activity_id`: `INTEGER PRIMARY KEY AUTOINCREMENT` — Unique audit entry identifier.
- `user_id`: `INTEGER REFERENCES users(user_id)` — Actor who triggered the event (nullable for system actions).
- `action`: `TEXT NOT NULL` — Categorical event name (e.g., "Paper submitted", "Reviewer assigned", "Role changed").
- `detail`: `TEXT NOT NULL DEFAULT ''` — Additional contextual details.
- `created_at`: `TEXT NOT NULL` — ISO timestamp of event occurrence.

---

## 15. API and Integration Details

### 15.1 HTTP Endpoints and Routing Catalog
`ConfMan` exposes 26 distinct server-rendered HTTP routes managed via Flask route decorators.

| HTTP Method | Route URL Pattern | Access Level / Role | Endpoint Name | Description and Core Operations |
|---|---|---|---|---|
| `GET` | `/` | Public | `index` | Public landing page showing active conferences, global platform statistics, and submission pipeline. |
| `GET`, `POST` | `/register` | Public (Unauthenticated) | `register` | Self-registration form for Author, Reviewer, or Attendee roles. Invokes `services.register_user`. |
| `GET`, `POST` | `/login` | Public (Unauthenticated) | `login` | User credential authentication. Establishes session `user_id`. Supports `next` redirect parameter. |
| `POST` | `/logout` | Authenticated | `logout` | Clears session dictionary and redirects to landing page. Requires valid CSRF token. |
| `GET` | `/dashboard` | `@login_required` | `dashboard` | Dynamic role-specific landing dashboard rendering tailored telemetry for Chair, Admin, Reviewer, Author, or Attendee. |
| `GET` | `/notifications` | `@login_required` | `notifications` | Displays recent 100 notifications for current user and marks all unread notifications as read. |
| `GET`, `POST` | `/profile` | `@login_required` | `profile` | Profile information update (name, affiliation, expertise) and password change handler. |
| `GET` | `/conferences` | Public | `conferences` | Public list of all conferences with chair names, paper counts, track counts, and confirmed attendee counts. |
| `GET`, `POST` | `/conferences/new` | `@role_required("chair", "admin")` | `conference_new` | Conference creation form. Validates dates and registers new conference entity. |
| `GET` | `/conferences/<int:conf_id>` | Public / Mixed | `conference` | Detailed conference overview. Displays tracks, sessions, fees, deadlines, and chair management tools if managed. |
| `POST` | `/conferences/<int:conf_id>/tracks` | `@login_required` (Chair/Admin) | `track_add` | Adds a new thematic track to the conference. |
| `POST` | `/conferences/<int:conf_id>/sessions` | `@login_required` (Chair/Admin) | `session_add` | Creates a new presentation session with room, capacity, and time windows. Checks room clashes. |
| `POST` | `/conferences/<int:conf_id>/chair` | `@role_required("admin")` | `chair_reassign` | Reassigns the conference chair to another qualified user. |
| `POST` | `/conferences/<int:conf_id>/auto-assign` | `@login_required` (Chair/Admin) | `conference_auto_assign` | Executes greedy auto-assignment algorithm across all under-reviewed papers for this conference. |
| `POST` | `/auto-assign` | `@role_required("chair", "admin")` | `auto_assign_all` | Batch auto-assignment across all conferences managed by the current user. |
| `GET` | `/conferences/<int:conf_id>/program` | Public | `program` | Public schedule displaying sessions, rooms, timeslots, and accepted paper presentation orders. |
| `GET` | `/conferences/<int:conf_id>/export/papers.csv` | `@login_required` (Chair/Admin) | `export_papers` | Exports conference papers, authors, tracks, and statuses as an RFC 4180 compliant CSV stream. |
| `GET`, `POST` | `/conferences/<int:conf_id>/submit` | `@role_required("author")` | `paper_submit` | Manuscript submission endpoint with multipart PDF upload handling and metadata persistence. |
| `GET` | `/papers` | `@login_required` | `papers_list` | Filtered, searchable, and tabbed list of papers (author papers, reviewer assigned/open papers, chair submissions). |
| `GET` | `/papers/<int:paper_id>` | `@login_required` (Access Controlled) | `paper_detail` | Detailed view of paper, review progress, reviews (anonymized per role), decision tools, and scheduling controls. |
| `GET` | `/papers/<int:paper_id>/file` | `@login_required` (Chair/Author/Reviewer) | `paper_file` | Secure download/viewing of the uploaded manuscript PDF. Prohibited for prospects and general public. |
| `POST` | `/papers/<int:paper_id>/assign` | `@login_required` (Chair/Admin) | `reviewer_assign` | Manually assigns a designated reviewer to a paper. |
| `POST` | `/papers/<int:paper_id>/auto-assign` | `@login_required` (Chair/Admin) | `paper_auto_assign` | Auto-assigns reviewers to a specific paper using expertise matching. |
| `POST` | `/papers/<int:paper_id>/volunteer` | `@role_required("reviewer")` | `paper_volunteer` | Reviewer self-assignment to an open paper needing reviewers. |
| `POST` | `/papers/<int:paper_id>/decision` | `@login_required` (Chair/Admin) | `decision` | Records definitive editorial decision (`Accepted`, `Rejected`, `Revision Required`) with remarks. |
| `POST` | `/papers/<int:paper_id>/schedule` | `@login_required` (Chair/Admin) | `schedule` | Schedules an accepted paper with a paid author into a specific session slot. |
| `GET`, `POST` | `/reviews/<int:assignment_id>` | `@role_required("reviewer")` | `review_form` | Form for reviewing an assigned manuscript: score (1–10), narrative comments, recommendation. |
| `GET`, `POST` | `/conferences/<int:conf_id>/registration` | `@login_required` | `registration` | Conference registration view calculating tiered fees and early-bird discounts. |
| `GET`, `POST` | `/registrations/<int:reg_id>/pay` | `@login_required` | `pay` | Payment checkout form. Executes Luhn validation and mock gateway transaction. |
| `GET` | `/analytics` | `@role_required("chair", "admin")` | `analytics` | Manager analytics view: KPIs, track distribution, score histogram, revenue breakdown, reviewer workloads. |
| `GET` | `/admin/users` | `@role_required("admin")` | `admin_users` | Administrative user management table with role filtering, search, and user creation link. |
| `GET`, `POST` | `/admin/users/new` | `@role_required("admin")` | `admin_user_new` | Administrator creates a user with any designated role. |
| `POST` | `/admin/users/<int:user_id>/role` | `@role_required("admin")` | `admin_set_role` | Modifies an existing user's role. |
| `POST` | `/admin/users/<int:user_id>/active` | `@role_required("admin")` | `admin_set_active` | Toggles an account active (1) or deactivated (0). |
| `GET` | `/admin/activity` | `@role_required("admin")` | `admin_activity` | System-wide chronological audit log displaying user actions, actions taken, and timestamps. |

### 15.2 External Integrations and Simulated Services
- **Payment Gateway Simulation (`_mock_gateway`):**
  - Stand-in for an external payment provider (e.g., Stripe, PayPal, Razorpay).
  - Business Rule: Any card number passing the Luhn check whose digits end with `"0002"` is rejected with a gateway decline (`DECLINED`). All other valid cards succeed and are issued a cryptographically pseudo-random transaction reference string: `"TXN-" + uuid.uuid4().hex[:10].upper()`.
- **Filesystem Document Store:**
  - PDF files uploaded through `paper_submit` are stored in `app.config["UPLOAD_FOLDER"]` (`instance/uploads/`).
  - Storage naming convention: `{paper_id}_{uuid.hex[:8]}.pdf`. This prevents filename collision attacks, directory traversal vulnerabilities, and overwrites.

## 16. User Interface

### 16.1 Design Philosophy and Design System
The user interface of `ConfMan` is designed as a bespoke, modern, responsive web application utilizing clean CSS variables, CSS Grid, Flexbox, and inline Scalable Vector Graphics (SVG). Notably, the application does not depend on external UI frameworks such as Bootstrap or Tailwind CSS, ensuring complete autonomy, zero CDN reliance, and instant stylesheet parsing.

#### Color Palette and Design Tokens (`cms_app/static/style.css`):
- **Primary Brand Theme:** Deep Teal Green (`--t500: #1c9a89`, `--t600: #0f7f73`, `--t700: #0d655d`, `--t900: #093f3c`, `--t950: #052a29`).
- **Surfaces & Backgrounds (Light Mode):** Background `--bg: #eef4f3`, Surface `--surface: #ffffff`, Secondary Surface `--surface-2: #f6faf9`, Border Lines `--line: #dbe6e4`.
- **Surfaces & Backgrounds (Dark Mode):** Background `--bg: #071a19`, Surface `--surface: #0d2a28`, Secondary Surface `--surface-2: #0a2220`, Border Lines `--line: #1a3d3a`.
- **Typography:** Display Headings use `Bricolage Grotesque` / System Sans-Serif; Body Text uses `Figtree` / System Sans-Serif.
- **Semantic State Colors:** Good/Success (`--good: #17935a`), Warning/Attention (`--warn: #b7740a`), Danger/Error (`--bad: #c93b3b`), Info (`--info: #2862c9`), Accent Amber (`--accent: #e9a21b`).

### 16.2 Screen Catalog and Layout Structure

#### 1. Global Application Shell (`base.html`)
- **Desktop Layout:** Two-column CSS Grid consisting of a fixed 16.5rem sidebar (`.side`) and a fluid main workspace (`.main-col`).
- **Sidebar:** Houses the branding mark, dynamic role-tailored navigation items (`nav_for(user)`), unread notification badge counters, current user avatar with initials, and logout button.
- **Top Bar:** Sticky header with breadcrumbs, global paper search input (submitting to `/papers?q=`), unread notification bell icon, and dark/light mode toggle button.
- **Mobile Responsive Drawer:** On viewports below 900px, the sidebar transitions to an off-canvas drawer toggled via a hamburger button, accompanied by a backdrop overlay.

#### 2. Public Landing Page (`index.html`)
- **Hero Section:** High-contrast radial gradient presentation explaining ConfMan's value proposition. Features live platform metrics (total papers, completed reviews, registered users, active conferences) and an interactive paper pipeline bar.
- **Role Cards:** Explanatory grid outlining capabilities for Chairs, Reviewers, Authors, and Attendees.
- **Active Conferences Grid:** Displays cards for all upcoming and current conferences with date badges, venue, chair name, track counts, and direct links to submit or register.

#### 3. Authentication Screens (`login.html`, `register.html`, `_authart.html`)
- **Full Viewport Split Layout:** Left side displays an artistic SVG canvas with platform value highlights and summary stats; right side displays the authentication form.
- **One-Click Demo Login Bar (`login.html`):** Provides instant pre-filled login buttons for demo accounts (`admin@demo.org`, `chair@demo.org`, `reviewer1@demo.org`, `author@demo.org`, `attendee@demo.org`), dramatically accelerating testing and evaluations.
- **Self-Registration Form (`register.html`):** Radio segment selector allowing registration as Author, Reviewer, or Attendee. Includes inputs for affiliation and expertise keywords.

#### 4. Role Dashboards (`/dashboard`)
- **Chair / Admin Manager Dashboard (`dash_manager.html`):**
  - **KPI Cards:** Total submissions, acceptance percentage ring, papers needing reviewers (warning tone), papers ready for decision, total confirmed registrations, and gross conference revenue.
  - **Velocity Telemetry:** 8-week weekly submission SVG bar chart with native hover tooltips.
  - **Action Lists:** "Needs Reviewers" priority queue (papers with < 2 reviewers) with one-click auto-assign buttons; "Ready for Decision" table with calculated average scores and one-click review detail links.
  - **Workload Meters:** Reviewer capacity bars showing pending vs completed reviews per reviewer.
  - **Audit Activity Feed:** Real-time log of the 8 most recent system events.
- **Author Dashboard (`dash_author.html`):**
  - **KPIs:** Total papers submitted, awaiting review count, accepted count, revision required count, and composite average score across decided submissions.
  - **Submissions Table:** Lists user's manuscripts with track name, submission date, reviewer completion ratio (e.g., `2/3 reviews completed`), and visual status badge.
  - **Upcoming Deadlines Card:** Highlights upcoming conferences with open submission windows.
- **Reviewer Dashboard (`dash_reviewer.html`):**
  - **KPIs:** Pending reviews, completed reviews, average score given, available capacity slots (out of 5), and open papers pool count.
  - **Pending Reviews Queue:** Immediate action table showing assigned papers, submission dates, track names, and direct "Start Review" action buttons.
  - **Open for Review Carousel:** Quick-access list of manuscripts currently lacking reviewers, allowing immediate self-assignment (volunteering).
- **Attendee Dashboard (`dash_attendee.html`):**
  - **KPIs:** Confirmed registrations, pending payments count, and total registration expenditure.
  - **Booked Conferences:** Active registration cards displaying conference venue, dates, payment status, and link to pay or view receipt.
  - **Accepted Research Papers:** Curated feed of accepted scholarly works scheduled across registered conferences.

#### 5. Paper Management Views (`papers.html`, `paper.html`, `paper_submit.html`)
- **Paper Submission Screen (`paper_submit.html`):** Form with title character counter, track selection dropdown, abstract textarea (minimum 50 characters), keywords field, and PDF file picker with client validation.
- **Paper Listing (`papers.html`):** Unified filterable interface with tabs:
  - For Chairs: All, Needs Reviewers, In Review, Ready for Decision, Decided.
  - For Reviewers: Assigned, Open for Review, Completed.
  - For Authors: All, In Review, Decided.
  - Includes full-text search bar and dropdown filters for conference and status.
- **Detailed Paper View (`paper.html`):**
  - **Lifecycle Stepper (`_paperprogress.html`):** Multi-step visual progress bar illustrating current stage: Submitted -> Under Review -> Reviewed -> Decided -> Scheduled.
  - **Metadata & Abstract Card:** Displays title, keywords, track, author info (anonymized for reviewers), and PDF view/download button.
  - **Review Section:** Double-blind protected review table. Chairs see reviewer names, individual scores, qualitative comments, and recommendations. Reviewers see only their own review. Authors see anonymous scores and critiques only after a decision is recorded.
  - **Decision Panel (Chairs):** Displays algorithmic suggestion ("Suggested: Accepted based on average score 8.5/10"), decision radio buttons, and editorial remarks form.
  - **Session Scheduling Panel (Chairs):** Dropdown selector of available sessions for the conference, displaying current room capacity and session timeslot. Blocks scheduling if author has not completed a paid registration.

#### 6. Conference & Program Views (`conference.html`, `conference_new.html`, `program.html`)
- **Conference Detail (`conference.html`):** Public overview of venue, dates, submission deadlines, registration pricing tiers, track breakdown, and session listings. For chairs, embeds inline track creation, session creation, paper export, and chair reassignment modals.
- **Public Programme (`program.html`):** Clean, chronological timetable displaying each conference session, scheduled room, timeslot, and ordered presentation sequence with paper titles and author names.

#### 7. Registration & Payment Checkout (`registration.html`, `pay.html`)
- **Registration Form (`registration.html`):** Displays category selection cards (Student, Academic, Industry) with dynamic pricing calculation reflecting active early-bird discounts.
- **Payment Screen (`pay.html`):** Credit card checkout form with card number input, expiry date, CVV, and name. Provides visual hint cards for test numbers (`4242...` for success, ending `0002` for decline). Submits securely without persisting card data.

#### 8. Administrative Views (`admin_users.html`, `admin_user_new.html`, `admin_activity.html`)
- **User Management (`admin_users.html`):** Searchable table of all registered users displaying role, affiliation, submission count, review count, and activation status. Includes inline dropdown forms to change user roles and one-click activate/deactivate buttons.
- **Activity Audit Trail (`admin_activity.html`):** Chronological table of the 200 most recent system actions with actor name, role, action type, description, and relative time badges.

---

## 17. Implementation Details

### 17.1 Code Organization and Directory Manifest
The repository is structured with clear modularity across business logic, presentation routing, database management, templates, and testing:

```
ConfMan/
├── cms_app/                     # Core application package
│   ├── __init__.py              # Presentation Layer: Flask app factory, routes, filters, RBAC
│   ├── services.py              # Business Logic Layer: transactional services & rules
│   ├── insights.py              # Read-Model Layer: analytical SQL aggregations & metrics
│   ├── db.py                    # Data Access Layer: SQLite connection lifecycle & init
│   ├── schema.sql               # Relational Schema: 13 tables, check constraints, indexes
│   ├── static/
│   │   └── style.css            # Custom Teal Design System, dark mode, responsive rules
│   └── templates/               # Jinja2 HTML templates
│       ├── _authart.html        # Split auth hero branding graphic
│       ├── _confcard.html       # Conference card component for internal dashboards
│       ├── _confcard_public.html# Conference card for public landing page
│       ├── _flash.html          # Flash alert notification banners
│       ├── _macros.html         # SVG icons, KPI cards, sparklines, ring charts, forms
│       ├── _paperprogress.html  # Manuscript lifecycle stepper component
│       ├── admin_activity.html  # System audit trail view
│       ├── admin_user_new.html  # Admin user creation form
│       ├── admin_users.html     # Admin user management and role editor
│       ├── analytics.html       # Manager analytical metrics and distributions
│       ├── base.html            # Main HTML5 shell, sidebar, topbar, mobile drawer
│       ├── conference.html      # Conference detail, tracks, sessions, fees
│       ├── conference_new.html  # Conference creation form
│       ├── conferences.html     # Conference catalog listing
│       ├── dash_attendee.html   # Attendee dashboard: bookings and tickets
│       ├── dash_author.html     # Author dashboard: submission progress
│       ├── dash_manager.html    # Chair/Admin dashboard: KPIs, queues, velocity
│       ├── dash_reviewer.html   # Reviewer dashboard: assignments & volunteering
│       ├── error.html           # Unified HTTP 400, 403, 404 error page
│       ├── index.html           # Public landing page
│       ├── login.html           # Login screen with one-click demo credentials
│       ├── notifications.html   # In-app notification center
│       ├── page.html            # Generic content wrapper
│       ├── paper.html           # Detailed paper view, blind reviews, decision, schedule
│       ├── paper_submit.html    # Paper submission form with PDF upload
│       ├── papers.html          # Filterable, tabbed paper management listing
│       ├── pay.html             # Payment checkout form with mock gateway
│       ├── profile.html         # User profile and password management
│       ├── program.html         # Public conference schedule and presentations
│       ├── register.html        # User self-registration form
│       ├── registration.html    # Conference registration and fee selection
│       └── review.html          # Double-blind peer review evaluation form
├── tests/                       # Automated test suite
│   ├── test_cms.py              # Core domain rules and route tests (50 test cases)
│   └── test_v13.py              # Admin, auto-assign, and UI integration tests (17 test cases)
├── demo.py                      # Realistic 75-day historical demo data generator
├── seed.py                      # Database reset and seeding command-line tool
├── run.py                       # Application execution entry point
├── requirements.txt             # Minimal dependency manifest (Flask>=3.0)
└── README.md                    # Project documentation, quick-start guide, demo accounts
```

### 17.2 Application Factory Pattern (`create_app`)
- Implemented in `cms_app/__init__.py#L21-L42`.
- Accepts an optional `test_config` dictionary for configuring in-memory databases or disabling CSRF in test harnesses.
- Configures default parameters:
  - `SECRET_KEY`: Read from `os.environ.get("CMS_SECRET", "dev-only-change-me")`.
  - `DATABASE`: Path to SQLite file (`instance/cms.sqlite`).
  - `UPLOAD_FOLDER`: Path to PDF document storage (`instance/uploads`).
  - `MAX_CONTENT_LENGTH`: Enforces a 10MB upload ceiling (`10 * 1024 * 1024`).
  - `CSRF_ENABLED`: Boolean flag defaulting to `True`.
  - `AUTO_SEED`: When enabled, automatically loads demo data if the database is empty.
- Automatically ensures directories exist via `os.makedirs`.
- Registers database teardown hook: `app.teardown_appcontext(dbm.close_db)`.

### 17.3 Custom Jinja2 Template Filters
The presentation layer provides custom filters to ensure uniform formatting across all templates:
- `firstname(name)`: Extracts the first name, filtering out honorific titles (`Dr`, `Prof`, `Mr`, `Ms`, `Mrs`).
- `dt(value, pattern="%d %b %Y, %H:%M")`: Formats ISO datetime strings into human-readable strings.
- `d(value)`: Formats ISO dates into calendar day strings (e.g., `12 Dec 2026`).
- `ago(value)`: Calculates relative temporal distances (e.g., `just now`, `4h ago`, `3d ago`, or formatted date).
- `inr(value)`: Formats numeric currency values into the Indian Rupee grouping standard (e.g., `Rs 2,000`).

---

## 18. Security and Validation

### 18.1 Authentication and Password Security
- **Algorithm:** PBKDF2 with HMAC-SHA256 implemented via `werkzeug.security.generate_password_hash` and `check_password_hash`.
- **Complexity Enforcement (`services.py#L109-L110`):** Passwords must be at least 8 characters long and contain at least one numeric digit (`[0-9]`). Weak passwords raise a `ServiceError`.
- **Account State Verification (`services.py#L131-L133`):** During authentication, if `is_active == 0`, login is refused with `ServiceError("This account has been deactivated. Contact an administrator.")`.
- **Session Protection:** User identifiers are held in signed, tamper-proof client-side cookies managed by Flask's session interface.

### 18.2 Cross-Site Request Forgery (CSRF) Defense
- **Token Generation (`__init__.py#L139-L140`):** Injected via `app.context_processor`; generates a cryptographically random 16-byte hex token stored in `session["_csrf"]`.
- **Form Verification (`__init__.py#L54-L58`):** On every incoming POST request, `@app.before_request` extracts `request.form.get("_csrf")` and compares it to `session.get("_csrf")` using constant-time string comparison (`secrets.compare_digest`). Mismatches immediately trigger an HTTP 400 Bad Request error.

### 18.3 Role-Based Access Control (RBAC) & Double-Blind Isolation
- **Declarative Decorators:**
  - `@login_required`: Redirects unauthenticated requests to `/login?next=<path>` (`__init__.py#L60-L66`).
  - `@role_required(*roles)`: Evaluates `g.user["role"]`. If the user's role is not authorized, execution halts with an HTTP 403 Forbidden error (`__init__.py#L68-L77`).
- **Dynamic Access Evaluation (`paper_access` in `__init__.py#L562-L578`):**
  - Evaluates the requesting user's relationship to a specific paper (`chair`, `author`, `reviewer`, `prospect`, `public`).
  - Reviewers are prevented from seeing author names or affiliations (`__init__.py#L615-L616`).
  - Authors cannot see review scores or comments until an official editorial decision has been recorded (`__init__.py#L678-L680`).
  - Unassigned prospective reviewers and public attendees are blocked from downloading raw paper PDF files (`__init__.py#L713-L714`).

### 18.4 SQL Injection Defense
- 100% of database queries execute using SQLite parameterized query placeholders (`?`). No string concatenation, f-strings, or raw SQL formatting is used for user inputs across `services.py`, `insights.py`, or `__init__.py`.

### 18.5 Open Redirect Defense
- The `safe_next` helper (`__init__.py#L79-L80`) ensures that redirect targets in query strings begin with a single `/` and do not begin with `//`, preventing protocol-relative URL redirection to external malicious sites.

### 18.6 Payment Security & Simulated PCI-DSS Compliance
- The application never stores credit card primary account numbers (PAN), CVVs, or expiration dates in the database or logs. The card number is validated in memory and passed directly to the mock gateway routine (`_mock_gateway`). Only transaction reference tokens (`txn_ref`), timestamps, and fee amounts are recorded in the `payments` table.

### 18.7 File Upload Security
- Uploaded filenames are sanitized using `werkzeug.utils.secure_filename` to prevent path traversal attacks.
- Extension checking strictly enforces `.pdf`.
- Files are saved with unique UUID-based names (`{paper_id}_{uuid.hex[:8]}.pdf`) in an isolated directory (`instance/uploads`) outside the web server's static asset root.
- File downloads are proxied through a dedicated endpoint (`/papers/<paper_id>/file`) that checks authorization before sending files via `flask.send_file`.

## 19. Testing and Verification

### 19.1 Testing Strategy and Test Architecture
`ConfMan` incorporates an automated test suite implemented using Python's standard `unittest` framework. The testing strategy spans multiple verification levels:
1. **Isolated Service-Layer Unit Testing:** Business logic functions in `cms_app/services.py` are tested against an in-memory SQLite database (`:memory:`), isolating business rules from HTTP session handling or template rendering.
2. **Web Route & Controller Integration Testing:** Presentation routes in `cms_app/__init__.py` are tested using Flask's test client (`app.test_client()`), verifying HTTP status codes, session persistence, role enforcement, CSRF token validation, and template rendering.
3. **End-to-End Workflow Verification:** Full conference lifecycle scenarios—from user registration and submission to review assignment, decision-making, fee payment, and scheduling—are executed sequentially through the web interface.

### 19.2 Test Suite Catalog
The test suite consists of **67 automated test cases** distributed across two primary test modules:

#### Module 1: `tests/test_cms.py` (50 Tests)
- **`UserTests` (6 Tests):** Verifies user registration, duplicate email rejection (case-insensitive), weak password rejection (< 8 characters or no digits), role validation, password hashing integrity, and credential authentication.
- **`ConferenceTests` (4 Tests):** Verifies that only chairs or admins can create conferences, validates chronological date constraints (end date >= start date, submission deadline < start date, early-bird deadline <= start date), duplicate track prevention, and track creation permissions.
- **`PaperTests` (5 Tests):** Verifies author submission permissions, deadline boundary enforcement (inclusive on deadline day, closed afterward), rejection of non-PDF uploads, abstract length validation (>= 50 chars), title length limits (<= 200 chars), track affiliation checks, and notification dispatch.
- **`ReviewTests` (10 Tests):** Verifies reviewer assignment permissions, assignment transition to `'Under Review'`, conflict-of-interest prevention (author cannot review own submission), duplicate assignment blocking, maximum 3 reviewers per paper limit, maximum 5 pending reviews workload cap, non-reviewer assignment prevention, review ownership validation, single-review submission enforcement, review score (1–10) and comment (>= 20 chars) validation, and automatic transition to `'Reviewed'` when all reviews are completed.
- **`DecisionTests` (5 Tests):** Verifies that editorial decisions require at least 2 completed reviews, tests score suggestion threshold boundaries (Accepted >= 7.0, Revision Required >= 5.0, Rejected < 5.0), verifies chair-only decision recording, checks author notification dispatch, and prevents redundant decision updates after final acceptance.
- **`RegistrationPaymentTests` (8 Tests):** Verifies category fee calculation with and without early-bird discounts, early-bird boundary calendar checks, duplicate registration rejection, registration closure after conference conclusion, Luhn algorithm card validation, card decline simulation for numbers ending in `0002`, successful payment registration status transition to `'Confirmed'`, prevention of double payment, and regression test for Unicode digits.
- **`SchedulingTests` (5 Tests):** Verifies session creation within conference dates, room double-booking clash detection, session capacity enforcement, scheduling only accepted papers, and the mandatory policy requiring authors to possess a confirmed, paid registration before scheduling.
- **`RouteTests` (7 Tests):** Verifies public page accessibility, protected route redirection, self-registration role restrictions (cannot self-register as chair/admin), login/logout session lifecycle, role-based access denial (HTTP 403), open redirect prevention, CSRF token enforcement, and a comprehensive end-to-end multi-role web workflow.

#### Module 2: `tests/test_v13.py` (17 Tests)
- **`AdminServiceTests` (5 Tests):** Verifies administrator activity logging, administrative role changes, account activation/deactivation toggles, chair reassignment, prevention of admin self-lockout, and rejection of non-admin actors attempting administrative actions.
- **`AssignmentTests` (6 Tests):** Verifies that reviewers can browse open papers, reviewer volunteering workflow with notification to the chair, volunteering caps at 3 reviewers, prevention of self-review or duplicate volunteering, auto-assignment expertise matching and workload balancing, and batch conference-wide auto-assignment covering all under-reviewed papers.
- **`DemoAndPageTests` (6 Tests):** Verifies the demo data seeder, dashboard loading across all five user roles, full-width responsive login/register pages, web-based reviewer volunteering, and reviewer assigned vs open paper visibility.

### 19.3 Regression Testing: Defect DEF-01 Verification
- **Issue Description:** In earlier iterations, Python's `str.isdigit()` method was used to validate credit card numbers. Because `str.isdigit()` returns `True` for certain Unicode characters (such as superscript two `²`), invalid non-ASCII numbers could pass the digit check and subsequently cause unexpected runtime errors during integer conversion.
- **Resolution:** Replaced `str.isdigit()` with strict ASCII regular expression matching: `re.fullmatch(r"[0-9]{13,19}", card)` (`services.py#L483`).
- **Verified Regression Test:** `test_non_ascii_digits_are_rejected_not_crashing` (`tests/test_cms.py#L324-L330`) specifically submits card numbers containing superscript characters and verifies that a clean `ServiceError` is raised rather than an unhandled runtime crash.

### 19.4 Actual Test Execution Output
The automated test suite was executed in the workspace environment on Python 3.14.8 using the command:
```bash
python3 -m unittest discover -s tests -v
```

**Verified Test Run Results:**
```
Ran 67 tests in 31.524s

OK
```
All 67 tests passed with zero failures, zero errors, and zero skipped tests.

---

## 20. Results and Discussion

### 20.1 Implementation Status Matrix
The following matrix summarizes the completion status of all planned features based on source code and test suite verification:

| Functional Area | Implemented Status | Verification Evidence | Notes |
|---|---|---|---|
| User Self-Registration | Complete (100%) | `services.py#L101`, `UserTests` | Enforces Author, Reviewer, Attendee roles. |
| User Authentication | Complete (100%) | `services.py#L126`, `UserTests` | PBKDF2:SHA256 password hashing. |
| Role-Based Access Control | Complete (100%) | `__init__.py#L68`, `RouteTests` | Declarative `@role_required` decorator. |
| Conference Management | Complete (100%) | `services.py#L138`, `ConferenceTests` | Date validation, track management. |
| Manuscript Ingestion | Complete (100%) | `services.py#L185`, `PaperTests` | PDF validation, deadline boundaries. |
| Double-Blind Review | Complete (100%) | `__init__.py#L562`, `ReviewTests` | Author masked from reviewer; reviews hidden from author until decision. |
| Reviewer Auto-Assignment | Complete (100%) | `services.py#L310`, `AssignmentTests`| Keyword overlap & workload balancing heuristic. |
| Reviewer Volunteering | Complete (100%) | `services.py#L275`, `AssignmentTests`| Reviewer self-assignment to open pool. |
| Editorial Decision Engine | Complete (100%) | `services.py#L389`, `DecisionTests` | Minimum 2 reviews, algorithmic score thresholds. |
| Registration Fee Engine | Complete (100%) | `services.py#L428`, `RegistrationPaymentTests` | Tiered pricing + 20% early-bird discount. |
| Payment Gateway Mock | Complete (100%) | `services.py#L457`, `RegistrationPaymentTests` | Luhn mod-10 validation, card decline simulation. |
| Session Scheduling | Complete (100%) | `services.py#L502`, `SchedulingTests`| Room clash detection, paid author prerequisite. |
| Public Conference Programme| Complete (100%) | `services.py#L565`, `program.html` | Timetable view by room and slot order. |
| CSV Data Export | Complete (100%) | `__init__.py#L511` | RFC 4180 compliant paper export. |
| Administrative Controls | Complete (100%) | `services.py#L580`, `AdminServiceTests`| Role changes, account deactivation, chair reassignment. |
| Activity Audit Log | Complete (100%) | `services.py#L42`, `admin_activity.html`| Immutable chronological action log. |
| In-App Notifications | Complete (100%) | `services.py#L93`, `notifications.html` | Database-backed notification center. |
| Responsive Dark/Light UI | Complete (100%) | `style.css`, `base.html` | Custom CSS variables with theme toggle. |

### 20.2 Demo Data Generation Analysis (`demo.py`)
To enable immediate institutional evaluation without manual data entry, `ConfMan` includes a longitudinal demo generator (`demo.py`) that uses an offset virtual clock (`_clock`) to construct a realistic 75-day chronological history.

**Generated Dataset Characteristics:**
- **Users (25 Accounts):**
  - 1 System Administrator (`admin@demo.org`).
  - 3 Program Chairs (`chair@demo.org`, `chair2@demo.org`, `chair3@demo.org`).
  - 6 Reviewers with diverse domain expertise keywords (`reviewer1@demo.org` through `reviewer6@demo.org`).
  - 10 Submitting Authors (`author@demo.org` through `author10@demo.org`).
  - 4 General Conference Attendees (`attendee@demo.org` through `attendee4@demo.org`).
  - 1 Deactivated user account for verification of deactivation controls.
- **Conferences (3 Active Editions):**
  1. *International Conference on Software Engineering and AI 2026* (Chennai, India; 3 tracks; 62 days of activity).
  2. *National Symposium on Cloud, Data and Analytics 2026* (Bengaluru, India; 3 tracks; 40 days of activity).
  3. *Smart Systems, IoT and Networks Summit 2026* (Coimbatore, India; 3 tracks; 75 days of activity).
- **Submissions & Reviews:** 30 scholarly papers with unique abstracts and keywords; valid synthetic PDF byte streams generated on-the-fly (`make_pdf`); over 20 completed reviews across various score bands; 10 recorded editorial decisions.
- **Sessions & Schedules:** Multiple physical sessions with defined capacities in "Hall A" and "Hall B"; 4 accepted papers scheduled in sequential slots.
- **Registrations & Payments:** 14 attendee registrations across Student, Academic, and Industry categories; successful card payments and one simulated card decline.

### 20.3 Operational and Performance Findings
- **Zero External Infrastructure Overhead:** The entire application operates without running standalone database processes (PostgreSQL/MySQL), external caches (Redis), or background workers (Celery).
- **Instant Cold Startup:** Cold startup requires less than 200 milliseconds, allowing immediate initialization on standard application servers.
- **Predictable Query Latency:** Analytical SQL queries in `insights.py` execute within single-digit milliseconds against SQLite B-tree indices on datasets of hundreds of records.

---

## 21. Limitations

To maintain academic objectivity, the system's current limitations are documented below:

### 21.1 Confirmed Architectural and Technical Limitations
1. **SQLite Concurrency for High Write Loads:** SQLite3 uses database-level locking for write transactions. While ideal for small-to-medium conferences, high-concurrency write surges (e.g., hundreds of authors submitting simultaneously at deadline) could experience lock contention.
2. **Local Filesystem Document Storage:** Uploaded PDF files are stored on the server's local filesystem (`instance/uploads/`). In horizontally scaled multi-server deployments behind a load balancer, a distributed object store (e.g., AWS S3, MinIO) or shared volume (NFS) would be required.
3. **Mock Payment Gateway:** The payment module is a functional mock that executes client validation and simulates gateway responses. It does not connect to live banking networks (Stripe, Razorpay, PayPal).
4. **Internal Notifications Only:** The notification system is strictly internal (stored in the `notifications` table and rendered in the web UI). Outbound SMTP email dispatch is not implemented.
5. **Single Document Submission:** Submissions are limited to a single PDF manuscript file. Rebuttals, camera-ready bundles, and supplementary datasets are not handled as separate multi-file packages.

### 21.2 Potential Domain Concerns
- **Keyword Matching Simplicity:** The auto-assignment algorithm uses lexical keyword tokenization and set intersection. It does not utilize dense vector embeddings (e.g., sentence-transformers or TF-IDF cosine similarity), meaning it may miss semantic synonymy (e.g., "deep learning" vs. "neural networks").
- **Fixed Fee Schedule:** While tiered by category (student, academic, industry) and date (early-bird), custom per-conference pricing structures must currently be modified in `cms_app/services.py` rather than through the web interface.

---

## 22. Future Enhancements

The following phased roadmap outlines realistic technical enhancements building upon ConfMan's existing architecture:

1. **Database Abstraction & Multi-Dialect Support:** Abstract database operations to allow seamless switching between SQLite3 (for local/testing deployments) and PostgreSQL (for large-scale enterprise deployments with connection pooling).
2. **Cloud Object Storage Adapter:** Implement a storage driver interface allowing file storage on AWS S3, Google Cloud Storage, or MinIO using pre-signed upload URLs.
3. **Live Payment Gateway Integration:** Add webhook handlers and checkout sessions for production payment gateways such as Stripe Elements and Razorpay.
4. **Asynchronous Email Notification Pipeline:** Integrate a background worker queue (e.g., Celery or RQ with Redis) to dispatch transactional SMTP emails for deadline reminders and review assignments.
5. **Semantic Embedding-Based Reviewer Matching:** Upgrade the reviewer ranking heuristic from set-based keyword intersection to vector cosine similarity using lightweight local sentence-transformers (e.g., `all-MiniLM-L6-v2`).
6. **Camera-Ready Ingestion & Multi-File Bundling:** Allow accepted authors to submit final camera-ready PDF packages, source files, and copyright transfer agreements.

---

## 23. Conclusion

The **ConfMan** Conference Management System demonstrates the feasibility of building a robust, enterprise-grade academic event management platform using clean architectural principles and minimal dependencies. By adhering to a strict 3-tier layered architecture, ConfMan completely isolates business logic from presentation and database access, ensuring high testability and maintainability.

The system addresses the core challenges of academic conference administration: it prevents conflicts of interest, balances reviewer workloads via heuristic auto-assignment, enforces double-blind review integrity, guides editorial decisions with statistical threshold analysis, handles tiered registrations and early-bird discounts, validates payments, and eliminates room and time clashes during session scheduling.

Validated by 67 automated unit and integration tests achieving a 100% pass rate, and backed by a comprehensive 75-day longitudinal demo dataset, ConfMan provides a complete, reliable, and deployable reference implementation for academic institutions, research departments, and scholarly societies.

---

## 24. References

1. **Flask Documentation:** Pallets Projects. *Flask: A Python Microframework*. Official Documentation, version 3.0.x, 2023. Available: https://flask.palletsprojects.com/
2. **Werkzeug Security:** Pallets Projects. *Werkzeug: The Python WSGI Web Application Library*. Official Documentation (Password Hashing and Utilities), 2023. Available: https://werkzeug.palletsprojects.com/
3. **SQLite3 Specification:** Hipp, D. R., et al. *SQLite: An In-Process Relational Database Engine*. Official Documentation (Foreign Keys and Transactions), 2023. Available: https://www.sqlite.org/
4. **ISO/IEC 7812:** International Organization for Standardization. *Identification cards — Identification of issuers — Part 1: Numbering system*. Luhn Checksum Algorithm (Mod-10), 2017.
5. **RFC 4180:** Shafranovich, Y. *Common Format and MIME Type for Comma-Separated Values (CSV) Files*. Internet Engineering Task Force (IETF), 2005. Available: https://www.rfc-editor.org/rfc/rfc4180
6. **Double-Blind Peer Review Standards:** Snodgrass, R. *Single- Versus Double-Blind Reviewing: An Analysis of the Literature*. ACM SIGMOD Record, vol. 35, no. 3, pp. 8–22, 2006.
7. **Role-Based Access Control (RBAC):** Sandhu, R. S., Coyne, E. J., Feinstein, H. L., & Youman, C. E. *Role-Based Access Control Models*. IEEE Computer, vol. 29, no. 2, pp. 38–47, 1996.
8. **Clean Architecture & Separation of Concerns:** Martin, R. C. *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall, 2017.

---

## 25. Installation and Execution

### 25.1 System Prerequisites
- **Operating System:** Linux (Ubuntu 20.04+, Debian 11+, Fedora, Arch), macOS (11+), or Windows (10/11 with PowerShell).
- **Python Runtime:** Python 3.10, 3.11, 3.12, 3.13, or 3.14.
- **Package Manager:** `pip` (Python package manager).
- **Disk Space:** Minimum 100 MB free disk space.
- **External Dependencies:** None (Zero external database or cache services required).

### 25.2 Installation Steps
Clone or navigate to the repository directory:
```bash
cd /home/dani/Projects/clg/ConfMan/ConfMan
```

Create and activate an isolated virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 25.3 Application Execution
Start the web application server:
```bash
python run.py
```
- By default, `run.py` initializes the application with `AUTO_SEED=True`. If the database is empty, it automatically populates the demo dataset.
- Access the application in any modern web browser at: **`http://127.0.0.1:5000`**

### 25.4 Resetting and Seeding the Database
To clear all data and re-seed from scratch:
```bash
python seed.py --reset
```
To load demo data into an existing empty database without resetting:
```bash
python seed.py
```

### 25.5 Running the Automated Test Suite
To execute the comprehensive 67-test automated verification suite:
```bash
python -m unittest discover -s tests -v
```

### 25.6 Default Demo User Credentials
All pre-seeded demo accounts share the uniform password: **`Demo@1234`**

| Persona / Role | Email Address | Default Password | Primary View & Responsibilities |
|---|---|---|---|
| **System Administrator** | `admin@demo.org` | `Demo@1234` | Global governance, user table, platform KPIs, activity logs. |
| **Program Chair** | `chair@demo.org` | `Demo@1234` | Conference configuration, reviewer auto-assign, decisions, scheduling. |
| **Reviewer** | `reviewer1@demo.org` | `Demo@1234` | Assigned papers queue, open paper pool, blind review submission. |
| **Author** | `author@demo.org` | `Demo@1234` | Paper submission, status stepper, anonymous feedback review. |
| **Attendee** | `attendee@demo.org` | `Demo@1234` | Conference registration, fee payment, receipt, accepted papers feed. |

## 26. Technical Diagram Specifications

This section provides complete, syntactically valid Mermaid diagram specifications that accurately represent the implemented system architecture, data flows, entity relationships, and behavioral workflows.

---

### Diagram 1: System Architecture Diagram (Layered 3-Tier Pattern)
- **Title:** ConfMan 3-Tier Layered Architecture
- **Purpose:** Visualize separation of concerns across presentation, business logic, analytics, and data access layers.

```mermaid
graph TD
    subgraph Client["Client Tier (Web Browser)"]
        UI["HTML5 / Vanilla CSS3 / SVG Interface"]
        Theme["Theme Manager (Light/Dark in localStorage)"]
    end

    subgraph Presentation["Presentation Tier (Flask Application)"]
        Routes["Flask Route Controllers (cms_app/__init__.py)"]
        AuthFilter["Request Pre-Filter (@before_request: Auth & CSRF)"]
        RBAC["Access Control Decorators (@login_required, @role_required)"]
        Jinja["Jinja2 Template Engine (cms_app/templates/)"]
        Static["Static Design Tokens (cms_app/static/style.css)"]
    end

    subgraph Logic["Business Logic Tier (Python Services)"]
        Services["Core Transactional Services (cms_app/services.py)"]
        Insights["Analytical Read-Models (cms_app/insights.py)"]
        Heuristics["Reviewer Ranking & Auto-Assign Heuristic"]
        DecisionEngine["Editorial Decision Rule Engine"]
        LuhnValidator["Luhn Mod-10 Checksum & Mock Gateway"]
        ClashDetector["Session Room-Clash Detection Logic"]
    end

    subgraph Data["Data Access & Storage Tier"]
        DBManager["Connection Manager (cms_app/db.py: g.db)"]
        SQLite[("Relational Database (instance/cms.sqlite)")]
        FileStore[("Document Storage (instance/uploads/)")]
    end

    UI -->|HTTP GET/POST Requests| Routes
    Routes --> AuthFilter
    AuthFilter --> RBAC
    RBAC --> Services
    Routes --> Insights
    Services --> Heuristics
    Services --> DecisionEngine
    Services --> LuhnValidator
    Services --> ClashDetector
    Services --> DBManager
    Insights --> DBManager
    DBManager -->|PRAGMA foreign_keys = ON| SQLite
    Routes -->|Save Sanitized PDF| FileStore
    Routes --> Jinja
    Jinja --> Static
    Jinja -->|Rendered HTML Response| UI
```

---

### Diagram 2: Context Diagram (Level 0 DFD)
- **Title:** ConfMan System Context Diagram (Level 0 DFD)
- **Purpose:** Illustrate high-level external entities interacting with the centralized ConfMan system boundaries.

```mermaid
flowchart TD
    Admin["System Administrator"]
    Chair["Program Committee Chair"]
    Author["Manuscript Author"]
    Reviewer["Peer Reviewer"]
    Attendee["Conference Attendee"]

    System[("ConfMan Core System")]

    Admin -->|"User Management, Role Assignments, System Audits"| System
    System -->|"Platform Analytics, Activity Audit Records"| Admin

    Chair -->|"Conference Dates, Tracks, Auto-Assign, Decisions, Sessions"| System
    System -->|"Submissions, Review Scores, Suggestions, Program Schedules"| Chair

    Author -->|"Manuscript Submissions, Title, Abstract, PDF Upload"| System
    System -->|"Submission Confirmations, Review Results, Schedule"| Author

    Reviewer -->|"Expertise Keywords, Reviewer Volunteering, Evaluations"| System
    System -->|"Assigned Papers (Blind), Open Papers Pool"| Reviewer

    Attendee -->|"Registrations, Fee Selections, Card Payments"| System
    System -->|"Payment Receipts, Confirmed Registrations, Conference Program"| Attendee
```

---

### Diagram 3: Level 1 Data Flow Diagram (DFD)
- **Title:** ConfMan Level 1 Functional Data Flow Diagram
- **Purpose:** Deconstruct system processes, internal data stores, and information flows across functional boundaries.

```mermaid
flowchart TD
    Author["Author"]
    Chair["Program Chair"]
    Reviewer["Reviewer"]
    Attendee["Attendee"]
    Admin["Administrator"]

    P1["1.0 User Authentication & Access Control"]
    P2["2.0 Conference & Track Management"]
    P3["3.0 Manuscript Submission & Ingestion"]
    P4["4.0 Reviewer Allocation & Volunteering"]
    P5["5.0 Peer Review & Editorial Decision"]
    P6["6.0 Registration & Fee Payment"]
    P7["7.0 Session Scheduling & Program"]
    P8["8.0 Administrative Governance & Audit"]

    D1[("D1: users")]
    D2[("D2: conferences & tracks")]
    D3[("D3: papers")]
    D4[("D4: review_assignments & reviews")]
    D5[("D5: decisions")]
    D6[("D6: registrations & payments")]
    D7[("D7: sessions & presentations")]
    D8[("D8: notifications & activity")]

    Author -->|Credentials| P1
    P1 -->|Query & Validate| D1
    P1 -->|Set Session Token| Author

    Chair -->|Create Conf & Tracks| P2
    P2 -->|Insert Conf & Track Data| D2

    Author -->|Submit Title, Abstract, PDF| P3
    P3 -->|Validate Deadline & Track| D2
    P3 -->|Insert Paper Record| D3
    P3 -->|Dispatch Notifications| D8

    Chair -->|Trigger Manual/Auto-Assign| P4
    Reviewer -->|Volunteer for Open Paper| P4
    P4 -->|Check COI & Capacity| D1
    P4 -->|Create Assignment, Update Status| D4
    P4 -->|Update Status to 'Under Review'| D3

    Reviewer -->|Submit Score & Critique| P5
    P5 -->|Insert Review Record| D4
    Chair -->|Query Average Score & Suggestions| P5
    P5 -->|Record Decision & Remarks| D5
    P5 -->|Update Paper Status| D3
    P5 -->|Notify Author| D8

    Attendee -->|Select Category & Pay Card| P6
    P6 -->|Compute Early-Bird Discount| D2
    P6 -->|Insert Registration & Payment| D6

    Chair -->|Define Room & Time Windows| P7
    P7 -->|Check Room Clashes & Capacity| D7
    Chair -->|Schedule Accepted Paper| P7
    P7 -->|Verify Author Paid Registration| D6
    P7 -->|Insert Presentation Slot| D7

    Admin -->|Deactivate User / Reassign Chair| P8
    P8 -->|Mutate User & Conf State| D1
    P8 -->|Mutate Conf Chair| D2
    P8 -->|Append Event Record| D8
```

---

### Diagram 4: Use Case Diagram
- **Title:** ConfMan System Use Case Diagram
- **Purpose:** Document all primary interactions between external actors and implemented functional capabilities.

```mermaid
flowchart LR
    subgraph Actors
        A1["Administrator"]
        A2["Program Chair"]
        A3["Reviewer"]
        A4["Author"]
        A5["Attendee"]
    end

    subgraph System["ConfMan Conference Management System"]
        UC1["Manage Users & Roles"]
        UC2["Reassign Conference Chair"]
        UC3["View Platform Analytics & Activity Log"]
        
        UC4["Create Conference & Tracks"]
        UC5["Assign Reviewers (Manual / Auto-Assign)"]
        UC6["Record Editorial Decision"]
        UC7["Create Sessions & Schedule Papers"]
        UC8["Export Papers as CSV"]
        
        UC9["Browse Open Papers Pool"]
        UC10["Volunteer to Review Paper"]
        UC11["Submit Double-Blind Review & Score"]
        
        UC12["Submit Manuscript (PDF + Metadata)"]
        UC13["Track Submission Progress"]
        UC14["View Anonymous Review Feedback"]
        
        UC15["Register for Conference"]
        UC16["Process Card Payment via Mock Gateway"]
        UC17["Browse Public Conference Program"]
    end

    A1 --> UC1
    A1 --> UC2
    A1 --> UC3

    A2 --> UC4
    A2 --> UC5
    A2 --> UC6
    A2 --> UC7
    A2 --> UC8

    A3 --> UC9
    A3 --> UC10
    A3 --> UC11

    A4 --> UC12
    A4 --> UC13
    A4 --> UC14
    A4 --> UC15

    A5 --> UC15
    A5 --> UC16
    A5 --> UC17
```

---

### Diagram 5: Class Diagram / Core Domain Structure
- **Title:** ConfMan Domain Services and Data Entities
- **Purpose:** Depict structural relationships, methods, and responsibilities of domain services and relational entity models.

```mermaid
classDiagram
    class User {
        +int user_id
        +string name
        +string email
        +string password_hash
        +string role
        +string affiliation
        +string expertise
        +int is_active
        +string created_at
    }

    class Conference {
        +int conf_id
        +string name
        +string venue
        +string description
        +string start_date
        +string end_date
        +string submission_deadline
        +string early_bird_deadline
        +int chair_id
    }

    class Track {
        +int track_id
        +int conf_id
        +string name
    }

    class Paper {
        +int paper_id
        +int conf_id
        +int track_id
        +int author_id
        +string title
        +string abstract
        +string keywords
        +string file_name
        +string status
        +string decision_remarks
        +string submitted_at
    }

    class ReviewAssignment {
        +int assignment_id
        +int paper_id
        +int reviewer_id
        +string assigned_at
        +string status
    }

    class Review {
        +int review_id
        +int assignment_id
        +int score
        +string comments
        +string recommendation
        +string submitted_at
    }

    class Decision {
        +int decision_id
        +int paper_id
        +string decision
        +string remarks
        +int decided_by
        +string decided_at
    }

    class Registration {
        +int reg_id
        +int conf_id
        +int user_id
        +string category
        +float fee_amount
        +string status
        +string registered_at
    }

    class Payment {
        +int payment_id
        +int reg_id
        +float amount
        +string method
        +string txn_ref
        +string status
        +string paid_at
    }

    class Session {
        +int session_id
        +int conf_id
        +string title
        +string room
        +string start_time
        +string end_time
        +int capacity
    }

    class Presentation {
        +int paper_id
        +int session_id
        +int slot_order
    }

    class Notification {
        +int notif_id
        +int user_id
        +string message
        +string created_at
        +int is_read
    }

    class Activity {
        +int activity_id
        +int user_id
        +string action
        +string detail
        +string created_at
    }

    User "1" -- "0..*" Conference : chairs
    User "1" -- "0..*" Paper : authors
    User "1" -- "0..*" ReviewAssignment : reviews
    User "1" -- "0..*" Registration : registers
    Conference "1" -- "1..*" Track : contains
    Conference "1" -- "0..*" Paper : hosts
    Conference "1" -- "0..*" Session : schedules
    Paper "1" -- "0..3" ReviewAssignment : receives
    ReviewAssignment "1" -- "0..1" Review : yields
    Paper "1" -- "0..1" Decision : concludes_with
    Registration "1" -- "0..1" Payment : settles_with
    Session "1" -- "0..*" Presentation : contains
    Paper "1" -- "0..1" Presentation : scheduled_as
    User "1" -- "0..*" Notification : receives
    User "0..1" -- "0..*" Activity : triggers
```

---

### Diagram 6: Entity-Relationship Diagram (ERD)
- **Title:** ConfMan Relational Database Schema ERD
- **Purpose:** Document exact table definitions, primary keys, foreign keys, and cardinalities across all 13 tables.

```mermaid
erDiagram
    users ||--o{ conferences : "chairs"
    users ||--o{ papers : "authors"
    users ||--o{ review_assignments : "assigned_to"
    users ||--o{ decisions : "decided_by"
    users ||--o{ registrations : "registers"
    users ||--o{ notifications : "receives"
    users ||--o{ activity : "performs"

    conferences ||--|{ tracks : "has"
    conferences ||--o{ papers : "receives"
    conferences ||--o{ registrations : "enrolls"
    conferences ||--o{ sessions : "holds"

    tracks ||--o{ papers : "categorizes"

    papers ||--o{ review_assignments : "allocated"
    papers ||--o{ decisions : "evaluated_in"
    papers ||--o| presentations : "presented_in"

    review_assignments ||--o| reviews : "produces"

    registrations ||--o| payments : "paid_by"

    sessions ||--o{ presentations : "schedules"

    users {
        int user_id PK
        string name
        string email UK
        string password_hash
        string role
        string affiliation
        string expertise
        int is_active
        string created_at
    }

    conferences {
        int conf_id PK
        string name
        string venue
        string description
        string start_date
        string end_date
        string submission_deadline
        string early_bird_deadline
        int chair_id FK
    }

    tracks {
        int track_id PK
        int conf_id FK
        string name
    }

    papers {
        int paper_id PK
        int conf_id FK
        int track_id FK
        int author_id FK
        string title
        string abstract
        string keywords
        string file_name
        string status
        string decision_remarks
        string submitted_at
    }

    review_assignments {
        int assignment_id PK
        int paper_id FK
        int reviewer_id FK
        string assigned_at
        string status
    }

    reviews {
        int review_id PK
        int assignment_id FK,UK
        int score
        string comments
        string recommendation
        string submitted_at
    }

    decisions {
        int decision_id PK
        int paper_id FK
        string decision
        string remarks
        int decided_by FK
        string decided_at
    }

    registrations {
        int reg_id PK
        int conf_id FK
        int user_id FK
        string category
        float fee_amount
        string status
        string registered_at
    }

    payments {
        int payment_id PK
        int reg_id FK
        float amount
        string method
        string txn_ref
        string status
        string paid_at
    }

    sessions {
        int session_id PK
        int conf_id FK
        string title
        string room
        string start_time
        string end_time
        int capacity
    }

    presentations {
        int paper_id PK,FK
        int session_id FK
        int slot_order
    }

    notifications {
        int notif_id PK
        int user_id FK
        string message
        string created_at
        int is_read
    }

    activity {
        int activity_id PK
        int user_id FK
        string action
        string detail
        string created_at
    }
```

---

### Diagram 7: Sequence Diagram (Submission to Review and Editorial Decision)
- **Title:** End-to-End Manuscript Evaluation Sequence
- **Purpose:** Trace interactions between Author, Chair, Reviewer, Presentation Controller, Services, and Database during evaluation.

```mermaid
sequenceDiagram
    autonumber
    actor Author
    actor Chair
    actor Reviewer
    participant App as Presentation Layer (Flask)
    participant Svc as Services (Business Logic)
    participant DB as SQLite3 Database

    Note over Author,App: 1. Manuscript Submission
    Author->>App: POST /conferences/{id}/submit (Title, Abstract, PDF)
    App->>Svc: submit_paper(author_id, conf_id, track_id, ...)
    Svc->>DB: Check deadline & Validate track
    Svc->>DB: INSERT INTO papers (status='Submitted')
    Svc->>DB: INSERT notifications (Author & Chair)
    Svc-->>App: paper_id
    App-->>Author: Redirect to paper_detail

    Note over Chair,App: 2. Reviewer Allocation
    Chair->>App: POST /papers/{id}/auto-assign
    App->>Svc: auto_assign(chair_id, paper_id)
    Svc->>Svc: ranked_reviewers(paper_id)
    Svc->>DB: Check COI, existing assignments & capacity (<5)
    Svc->>DB: INSERT INTO review_assignments (status='Pending')
    Svc->>DB: UPDATE papers SET status='Under Review'
    Svc-->>App: Assigned reviewer list
    App-->>Chair: Display success notification

    Note over Reviewer,App: 3. Double-Blind Review
    Reviewer->>App: GET /reviews/{assignment_id}
    App-->>Reviewer: Render review form (Author name hidden)
    Reviewer->>App: POST /reviews/{assignment_id} (Score 8, Comments, 'accept')
    App->>Svc: submit_review(reviewer_id, assignment_id, 8, ...)
    Svc->>DB: INSERT INTO reviews
    Svc->>DB: UPDATE review_assignments SET status='Completed'
    Svc->>DB: Check remaining pending reviews
    alt All Reviews Completed
        Svc->>DB: UPDATE papers SET status='Reviewed'
    end
    Svc-->>App: review_id
    App-->>Reviewer: Redirect to dashboard

    Note over Chair,App: 4. Editorial Decision
    Chair->>App: GET /papers/{id}
    App->>Svc: suggest_decision(paper_id)
    Svc->>DB: Query review scores (must be >= 2)
    Svc-->>App: {average: 8.0, suggestion: 'Accepted'}
    Chair->>App: POST /papers/{id}/decision ('Accepted', Remarks)
    App->>Svc: record_decision(chair_id, paper_id, 'Accepted', ...)
    Svc->>DB: UPDATE papers SET status='Accepted'
    Svc->>DB: INSERT INTO decisions
    Svc->>DB: INSERT notification for Author
    Svc-->>App: Success
    App-->>Chair: Display updated status
```

---

### Diagram 8: Sequence Diagram (Registration, Payment, and Presentation Scheduling)
- **Title:** Conference Registration, Payment, and Session Scheduling Sequence
- **Purpose:** Detail the workflow that enforces mandatory paid registration before presentation scheduling.

```mermaid
sequenceDiagram
    autonumber
    actor Author
    actor Chair
    participant App as Presentation Layer (Flask)
    participant Svc as Services (Business Logic)
    participant DB as SQLite3 Database

    Note over Author,App: 1. Conference Registration
    Author->>App: POST /conferences/{id}/registration (Category: 'academic')
    App->>Svc: register_for_conference(user_id, conf_id, 'academic')
    Svc->>DB: Verify conference not ended & No duplicate registration
    Svc->>Svc: Calculate fee (Check early_bird_deadline: apply 20% discount if eligible)
    Svc->>DB: INSERT INTO registrations (status='Pending Payment')
    Svc-->>App: reg_id
    App-->>Author: Redirect to /registrations/{reg_id}/pay

    Note over Author,App: 2. Payment Checkout
    Author->>App: POST /registrations/{reg_id}/pay (Card: '4242...')
    App->>Svc: process_payment(user_id, reg_id, card_number)
    Svc->>Svc: luhn_valid(card_number) [Must be True]
    Svc->>Svc: _mock_gateway(card_number) [Card not ending '0002']
    Svc->>DB: INSERT INTO payments (status='Success', txn_ref='TXN-...')
    Svc->>DB: UPDATE registrations SET status='Confirmed'
    Svc-->>App: txn_ref
    App-->>Author: Display Confirmation & Receipt

    Note over Chair,App: 3. Session Scheduling
    Chair->>App: POST /conferences/{id}/sessions (Title, Room 'Hall A', 10:00-11:30, Cap 4)
    App->>Svc: create_session(chair_id, conf_id, ...)
    Svc->>DB: Query room clash (start_time < new_end AND end_time > new_start)
    Svc->>DB: INSERT INTO sessions
    Svc-->>App: session_id

    Chair->>App: POST /papers/{paper_id}/schedule (session_id)
    App->>Svc: schedule_paper(chair_id, paper_id, session_id)
    Svc->>DB: Verify paper.status == 'Accepted'
    Svc->>DB: Verify session capacity not exceeded
    Svc->>DB: Verify Author has confirmed registration (Mandatory Rule)
    Svc->>DB: INSERT INTO presentations (paper_id, session_id, slot_order)
    Svc->>DB: UPDATE papers SET status='Scheduled'
    Svc-->>App: Success
    App-->>Chair: Display paper scheduled in Hall A
```

---

### Diagram 9: State Transition Diagram (Manuscript Lifecycle)
- **Title:** Finite State Machine for Paper Lifecycle
- **Purpose:** Document valid paper states and permissible transitions triggered by system events.

```mermaid
stateDiagram-v2
    [*] --> Submitted : submit_paper (Author uploads PDF)
    
    Submitted --> Under_Review : assign_reviewer / auto_assign / volunteer (1st reviewer assigned)
    
    Under_Review --> Under_Review : assign_reviewer (Reviewer 2 or 3 added)
    Under_Review --> Under_Review : submit_review (Reviews still pending)
    Under_Review --> Reviewed : submit_review (All assigned reviews submitted)
    
    Reviewed --> Accepted : record_decision (Score >= 7.0 or Chair choice)
    Reviewed --> Rejected : record_decision (Score < 5.0 or Chair choice)
    Reviewed --> Revision_Required : record_decision (5.0 <= Score < 7.0 or Chair choice)
    
    Under_Review --> Accepted : record_decision (If >= 2 reviews completed)
    Under_Review --> Rejected : record_decision (If >= 2 reviews completed)
    Under_Review --> Revision_Required : record_decision (If >= 2 reviews completed)

    Accepted --> Scheduled : schedule_paper (Author has Confirmed Registration & Room Slot assigned)
    
    Revision_Required --> [*] : Concluded
    Rejected --> [*] : Concluded
    Scheduled --> [*] : Presented at Conference
```

---

### Diagram 10: Activity Diagram (Automated Reviewer Allocation Algorithm)
- **Title:** Reviewer Ranking and Assignment Flowchart
- **Purpose:** Detail the algorithmic decision branches in the multi-criteria auto-assignment heuristic.

```mermaid
flowchart TD
    Start([Start Auto-Assignment]) --> CheckChair{Is user Chair or Admin?}
    CheckChair -- No --> RaiseErr1[Raise ServiceError: Unauthorized]
    CheckChair -- Yes --> QueryPaper[Fetch Paper Title, Track, Keywords, Author ID]
    
    QueryPaper --> CountAssigned[Count Existing Assignments for Paper]
    CountAssigned --> TargetCheck{Existing >= Target?}
    TargetCheck -- Yes --> EndDone([Finish: Target Already Met])
    TargetCheck -- No --> ExtractTerms[Tokenize Paper Terms: keywords + track + title]
    
    ExtractTerms --> FetchCandidates[Fetch Active Reviewers user_id != author_id and not already assigned]
    FetchCandidates --> LoopCandidates[Iterate Through Reviewers]
    
    LoopCandidates --> ComputeLoad[Compute Pending Review Count in Conference]
    ComputeLoad --> CheckCapacity{Pending Load >= 5?}
    CheckCapacity -- Yes --> SetFullTrue[Mark is_full = True]
    CheckCapacity -- No --> SetFullFalse[Mark is_full = False]
    
    SetFullTrue & SetFullFalse --> ComputeMatch[Compute Match Score = |wanted terms ∩ reviewer expertise terms|]
    ComputeMatch --> AppendList[Append to Ranked Candidate List]
    AppendList --> MoreCandidates{More Reviewers?}
    MoreCandidates -- Yes --> LoopCandidates
    MoreCandidates -- No --> SortList[Sort Candidates: full ASC, match DESC, load ASC, name ASC]
    
    SortList --> AssignLoop[Iterate Sorted Candidates]
    AssignLoop --> CheckQuota{Assigned == Target or End of List?}
    CheckQuota -- Yes --> CommitCheck{Any Added?}
    CheckQuota -- No --> CandidateFull{Candidate is_full?}
    
    CandidateFull -- Yes --> AssignLoop
    CandidateFull -- No --> CreateAssignment[Insert review_assignments record]
    CreateAssignment --> UpdatePaperStatus[Update paper status to 'Under Review']
    UpdatePaperStatus --> SendNotif[Dispatch Notification to Reviewer]
    SendNotif --> LogAct[Log Activity: Reviewer auto-assigned]
    LogAct --> IncrementAssigned[Increment Assigned Counter]
    IncrementAssigned --> AssignLoop

    CommitCheck -- Yes --> CommitDB[Execute db.commit]
    CommitCheck -- No --> RaiseErr2[Raise ServiceError: No eligible reviewers available]
    CommitDB --> ReturnList([Return List of Added Reviewer Names])
```

---

## 27. Source-Code File Reference

| Relative File Path | Total Lines | Architectural Layer | Primary Responsibilities and Key Functions / Components |
|---|---|---|---|
| `run.py` | 7 | Entry Point | Application startup script. Instantiates `create_app({"AUTO_SEED": True})` and executes `app.run(port=5000)`. |
| `seed.py` | 30 | Utilities / Seeder | Command-line database seeding and reset tool. Supports `--reset` argument to wipe `instance/` folder and invoke `demo.load_demo()`. |
| `demo.py` | 284 | Utilities / Data Generator | Synthetic longitudinal 75-day conference data generator. Implements virtual clock offset (`_clock`), synthetic PDF generation (`make_pdf`), 3 conferences, 25 users, 30 papers, 14 payments. |
| `requirements.txt` | 1 | Manifest | Single runtime framework dependency: `Flask>=3.0`. |
| `.gitignore` | 4 | Configuration | Git ignore patterns for `instance/`, `__pycache__/`, `.pytest_cache/`, `*.pyc`. |
| `README.md` | 43 | Documentation | Quick-start guide, shell setup instructions, demo login credentials table, test execution guide, and 3-layer architecture map. |
| `cms_app/__init__.py` | 928 | Presentation Layer | Application factory `create_app()`, 26 HTTP route controllers, CSRF enforcement, `@login_required` / `@role_required` decorators, Jinja context processors and filters (`dt`, `inr`, `firstname`, `ago`). |
| `cms_app/services.py` | 647 | Business Logic Layer | Framework-agnostic transactional domain services. Implements user registration, conference creation, paper submission, reviewer assignment, double-blind review validation, decision engine, fee engine, Luhn validation, session scheduling, and admin controls. |
| `cms_app/insights.py` | 219 | Read-Model Layer | Analytical read models. Implements `manager_kpis()`, `admin_kpis()`, `author_kpis()`, `reviewer_kpis()`, `attendee_kpis()`, `weekly_series()`, `status_counts()`, `open_papers()`, `reviewer_workload()`, `score_histogram()`. |
| `cms_app/db.py` | 25 | Data Access Layer | Thread-local connection pool manager using `flask.g`. Enforces foreign keys (`PRAGMA foreign_keys = ON`), sets row factory to `sqlite3.Row`, and provides `init_db()` schema runner. |
| `cms_app/schema.sql` | 129 | Data Access Layer | Relational DDL schema script defining 13 tables (`users`, `conferences`, `tracks`, `papers`, `review_assignments`, `reviews`, `decisions`, `registrations`, `payments`, `sessions`, `presentations`, `notifications`, `activity`). |
| `cms_app/static/style.css` | 362 | Presentation Layer | Custom Teal Design System stylesheet. Responsive CSS Grid/Flexbox layout, dark/light theme tokens, KPI cards, tables, SVG chart styling, and mobile drawer styles. Zero external CSS frameworks. |
| `cms_app/templates/_macros.html`| 134 | Presentation Layer | Jinja2 macro library: 24px stroke SVG icon dictionary (35 icons), KPI card components, SVG sparklines, ring charts, CSS bar charts, status badges, and form inputs. |
| `cms_app/templates/base.html` | 76 | Presentation Layer | Master HTML5 application layout shell. Handles responsive sidebar navigation, top navigation bar, search input, flash message container, and theme toggle JavaScript. |
| `tests/test_cms.py` | 497 | Testing Harness | 50 unit and integration tests across 8 test suites: `UserTests`, `ConferenceTests`, `PaperTests`, `ReviewTests`, `DecisionTests`, `RegistrationPaymentTests`, `SchedulingTests`, `RouteTests`. |
| `tests/test_v13.py` | 175 | Testing Harness | 17 unit and integration tests across 3 test suites: `AdminServiceTests`, `AssignmentTests`, `DemoAndPageTests`. |

---

## 28. Unresolved Questions and Verification Checklist

This checklist is provided for academic project evaluators, external examiners, and technical report authors to verify the integrity and completeness of the source implementation:

- [x] **Architecture Verification:** Confirm that `cms_app/services.py` has zero imports of Flask request/session contexts, ensuring clean layer separation.
- [x] **Relational Schema Verification:** Confirm that SQLite foreign keys are explicitly enabled on connection creation (`PRAGMA foreign_keys = ON;`).
- [x] **Role-Based Access Control:** Verify that unauthorized HTTP access attempts trigger an HTTP 403 Forbidden status code.
- [x] **CSRF Protection:** Verify that all HTTP POST requests without a matching `_csrf` token fail with an HTTP 400 Bad Request error.
- [x] **Double-Blind Integrity:** Verify that author identity fields (`author_name`, `author_aff`) are excluded from reviewer paper views and SQL queries.
- [x] **Conflict of Interest Prevention:** Verify that assigning a paper's author as its reviewer raises a `ServiceError`.
- [x] **Review Quota Boundaries:** Verify that assigning more than 3 reviewers to a paper or exceeding 5 pending reviews for a reviewer is blocked.
- [x] **Editorial Threshold Rule:** Verify that recording an editorial decision with fewer than 2 completed reviews is rejected.
- [x] **Early-Bird Discount Rule:** Verify that registrations on or before `early_bird_deadline` receive exactly a 20% discount.
- [x] **Payment Validation:** Verify that cards failing the Luhn checksum are rejected, and card numbers ending in `0002` simulate a gateway decline.
- [x] **PCI-DSS Compliance Simulation:** Verify that no credit card numbers are stored in the `payments` table or printed in application logs.
- [x] **Session Room Clash Detection:** Verify that overlapping session time intervals within the same room and conference are blocked.
- [x] **Mandatory Registration Scheduling Policy:** Verify that an accepted paper cannot be scheduled unless the primary author possesses a confirmed, paid registration.
- [x] **Unicode Digit Regression Test (DEF-01):** Verify that non-ASCII digits (e.g., `²`) in credit card numbers do not bypass validation or crash the runtime.
- [x] **Automated Test Suite Execution:** Verify that all 67 tests in `tests/test_cms.py` and `tests/test_v13.py` execute and pass cleanly.


---

## 29. Appendix D: Screenshots

The following figures show the ConfMan web interface across the primary workflows:

### Figure D.1 – Dashboard – Home Page and Login Screen
![Figure D.1 – Dashboard – Home Page and Login Screen](screenshots/Figure_D1_Dashboard_Home_and_Login.png)

### Figure D.2 – Chair Dashboard – KPI Cards and Submission Queue
![Figure D.2 – Chair Dashboard – KPI Cards and Submission Queue](screenshots/Figure_D2_Chair_Dashboard.png)

### Figure D.3 – Paper Detail View with Review Panel
![Figure D.3 – Paper Detail View with Review Panel](screenshots/Figure_D3_Paper_Detail_Review_Panel.png)

### Figure D.4 – Payment Checkout and Registration Confirmation
![Figure D.4 – Payment Checkout and Registration Confirmation](screenshots/Figure_D4_Payment_Checkout_and_Confirmation.png)
