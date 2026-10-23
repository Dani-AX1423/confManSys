"""Read-models behind the dashboards and charts (KPIs, series, pipelines).

Pure SQL over the same SQLite connection; no business rules live here.
"""
from datetime import datetime, timedelta

from . import services as svc

STATUSES = ["Submitted", "Under Review", "Reviewed", "Accepted", "Revision Required",
            "Rejected", "Scheduled"]


def _scope(user, db):
    """Conference ids the user manages: all for admin, own for chair."""
    if user["role"] == "admin":
        return [r[0] for r in db.execute("SELECT conf_id FROM conferences")]
    return [r[0] for r in db.execute(
        "SELECT conf_id FROM conferences WHERE chair_id=?", (user["user_id"],))]


def _in(ids):
    return ",".join("?" for _ in ids) or "NULL"


def weekly_series(db, sql, args, weeks=8, today=None):
    """Counts per week for the last N weeks; `sql` must select one timestamp column."""
    end = today or datetime.fromisoformat(svc._now())
    start = (end - timedelta(weeks=weeks - 1)).replace(hour=0, minute=0, second=0)
    start -= timedelta(days=start.weekday())
    buckets = [0] * weeks
    for (stamp,) in db.execute(sql, args):
        d = datetime.fromisoformat(stamp)
        idx = (d - start).days // 7
        if 0 <= idx < weeks:
            buckets[idx] += 1
    labels = [(start + timedelta(weeks=i)).strftime("%d %b") for i in range(weeks)]
    return {"labels": labels, "vals": buckets}


def status_counts(db, ids):
    counts = {s: 0 for s in STATUSES}
    for s, n in db.execute(
            f"SELECT status, COUNT(*) FROM papers WHERE conf_id IN ({_in(ids)}) GROUP BY status", ids):
        counts[s] = n
    return counts


def manager_kpis(db, user):
    """KPIs for chair (own conferences) and admin (all conferences)."""
    ids = _scope(user, db)
    q = _in(ids)
    one = lambda sql, a=ids: db.execute(sql, a).fetchone()[0]
    sc = status_counts(db, ids)
    total = sum(sc.values())
    decided = sc["Accepted"] + sc["Rejected"] + sc["Revision Required"] + sc["Scheduled"]
    accepted = sc["Accepted"] + sc["Scheduled"]
    needs = one(f"SELECT COUNT(*) FROM papers p WHERE p.conf_id IN ({q}) AND p.status IN"
                " ('Submitted','Under Review') AND (SELECT COUNT(*) FROM review_assignments ra"
                " WHERE ra.paper_id=p.paper_id) < ?", ids + [svc.MIN_REVIEWS_FOR_DECISION])
    assigned = one(f"SELECT COUNT(*) FROM review_assignments ra JOIN papers p ON p.paper_id=ra.paper_id"
                   f" WHERE p.conf_id IN ({q})")
    done = one(f"SELECT COUNT(*) FROM review_assignments ra JOIN papers p ON p.paper_id=ra.paper_id"
               f" WHERE p.conf_id IN ({q}) AND ra.status='Completed'")
    avg = db.execute(
        f"SELECT AVG(r.score) FROM reviews r JOIN review_assignments ra ON ra.assignment_id=r.assignment_id"
        f" JOIN papers p ON p.paper_id=ra.paper_id WHERE p.conf_id IN ({q})", ids).fetchone()[0]
    regs = one(f"SELECT COUNT(*) FROM registrations WHERE conf_id IN ({q}) AND status='Confirmed'")
    regs_pending = one(f"SELECT COUNT(*) FROM registrations WHERE conf_id IN ({q}) AND status='Pending Payment'")
    revenue = db.execute(
        f"SELECT COALESCE(SUM(fee_amount),0) FROM registrations WHERE conf_id IN ({q}) AND status='Confirmed'",
        ids).fetchone()[0]
    ready = one(f"SELECT COUNT(*) FROM papers p WHERE p.conf_id IN ({q}) AND p.status IN ('Under Review','Reviewed')"
                " AND (SELECT COUNT(*) FROM reviews r JOIN review_assignments ra ON ra.assignment_id=r.assignment_id"
                " WHERE ra.paper_id=p.paper_id) >= ?", ids + [svc.MIN_REVIEWS_FOR_DECISION])
    sub = weekly_series(db, f"SELECT submitted_at FROM papers WHERE conf_id IN ({q})", ids)
    this_week, last_week = sub["vals"][-1], sub["vals"][-2]
    rev_series = weekly_series(
        db, f"SELECT r.submitted_at FROM reviews r JOIN review_assignments ra ON ra.assignment_id=r.assignment_id"
            f" JOIN papers p ON p.paper_id=ra.paper_id WHERE p.conf_id IN ({q})", ids)
    return {
        "ids": ids, "conferences": len(ids), "status": sc, "total": total, "decided": decided,
        "accepted": accepted, "accept_rate": round(100 * accepted / decided) if decided else 0,
        "needs_reviewers": needs, "ready_for_decision": ready,
        "review_assigned": assigned, "review_done": done,
        "review_pct": round(100 * done / assigned) if assigned else 0,
        "avg_score": round(avg, 1) if avg else 0,
        "regs": regs, "regs_pending": regs_pending, "revenue": revenue,
        "submissions": sub, "reviews_series": rev_series,
        "sub_delta": this_week - last_week, "sub_this_week": this_week,
    }


def track_breakdown(db, ids):
    return db.execute(
        f"SELECT t.name, COUNT(p.paper_id) AS n, SUM(p.status IN ('Accepted','Scheduled')) AS acc"
        f" FROM tracks t LEFT JOIN papers p ON p.track_id=t.track_id WHERE t.conf_id IN ({_in(ids)})"
        f" GROUP BY t.name ORDER BY n DESC", ids).fetchall()


def reviewer_workload(db, ids, limit=8):
    return db.execute(
        f"SELECT u.user_id, u.name, u.expertise,"
        f" SUM(ra.status='Pending') AS pending, SUM(ra.status='Completed') AS done"
        f" FROM users u LEFT JOIN review_assignments ra ON ra.reviewer_id=u.user_id"
        f" WHERE u.role='reviewer' AND u.is_active=1 GROUP BY u.user_id ORDER BY pending DESC, u.name"
        f" LIMIT {int(limit)}").fetchall()


def score_histogram(db, ids):
    bins = [0] * 10
    for (s,) in db.execute(
            f"SELECT r.score FROM reviews r JOIN review_assignments ra ON ra.assignment_id=r.assignment_id"
            f" JOIN papers p ON p.paper_id=ra.paper_id WHERE p.conf_id IN ({_in(ids)})", ids):
        bins[s - 1] += 1
    return bins


def revenue_by_conference(db, ids):
    return db.execute(
        f"SELECT c.conf_id, c.name, COALESCE(SUM(CASE WHEN r.status='Confirmed' THEN r.fee_amount END),0) AS rev,"
        f" SUM(r.status='Confirmed') AS paid, SUM(r.status='Pending Payment') AS pending"
        f" FROM conferences c LEFT JOIN registrations r ON r.conf_id=c.conf_id"
        f" WHERE c.conf_id IN ({_in(ids)}) GROUP BY c.conf_id ORDER BY c.start_date", ids).fetchall()


def admin_kpis(db):
    one = lambda sql: db.execute(sql).fetchone()[0]
    roles = {r: 0 for r in svc.ROLES}
    for role, n in db.execute("SELECT role, COUNT(*) FROM users WHERE is_active=1 GROUP BY role"):
        roles[role] = n
    users = sum(roles.values())
    signups = weekly_series(db, "SELECT created_at FROM users", ())
    return {
        "roles": roles, "users": users, "inactive": one("SELECT COUNT(*) FROM users WHERE is_active=0"),
        "signups": signups,
        "signups_week": signups["vals"][-1],
        "conferences": one("SELECT COUNT(*) FROM conferences"),
        "papers": one("SELECT COUNT(*) FROM papers"),
        "reviews": one("SELECT COUNT(*) FROM reviews"),
        "payments": one("SELECT COUNT(*) FROM payments WHERE status='Success'"),
        "failed_payments": one("SELECT COUNT(*) FROM payments WHERE status='Failed'"),
    }


# ------------------------------------------------------------ per-role KPIs
def author_kpis(db, user):
    uid = user["user_id"]
    rows = db.execute("SELECT status, COUNT(*) FROM papers WHERE author_id=? GROUP BY status", (uid,)).fetchall()
    c = {s: n for s, n in rows}
    total = sum(c.values())
    avg = db.execute(
        "SELECT AVG(r.score) FROM reviews r JOIN review_assignments ra ON ra.assignment_id=r.assignment_id"
        " JOIN papers p ON p.paper_id=ra.paper_id WHERE p.author_id=? AND p.status IN"
        " ('Accepted','Rejected','Revision Required','Scheduled')", (uid,)).fetchone()[0]
    waiting = db.execute(
        "SELECT COUNT(*) FROM papers p WHERE p.author_id=? AND p.status IN ('Submitted','Under Review','Reviewed')",
        (uid,)).fetchone()[0]
    no_rev = db.execute(
        "SELECT COUNT(*) FROM papers p WHERE p.author_id=? AND p.status='Submitted'"
        " AND NOT EXISTS (SELECT 1 FROM review_assignments ra WHERE ra.paper_id=p.paper_id)", (uid,)).fetchone()[0]
    return {"total": total, "counts": c, "waiting": waiting, "waiting_no_reviewer": no_rev,
            "accepted": c.get("Accepted", 0) + c.get("Scheduled", 0),
            "revision": c.get("Revision Required", 0), "rejected": c.get("Rejected", 0),
            "avg_score": round(avg, 1) if avg else None}


def reviewer_kpis(db, user):
    uid = user["user_id"]
    pending = svc.pending_reviews(db, uid)
    done = db.execute("SELECT COUNT(*) FROM review_assignments WHERE reviewer_id=? AND status='Completed'",
                      (uid,)).fetchone()[0]
    avg = db.execute(
        "SELECT AVG(r.score) FROM reviews r JOIN review_assignments ra ON ra.assignment_id=r.assignment_id"
        " WHERE ra.reviewer_id=?", (uid,)).fetchone()[0]
    open_n = len(open_papers(db, user))
    series = weekly_series(
        db, "SELECT r.submitted_at FROM reviews r JOIN review_assignments ra ON ra.assignment_id=r.assignment_id"
            " WHERE ra.reviewer_id=?", (uid,))
    return {"pending": pending, "done": done, "assigned": pending + done,
            "avg_score": round(avg, 1) if avg else None, "open": open_n,
            "capacity": svc.MAX_PENDING_REVIEWS_PER_REVIEWER,
            "slots_left": max(svc.MAX_PENDING_REVIEWS_PER_REVIEWER - pending, 0), "series": series}


def open_papers(db, user, q="", conf_id=None):
    """Papers still short of reviewers that this reviewer may volunteer for."""
    uid = user["user_id"]
    sql = ("SELECT p.*, c.name AS conf_name, t.name AS track_name,"
           " (SELECT COUNT(*) FROM review_assignments ra WHERE ra.paper_id=p.paper_id) AS n_reviewers"
           " FROM papers p JOIN conferences c ON c.conf_id=p.conf_id JOIN tracks t ON t.track_id=p.track_id"
           " WHERE p.status IN ('Submitted','Under Review') AND p.author_id != ?"
           " AND NOT EXISTS (SELECT 1 FROM review_assignments ra WHERE ra.paper_id=p.paper_id AND ra.reviewer_id=?)"
           " AND (SELECT COUNT(*) FROM review_assignments ra WHERE ra.paper_id=p.paper_id) < ?")
    args = [uid, uid, svc.MAX_REVIEWERS_PER_PAPER]
    if q:
        sql += " AND (p.title LIKE ? OR p.keywords LIKE ? OR c.name LIKE ?)"
        args += [f"%{q}%"] * 3
    if conf_id:
        sql += " AND p.conf_id=?"
        args.append(conf_id)
    sql += " ORDER BY n_reviewers ASC, p.submitted_at"
    mine = svc._terms(user["expertise"])
    rows = []
    for r in db.execute(sql, args).fetchall():
        match = len(mine & svc._terms(f"{r['keywords']} {r['track_name']} {r['title']}"))
        rows.append((match, dict(r)))
    rows.sort(key=lambda x: (-x[0], x[1]["n_reviewers"]))
    for match, d in rows:
        d["match"] = match
    return [d for _, d in rows]


def attendee_kpis(db, user):
    uid = user["user_id"]
    regs = db.execute("SELECT status, COUNT(*) FROM registrations WHERE user_id=? GROUP BY status", (uid,)).fetchall()
    c = {s: n for s, n in regs}
    spent = db.execute("SELECT COALESCE(SUM(fee_amount),0) FROM registrations WHERE user_id=? AND status='Confirmed'",
                       (uid,)).fetchone()[0]
    return {"confirmed": c.get("Confirmed", 0), "pending": c.get("Pending Payment", 0), "spent": spent}
