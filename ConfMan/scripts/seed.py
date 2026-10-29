#!/usr/bin/env python3
"""Database seeding and reset script for ConfMan."""
import os
import shutil
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cms_app import create_app, db as dbm
from demo import load_demo


def main():
    app = create_app()
    if "--reset" in sys.argv:
        shutil.rmtree(app.instance_path, ignore_errors=True)
        # Also clean up custom db directory if configured
        db_path = app.config.get("DATABASE")
        if db_path and os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass
        app = create_app()

    with app.app_context():
        if dbm.get_db().execute("SELECT 1 FROM users LIMIT 1").fetchone():
            print("The database already has data. Run: python scripts/seed.py --reset")
            return
        load_demo(app)
        print("Demo data loaded successfully.")
        print("Accounts: admin@demo.org, chair@demo.org, reviewer1@demo.org, author@demo.org, attendee@demo.org")
        print("Password for all demo accounts: Demo@1234")


if __name__ == "__main__":
    main()
