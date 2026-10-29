"""Vercel serverless function entry point for ConfMan Flask application.

Handles deployments whether Vercel builds from repository root or project folder.
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFMAN_DIR = os.path.join(BASE_DIR, "ConfMan")

# Add ConfMan directory and base directory to sys.path
for path in (CONFMAN_DIR, BASE_DIR):
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)

from cms_app import create_app

app = create_app()
