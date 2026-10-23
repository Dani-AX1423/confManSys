PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('admin','chair','reviewer','author','attendee')),
    affiliation   TEXT NOT NULL DEFAULT '',
    expertise     TEXT NOT NULL DEFAULT '',
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conferences (
    conf_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name                TEXT NOT NULL,
    venue               TEXT NOT NULL,
    description         TEXT NOT NULL DEFAULT '',
    start_date          TEXT NOT NULL,
    end_date            TEXT NOT NULL,
    submission_deadline TEXT NOT NULL,
    early_bird_deadline TEXT NOT NULL,
    chair_id            INTEGER NOT NULL REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS tracks (
    track_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conf_id  INTEGER NOT NULL REFERENCES conferences(conf_id) ON DELETE CASCADE,
    name     TEXT NOT NULL,
    UNIQUE (conf_id, name)
);

CREATE TABLE IF NOT EXISTS papers (
    paper_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    conf_id          INTEGER NOT NULL REFERENCES conferences(conf_id),
    track_id         INTEGER NOT NULL REFERENCES tracks(track_id),
    author_id        INTEGER NOT NULL REFERENCES users(user_id),
    title            TEXT NOT NULL,
    abstract         TEXT NOT NULL,
    keywords         TEXT NOT NULL DEFAULT '',
    file_name        TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'Submitted'
        CHECK (status IN ('Submitted','Under Review','Reviewed','Accepted','Rejected','Revision Required','Scheduled')),
    decision_remarks TEXT NOT NULL DEFAULT '',
    submitted_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS review_assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id      INTEGER NOT NULL REFERENCES papers(paper_id),
    reviewer_id   INTEGER NOT NULL REFERENCES users(user_id),
    assigned_at   TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending','Completed')),
    UNIQUE (paper_id, reviewer_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id  INTEGER NOT NULL UNIQUE REFERENCES review_assignments(assignment_id),
    score          INTEGER NOT NULL CHECK (score BETWEEN 1 AND 10),
    comments       TEXT NOT NULL,
    recommendation TEXT NOT NULL
        CHECK (recommendation IN ('accept','minor revision','major revision','reject')),
    submitted_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id    INTEGER NOT NULL REFERENCES papers(paper_id),
    decision    TEXT NOT NULL CHECK (decision IN ('Accepted','Rejected','Revision Required')),
    remarks     TEXT NOT NULL DEFAULT '',
    decided_by  INTEGER NOT NULL REFERENCES users(user_id),
    decided_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS registrations (
    reg_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    conf_id       INTEGER NOT NULL REFERENCES conferences(conf_id),
    user_id       INTEGER NOT NULL REFERENCES users(user_id),
    category      TEXT NOT NULL CHECK (category IN ('student','academic','industry')),
    fee_amount    REAL NOT NULL,
    status        TEXT NOT NULL DEFAULT 'Pending Payment'
        CHECK (status IN ('Pending Payment','Confirmed','Cancelled')),
    registered_at TEXT NOT NULL,
    UNIQUE (conf_id, user_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    reg_id     INTEGER NOT NULL REFERENCES registrations(reg_id),
    amount     REAL NOT NULL,
    method     TEXT NOT NULL DEFAULT 'card',
    txn_ref    TEXT NOT NULL,
    status     TEXT NOT NULL CHECK (status IN ('Success','Failed')),
    paid_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conf_id    INTEGER NOT NULL REFERENCES conferences(conf_id),
    title      TEXT NOT NULL,
    room       TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time   TEXT NOT NULL,
    capacity   INTEGER NOT NULL DEFAULT 4
);

CREATE TABLE IF NOT EXISTS presentations (
    paper_id   INTEGER PRIMARY KEY REFERENCES papers(paper_id),
    session_id INTEGER NOT NULL REFERENCES sessions(session_id),
    slot_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    notif_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(user_id),
    message    TEXT NOT NULL,
    created_at TEXT NOT NULL,
    is_read    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS activity (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(user_id),
    action      TEXT NOT NULL,
    detail      TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);
