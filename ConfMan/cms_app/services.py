"""Business logic layer for the Conference Management System.

Every function takes an open sqlite3 connection (`db`) so the rules can be
unit-tested without starting Flask. Rule violations raise ServiceError.
"""
import re
import uuid
from datetime import date, datetime

from werkzeug.security import check_password_hash, generate_password_hash


class ServiceError(Exception):
    """Raised when a business rule or validation rule is violated."""


ROLES = ("admin", "chair", "reviewer", "author", "attendee")
SELF_REGISTER_ROLES = ("author", "reviewer", "attendee")
MAX_REVIEWERS_PER_PAPER = 3
MAX_PENDING_REVIEWS_PER_REVIEWER = 5
MIN_REVIEWS_FOR_DECISION = 2
FEES = {"student": 500.0, "academic": 1000.0, "industry": 2000.0}
EARLY_BIRD_DISCOUNT = 0.20
RECOMMENDATIONS = ("accept", "minor revision", "major revision", "reject")
DECISIONS = ("Accepted", "Rejected", "Revision Required")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# ----------------------------------------------------------------- helpers
_clock = None  # demo seeding replaces this so history looks realistic


def set_clock(fn):
    global _clock
    _clock = fn


def _now():
    return (_clock() if _clock else datetime.now()).isoformat(timespec="seconds")


def log_activity(db, user_id, action, detail=""):
    db.execute("INSERT INTO activity(user_id, action, detail, created_at) VALUES (?,?,?,?)",
               (user_id, action, detail, _now()))


def _today(today):
    return today or _now()[:10]


def _parse_date(value, label):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ServiceError(f"{label} must be a valid date (YYYY-MM-DD).")


def _parse_dt(value, label):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ServiceError(f"{label} must be a valid date and time.")


def _user(db, user_id):
    row = db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        raise ServiceError("User not found.")
    return row


def _conference(db, conf_id):
    row = db.execute("SELECT * FROM conferences WHERE conf_id = ?", (conf_id,)).fetchone()
    if row is None:
        raise ServiceError("Conference not found.")
    return row


def _paper(db, paper_id):
    row = db.execute("SELECT * FROM papers WHERE paper_id = ?", (paper_id,)).fetchone()
    if row is None:
        raise ServiceError("Paper not found.")
    return row


def _require_chair(db, conf, user_id):
    user = _user(db, user_id)
    if user["role"] == "admin" or conf["chair_id"] == user_id:
        return user
    raise ServiceError("Only the conference chair can perform this action.")


def notify(db, user_id, message):
    db.execute(
        "INSERT INTO notifications(user_id, message, created_at) VALUES (?,?,?)",
        (user_id, message, _now()),
    )


# ------------------------------------------------------------------- users
def register_user(db, name, email, password, role, affiliation="", expertise=""):
    name = (name or "").strip()
    email = (email or "").strip().lower()
    password = password or ""
    if not name:
        raise ServiceError("Name is required.")
    if not EMAIL_RE.match(email):
        raise ServiceError("Enter a valid email address.")
    if len(password) < 8 or not re.search(r"\d", password):
        raise ServiceError("Password must be at least 8 characters and contain a digit.")
    if role not in ROLES:
        raise ServiceError("Invalid role.")
    if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
        raise ServiceError("An account with this email already exists.")
    cur = db.execute(
        "INSERT INTO users(name, email, password_hash, role, affiliation, expertise, created_at)"
        " VALUES (?,?,?,?,?,?,?)",
        (name, email, generate_password_hash(password), role, (affiliation or "").strip(),
         (expertise or "").strip(), _now()),
    )
    log_activity(db, cur.lastrowid, "Account created", f"{name} joined as {role}")
    db.commit()
    return cur.lastrowid


def authenticate(db, email, password):
    row = db.execute(
        "SELECT * FROM users WHERE email = ?", ((email or "").strip().lower(),)
    ).fetchone()
    if row and check_password_hash(row["password_hash"], password or ""):
        if not row["is_active"]:
            raise ServiceError("This account has been deactivated. Contact an administrator.")
        return row
    return None


# ------------------------------------------------------ conferences/tracks
def create_conference(db, user_id, name, venue, start_date, end_date,
                      submission_deadline, early_bird_deadline, description="", chair_id=None):
    user = _user(db, user_id)
    if user["role"] not in ("chair", "admin"):
        raise ServiceError("Only a chair or admin can create a conference.")
    if not (name or "").strip() or not (venue or "").strip():
        raise ServiceError("Conference name and venue are required.")
    start = _parse_date(start_date, "Start date")
    end = _parse_date(end_date, "End date")
    deadline = _parse_date(submission_deadline, "Submission deadline")
    early = _parse_date(early_bird_deadline, "Early-bird deadline")
    if end < start:
        raise ServiceError("End date cannot be before the start date.")
    if deadline >= start:
        raise ServiceError("Submission deadline must be before the conference starts.")
    if early > start:
        raise ServiceError("Early-bird deadline cannot be after the conference starts.")
    owner = user_id
    if chair_id and user["role"] == "admin":
        if _user(db, chair_id)["role"] not in ("chair", "admin"):
            raise ServiceError("The selected chair must have the Chair role.")
        owner = chair_id
    cur = db.execute(
        "INSERT INTO conferences(name, venue, description, start_date, end_date, submission_deadline,"
        " early_bird_deadline, chair_id) VALUES (?,?,?,?,?,?,?,?)",
        (name.strip(), venue.strip(), (description or "").strip(), start_date, end_date,
         submission_deadline, early_bird_deadline, owner),
    )
    log_activity(db, user_id, "Conference created", name.strip())
    db.commit()
    return cur.lastrowid


def add_track(db, user_id, conf_id, name):
    conf = _conference(db, conf_id)
    _require_chair(db, conf, user_id)
    name = (name or "").strip()
    if not name:
        raise ServiceError("Track name is required.")
    if db.execute("SELECT 1 FROM tracks WHERE conf_id=? AND name=?", (conf_id, name)).fetchone():
        raise ServiceError("This track already exists.")
    cur = db.execute("INSERT INTO tracks(conf_id, name) VALUES (?,?)", (conf_id, name))
    db.commit()
    return cur.lastrowid


# ------------------------------------------------------------------ papers
def submit_paper(db, author_id, conf_id, track_id, title, abstract, keywords,
                 file_name, today=None):
    author = _user(db, author_id)
    if author["role"] != "author":
        raise ServiceError("Only users with the Author role can submit papers.")
    conf = _conference(db, conf_id)
    if _parse_date(_today(today), "Today") > _parse_date(conf["submission_deadline"], "Deadline"):
        raise ServiceError("The submission deadline has passed.")
    track = db.execute(
        "SELECT * FROM tracks WHERE track_id=? AND conf_id=?", (track_id, conf_id)
    ).fetchone()
    if track is None:
        raise ServiceError("Select a valid track for this conference.")
    title = (title or "").strip()
    abstract = (abstract or "").strip()
    if not title or len(title) > 200:
        raise ServiceError("Title is required and must be at most 200 characters.")
    if len(abstract) < 50:
        raise ServiceError("Abstract must be at least 50 characters.")
    if not (file_name or "").lower().endswith(".pdf"):
        raise ServiceError("Only PDF files are accepted.")
    cur = db.execute(
        "INSERT INTO papers(conf_id, track_id, author_id, title, abstract, keywords,"
        " file_name, status, submitted_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (conf_id, track_id, author_id, title, abstract, (keywords or "").strip(),
         file_name, "Submitted", _now()),
    )
    notify(db, author_id, f"Your paper '{title}' was submitted successfully.")
    notify(db, conf["chair_id"], f"New paper submitted: '{title}'. Assign reviewers.")
    log_activity(db, author_id, "Paper submitted", f"'{title}' to {conf['name']}")
    db.commit()
    return cur.lastrowid


# ----------------------------------------------------------------- reviews
def _check_assignable(db, paper, reviewer):
    """Shared rules for chair assignment, volunteering and auto-assign."""
    reviewer_id = reviewer["user_id"]
    if reviewer["role"] != "reviewer":
        raise ServiceError("The selected user is not a reviewer.")
    if not reviewer["is_active"]:
        raise ServiceError("This reviewer account is deactivated.")
    if reviewer_id == paper["author_id"]:
        raise ServiceError("Conflict of interest: a reviewer cannot review their own paper.")
    if paper["status"] not in ("Submitted", "Under Review", "Reviewed"):
        raise ServiceError("Reviewers can only be assigned while the paper is awaiting a decision.")
    if db.execute("SELECT 1 FROM review_assignments WHERE paper_id=? AND reviewer_id=?",
                  (paper["paper_id"], reviewer_id)).fetchone():
        raise ServiceError("This reviewer is already assigned to the paper.")
    count = db.execute("SELECT COUNT(*) FROM review_assignments WHERE paper_id=?",
                       (paper["paper_id"],)).fetchone()[0]
    if count >= MAX_REVIEWERS_PER_PAPER:
        raise ServiceError(f"A paper can have at most {MAX_REVIEWERS_PER_PAPER} reviewers.")
    if pending_reviews(db, reviewer_id, paper["conf_id"]) >= MAX_PENDING_REVIEWS_PER_REVIEWER:
        raise ServiceError("This reviewer already has the maximum number of pending reviews.")


def pending_reviews(db, reviewer_id, conf_id=None):
    sql = ("SELECT COUNT(*) FROM review_assignments ra JOIN papers p ON p.paper_id = ra.paper_id"
           " WHERE ra.reviewer_id=? AND ra.status='Pending'")
    args = [reviewer_id]
    if conf_id is not None:
        sql += " AND p.conf_id=?"
        args.append(conf_id)
    return db.execute(sql, args).fetchone()[0]


def _insert_assignment(db, paper, reviewer, by_id, how):
    cur = db.execute(
        "INSERT INTO review_assignments(paper_id, reviewer_id, assigned_at) VALUES (?,?,?)",
        (paper["paper_id"], reviewer["user_id"], _now()),
    )
    db.execute("UPDATE papers SET status='Under Review' WHERE paper_id=? AND status IN ('Submitted','Reviewed')",
               (paper["paper_id"],))
    notify(db, reviewer["user_id"], f"You have been assigned to review '{paper['title']}'.")
    log_activity(db, by_id, f"Reviewer {how}", f"{reviewer['name']} on '{paper['title']}'")
    return cur.lastrowid


def assign_reviewer(db, chair_id, paper_id, reviewer_id):
    paper = _paper(db, paper_id)
    conf = _conference(db, paper["conf_id"])
    _require_chair(db, conf, chair_id)
    reviewer = _user(db, reviewer_id)
    _check_assignable(db, paper, reviewer)
    aid = _insert_assignment(db, paper, reviewer, chair_id, "assigned")
    db.commit()
    return aid


def volunteer_to_review(db, reviewer_id, paper_id):
    """A reviewer picks up a paper that still needs reviewers (self-assignment)."""
    reviewer = _user(db, reviewer_id)
    paper = _paper(db, paper_id)
    _check_assignable(db, paper, reviewer)
    aid = _insert_assignment(db, paper, reviewer, reviewer_id, "volunteered")
    conf = _conference(db, paper["conf_id"])
    notify(db, conf["chair_id"], f"{reviewer['name']} volunteered to review '{paper['title']}'.")
    db.commit()
    return aid


def _terms(text):
    return {w for w in re.split(r"[^a-z0-9+#]+", (text or "").lower()) if len(w) > 2}


def ranked_reviewers(db, paper_id):
    """Eligible reviewers for a paper, best match first (expertise overlap, then lowest load)."""
    paper = _paper(db, paper_id)
    track = db.execute("SELECT name FROM tracks WHERE track_id=?", (paper["track_id"],)).fetchone()
    wanted = _terms(f"{paper['keywords']} {track['name']} {paper['title']}")
    rows = db.execute(
        "SELECT * FROM users WHERE role='reviewer' AND is_active=1 AND user_id != ?"
        " AND user_id NOT IN (SELECT reviewer_id FROM review_assignments WHERE paper_id=?)",
        (paper["author_id"], paper_id)).fetchall()
    ranked = []
    for r in rows:
        load = pending_reviews(db, r["user_id"], paper["conf_id"])
        match = len(wanted & _terms(r["expertise"]))
        ranked.append({"user": r, "match": match, "load": load,
                       "full": load >= MAX_PENDING_REVIEWS_PER_REVIEWER})
    ranked.sort(key=lambda x: (x["full"], -x["match"], x["load"], x["user"]["name"]))
    return ranked


def auto_assign(db, chair_id, paper_id, target=MAX_REVIEWERS_PER_PAPER):
    """Fill the paper up to `target` reviewers using expertise match and lowest workload."""
    paper = _paper(db, paper_id)
    conf = _conference(db, paper["conf_id"])
    _require_chair(db, conf, chair_id)
    have = db.execute("SELECT COUNT(*) FROM review_assignments WHERE paper_id=?",
                      (paper_id,)).fetchone()[0]
    added = []
    for cand in ranked_reviewers(db, paper_id):
        if have + len(added) >= min(target, MAX_REVIEWERS_PER_PAPER):
            break
        if cand["full"]:
            continue
        _insert_assignment(db, paper, cand["user"], chair_id, "auto-assigned")
        paper = _paper(db, paper_id)
        added.append(cand["user"]["name"])
    if not added:
        raise ServiceError("No eligible reviewers are available for this paper.")
    db.commit()
    return added


def auto_assign_conference(db, chair_id, conf_id):
    """Auto-assign every paper that still has fewer than the minimum reviewers."""
    conf = _conference(db, conf_id)
    _require_chair(db, conf, chair_id)
    papers = db.execute(
        "SELECT p.paper_id FROM papers p WHERE p.conf_id=? AND p.status IN ('Submitted','Under Review')"
        " AND (SELECT COUNT(*) FROM review_assignments ra WHERE ra.paper_id=p.paper_id) < ?",
        (conf_id, MIN_REVIEWS_FOR_DECISION)).fetchall()
    done = 0
    for row in papers:
        try:
            auto_assign(db, chair_id, row["paper_id"])
            done += 1
        except ServiceError:
            pass
    return done


def submit_review(db, reviewer_id, assignment_id, score, comments, recommendation):
    asg = db.execute("SELECT * FROM review_assignments WHERE assignment_id=?",
                     (assignment_id,)).fetchone()
    if asg is None or asg["reviewer_id"] != reviewer_id:
        raise ServiceError("This review assignment does not belong to you.")
    if asg["status"] == "Completed":
        raise ServiceError("You have already submitted this review.")
    try:
        score = int(score)
    except (TypeError, ValueError):
        raise ServiceError("Score must be a whole number between 1 and 10.")
    if not 1 <= score <= 10:
        raise ServiceError("Score must be a whole number between 1 and 10.")
    comments = (comments or "").strip()
    if len(comments) < 20:
        raise ServiceError("Comments must be at least 20 characters.")
    if recommendation not in RECOMMENDATIONS:
        raise ServiceError("Select a valid recommendation.")
    paper = _paper(db, asg["paper_id"])
    conf = _conference(db, paper["conf_id"])
    cur = db.execute(
        "INSERT INTO reviews(assignment_id, score, comments, recommendation, submitted_at)"
        " VALUES (?,?,?,?,?)",
        (assignment_id, score, comments, recommendation, _now()),
    )
    db.execute("UPDATE review_assignments SET status='Completed' WHERE assignment_id=?",
               (assignment_id,))
    still_pending = db.execute(
        "SELECT COUNT(*) FROM review_assignments WHERE paper_id=? AND status='Pending'",
        (paper["paper_id"],),
    ).fetchone()[0]
    if still_pending == 0:
        db.execute("UPDATE papers SET status='Reviewed' WHERE paper_id=?", (paper["paper_id"],))
    notify(db, conf["chair_id"], f"A review was submitted for '{paper['title']}'.")
    log_activity(db, reviewer_id, "Review submitted", f"'{paper['title']}' scored {score}/10")
    db.commit()
    return cur.lastrowid


def suggest_decision(db, paper_id):
    rows = db.execute(
        "SELECT r.score FROM reviews r JOIN review_assignments ra"
        " ON ra.assignment_id = r.assignment_id WHERE ra.paper_id=?", (paper_id,)
    ).fetchall()
    if len(rows) < MIN_REVIEWS_FOR_DECISION:
        raise ServiceError(f"At least {MIN_REVIEWS_FOR_DECISION} completed reviews are required.")
    average = round(sum(r["score"] for r in rows) / len(rows), 2)
    if average >= 7:
        suggestion = "Accepted"
    elif average >= 5:
        suggestion = "Revision Required"
    else:
        suggestion = "Rejected"
    return {"average": average, "count": len(rows), "suggestion": suggestion}


def record_decision(db, chair_id, paper_id, decision, remarks=""):
    paper = _paper(db, paper_id)
    conf = _conference(db, paper["conf_id"])
    _require_chair(db, conf, chair_id)
    if decision not in DECISIONS:
        raise ServiceError("Select a valid decision.")
    if paper["status"] not in ("Under Review", "Reviewed"):
        raise ServiceError("A decision can only be recorded for a paper that is under review.")
    suggest_decision(db, paper_id)  # raises if too few reviews
    db.execute("UPDATE papers SET status=?, decision_remarks=? WHERE paper_id=?",
               (decision, (remarks or "").strip(), paper_id))
    db.execute(
        "INSERT INTO decisions(paper_id, decision, remarks, decided_by, decided_at)"
        " VALUES (?,?,?,?,?)",
        (paper_id, decision, (remarks or "").strip(), chair_id, _now()),
    )
    notify(db, paper["author_id"], f"Decision for '{paper['title']}': {decision}.")
    log_activity(db, chair_id, f"Paper {decision.lower()}", f"'{paper['title']}'")
    db.commit()


# ------------------------------------------------- registration & payment
def registration_fee(category, early_bird):
    if category not in FEES:
        raise ServiceError("Select a valid registration category.")
    fee = FEES[category]
    if early_bird:
        fee *= 1 - EARLY_BIRD_DISCOUNT
    return round(fee, 2)


def register_for_conference(db, user_id, conf_id, category, today=None):
    _user(db, user_id)
    conf = _conference(db, conf_id)
    now = _parse_date(_today(today), "Today")
    if now > _parse_date(conf["end_date"], "End date"):
        raise ServiceError("Registration is closed because the conference has ended.")
    if db.execute("SELECT 1 FROM registrations WHERE conf_id=? AND user_id=?",
                  (conf_id, user_id)).fetchone():
        raise ServiceError("You are already registered for this conference.")
    early = now <= _parse_date(conf["early_bird_deadline"], "Early-bird deadline")
    fee = registration_fee(category, early)
    cur = db.execute(
        "INSERT INTO registrations(conf_id, user_id, category, fee_amount, registered_at)"
        " VALUES (?,?,?,?,?)",
        (conf_id, user_id, category, fee, _now()),
    )
    db.commit()
    return cur.lastrowid


def luhn_valid(number):
    digits = [int(c) for c in number]
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def _mock_gateway(card_number):
    """Stand-in for the external payment gateway. Cards ending 0002 are declined."""
    if card_number.endswith("0002"):
        return False, "DECLINED"
    return True, "TXN-" + uuid.uuid4().hex[:10].upper()


def process_payment(db, user_id, reg_id, card_number):
    reg = db.execute("SELECT * FROM registrations WHERE reg_id=?", (reg_id,)).fetchone()
    if reg is None or reg["user_id"] != user_id:
        raise ServiceError("Registration not found.")
    if reg["status"] == "Confirmed":
        raise ServiceError("This registration is already paid.")
    card = re.sub(r"[ -]", "", card_number or "")
    if not re.fullmatch(r"[0-9]{13,19}", card) or not luhn_valid(card):
        raise ServiceError("Enter a valid card number.")
    ok, ref = _mock_gateway(card)  # the card number is never stored
    db.execute(
        "INSERT INTO payments(reg_id, amount, method, txn_ref, status, paid_at)"
        " VALUES (?,?,?,?,?,?)",
        (reg_id, reg["fee_amount"], "card", ref, "Success" if ok else "Failed", _now()),
    )
    if not ok:
        db.commit()
        raise ServiceError("Payment was declined by the gateway. Please try another card.")
    db.execute("UPDATE registrations SET status='Confirmed' WHERE reg_id=?", (reg_id,))
    notify(db, user_id, f"Payment received (ref {ref}). Your registration is confirmed.")
    log_activity(db, user_id, "Payment received", f"Rs {reg['fee_amount']:.0f} ({ref})")
    db.commit()
    return ref


# ------------------------------------------------------------- scheduling
def create_session(db, user_id, conf_id, title, room, start_time, end_time, capacity=4):
    conf = _conference(db, conf_id)
    _require_chair(db, conf, user_id)
    if not (title or "").strip() or not (room or "").strip():
        raise ServiceError("Session title and room are required.")
    start = _parse_dt(start_time, "Start time")
    end = _parse_dt(end_time, "End time")
    if end <= start:
        raise ServiceError("End time must be after the start time.")
    if not (_parse_date(conf["start_date"], "Start") <= start.date() <= _parse_date(conf["end_date"], "End")
            and start.date() == end.date()):
        raise ServiceError("A session must fall within the conference dates.")
    try:
        capacity = int(capacity)
    except (TypeError, ValueError):
        raise ServiceError("Capacity must be a number.")
    if capacity < 1:
        raise ServiceError("Capacity must be at least 1.")
    clash = db.execute(
        "SELECT 1 FROM sessions WHERE conf_id=? AND room=? AND start_time < ? AND end_time > ?",
        (conf_id, room.strip(), end.isoformat(timespec="minutes"), start.isoformat(timespec="minutes")),
    ).fetchone()
    if clash:
        raise ServiceError("Another session already uses this room at that time.")
    cur = db.execute(
        "INSERT INTO sessions(conf_id, title, room, start_time, end_time, capacity)"
        " VALUES (?,?,?,?,?,?)",
        (conf_id, title.strip(), room.strip(), start.isoformat(timespec="minutes"),
         end.isoformat(timespec="minutes"), capacity),
    )
    db.commit()
    return cur.lastrowid


def schedule_paper(db, user_id, paper_id, session_id):
    paper = _paper(db, paper_id)
    conf = _conference(db, paper["conf_id"])
    _require_chair(db, conf, user_id)
    sess = db.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
    if sess is None or sess["conf_id"] != paper["conf_id"]:
        raise ServiceError("Select a session of the same conference.")
    if paper["status"] != "Accepted":
        raise ServiceError("Only accepted papers can be scheduled.")
    if db.execute("SELECT 1 FROM presentations WHERE paper_id=?", (paper_id,)).fetchone():
        raise ServiceError("This paper is already scheduled.")
    used = db.execute("SELECT COUNT(*) FROM presentations WHERE session_id=?",
                      (session_id,)).fetchone()[0]
    if used >= sess["capacity"]:
        raise ServiceError("This session is full.")
    registered = db.execute(
        "SELECT 1 FROM registrations WHERE conf_id=? AND user_id=? AND status='Confirmed'",
        (paper["conf_id"], paper["author_id"]),
    ).fetchone()
    if not registered:
        raise ServiceError("The author must complete a paid registration before scheduling.")
    db.execute("INSERT INTO presentations(paper_id, session_id, slot_order) VALUES (?,?,?)",
               (paper_id, session_id, used + 1))
    db.execute("UPDATE papers SET status='Scheduled' WHERE paper_id=?", (paper_id,))
    notify(db, paper["author_id"],
           f"'{paper['title']}' is scheduled in {sess['title']} ({sess['room']}) at {sess['start_time']}.")
    db.commit()


def get_program(db, conf_id):
    sessions = db.execute(
        "SELECT * FROM sessions WHERE conf_id=? ORDER BY start_time, room", (conf_id,)
    ).fetchall()
    program = []
    for s in sessions:
        papers = db.execute(
            "SELECT p.paper_id, p.title, u.name AS author, pr.slot_order FROM presentations pr"
            " JOIN papers p ON p.paper_id = pr.paper_id JOIN users u ON u.user_id = p.author_id"
            " WHERE pr.session_id=? ORDER BY pr.slot_order", (s["session_id"],)
        ).fetchall()
        program.append({"session": s, "papers": papers})
    return program


# ------------------------------------------------------------------- admin
def _require_admin(db, admin_id):
    user = _user(db, admin_id)
    if user["role"] != "admin":
        raise ServiceError("Only an administrator can do this.")
    return user


def admin_create_user(db, admin_id, name, email, password, role, affiliation="", expertise=""):
    _require_admin(db, admin_id)
    uid = register_user(db, name, email, password, role, affiliation, expertise)
    log_activity(db, admin_id, "User created by admin", f"{name} ({role})")
    db.commit()
    return uid


def set_user_role(db, admin_id, user_id, role):
    _require_admin(db, admin_id)
    if role not in ROLES:
        raise ServiceError("Invalid role.")
    target = _user(db, user_id)
    if target["user_id"] == admin_id and role != "admin":
        raise ServiceError("You cannot remove your own admin role.")
    db.execute("UPDATE users SET role=? WHERE user_id=?", (role, user_id))
    log_activity(db, admin_id, "Role changed", f"{target['name']}: {target['role']} to {role}")
    notify(db, user_id, f"Your role was changed to {role}.")
    db.commit()


def set_user_active(db, admin_id, user_id, active):
    _require_admin(db, admin_id)
    target = _user(db, user_id)
    if target["user_id"] == admin_id and not active:
        raise ServiceError("You cannot deactivate your own account.")
    db.execute("UPDATE users SET is_active=? WHERE user_id=?", (1 if active else 0, user_id))
    log_activity(db, admin_id, "Account activated" if active else "Account deactivated", target["name"])
    db.commit()


def reassign_chair(db, admin_id, conf_id, chair_id):
    _require_admin(db, admin_id)
    conf = _conference(db, conf_id)
    new = _user(db, chair_id)
    if new["role"] not in ("chair", "admin"):
        raise ServiceError("The selected user does not have the Chair role.")
    db.execute("UPDATE conferences SET chair_id=? WHERE conf_id=?", (chair_id, conf_id))
    log_activity(db, admin_id, "Chair reassigned", f"{conf['name']} now chaired by {new['name']}")
    notify(db, chair_id, f"You are now the chair of '{conf['name']}'.")
    db.commit()


def update_profile(db, user_id, name, affiliation, expertise):
    name = (name or "").strip()
    if not name:
        raise ServiceError("Name is required.")
    db.execute("UPDATE users SET name=?, affiliation=?, expertise=? WHERE user_id=?",
               (name, (affiliation or "").strip(), (expertise or "").strip(), user_id))
    db.commit()


def change_password(db, user_id, current, new):
    user = _user(db, user_id)
    if not check_password_hash(user["password_hash"], current or ""):
        raise ServiceError("Current password is incorrect.")
    if len(new or "") < 8 or not re.search(r"\d", new):
        raise ServiceError("Password must be at least 8 characters and contain a digit.")
    db.execute("UPDATE users SET password_hash=? WHERE user_id=?", (generate_password_hash(new), user_id))
    db.commit()
