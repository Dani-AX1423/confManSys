"""Root Flask entry point for Vercel auto-detection and local runners."""
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFMAN_DIR = os.path.join(BASE_DIR, "ConfMan")

for path in (CONFMAN_DIR, BASE_DIR):
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)

from cms_app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
