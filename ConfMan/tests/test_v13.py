"""Tests for v1.3: admin role, reviewer volunteering, auto-assign and the role dashboards."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from test_cms import Base  # noqa: E402
from cms_app import create_app, services as svc, insights  # noqa: E402
from demo import load_demo  # noqa: E402


class AdminServiceTests(Base):
    def setUp(self):
        super().setUp()
        self.admin = svc.register_user(self.db, "Anita Admin", "admin@x.org", "adminpass1", "admin")

    def test_admin_can_change_role_and_deactivate(self):
        svc.set_user_role(self.db, self.admin, self.author, "reviewer")
        self.assertEqual(svc._user(self.db, self.author)["role"], "reviewer")
        svc.set_user_active(self.db, self.admin, self.rev4, False)
        self.assertEqual(svc._user(self.db, self.rev4)["is_active"], 0)

    def test_non_admin_is_refused(self):
        with self.assertRaises(svc.ServiceError):
            svc.set_user_role(self.db, self.chair, self.author, "chair")
        with self.assertRaises(svc.ServiceError):
            svc.set_user_active(self.db, self.author, self.rev1, False)

    def test_admin_cannot_lock_themselves_out(self):
        with self.assertRaises(svc.ServiceError):
            svc.set_user_role(self.db, self.admin, self.admin, "author")
        with self.assertRaises(svc.ServiceError):
            svc.set_user_active(self.db, self.admin, self.admin, False)

    def test_admin_can_reassign_chair(self):
        other = svc.register_user(self.db, "Second Chair", "c2@x.org", "chairpass2", "chair")
        svc.reassign_chair(self.db, self.admin, self.conf, other)
        row = self.db.execute("SELECT chair_id FROM conferences WHERE conf_id=?", (self.conf,)).fetchone()
        self.assertEqual(row["chair_id"], other)
        with self.assertRaises(svc.ServiceError):
            svc.reassign_chair(self.db, self.admin, self.conf, self.author)

    def test_admin_actions_are_logged(self):
        svc.set_user_role(self.db, self.admin, self.author, "attendee")
        n = self.db.execute("SELECT COUNT(*) FROM activity WHERE action='Role changed'").fetchone()[0]
        self.assertEqual(n, 1)


class AssignmentTests(Base):
    def test_reviewer_can_volunteer_and_chair_is_told(self):
        pid = self.paper()
        svc.volunteer_to_review(self.db, self.rev1, pid)
        self.assertEqual(svc.pending_reviews(self.db, self.rev1), 1)
        msgs = self.db.execute("SELECT message FROM notifications WHERE user_id=?", (self.chair,)).fetchall()
        self.assertTrue(any("volunteered" in m["message"] for m in msgs))

    def test_cannot_volunteer_twice_or_for_own_paper(self):
        pid = self.paper()
        svc.volunteer_to_review(self.db, self.rev1, pid)
        with self.assertRaises(svc.ServiceError):
            svc.volunteer_to_review(self.db, self.rev1, pid)
        svc.set_user_role  # author is not a reviewer so also refused
        with self.assertRaises(svc.ServiceError):
            svc.volunteer_to_review(self.db, self.author, pid)

    def test_volunteering_stops_at_three_reviewers(self):
        pid = self.paper()
        for r in (self.rev1, self.rev2, self.rev3):
            svc.volunteer_to_review(self.db, r, pid)
        with self.assertRaises(svc.ServiceError):
            svc.volunteer_to_review(self.db, self.rev4, pid)

    def test_auto_assign_fills_paper_and_matches_expertise(self):
        self.db.execute("UPDATE users SET expertise='review workflow' WHERE user_id=?", (self.rev3,))
        pid = self.paper()
        ranked = svc.ranked_reviewers(self.db, pid)
        self.assertEqual(ranked[0]["user"]["user_id"], self.rev3)
        added = svc.auto_assign(self.db, self.chair, pid)
        self.assertEqual(len(added), 3)
        self.assertIn("Kiran Reviewer", added)

    def test_auto_assign_conference_covers_all_short_papers(self):
        self.paper(title="First paper title here")
        self.paper(title="Second paper title here")
        svc.auto_assign_conference(self.db, self.chair, self.conf)
        short = self.db.execute(
            "SELECT COUNT(*) FROM papers p WHERE (SELECT COUNT(*) FROM review_assignments ra"
            " WHERE ra.paper_id=p.paper_id) < 2").fetchone()[0]
        self.assertEqual(short, 0)

    def test_new_reviewer_sees_papers_open_for_review(self):
        self.paper()
        jeni = svc.register_user(self.db, "Jeni", "jeni@x.org", "jenipass12", "reviewer")
        user = svc._user(self.db, jeni)
        self.assertEqual(len(insights.open_papers(self.db, user)), 1)


class DemoAndPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.app = create_app({"TESTING": True, "CSRF_ENABLED": False,
                              "DATABASE": os.path.join(cls.tmp.name, "d.sqlite"),
                              "UPLOAD_FOLDER": os.path.join(cls.tmp.name, "up")})
        os.makedirs(cls.app.config["UPLOAD_FOLDER"], exist_ok=True)
        with cls.app.app_context():
            load_demo(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def client(self, email):
        c = self.app.test_client()
        c.post("/login", data={"email": email, "password": "Demo@1234"})
        return c

    def test_demo_data_is_rich(self):
        with self.app.app_context():
            from cms_app import db as dbm
            d = dbm.get_db()
            self.assertGreaterEqual(d.execute("SELECT COUNT(*) FROM papers").fetchone()[0], 25)
            self.assertGreaterEqual(d.execute("SELECT COUNT(*) FROM conferences").fetchone()[0], 3)
            self.assertEqual(d.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0], 1)

    def test_every_role_dashboard_loads(self):
        for email in ("admin@demo.org", "chair@demo.org", "reviewer1@demo.org",
                      "author@demo.org", "attendee@demo.org"):
            r = self.client(email).get("/dashboard")
            self.assertEqual(r.status_code, 200, email)
            self.assertIn(b"kpi-num", r.data)

    def test_admin_pages_and_access_control(self):
        admin = self.client("admin@demo.org")
        for url in ("/admin/users", "/admin/activity", "/analytics", "/papers"):
            self.assertEqual(admin.get(url).status_code, 200, url)
        self.assertEqual(self.client("author@demo.org").get("/admin/users").status_code, 403)
        self.assertEqual(self.client("chair@demo.org").get("/admin/activity").status_code, 403)

    def test_reviewer_has_assigned_and_open_papers(self):
        rev = self.client("reviewer1@demo.org")
        self.assertIn(b"Write review", rev.get("/papers").data)
        self.assertEqual(rev.get("/papers?tab=open").status_code, 200)

    def test_new_reviewer_can_volunteer_through_the_web(self):
        c = self.app.test_client()
        c.post("/register", data={"name": "Jeni", "email": "jeni@x.org", "password": "password123",
                                  "role": "reviewer", "affiliation": "LICET", "expertise": "networks"})
        c.post("/login", data={"email": "jeni@x.org", "password": "password123"})
        page = c.get("/papers?tab=open")
        self.assertEqual(page.status_code, 200)
        with self.app.app_context():
            from cms_app import db as dbm
            pid = insights.open_papers(dbm.get_db(), dbm.get_db().execute(
                "SELECT * FROM users WHERE email='jeni@x.org'").fetchone())[0]["paper_id"]
        r = c.post(f"/papers/{pid}/volunteer", follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Write review", c.get("/papers").data)

    def test_login_and_register_are_full_width(self):
        import re
        with open(os.path.join(os.path.dirname(__file__), "..", "cms_app", "static", "style.css")) as fh:
            css = fh.read()
        rule = re.search(r"\n\.auth\{([^}]*)\}", css).group(1)
        self.assertNotIn("max-width", rule)
        self.assertIn("min-height:100vh", rule.replace(" ", ""))
        for url in ("/login", "/register"):
            self.assertIn(b"auth-art", self.app.test_client().get(url).data)


if __name__ == "__main__":
    unittest.main()
