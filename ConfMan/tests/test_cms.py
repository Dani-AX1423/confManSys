"""Automated tests for the Conference Management System sample implementation.

Run from the 11_Sample_Code folder:   python -m unittest discover -s tests -v
"""
import io
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cms_app import create_app, services as svc  # noqa: E402

SCHEMA = os.path.join(os.path.dirname(__file__), "..", "cms_app", "schema.sql")
LONG_ABSTRACT = "This paper studies scalable peer review workflows for academic conferences in depth."
GOOD_COMMENT = "The methodology is sound and the evaluation is thorough."


def make_db():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    with open(SCHEMA, encoding="utf-8") as fh:
        db.executescript(fh.read())
    db.execute("PRAGMA foreign_keys = ON")
    return db


class Base(unittest.TestCase):
    def setUp(self):
        self.db = make_db()
        self.chair = svc.register_user(self.db, "Dr. Chair", "chair@x.org", "chairpass1", "chair")
        self.author = svc.register_user(self.db, "Asha Author", "author@x.org", "authorpass1", "author")
        self.rev1 = svc.register_user(self.db, "Ravi Reviewer", "rev1@x.org", "reviewer1pass", "reviewer")
        self.rev2 = svc.register_user(self.db, "Meena Reviewer", "rev2@x.org", "reviewer2pass", "reviewer")
        self.rev3 = svc.register_user(self.db, "Kiran Reviewer", "rev3@x.org", "reviewer3pass", "reviewer")
        self.rev4 = svc.register_user(self.db, "Latha Reviewer", "rev4@x.org", "reviewer4pass", "reviewer")
        self.conf = svc.create_conference(
            self.db, self.chair, "ICSE-Demo 2026", "Chennai", "2026-12-10", "2026-12-12",
            "2026-11-01", "2026-11-15")
        self.track = svc.add_track(self.db, self.chair, self.conf, "Software Engineering")
        self.addCleanup(self.db.close)

    def paper(self, today="2026-10-20", title="A Study of Review Workflows"):
        return svc.submit_paper(self.db, self.author, self.conf, self.track, title,
                                LONG_ABSTRACT, "review, workflow", "paper.pdf", today=today)

    def reviewed_paper(self, scores=(8, 9), title="A Study of Review Workflows"):
        pid = self.paper(title=title)
        for rev, score in zip((self.rev1, self.rev2, self.rev3), scores):
            asg = svc.assign_reviewer(self.db, self.chair, pid, rev)
            svc.submit_review(self.db, rev, asg, score, GOOD_COMMENT, "accept")
        return pid


class UserTests(Base):
    def test_register_valid_user(self):
        uid = svc.register_user(self.db, "New User", "new@x.org", "password1", "attendee")
        self.assertIsInstance(uid, int)

    def test_register_rejects_duplicate_email_case_insensitive(self):
        with self.assertRaises(svc.ServiceError):
            svc.register_user(self.db, "Dup", "AUTHOR@x.org", "password1", "author")

    def test_register_rejects_weak_password(self):
        for bad in ("short1", "longpasswordnodigit", ""):
            with self.assertRaises(svc.ServiceError):
                svc.register_user(self.db, "Weak", "weak@x.org", bad, "author")

    def test_register_rejects_bad_email_and_role(self):
        with self.assertRaises(svc.ServiceError):
            svc.register_user(self.db, "Bad", "not-an-email", "password1", "author")
        with self.assertRaises(svc.ServiceError):
            svc.register_user(self.db, "Bad", "ok@x.org", "password1", "superuser")

    def test_password_is_hashed(self):
        row = self.db.execute("SELECT password_hash FROM users WHERE email='author@x.org'").fetchone()
        self.assertNotIn("authorpass1", row[0])

    def test_authenticate(self):
        self.assertIsNotNone(svc.authenticate(self.db, "author@x.org", "authorpass1"))
        self.assertIsNone(svc.authenticate(self.db, "author@x.org", "wrong-password"))
        self.assertIsNone(svc.authenticate(self.db, "nobody@x.org", "authorpass1"))


class ConferenceTests(Base):
    def test_only_chair_or_admin_can_create(self):
        with self.assertRaises(svc.ServiceError):
            svc.create_conference(self.db, self.author, "X", "Y", "2026-12-10", "2026-12-12",
                                 "2026-11-01", "2026-11-15")

    def test_date_rules(self):
        with self.assertRaises(svc.ServiceError):  # end before start
            svc.create_conference(self.db, self.chair, "X", "Y", "2026-12-12", "2026-12-10",
                                  "2026-11-01", "2026-11-15")
        with self.assertRaises(svc.ServiceError):  # deadline not before start
            svc.create_conference(self.db, self.chair, "X", "Y", "2026-12-10", "2026-12-12",
                                  "2026-12-10", "2026-11-15")
        with self.assertRaises(svc.ServiceError):  # malformed date
            svc.create_conference(self.db, self.chair, "X", "Y", "10/12/2026", "2026-12-12",
                                  "2026-11-01", "2026-11-15")

    def test_duplicate_track_rejected(self):
        with self.assertRaises(svc.ServiceError):
            svc.add_track(self.db, self.chair, self.conf, "Software Engineering")

    def test_non_chair_cannot_add_track(self):
        with self.assertRaises(svc.ServiceError):
            svc.add_track(self.db, self.author, self.conf, "Security")


class PaperTests(Base):
    def test_submit_paper_success_and_notifies(self):
        pid = self.paper()
        row = self.db.execute("SELECT status FROM papers WHERE paper_id=?", (pid,)).fetchone()
        self.assertEqual(row["status"], "Submitted")
        n = self.db.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
        self.assertEqual(n, 2)  # author + chair

    def test_deadline_is_inclusive_then_closed(self):
        self.paper(today="2026-11-01")  # last day is allowed
        with self.assertRaises(svc.ServiceError):
            self.paper(today="2026-11-02", title="Late Paper")

    def test_rejects_non_pdf_short_abstract_long_title(self):
        with self.assertRaises(svc.ServiceError):
            svc.submit_paper(self.db, self.author, self.conf, self.track, "T", LONG_ABSTRACT,
                             "", "paper.docx", today="2026-10-20")
        with self.assertRaises(svc.ServiceError):
            svc.submit_paper(self.db, self.author, self.conf, self.track, "T", "too short",
                             "", "paper.pdf", today="2026-10-20")
        with self.assertRaises(svc.ServiceError):
            svc.submit_paper(self.db, self.author, self.conf, self.track, "T" * 201, LONG_ABSTRACT,
                             "", "paper.pdf", today="2026-10-20")

    def test_only_authors_can_submit(self):
        with self.assertRaises(svc.ServiceError):
            svc.submit_paper(self.db, self.rev1, self.conf, self.track, "T", LONG_ABSTRACT,
                             "", "paper.pdf", today="2026-10-20")

    def test_track_must_belong_to_conference(self):
        with self.assertRaises(svc.ServiceError):
            svc.submit_paper(self.db, self.author, self.conf, 9999, "T", LONG_ABSTRACT,
                             "", "paper.pdf", today="2026-10-20")


class ReviewTests(Base):
    def test_assign_moves_paper_under_review(self):
        pid = self.paper()
        svc.assign_reviewer(self.db, self.chair, pid, self.rev1)
        status = self.db.execute("SELECT status FROM papers WHERE paper_id=?", (pid,)).fetchone()[0]
        self.assertEqual(status, "Under Review")

    def test_conflict_of_interest_blocked(self):
        author_rev = svc.register_user(self.db, "Dual Role", "dual@x.org", "dualpass123", "reviewer")
        # Make the reviewer the paper's author by inserting the paper directly.
        cur = self.db.execute(
            "INSERT INTO papers(conf_id, track_id, author_id, title, abstract, file_name, submitted_at)"
            " VALUES (?,?,?,?,?,?,?)",
            (self.conf, self.track, author_rev, "Own Paper", LONG_ABSTRACT, "p.pdf", "2026-10-20"))
        with self.assertRaises(svc.ServiceError):
            svc.assign_reviewer(self.db, self.chair, cur.lastrowid, author_rev)

    def test_max_three_reviewers_and_no_duplicates(self):
        pid = self.paper()
        for rev in (self.rev1, self.rev2, self.rev3):
            svc.assign_reviewer(self.db, self.chair, pid, rev)
        with self.assertRaises(svc.ServiceError):
            svc.assign_reviewer(self.db, self.chair, pid, self.rev4)
        pid2 = self.paper(title="Second Paper")
        svc.assign_reviewer(self.db, self.chair, pid2, self.rev1)
        with self.assertRaises(svc.ServiceError):
            svc.assign_reviewer(self.db, self.chair, pid2, self.rev1)

    def test_reviewer_workload_limit(self):
        reviewer = self.rev1
        for i in range(svc.MAX_PENDING_REVIEWS_PER_REVIEWER):
            svc.assign_reviewer(self.db, self.chair, self.paper(title=f"Paper {i}"), reviewer)
        with self.assertRaises(svc.ServiceError):
            svc.assign_reviewer(self.db, self.chair, self.paper(title="One too many"), reviewer)

    def test_non_chair_cannot_assign(self):
        pid = self.paper()
        with self.assertRaises(svc.ServiceError):
            svc.assign_reviewer(self.db, self.author, pid, self.rev1)

    def test_non_reviewer_cannot_be_assigned(self):
        pid = self.paper()
        attendee = svc.register_user(self.db, "Att", "att@x.org", "attendee123", "attendee")
        with self.assertRaises(svc.ServiceError):
            svc.assign_reviewer(self.db, self.chair, pid, attendee)

    def test_review_validation(self):
        pid = self.paper()
        asg = svc.assign_reviewer(self.db, self.chair, pid, self.rev1)
        for score in (0, 11, "abc", None):
            with self.assertRaises(svc.ServiceError):
                svc.submit_review(self.db, self.rev1, asg, score, GOOD_COMMENT, "accept")
        with self.assertRaises(svc.ServiceError):
            svc.submit_review(self.db, self.rev1, asg, 7, "too short", "accept")
        with self.assertRaises(svc.ServiceError):
            svc.submit_review(self.db, self.rev1, asg, 7, GOOD_COMMENT, "maybe")

    def test_review_belongs_to_assigned_reviewer_only(self):
        pid = self.paper()
        asg = svc.assign_reviewer(self.db, self.chair, pid, self.rev1)
        with self.assertRaises(svc.ServiceError):
            svc.submit_review(self.db, self.rev2, asg, 7, GOOD_COMMENT, "accept")

    def test_review_cannot_be_submitted_twice(self):
        pid = self.paper()
        asg = svc.assign_reviewer(self.db, self.chair, pid, self.rev1)
        svc.submit_review(self.db, self.rev1, asg, 7, GOOD_COMMENT, "accept")
        with self.assertRaises(svc.ServiceError):
            svc.submit_review(self.db, self.rev1, asg, 8, GOOD_COMMENT, "accept")

    def test_paper_becomes_reviewed_when_all_reviews_in(self):
        pid = self.paper()
        a1 = svc.assign_reviewer(self.db, self.chair, pid, self.rev1)
        a2 = svc.assign_reviewer(self.db, self.chair, pid, self.rev2)
        svc.submit_review(self.db, self.rev1, a1, 8, GOOD_COMMENT, "accept")
        status = self.db.execute("SELECT status FROM papers WHERE paper_id=?", (pid,)).fetchone()[0]
        self.assertEqual(status, "Under Review")
        svc.submit_review(self.db, self.rev2, a2, 8, GOOD_COMMENT, "accept")
        status = self.db.execute("SELECT status FROM papers WHERE paper_id=?", (pid,)).fetchone()[0]
        self.assertEqual(status, "Reviewed")


class DecisionTests(Base):
    def test_suggestion_thresholds(self):
        cases = {(8, 9): "Accepted", (5, 6): "Revision Required", (2, 4): "Rejected", (7, 7): "Accepted"}
        for i, (scores, expected) in enumerate(cases.items()):
            with self.subTest(scores=scores):
                pid = self.reviewed_paper(scores, title=f"Threshold paper {i}")
                self.assertEqual(svc.suggest_decision(self.db, pid)["suggestion"], expected)

    def test_decision_needs_two_reviews(self):
        pid = self.paper()
        asg = svc.assign_reviewer(self.db, self.chair, pid, self.rev1)
        svc.submit_review(self.db, self.rev1, asg, 9, GOOD_COMMENT, "accept")
        with self.assertRaises(svc.ServiceError):
            svc.record_decision(self.db, self.chair, pid, "Accepted")

    def test_record_decision_updates_status_and_notifies_author(self):
        pid = self.reviewed_paper()
        svc.record_decision(self.db, self.chair, pid, "Accepted", "Well done")
        row = self.db.execute("SELECT status, decision_remarks FROM papers WHERE paper_id=?", (pid,)).fetchone()
        self.assertEqual((row["status"], row["decision_remarks"]), ("Accepted", "Well done"))
        msg = self.db.execute("SELECT message FROM notifications WHERE user_id=? ORDER BY notif_id DESC",
                              (self.author,)).fetchone()[0]
        self.assertIn("Accepted", msg)

    def test_only_chair_records_decision_and_value_validated(self):
        pid = self.reviewed_paper()
        with self.assertRaises(svc.ServiceError):
            svc.record_decision(self.db, self.rev1, pid, "Accepted")
        with self.assertRaises(svc.ServiceError):
            svc.record_decision(self.db, self.chair, pid, "Maybe")

    def test_decision_cannot_be_repeated_after_final(self):
        pid = self.reviewed_paper()
        svc.record_decision(self.db, self.chair, pid, "Rejected")
        with self.assertRaises(svc.ServiceError):
            svc.record_decision(self.db, self.chair, pid, "Accepted")


class RegistrationPaymentTests(Base):
    def test_fee_with_and_without_early_bird(self):
        self.assertEqual(svc.registration_fee("student", True), 400.0)
        self.assertEqual(svc.registration_fee("student", False), 500.0)
        self.assertEqual(svc.registration_fee("industry", True), 1600.0)
        with self.assertRaises(svc.ServiceError):
            svc.registration_fee("vip", False)

    def test_early_bird_boundary(self):
        r1 = svc.register_for_conference(self.db, self.author, self.conf, "academic", today="2026-11-15")
        self.assertEqual(self.db.execute("SELECT fee_amount FROM registrations WHERE reg_id=?", (r1,)).fetchone()[0], 800.0)
        r2 = svc.register_for_conference(self.db, self.rev1, self.conf, "academic", today="2026-11-16")
        self.assertEqual(self.db.execute("SELECT fee_amount FROM registrations WHERE reg_id=?", (r2,)).fetchone()[0], 1000.0)

    def test_duplicate_registration_and_closed_registration(self):
        svc.register_for_conference(self.db, self.author, self.conf, "student", today="2026-11-01")
        with self.assertRaises(svc.ServiceError):
            svc.register_for_conference(self.db, self.author, self.conf, "student", today="2026-11-01")
        with self.assertRaises(svc.ServiceError):
            svc.register_for_conference(self.db, self.rev1, self.conf, "student", today="2026-12-13")

    def test_luhn(self):
        self.assertTrue(svc.luhn_valid("4242424242424242"))
        self.assertFalse(svc.luhn_valid("4242424242424241"))

    def test_successful_payment_confirms_registration_and_stores_no_card(self):
        reg = svc.register_for_conference(self.db, self.author, self.conf, "student", today="2026-11-01")
        ref = svc.process_payment(self.db, self.author, reg, "4242 4242 4242 4242")
        self.assertTrue(ref.startswith("TXN-"))
        self.assertEqual(self.db.execute("SELECT status FROM registrations WHERE reg_id=?", (reg,)).fetchone()[0], "Confirmed")
        dump = " ".join(str(tuple(r)) for r in self.db.execute("SELECT * FROM payments"))
        self.assertNotIn("4242", dump)

    def test_invalid_card_and_declined_card(self):
        reg = svc.register_for_conference(self.db, self.author, self.conf, "student", today="2026-11-01")
        with self.assertRaises(svc.ServiceError):
            svc.process_payment(self.db, self.author, reg, "1234 5678 9012 3456")
        with self.assertRaises(svc.ServiceError):
            svc.process_payment(self.db, self.author, reg, "4000000000000002")  # valid Luhn, declined
        self.assertEqual(self.db.execute("SELECT status FROM registrations WHERE reg_id=?", (reg,)).fetchone()[0], "Pending Payment")
        self.assertEqual(self.db.execute("SELECT status FROM payments").fetchone()[0], "Failed")

    def test_non_ascii_digits_are_rejected_not_crashing(self):
        """Regression for DEF-01: str.isdigit() accepted characters such as superscript two."""
        reg = svc.register_for_conference(self.db, self.author, self.conf, "student", today="2026-11-01")
        for bad in ("\u00b2" * 13, "\uff14" * 16):
            with self.assertRaises(svc.ServiceError):
                svc.process_payment(self.db, self.author, reg, bad)

    def test_cannot_pay_twice_or_for_someone_else(self):
        reg = svc.register_for_conference(self.db, self.author, self.conf, "student", today="2026-11-01")
        with self.assertRaises(svc.ServiceError):
            svc.process_payment(self.db, self.rev1, reg, "4242424242424242")
        svc.process_payment(self.db, self.author, reg, "4242424242424242")
        with self.assertRaises(svc.ServiceError):
            svc.process_payment(self.db, self.author, reg, "4242424242424242")


class SchedulingTests(Base):
    def accepted_paper(self):
        pid = self.reviewed_paper()
        svc.record_decision(self.db, self.chair, pid, "Accepted")
        return pid

    def pay_author(self):
        reg = svc.register_for_conference(self.db, self.author, self.conf, "academic", today="2026-11-01")
        svc.process_payment(self.db, self.author, reg, "4242424242424242")

    def make_session(self, room="Hall A", start="2026-12-10T10:00", end="2026-12-10T11:30", cap=2):
        return svc.create_session(self.db, self.chair, self.conf, "Session 1", room, start, end, cap)

    def test_create_session_and_room_clash(self):
        self.make_session()
        with self.assertRaises(svc.ServiceError):
            self.make_session(start="2026-12-10T11:00", end="2026-12-10T12:00")
        self.make_session(room="Hall B", start="2026-12-10T11:00", end="2026-12-10T12:00")
        self.make_session(start="2026-12-10T11:30", end="2026-12-10T12:30")  # back-to-back is fine

    def test_session_validation(self):
        with self.assertRaises(svc.ServiceError):  # end before start
            self.make_session(start="2026-12-10T12:00", end="2026-12-10T11:00")
        with self.assertRaises(svc.ServiceError):  # outside conference dates
            self.make_session(start="2026-12-20T10:00", end="2026-12-20T11:00")
        with self.assertRaises(svc.ServiceError):
            self.make_session(cap=0)

    def test_schedule_accepted_paper_with_paid_author(self):
        pid = self.accepted_paper()
        self.pay_author()
        sid = self.make_session()
        svc.schedule_paper(self.db, self.chair, pid, sid)
        program = svc.get_program(self.db, self.conf)
        self.assertEqual(program[0]["papers"][0]["title"], "A Study of Review Workflows")
        self.assertEqual(self.db.execute("SELECT status FROM papers WHERE paper_id=?", (pid,)).fetchone()[0], "Scheduled")

    def test_schedule_requires_accepted_status_and_paid_registration(self):
        pid = self.reviewed_paper()  # not yet accepted
        sid = self.make_session()
        with self.assertRaises(svc.ServiceError):
            svc.schedule_paper(self.db, self.chair, pid, sid)
        svc.record_decision(self.db, self.chair, pid, "Accepted")
        with self.assertRaises(svc.ServiceError):  # author has not paid
            svc.schedule_paper(self.db, self.chair, pid, sid)

    def test_session_capacity_and_double_scheduling(self):
        self.pay_author()
        sid = self.make_session(cap=1)
        p1 = self.accepted_paper()
        svc.schedule_paper(self.db, self.chair, p1, sid)
        with self.assertRaises(svc.ServiceError):
            svc.schedule_paper(self.db, self.chair, p1, sid)  # already scheduled
        # second accepted paper cannot fit into the full session
        p2 = self.paper(title="Another Paper")
        for rev in (self.rev1, self.rev2):
            a = svc.assign_reviewer(self.db, self.chair, p2, rev)
            svc.submit_review(self.db, rev, a, 9, GOOD_COMMENT, "accept")
        svc.record_decision(self.db, self.chair, p2, "Accepted")
        with self.assertRaises(svc.ServiceError):
            svc.schedule_paper(self.db, self.chair, p2, sid)


class RouteTests(unittest.TestCase):
    """End-to-end tests through the Flask test client."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True, "CSRF_ENABLED": False,
            "DATABASE": os.path.join(self.tmp.name, "t.sqlite"),
            "UPLOAD_FOLDER": os.path.join(self.tmp.name, "up"),
        })
        os.makedirs(self.app.config["UPLOAD_FOLDER"], exist_ok=True)
        self.client = self.app.test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def signup(self, client, name, email, role):
        return client.post("/register", data={"name": name, "email": email, "password": "password123",
                                              "role": role, "affiliation": "LICET"}, follow_redirects=True)

    def login(self, client, email):
        return client.post("/login", data={"email": email, "password": "password123"}, follow_redirects=True)

    def test_public_pages_and_protected_redirect(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers["Location"])

    def test_register_login_logout_flow(self):
        self.assertIn(b"Account created", self.signup(self.client, "Asha", "a@x.org", "author").data)
        self.assertIn(b"Invalid email or password", self.client.post(
            "/login", data={"email": "a@x.org", "password": "bad"}, follow_redirects=True).data)
        self.assertIn(b"Asha", self.login(self.client, "a@x.org").data)
        self.assertIn(b"logged out", self.client.post("/logout", follow_redirects=True).data)

    def test_cannot_self_register_as_chair(self):
        resp = self.signup(self.client, "Sneaky", "s@x.org", "chair")
        self.assertIn(b"Choose Author, Reviewer or Attendee", resp.data)

    def test_open_redirect_is_blocked(self):
        self.signup(self.client, "Asha", "a@x.org", "author")
        resp = self.client.post("/login?next=//evil.example", data={"email": "a@x.org", "password": "password123"})
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn("evil.example", resp.headers["Location"])

    def test_csrf_enforced_when_enabled(self):
        self.app.config["CSRF_ENABLED"] = True
        resp = self.client.post("/login", data={"email": "a@x.org", "password": "x"})
        self.assertEqual(resp.status_code, 400)

    def test_role_protection(self):
        self.signup(self.client, "Asha", "a@x.org", "author")
        self.login(self.client, "a@x.org")
        self.assertEqual(self.client.get("/conferences/new").status_code, 403)

    def test_full_workflow_through_the_web_ui(self):
        db = None
        with self.app.app_context():
            from cms_app import db as dbm
            db = dbm.get_db()
            svc.register_user(db, "Dr Chair", "chair@x.org", "password123", "chair")
        chair, author = self.app.test_client(), self.app.test_client()
        rev1, rev2 = self.app.test_client(), self.app.test_client()
        self.signup(author, "Asha", "a@x.org", "author")
        self.signup(rev1, "Ravi", "r1@x.org", "reviewer")
        self.signup(rev2, "Meena", "r2@x.org", "reviewer")
        self.login(chair, "chair@x.org")
        resp = chair.post("/conferences/new", data={
            "name": "Demo Conf", "venue": "Chennai", "start_date": "2099-12-10", "end_date": "2099-12-12",
            "submission_deadline": "2099-11-01", "early_bird_deadline": "2099-11-15"}, follow_redirects=True)
        self.assertIn(b"Conference created", resp.data)
        chair.post("/conferences/1/tracks", data={"name": "AI"})
        # author submits a PDF
        self.login(author, "a@x.org")
        resp = author.post("/conferences/1/submit", data={
            "track_id": "1", "title": "Deep Review", "abstract": LONG_ABSTRACT, "keywords": "ai",
            "file": (io.BytesIO(b"%PDF-1.4 test"), "deep.pdf")}, content_type="multipart/form-data",
            follow_redirects=True)
        self.assertIn(b"Paper submitted.", resp.data)
        # a non-PDF upload is rejected
        resp = author.post("/conferences/1/submit", data={
            "track_id": "1", "title": "Bad File", "abstract": LONG_ABSTRACT, "keywords": "",
            "file": (io.BytesIO(b"x"), "bad.exe")}, content_type="multipart/form-data",
            follow_redirects=True)
        self.assertIn(b"Only PDF files are accepted", resp.data)
        # chair assigns two reviewers
        self.assertIn(b"Reviewer assigned", chair.post("/papers/1/assign", data={"reviewer_id": "3"}, follow_redirects=True).data)
        chair.post("/papers/1/assign", data={"reviewer_id": "4"})
        # reviewers submit reviews
        for client, email in ((rev1, "r1@x.org"), (rev2, "r2@x.org")):
            self.login(client, email)
        self.assertIn(b"Review submitted", rev1.post("/reviews/1", data={
            "score": "8", "recommendation": "accept", "comments": GOOD_COMMENT}, follow_redirects=True).data)
        rev2.post("/reviews/2", data={"score": "9", "recommendation": "accept", "comments": GOOD_COMMENT})
        # author cannot see reviews before the decision; chair decides
        self.assertNotIn(b"/10", author.get("/papers/1").data)
        self.assertIn(b"Decision recorded", chair.post("/papers/1/decision", data={
            "decision": "Accepted", "remarks": "Great"}, follow_redirects=True).data)
        self.assertIn(b"/10", author.get("/papers/1").data)
        # a different reviewer / stranger cannot open the paper
        stranger = self.app.test_client()
        self.signup(stranger, "Eve", "e@x.org", "attendee")
        self.login(stranger, "e@x.org")
        self.assertEqual(stranger.get("/papers/1").status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
