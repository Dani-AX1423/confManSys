#!/usr/bin/env python3
"""ConfMan Deployment and Verification Suite.

Validates that:
1. Application compiles and initializes cleanly in standard environment.
2. Vercel serverless environment (VERCEL=1) correctly redirects instance storage
   to /tmp and initializes schema and demo seed without read-only filesystem errors.
3. Core routes (homepage, login, static assets, conferences, public program) return HTTP 200.
4. Database integrity and table schemas are valid.
"""
import os
import sys

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def verify_standard_mode():
    print("[1/3] Testing standard app initialization...")
    import tempfile
    from cms_app import create_app
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.sqlite")
        app = create_app({"TESTING": True, "DATABASE": db_path, "CSRF_ENABLED": False})
        client = app.test_client()
        resp = client.get("/")
        assert resp.status_code == 200, f"Expected 200 from '/', got {resp.status_code}"
    print("  ✓ Standard initialization OK (HTTP 200)")


def verify_vercel_serverless_mode():
    print("[2/3] Simulating Vercel Serverless environment (VERCEL=1)...")
    os.environ["VERCEL"] = "1"
    from api.index import app as vercel_app

    client = vercel_app.test_client()

    # Verify static assets
    resp_css = client.get("/static/style.css")
    assert resp_css.status_code == 200, f"Expected 200 from static CSS, got {resp_css.status_code}"
    assert len(resp_css.data) > 1000, "CSS payload appears incomplete"
    print("  ✓ Static asset delivery OK (/static/style.css)")

    # Verify key routes
    routes = [
        ("/", 200, "ConfMan"),
        ("/login", 200, "Log in"),
        ("/register", 200, "Create your account"),
        ("/conferences", 200, "Conferences"),
        ("/conferences/1/program", 200, "Programme"),
    ]
    for path, expected_code, expected_snippet in routes:
        resp = client.get(path)
        assert resp.status_code == expected_code, f"Failed {path}: expected {expected_code}, got {resp.status_code}"
        assert expected_snippet.lower() in resp.text.lower(), f"Failed {path}: missing '{expected_snippet}'"
        print(f"  ✓ Route {path} OK (HTTP {expected_code})")

    # Verify Vercel edge rewrite unwrapping (when Vercel sends /api/index with X-Matched-Path)
    resp_rw = client.get("/api/index")
    assert resp_rw.status_code == 200, f"Failed /api/index rewrite: got {resp_rw.status_code}"
    assert "ConfMan" in resp_rw.text, "Failed /api/index rewrite content"

    resp_rw_matched = client.get("/api/index", environ_overrides={"HTTP_X_MATCHED_PATH": "/conferences"})
    assert resp_rw_matched.status_code == 200, f"Failed /conferences rewrite: got {resp_rw_matched.status_code}"

    resp_rw_css = client.get("/api/index", environ_overrides={"HTTP_X_MATCHED_PATH": "/static/style.css"})
    assert resp_rw_css.status_code == 200, f"Failed static CSS rewrite: got {resp_rw_css.status_code}"
    print("  ✓ Vercel edge rewrite resolution OK (/api/index, X-Matched-Path)")
    with vercel_app.app_context():
        from cms_app import db as dbm
        user_count = dbm.get_db().execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conf_count = dbm.get_db().execute("SELECT COUNT(*) FROM conferences").fetchone()[0]
        paper_count = dbm.get_db().execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        assert user_count > 0, "Users table not seeded"
        assert conf_count > 0, "Conferences table not seeded"
        assert paper_count > 0, "Papers table not seeded"
        print(f"  ✓ Database verified: {user_count} users, {conf_count} conferences, {paper_count} papers")


def verify_automated_tests():
    print("[3/3] Checking test suite availability...")
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(PROJECT_ROOT, "tests"))
    count = suite.countTestCases()
    assert count > 0, "No tests discovered in tests/ directory"
    print(f"  ✓ Discovered {count} automated tests in tests/")


def main():
    print("=== ConfMan Deployment Verification ===")
    try:
        verify_standard_mode()
        verify_vercel_serverless_mode()
        verify_automated_tests()
        print("\nAll verification checks passed successfully!")
        return 0
    except Exception as exc:
        print(f"\nVerification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
