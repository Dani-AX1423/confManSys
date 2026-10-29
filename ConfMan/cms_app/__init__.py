"""Conference Management System - Flask presentation layer (routes)."""
import csv
import functools
import io
import os
import secrets
import uuid
from datetime import date, datetime

from flask import (Flask, Response, abort, flash, g, redirect, render_template, request,
                   send_file, session, url_for)
from werkzeug.utils import secure_filename

from . import db as dbm
from . import insights
from . import services as svc

DECIDED = ("Accepted", "Rejected", "Revision Required", "Scheduled")


def create_app(test_config=None):
    app = Flask(__name__)

    is_vercel = bool(os.environ.get("VERCEL"))
    default_instance = "/tmp/confman_instance" if is_vercel else app.instance_path
    db_path = os.environ.get("CMS_DATABASE", os.path.join(default_instance, "cms.sqlite"))
    upload_folder = os.environ.get("CMS_UPLOAD_FOLDER", os.path.join(default_instance, "uploads"))
    auto_seed_env = os.environ.get("CMS_AUTO_SEED")
    if auto_seed_env is not None:
        auto_seed = auto_seed_env.lower() in ("1", "true", "yes")
    else:
        auto_seed = True if is_vercel else False

    app.config.update(
        SECRET_KEY=os.environ.get("CMS_SECRET", "dev-only-change-me"),
        DATABASE=db_path,
        UPLOAD_FOLDER=upload_folder,
        MAX_CONTENT_LENGTH=10 * 1024 * 1024,
        CSRF_ENABLED=os.environ.get("CMS_CSRF_ENABLED", "true").lower() in ("1", "true", "yes"),
        AUTO_SEED=auto_seed,
    )
    if test_config:
        app.config.update(test_config)

    db_dir = os.path.dirname(app.config["DATABASE"])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    if app.config.get("UPLOAD_FOLDER"):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    app.teardown_appcontext(dbm.close_db)
    with app.app_context():
        dbm.init_db()
        if app.config["AUTO_SEED"]:
            if not dbm.get_db().execute("SELECT 1 FROM users LIMIT 1").fetchone():
                from demo import load_demo
                load_demo(app)

    # ------------------------------------------------------------ security
    @app.before_request
    def load_user_and_check_csrf():
        uid = session.get("user_id")
        g.user = None
        if uid is not None:
            row = dbm.get_db().execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
            if row is not None and row["is_active"]:
                g.user = row
            else:
                session.pop("user_id", None)
        if app.config["CSRF_ENABLED"] and request.method == "POST":
            sent = request.form.get("_csrf", "")
            token = session.get("_csrf", "")
            if not token or not secrets.compare_digest(token, sent):
                abort(400, "Invalid or missing CSRF token.")

    def login_required(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    def role_required(*roles):
        def decorator(view):
            @functools.wraps(view)
            @login_required
            def wrapped(*args, **kwargs):
                if g.user["role"] not in roles:
                    abort(403)
                return view(*args, **kwargs)
            return wrapped
        return decorator

    def safe_next(target):
        return target if target and target.startswith("/") and not target.startswith("//") else None

    def flash_error(exc):
        flash(str(exc), "error")

    def db():
        return dbm.get_db()

    def is_manager():
        return g.user is not None and g.user["role"] in ("chair", "admin")

    def manages(conf):
        return g.user is not None and (g.user["role"] == "admin" or g.user["user_id"] == conf["chair_id"])

    # ------------------------------------------------------ template context
    def nav_for(user):
        c = db()
        unread = c.execute("SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0",
                           (user["user_id"],)).fetchone()[0]
        role = user["role"]
        items = [("Dashboard", url_for("dashboard"), "grid", None)]
        if role == "admin":
            items += [("Users", url_for("admin_users"), "users", None),
                      ("Conferences", url_for("conferences"), "calendar", None),
                      ("All papers", url_for("papers_list"), "file", None),
                      ("Analytics", url_for("analytics"), "chart", None),
                      ("Activity log", url_for("admin_activity"), "pulse", None)]
        elif role == "chair":
            needs = insights.manager_kpis(c, user)["needs_reviewers"]
            items += [("Conferences", url_for("conferences"), "calendar", None),
                      ("Papers", url_for("papers_list"), "file", None),
                      ("Needs reviewers", url_for("papers_list", tab="needs"), "userplus", needs or None),
                      ("Analytics", url_for("analytics"), "chart", None)]
        elif role == "author":
            items += [("My papers", url_for("papers_list"), "file", None),
                      ("Conferences", url_for("conferences"), "calendar", None)]
        elif role == "reviewer":
            k = insights.reviewer_kpis(c, user)
            items += [("Assigned papers", url_for("papers_list"), "file", k["pending"] or None),
                      ("Open for review", url_for("papers_list", tab="open"), "inbox", k["open"] or None),
                      ("Completed", url_for("papers_list", tab="done"), "check", None),
                      ("Conferences", url_for("conferences"), "calendar", None)]
        else:
            items += [("Accepted papers", url_for("papers_list"), "file", None),
                      ("Conferences", url_for("conferences"), "calendar", None)]
        items += [("Notifications", url_for("notifications"), "bell", unread or None),
                  ("Profile", url_for("profile"), "user", None)]
        out = []
        for label, href, icon, badge in items:
            path, _, qs = href.partition("?")
            active = request.path == path and (request.query_string.decode() == qs or (
                not qs and path != "/papers" and True) or (not qs and path == "/papers" and not request.args.get("tab")))
            if path == "/conferences" and request.path.startswith("/conferences/"):
                active = True
            out.append({"label": label, "href": href, "icon": icon, "badge": badge, "active": active})
        return out, unread

    @app.context_processor
    def inject_globals():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        nav, unread = ([], 0)
        if g.get("user"):
            nav, unread = nav_for(g.user)
        return {"csrf_token": session["_csrf"], "current_user": g.get("user"),
                "unread_count": unread, "nav": nav, "STATUSES": insights.STATUSES,
                "today": date.today().isoformat()}

    app.jinja_env.globals["csrf_value"] = lambda: session.get("_csrf", "")

    @app.template_filter("firstname")
    def firstname(name):
        parts = [w for w in (name or "").split() if w.rstrip(".").lower() not in ("dr", "prof", "mr", "ms", "mrs")]
        return (parts or (name or "").split() or [""])[0]

    @app.template_filter("dt")
    def fmt_dt(value, pattern="%d %b %Y, %H:%M"):
        try:
            return datetime.fromisoformat(value).strftime(pattern)
        except (TypeError, ValueError):
            return value or ""

    @app.template_filter("d")
    def fmt_d(value):
        return fmt_dt(value, "%d %b %Y")

    @app.template_filter("ago")
    def ago(value):
        try:
            delta = datetime.now() - datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return value or ""
        days = delta.days
        if days <= 0:
            hours = delta.seconds // 3600
            return f"{hours}h ago" if hours else "just now"
        if days < 30:
            return f"{days}d ago"
        return datetime.fromisoformat(value).strftime("%d %b %Y")

    @app.template_filter("inr")
    def inr(value):
        n = int(round(value or 0))
        s = str(abs(n))
        if len(s) > 3:
            head, tail = s[:-3], s[-3:]
            parts = []
            while len(head) > 2:
                parts.insert(0, head[-2:])
                head = head[:-2]
            if head:
                parts.insert(0, head)
            s = ",".join(parts + [tail])
        return ("-" if n < 0 else "") + "Rs " + s

    # --------------------------------------------------------- public pages
    @app.route("/")
    def index():
        if g.user:
            return redirect(url_for("dashboard"))
        c = db()
        confs = c.execute("SELECT c.*, u.name AS chair_name FROM conferences c JOIN users u"
                          " ON u.user_id=c.chair_id ORDER BY c.start_date").fetchall()
        stats = {
            "papers": c.execute("SELECT COUNT(*) FROM papers").fetchone()[0],
            "reviews": c.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
            "people": c.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "conferences": len(confs),
        }
        pipeline = insights.status_counts(c, [x["conf_id"] for x in confs])
        return render_template("index.html", conferences=confs, stats=stats, pipeline=pipeline)

    @app.route("/register", methods=("GET", "POST"))
    def register():
        if g.user:
            return redirect(url_for("dashboard"))
        form = {}
        if request.method == "POST":
            form = request.form
            role = form.get("role", "")
            try:
                if role not in svc.SELF_REGISTER_ROLES:
                    raise svc.ServiceError("Choose Author, Reviewer or Attendee.")
                svc.register_user(db(), form.get("name"), form.get("email"), form.get("password"),
                                  role, form.get("affiliation"), form.get("expertise"))
                flash("Account created. Log in to continue.", "success")
                return redirect(url_for("login"))
            except svc.ServiceError as exc:
                flash_error(exc)
        return render_template("register.html", form=form)

    def public_stats():
        c = db()
        ids = [r[0] for r in c.execute("SELECT conf_id FROM conferences")]
        return {"papers": c.execute("SELECT COUNT(*) FROM papers").fetchone()[0],
                "reviews": c.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
                "people": c.execute("SELECT COUNT(*) FROM users").fetchone()[0],
                "conferences": len(ids)}, insights.status_counts(c, ids)

    @app.context_processor
    def inject_public():
        if request.endpoint in ("login", "register"):
            stats, pipeline = public_stats()
            demo = None
            if db().execute("SELECT 1 FROM users WHERE email='admin@demo.org'").fetchone():
                demo = [("admin@demo.org", "Admin", "Users, platform KPIs"), ("chair@demo.org", "Chair", "Assign and decide"),
                        ("reviewer1@demo.org", "Reviewer", "Pending reviews"), ("author@demo.org", "Author", "Track my papers"),
                        ("attendee@demo.org", "Attendee", "Register and pay")]
            return {"stats": stats, "pipeline": pipeline, "demo": demo}
        return {}

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if g.user:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            try:
                user = svc.authenticate(db(), request.form.get("email"), request.form.get("password"))
            except svc.ServiceError as exc:
                flash_error(exc)
                user = False
            if user is None:
                flash("Invalid email or password.", "error")
            elif user:
                session.clear()
                session["user_id"] = user["user_id"]
                return redirect(safe_next(request.args.get("next")) or url_for("dashboard"))
        return render_template("login.html")

    @app.route("/logout", methods=("POST",))
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("index"))

    # ------------------------------------------------------------ dashboards
    @app.route("/dashboard")
    @login_required
    def dashboard():
        c, user = db(), g.user
        role = user["role"]
        if role in ("admin", "chair"):
            k = insights.manager_kpis(c, user)
            ids = k["ids"]
            q = insights._in(ids)
            confs = c.execute(
                f"SELECT c.*, (SELECT COUNT(*) FROM papers p WHERE p.conf_id=c.conf_id) AS n_papers,"
                f" (SELECT COUNT(*) FROM registrations r WHERE r.conf_id=c.conf_id AND r.status='Confirmed') AS n_regs,"
                f" (SELECT COUNT(*) FROM papers p WHERE p.conf_id=c.conf_id AND p.status IN ('Accepted','Scheduled')) AS n_acc,"
                f" (SELECT COUNT(*) FROM papers p WHERE p.conf_id=c.conf_id AND p.status NOT IN ('Submitted','Under Review','Reviewed')) AS n_decided"
                f" FROM conferences c WHERE c.conf_id IN ({q}) ORDER BY c.start_date", ids).fetchall()
            need = c.execute(
                f"SELECT p.paper_id, p.title, p.submitted_at, p.keywords, cf.name AS conf_name, t.name AS track_name,"
                f" (SELECT COUNT(*) FROM review_assignments ra WHERE ra.paper_id=p.paper_id) AS n_rev"
                f" FROM papers p JOIN conferences cf ON cf.conf_id=p.conf_id JOIN tracks t ON t.track_id=p.track_id"
                f" WHERE p.conf_id IN ({q}) AND p.status IN ('Submitted','Under Review') AND"
                f" (SELECT COUNT(*) FROM review_assignments ra WHERE ra.paper_id=p.paper_id) < ?"
                f" ORDER BY p.submitted_at LIMIT 6", ids + [svc.MIN_REVIEWS_FOR_DECISION]).fetchall()
            ready = c.execute(
                f"SELECT p.paper_id, p.title, cf.name AS conf_name,"
                f" (SELECT ROUND(AVG(r.score),1) FROM reviews r JOIN review_assignments ra ON ra.assignment_id=r.assignment_id"
                f"  WHERE ra.paper_id=p.paper_id) AS avg_score,"
                f" (SELECT COUNT(*) FROM reviews r JOIN review_assignments ra ON ra.assignment_id=r.assignment_id"
                f"  WHERE ra.paper_id=p.paper_id) AS n_done"
                f" FROM papers p JOIN conferences cf ON cf.conf_id=p.conf_id WHERE p.conf_id IN ({q})"
                f" AND p.status IN ('Under Review','Reviewed') AND (SELECT COUNT(*) FROM reviews r JOIN review_assignments ra"
                f" ON ra.assignment_id=r.assignment_id WHERE ra.paper_id=p.paper_id) >= ? LIMIT 6",
                ids + [svc.MIN_REVIEWS_FOR_DECISION]).fetchall()
            activity = c.execute(
                "SELECT a.*, u.name AS who FROM activity a LEFT JOIN users u ON u.user_id=a.user_id"
                " ORDER BY a.created_at DESC, a.activity_id DESC LIMIT 8").fetchall()
            ctx = dict(k=k, confs=confs, need=need, ready=ready, activity=activity,
                       workload=insights.reviewer_workload(c, ids, 6), tracks=insights.track_breakdown(c, ids),
                       cap=svc.MAX_PENDING_REVIEWS_PER_REVIEWER)
            if role == "admin":
                ctx["a"] = insights.admin_kpis(c)
                ctx["newest"] = c.execute("SELECT * FROM users ORDER BY user_id DESC LIMIT 6").fetchall()
            return render_template("dash_manager.html", **ctx)
        if role == "author":
            k = insights.author_kpis(c, user)
            papers = c.execute(
                "SELECT p.*, cf.name AS conf_name, t.name AS track_name,"
                " (SELECT COUNT(*) FROM review_assignments ra WHERE ra.paper_id=p.paper_id) AS n_rev,"
                " (SELECT COUNT(*) FROM review_assignments ra WHERE ra.paper_id=p.paper_id AND ra.status='Completed') AS n_done"
                " FROM papers p JOIN conferences cf ON cf.conf_id=p.conf_id JOIN tracks t ON t.track_id=p.track_id"
                " WHERE p.author_id=? ORDER BY p.submitted_at DESC", (user["user_id"],)).fetchall()
            confs = c.execute("SELECT * FROM conferences WHERE submission_deadline >= ? ORDER BY submission_deadline",
                              (date.today().isoformat(),)).fetchall()
            regs = c.execute("SELECT r.*, cf.name AS conf_name FROM registrations r JOIN conferences cf ON cf.conf_id=r.conf_id"
                             " WHERE r.user_id=?", (user["user_id"],)).fetchall()
            return render_template("dash_author.html", k=k, papers=papers, confs=confs, regs=regs)
        if role == "reviewer":
            k = insights.reviewer_kpis(c, user)
            mine = c.execute(
                "SELECT ra.*, p.title, p.keywords, cf.name AS conf_name, t.name AS track_name FROM review_assignments ra"
                " JOIN papers p ON p.paper_id=ra.paper_id JOIN conferences cf ON cf.conf_id=p.conf_id"
                " JOIN tracks t ON t.track_id=p.track_id WHERE ra.reviewer_id=? AND ra.status='Pending'"
                " ORDER BY ra.assigned_at", (user["user_id"],)).fetchall()
            recent = c.execute(
                "SELECT r.score, r.recommendation, r.submitted_at, p.title FROM reviews r"
                " JOIN review_assignments ra ON ra.assignment_id=r.assignment_id JOIN papers p ON p.paper_id=ra.paper_id"
                " WHERE ra.reviewer_id=? ORDER BY r.review_id DESC LIMIT 5", (user["user_id"],)).fetchall()
            return render_template("dash_reviewer.html", k=k, mine=mine, recent=recent,
                                   open_list=insights.open_papers(c, user)[:6])
        k = insights.attendee_kpis(c, user)
        regs = c.execute("SELECT r.*, cf.name AS conf_name, cf.start_date, cf.venue FROM registrations r"
                         " JOIN conferences cf ON cf.conf_id=r.conf_id WHERE r.user_id=?", (user["user_id"],)).fetchall()
        confs = c.execute("SELECT * FROM conferences WHERE end_date >= ? ORDER BY start_date",
                          (date.today().isoformat(),)).fetchall()
        accepted = c.execute(
            "SELECT p.paper_id, p.title, p.keywords, cf.name AS conf_name FROM papers p JOIN conferences cf"
            " ON cf.conf_id=p.conf_id WHERE p.status IN ('Accepted','Scheduled') ORDER BY p.submitted_at DESC LIMIT 6").fetchall()
        return render_template("dash_attendee.html", k=k, regs=regs, confs=confs, accepted=accepted)

    @app.route("/notifications")
    @login_required
    def notifications():
        c = db()
        rows = c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC, notif_id DESC LIMIT 100",
                         (g.user["user_id"],)).fetchall()
        unread_ids = {r["notif_id"] for r in rows if not r["is_read"]}
        c.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (g.user["user_id"],))
        c.commit()
        return render_template("notifications.html", notifications=rows, unread_ids=unread_ids)

    @app.route("/profile", methods=("GET", "POST"))
    @login_required
    def profile():
        if request.method == "POST":
            f = request.form
            try:
                if f.get("form") == "password":
                    svc.change_password(db(), g.user["user_id"], f.get("current"), f.get("new"))
                    flash("Password changed.", "success")
                else:
                    svc.update_profile(db(), g.user["user_id"], f.get("name"), f.get("affiliation"),
                                       f.get("expertise"))
                    flash("Profile saved.", "success")
                return redirect(url_for("profile"))
            except svc.ServiceError as exc:
                flash_error(exc)
        return render_template("profile.html")

    # ------------------------------------------------------------ conference
    @app.route("/conferences")
    def conferences():
        c = db()
        rows = c.execute(
            "SELECT c.*, u.name AS chair_name,"
            " (SELECT COUNT(*) FROM papers p WHERE p.conf_id=c.conf_id) AS n_papers,"
            " (SELECT COUNT(*) FROM tracks t WHERE t.conf_id=c.conf_id) AS n_tracks,"
            " (SELECT COUNT(*) FROM registrations r WHERE r.conf_id=c.conf_id AND r.status='Confirmed') AS n_regs"
            " FROM conferences c JOIN users u ON u.user_id=c.chair_id ORDER BY c.start_date").fetchall()
        return render_template("conferences.html", conferences=rows)

    @app.route("/conferences/new", methods=("GET", "POST"))
    @role_required("chair", "admin")
    def conference_new():
        chairs = db().execute("SELECT user_id, name FROM users WHERE role IN ('chair','admin') AND is_active=1"
                              " ORDER BY name").fetchall()
        form = {}
        if request.method == "POST":
            f = form = request.form
            try:
                conf_id = svc.create_conference(
                    db(), g.user["user_id"], f.get("name"), f.get("venue"), f.get("start_date"),
                    f.get("end_date"), f.get("submission_deadline"), f.get("early_bird_deadline"),
                    f.get("description", ""), f.get("chair_id", type=int))
                flash("Conference created. Add tracks next.", "success")
                return redirect(url_for("conference", conf_id=conf_id))
            except svc.ServiceError as exc:
                flash_error(exc)
        return render_template("conference_new.html", chairs=chairs, form=form)

    @app.route("/conferences/<int:conf_id>")
    def conference(conf_id):
        c = db()
        conf = c.execute("SELECT cf.*, u.name AS chair_name FROM conferences cf JOIN users u"
                         " ON u.user_id=cf.chair_id WHERE conf_id=?", (conf_id,)).fetchone()
        if conf is None:
            abort(404)
        tracks = c.execute(
            "SELECT t.*, (SELECT COUNT(*) FROM papers p WHERE p.track_id=t.track_id) AS n FROM tracks t"
            " WHERE conf_id=?", (conf_id,)).fetchall()
        sessions = c.execute(
            "SELECT s.*, (SELECT COUNT(*) FROM presentations pr WHERE pr.session_id=s.session_id) AS used"
            " FROM sessions s WHERE conf_id=? ORDER BY start_time", (conf_id,)).fetchall()
        manager = manages(conf)
        papers, chairs = [], []
        if manager:
            papers = c.execute(
                "SELECT p.*, u.name AS author_name, t.name AS track_name,"
                " (SELECT COUNT(*) FROM review_assignments ra WHERE ra.paper_id=p.paper_id) AS n_rev"
                " FROM papers p JOIN users u ON u.user_id=p.author_id JOIN tracks t ON t.track_id=p.track_id"
                " WHERE p.conf_id=? ORDER BY p.paper_id DESC", (conf_id,)).fetchall()
            chairs = c.execute("SELECT user_id, name FROM users WHERE role IN ('chair','admin') AND is_active=1").fetchall()
        k = insights.status_counts(c, [conf_id])
        my_reg = None
        if g.user:
            my_reg = c.execute("SELECT * FROM registrations WHERE conf_id=? AND user_id=?",
                               (conf_id, g.user["user_id"])).fetchone()
        stats = {
            "papers": sum(k.values()), "accepted": k["Accepted"] + k["Scheduled"],
            "regs": c.execute("SELECT COUNT(*) FROM registrations WHERE conf_id=? AND status='Confirmed'", (conf_id,)).fetchone()[0],
        }
        days_left = (date.fromisoformat(conf["submission_deadline"]) - date.today()).days
        return render_template("conference.html", conf=conf, tracks=tracks, sessions=sessions,
                               is_chair=manager, papers=papers, fees=svc.FEES, chairs=chairs,
                               discount=int(svc.EARLY_BIRD_DISCOUNT * 100), my_reg=my_reg,
                               stats=stats, pipeline=k, days_left=days_left)

    @app.route("/conferences/<int:conf_id>/tracks", methods=("POST",))
    @login_required
    def track_add(conf_id):
        try:
            svc.add_track(db(), g.user["user_id"], conf_id, request.form.get("name"))
            flash("Track added.", "success")
        except svc.ServiceError as exc:
            flash_error(exc)
        return redirect(url_for("conference", conf_id=conf_id))

    @app.route("/conferences/<int:conf_id>/sessions", methods=("POST",))
    @login_required
    def session_add(conf_id):
        f = request.form
        try:
            svc.create_session(db(), g.user["user_id"], conf_id, f.get("title"), f.get("room"),
                               f.get("start_time"), f.get("end_time"), f.get("capacity", 4))
            flash("Session created.", "success")
        except svc.ServiceError as exc:
            flash_error(exc)
        return redirect(url_for("conference", conf_id=conf_id))

    @app.route("/conferences/<int:conf_id>/chair", methods=("POST",))
    @role_required("admin")
    def chair_reassign(conf_id):
        try:
            svc.reassign_chair(db(), g.user["user_id"], conf_id, request.form.get("chair_id", type=int))
            flash("Chair reassigned.", "success")
        except svc.ServiceError as exc:
            flash_error(exc)
        return redirect(url_for("conference", conf_id=conf_id))

    @app.route("/conferences/<int:conf_id>/auto-assign", methods=("POST",))
    @login_required
    def conference_auto_assign(conf_id):
        try:
            n = svc.auto_assign_conference(db(), g.user["user_id"], conf_id)
            flash(f"Reviewers assigned automatically to {n} paper{'s' if n != 1 else ''}." if n
                  else "Every paper already has enough reviewers.", "success")
        except svc.ServiceError as exc:
            flash_error(exc)
        return redirect(request.form.get("back") if safe_next(request.form.get("back")) else url_for("dashboard"))

    @app.route("/auto-assign", methods=("POST",))
    @role_required("chair", "admin")
    def auto_assign_all():
        total = 0
        for conf_id in insights._scope(g.user, db()):
            total += svc.auto_assign_conference(db(), g.user["user_id"], conf_id)
        flash(f"Reviewers assigned automatically to {total} paper{'s' if total != 1 else ''}." if total
              else "Every paper already has enough reviewers, or no eligible reviewers are free.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/conferences/<int:conf_id>/program")
    def program(conf_id):
        conf = db().execute("SELECT * FROM conferences WHERE conf_id=?", (conf_id,)).fetchone()
        if conf is None:
            abort(404)
        return render_template("program.html", conf=conf, program=svc.get_program(db(), conf_id))

    @app.route("/conferences/<int:conf_id>/export/papers.csv")
    @login_required
    def export_papers(conf_id):
        conf = db().execute("SELECT * FROM conferences WHERE conf_id=?", (conf_id,)).fetchone()
        if conf is None:
            abort(404)
        if not manages(conf):
            abort(403)
        rows = db().execute(
            "SELECT p.paper_id, p.title, u.name, t.name AS track, p.status, p.submitted_at FROM papers p"
            " JOIN users u ON u.user_id=p.author_id JOIN tracks t ON t.track_id=p.track_id WHERE p.conf_id=?",
            (conf_id,)).fetchall()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Paper ID", "Title", "Author", "Track", "Status", "Submitted"])
        for r in rows:
            w.writerow(list(r))
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=papers_{conf_id}.csv"})

    # --------------------------------------------------------------- papers
    @app.route("/conferences/<int:conf_id>/submit", methods=("GET", "POST"))
    @role_required("author")
    def paper_submit(conf_id):
        c = db()
        conf = c.execute("SELECT * FROM conferences WHERE conf_id=?", (conf_id,)).fetchone()
        if conf is None:
            abort(404)
        tracks = c.execute("SELECT * FROM tracks WHERE conf_id=?", (conf_id,)).fetchall()
        form = {}
        if request.method == "POST":
            f = form = request.form
            upload = request.files.get("file")
            original = secure_filename(upload.filename) if upload and upload.filename else ""
            try:
                paper_id = svc.submit_paper(c, g.user["user_id"], conf_id, f.get("track_id", type=int),
                                            f.get("title"), f.get("abstract"), f.get("keywords"), original)
                stored = os.path.join(app.config["UPLOAD_FOLDER"], f"{paper_id}_{uuid.uuid4().hex[:8]}.pdf")
                upload.save(stored)
                flash("Paper submitted. The chair has been notified and will assign reviewers.", "success")
                return redirect(url_for("paper_detail", paper_id=paper_id))
            except svc.ServiceError as exc:
                flash_error(exc)
        return render_template("paper_submit.html", conf=conf, tracks=tracks, form=form)

    def paper_row(paper_id):
        return db().execute(
            "SELECT p.*, u.name AS author_name, u.affiliation AS author_aff, t.name AS track_name FROM papers p"
            " JOIN users u ON u.user_id=p.author_id JOIN tracks t ON t.track_id=p.track_id"
            " WHERE p.paper_id=?", (paper_id,)).fetchone()

    def paper_access(paper):
        """Viewer's relation to a paper, or abort(403)."""
        c = db()
        conf = c.execute("SELECT * FROM conferences WHERE conf_id=?", (paper["conf_id"],)).fetchone()
        uid, role = g.user["user_id"], g.user["role"]
        if manages(conf):
            return "chair", conf
        if uid == paper["author_id"]:
            return "author", conf
        if c.execute("SELECT 1 FROM review_assignments WHERE paper_id=? AND reviewer_id=?",
                     (paper["paper_id"], uid)).fetchone():
            return "reviewer", conf
        if role == "reviewer" and paper["status"] in ("Submitted", "Under Review"):
            return "prospect", conf
        if paper["status"] in ("Accepted", "Scheduled"):
            return "public", conf
        abort(403)

    @app.route("/papers")
    @login_required
    def papers_list():
        c, user = db(), g.user
        role = user["role"]
        tab = request.args.get("tab", "")
        q = (request.args.get("q") or "").strip()
        status = request.args.get("status", "")
        conf_filter = request.args.get("conf", type=int)
        if role == "reviewer" and tab == "open":
            rows = insights.open_papers(c, user, q, conf_filter)
            tabs = reviewer_tabs(c, user)
            return render_template("papers.html", rows=rows, tab="open", tabs=tabs, q=q, status="",
                                   mode="open", title="Open for review",
                                   subtitle="Papers that still need reviewers. Pick the ones that match your expertise.",
                                   confs=c.execute("SELECT conf_id, name FROM conferences").fetchall(), conf_filter=conf_filter)
        base = ("SELECT p.*, cf.name AS conf_name, t.name AS track_name, u.name AS author_name,"
                " (SELECT COUNT(*) FROM review_assignments ra WHERE ra.paper_id=p.paper_id) AS n_rev,"
                " (SELECT COUNT(*) FROM review_assignments ra WHERE ra.paper_id=p.paper_id AND ra.status='Completed') AS n_done,"
                " (SELECT ROUND(AVG(r.score),1) FROM reviews r JOIN review_assignments ra ON ra.assignment_id=r.assignment_id"
                "  WHERE ra.paper_id=p.paper_id) AS avg_score")
        frm = (" FROM papers p JOIN conferences cf ON cf.conf_id=p.conf_id JOIN tracks t ON t.track_id=p.track_id"
               " JOIN users u ON u.user_id=p.author_id")
        where, args = [], []
        mode, title, subtitle = "all", "Papers", ""
        tabs = []
        if role == "author":
            where.append("p.author_id=?"); args.append(user["user_id"])
            title, subtitle = "My papers", "Everything you have submitted, with live review progress."
            tabs = [("", "All"), ("review", "In review"), ("decided", "Decided")]
            if tab == "review":
                where.append("p.status IN ('Submitted','Under Review','Reviewed')")
            elif tab == "decided":
                where.append("p.status IN ('Accepted','Rejected','Revision Required','Scheduled')")
        elif role == "reviewer":
            base = base.replace("u.name AS author_name,", "")
            frm = frm.replace(" JOIN users u ON u.user_id=p.author_id", "")
            base += ", ra.assignment_id, ra.status AS ra_status, ra.assigned_at"
            frm += " JOIN review_assignments ra ON ra.paper_id=p.paper_id"
            where.append("ra.reviewer_id=?"); args.append(user["user_id"])
            mode = "reviewer"
            title, subtitle = "Assigned papers", "Author names are hidden so you can review blind."
            tabs = reviewer_tabs(c, user)
            if tab == "done":
                where.append("ra.status='Completed'"); title = "Completed reviews"
            else:
                where.append("ra.status='Pending'")
        elif role in ("chair", "admin"):
            if role == "chair":
                where.append("cf.chair_id=?"); args.append(user["user_id"])
            title = "All papers" if role == "admin" else "Papers"
            subtitle = "Every submission you manage. Assign reviewers and record decisions from here."
            tabs = [("", "All"), ("needs", "Needs reviewers"), ("review", "In review"),
                    ("ready", "Ready for decision"), ("decided", "Decided")]
            if tab == "needs":
                where.append("p.status IN ('Submitted','Under Review') AND (SELECT COUNT(*) FROM review_assignments ra"
                             " WHERE ra.paper_id=p.paper_id) < ?"); args.append(svc.MIN_REVIEWS_FOR_DECISION)
            elif tab == "review":
                where.append("p.status IN ('Under Review','Reviewed')")
            elif tab == "ready":
                where.append("p.status IN ('Under Review','Reviewed') AND (SELECT COUNT(*) FROM reviews r JOIN"
                             " review_assignments ra ON ra.assignment_id=r.assignment_id WHERE ra.paper_id=p.paper_id) >= ?")
                args.append(svc.MIN_REVIEWS_FOR_DECISION)
            elif tab == "decided":
                where.append("p.status IN ('Accepted','Rejected','Revision Required','Scheduled')")
        else:
            where.append("p.status IN ('Accepted','Scheduled')")
            title, subtitle = "Accepted papers", "Peer-reviewed papers that will be presented at the conferences."
        if status in insights.STATUSES:
            where.append("p.status=?"); args.append(status)
        if q:
            where.append("(p.title LIKE ? OR p.keywords LIKE ? OR cf.name LIKE ?)"); args += [f"%{q}%"] * 3
        if conf_filter:
            where.append("p.conf_id=?"); args.append(conf_filter)
        sql = base + frm + (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY p.submitted_at DESC"
        rows = c.execute(sql, args).fetchall()
        return render_template("papers.html", rows=rows, tab=tab, tabs=tabs, q=q, status=status, mode=mode,
                               title=title, subtitle=subtitle, conf_filter=conf_filter,
                               confs=c.execute("SELECT conf_id, name FROM conferences").fetchall())

    def reviewer_tabs(c, user):
        k = insights.reviewer_kpis(c, user)
        return [("", f"Assigned ({k['pending']})"), ("open", f"Open for review ({k['open']})"),
                ("done", f"Completed ({k['done']})")]

    @app.route("/papers/<int:paper_id>")
    @login_required
    def paper_detail(paper_id):
        c = db()
        paper = paper_row(paper_id)
        if paper is None:
            abort(404)
        relation, conf = paper_access(paper)
        assignments = c.execute(
            "SELECT ra.*, u.name AS reviewer_name, u.expertise, r.score, r.comments, r.recommendation, r.submitted_at AS reviewed_at"
            " FROM review_assignments ra JOIN users u ON u.user_id=ra.reviewer_id"
            " LEFT JOIN reviews r ON r.assignment_id=ra.assignment_id WHERE ra.paper_id=? ORDER BY ra.assignment_id",
            (paper_id,)).fetchall()
        decided = paper["status"] in DECIDED
        show_reviews = relation == "chair" or (relation == "author" and decided)
        suggestion, ranked, sessions = None, [], []
        if relation == "chair":
            try:
                suggestion = svc.suggest_decision(c, paper_id)
            except svc.ServiceError:
                suggestion = None
            if paper["status"] in ("Submitted", "Under Review", "Reviewed") and len(assignments) < svc.MAX_REVIEWERS_PER_PAPER:
                ranked = svc.ranked_reviewers(c, paper_id)
            sessions = c.execute("SELECT s.*, (SELECT COUNT(*) FROM presentations pr WHERE pr.session_id=s.session_id) AS used"
                                 " FROM sessions s WHERE conf_id=? ORDER BY start_time", (paper["conf_id"],)).fetchall()
        my_assignment = next((a for a in assignments if a["reviewer_id"] == g.user["user_id"]), None)
        decision_row = c.execute("SELECT d.*, u.name AS by_name FROM decisions d JOIN users u ON u.user_id=d.decided_by"
                                 " WHERE paper_id=? ORDER BY decision_id DESC LIMIT 1", (paper_id,)).fetchone()
        sched = c.execute("SELECT s.*, pr.slot_order FROM presentations pr JOIN sessions s ON s.session_id=pr.session_id"
                          " WHERE pr.paper_id=?", (paper_id,)).fetchone()
        can_volunteer = False
        if relation == "prospect":
            can_volunteer = (len(assignments) < svc.MAX_REVIEWERS_PER_PAPER and
                             svc.pending_reviews(c, g.user["user_id"], paper["conf_id"]) < svc.MAX_PENDING_REVIEWS_PER_REVIEWER)
        return render_template("paper.html", paper=paper, relation=relation, conf=conf,
                               assignments=assignments, show_reviews=show_reviews, suggestion=suggestion,
                               ranked=ranked, sessions=sessions, decisions=svc.DECISIONS,
                               my_assignment=my_assignment, decision_row=decision_row, sched=sched,
                               can_volunteer=can_volunteer, min_reviews=svc.MIN_REVIEWS_FOR_DECISION,
                               max_reviews=svc.MAX_REVIEWERS_PER_PAPER)

    @app.route("/papers/<int:paper_id>/file")
    @login_required
    def paper_file(paper_id):
        paper = paper_row(paper_id)
        if paper is None:
            abort(404)
        relation, _conf = paper_access(paper)
        if relation in ("prospect", "public"):
            abort(403)
        folder = app.config["UPLOAD_FOLDER"]
        matches = sorted(f for f in os.listdir(folder) if f.startswith(f"{paper_id}_"))
        if not matches:
            abort(404)
        return send_file(os.path.join(folder, matches[-1]), mimetype="application/pdf",
                         download_name=paper["file_name"], as_attachment=request.args.get("dl") == "1")

    def back_to_paper(paper_id):
        return redirect(url_for("paper_detail", paper_id=paper_id))

    @app.route("/papers/<int:paper_id>/assign", methods=("POST",))
    @login_required
    def reviewer_assign(paper_id):
        try:
            svc.assign_reviewer(db(), g.user["user_id"], paper_id, request.form.get("reviewer_id", type=int))
            flash("Reviewer assigned and notified.", "success")
        except svc.ServiceError as exc:
            flash_error(exc)
        return back_to_paper(paper_id)

    @app.route("/papers/<int:paper_id>/auto-assign", methods=("POST",))
    @login_required
    def paper_auto_assign(paper_id):
        try:
            names = svc.auto_assign(db(), g.user["user_id"], paper_id)
            flash("Auto-assigned: " + ", ".join(names) + ".", "success")
        except svc.ServiceError as exc:
            flash_error(exc)
        return redirect(request.form.get("back") if safe_next(request.form.get("back")) else
                        url_for("paper_detail", paper_id=paper_id))

    @app.route("/papers/<int:paper_id>/volunteer", methods=("POST",))
    @role_required("reviewer")
    def paper_volunteer(paper_id):
        try:
            aid = svc.volunteer_to_review(db(), g.user["user_id"], paper_id)
            flash("Paper added to your review list.", "success")
            if request.form.get("next") == "review":
                return redirect(url_for("review_form", assignment_id=aid))
        except svc.ServiceError as exc:
            flash_error(exc)
        return redirect(request.form.get("back") if safe_next(request.form.get("back")) else
                        url_for("paper_detail", paper_id=paper_id))

    @app.route("/papers/<int:paper_id>/decision", methods=("POST",))
    @login_required
    def decision(paper_id):
        try:
            svc.record_decision(db(), g.user["user_id"], paper_id, request.form.get("decision"),
                                request.form.get("remarks"))
            flash("Decision recorded and the author notified.", "success")
        except svc.ServiceError as exc:
            flash_error(exc)
        return back_to_paper(paper_id)

    @app.route("/papers/<int:paper_id>/schedule", methods=("POST",))
    @login_required
    def schedule(paper_id):
        try:
            svc.schedule_paper(db(), g.user["user_id"], paper_id, request.form.get("session_id", type=int))
            flash("Paper scheduled.", "success")
        except svc.ServiceError as exc:
            flash_error(exc)
        return back_to_paper(paper_id)

    # -------------------------------------------------------------- reviews
    @app.route("/reviews/<int:assignment_id>", methods=("GET", "POST"))
    @role_required("reviewer")
    def review_form(assignment_id):
        c = db()
        asg = c.execute(
            "SELECT ra.*, p.title, p.abstract, p.keywords, p.paper_id, cf.name AS conf_name, t.name AS track_name"
            " FROM review_assignments ra JOIN papers p ON p.paper_id=ra.paper_id"
            " JOIN conferences cf ON cf.conf_id=p.conf_id JOIN tracks t ON t.track_id=p.track_id"
            " WHERE ra.assignment_id=?", (assignment_id,)).fetchone()
        if asg is None or asg["reviewer_id"] != g.user["user_id"]:
            abort(404)
        form = {}
        if request.method == "POST":
            f = form = request.form
            try:
                svc.submit_review(c, g.user["user_id"], assignment_id, f.get("score"), f.get("comments"),
                                  f.get("recommendation"))
                flash("Review submitted. Thank you.", "success")
                return redirect(url_for("dashboard"))
            except svc.ServiceError as exc:
                flash_error(exc)
        return render_template("review.html", asg=asg, recommendations=svc.RECOMMENDATIONS, form=form)

    # ------------------------------------------------ registration & payment
    @app.route("/conferences/<int:conf_id>/registration", methods=("GET", "POST"))
    @login_required
    def registration(conf_id):
        c = db()
        conf = c.execute("SELECT * FROM conferences WHERE conf_id=?", (conf_id,)).fetchone()
        if conf is None:
            abort(404)
        if request.method == "POST":
            try:
                reg_id = svc.register_for_conference(c, g.user["user_id"], conf_id, request.form.get("category"))
                return redirect(url_for("pay", reg_id=reg_id))
            except svc.ServiceError as exc:
                flash_error(exc)
        early = date.today() <= date.fromisoformat(conf["early_bird_deadline"])
        return render_template("registration.html", conf=conf, fees=svc.FEES, early=early,
                               discount=int(svc.EARLY_BIRD_DISCOUNT * 100))

    @app.route("/registrations/<int:reg_id>/pay", methods=("GET", "POST"))
    @login_required
    def pay(reg_id):
        c = db()
        reg = c.execute("SELECT r.*, cf.name AS conf_name FROM registrations r JOIN conferences cf"
                        " ON cf.conf_id=r.conf_id WHERE r.reg_id=? AND r.user_id=?",
                        (reg_id, g.user["user_id"])).fetchone()
        if reg is None:
            abort(404)
        if request.method == "POST":
            try:
                ref = svc.process_payment(c, g.user["user_id"], reg_id, request.form.get("card"))
                flash(f"Payment successful. Reference {ref}.", "success")
                return redirect(url_for("dashboard"))
            except svc.ServiceError as exc:
                flash_error(exc)
        return render_template("pay.html", reg=reg)

    # ----------------------------------------------------------- analytics
    @app.route("/analytics")
    @role_required("chair", "admin")
    def analytics():
        c = db()
        k = insights.manager_kpis(c, g.user)
        ids = k["ids"]
        return render_template("analytics.html", k=k, tracks=insights.track_breakdown(c, ids),
                               hist=insights.score_histogram(c, ids), revenue=insights.revenue_by_conference(c, ids),
                               workload=insights.reviewer_workload(c, ids, 10), cap=svc.MAX_PENDING_REVIEWS_PER_REVIEWER)

    # --------------------------------------------------------------- admin
    @app.route("/admin/users", methods=("GET", "POST"))
    @role_required("admin")
    def admin_users():
        c = db()
        q = (request.args.get("q") or "").strip()
        role = request.args.get("role", "")
        sql = ("SELECT u.*, (SELECT COUNT(*) FROM papers p WHERE p.author_id=u.user_id) AS n_papers,"
               " (SELECT COUNT(*) FROM review_assignments ra WHERE ra.reviewer_id=u.user_id) AS n_reviews FROM users u")
        where, args = [], []
        if q:
            where.append("(u.name LIKE ? OR u.email LIKE ? OR u.affiliation LIKE ?)"); args += [f"%{q}%"] * 3
        if role in svc.ROLES:
            where.append("u.role=?"); args.append(role)
        sql += (" WHERE " + " AND ".join(where) if where else "") + " ORDER BY u.user_id"
        rows = c.execute(sql, args).fetchall()
        counts = {r: n for r, n in c.execute("SELECT role, COUNT(*) FROM users GROUP BY role")}
        return render_template("admin_users.html", users=rows, q=q, role=role, roles=svc.ROLES, counts=counts)

    @app.route("/admin/users/new", methods=("GET", "POST"))
    @role_required("admin")
    def admin_user_new():
        form = {}
        if request.method == "POST":
            f = form = request.form
            try:
                svc.admin_create_user(db(), g.user["user_id"], f.get("name"), f.get("email"), f.get("password"),
                                      f.get("role"), f.get("affiliation"), f.get("expertise"))
                flash("User created.", "success")
                return redirect(url_for("admin_users"))
            except svc.ServiceError as exc:
                flash_error(exc)
        return render_template("admin_user_new.html", roles=svc.ROLES, form=form)

    @app.route("/admin/users/<int:user_id>/role", methods=("POST",))
    @role_required("admin")
    def admin_set_role(user_id):
        try:
            svc.set_user_role(db(), g.user["user_id"], user_id, request.form.get("role"))
            flash("Role updated.", "success")
        except svc.ServiceError as exc:
            flash_error(exc)
        return redirect(request.form.get("back") if safe_next(request.form.get("back")) else url_for("admin_users"))

    @app.route("/admin/users/<int:user_id>/active", methods=("POST",))
    @role_required("admin")
    def admin_set_active(user_id):
        try:
            svc.set_user_active(db(), g.user["user_id"], user_id, request.form.get("active") == "1")
            flash("Account updated.", "success")
        except svc.ServiceError as exc:
            flash_error(exc)
        return redirect(request.form.get("back") if safe_next(request.form.get("back")) else url_for("admin_users"))

    @app.route("/admin/activity")
    @role_required("admin")
    def admin_activity():
        rows = db().execute("SELECT a.*, u.name AS who, u.role AS who_role FROM activity a LEFT JOIN users u"
                            " ON u.user_id=a.user_id ORDER BY a.created_at DESC, a.activity_id DESC LIMIT 200").fetchall()
        return render_template("admin_activity.html", rows=rows)

    # -------------------------------------------------------------- errors
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("error.html", code=403, title="You don't have access to this page",
                               text="Your role can't open this page. Go back to your dashboard to continue."), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("error.html", code=404, title="We couldn't find that page",
                               text="The link may be old or the item may have been removed."), 404

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", code=400, title="That request couldn't be processed",
                               text=getattr(e, "description", "") or "Reload the page and try again."), 400

    return app
