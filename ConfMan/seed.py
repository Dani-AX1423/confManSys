"""Load the rich demo data.

    python seed.py            load demo data into an empty database
    python seed.py --reset    delete the database and uploads first, then load
Demo accounts all use the password Demo@1234.
"""
import os
import shutil
import sys

from cms_app import create_app, db as dbm
from demo import load_demo


def main():
    app = create_app()
    if "--reset" in sys.argv:
        shutil.rmtree(app.instance_path, ignore_errors=True)
        app = create_app()
    with app.app_context():
        if dbm.get_db().execute("SELECT 1 FROM users LIMIT 1").fetchone():
            print("The database already has data. Run:  python seed.py --reset")
            return
        load_demo(app)
        print("Demo data loaded. Log in with admin@demo.org, chair@demo.org, reviewer1@demo.org, "
              "author@demo.org or attendee@demo.org (password Demo@1234).")


if __name__ == "__main__":
    main()
