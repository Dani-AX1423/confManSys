"""Vercel serverless function entry point for ConfMan Flask application."""
import os
import sys

# Ensure the project root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cms_app import create_app

# Instantiate Flask application.
# In Vercel serverless functions, VERCEL=1 is automatically set,
# directing ephemeral storage to /tmp and auto-seeding demo data if empty.
app = create_app()
