# Contributing to ConfMan

Thank you for your interest in contributing to **ConfMan**! We welcome bug reports, feature proposals, and pull requests.

---

## Code of Conduct

Please treat all community members with respect, kindness, and professionalism.

---

## Development Workflow

1. **Fork the Repository**:
   Fork the repository on GitHub and clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/confManSys.git
   cd confManSys/ConfMan
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

4. **Run the Local Server**:
   ```bash
   python run.py
   ```

5. **Run the Automated Tests**:
   Ensure all 67 tests continue to pass before committing:
   ```bash
   python -m unittest discover -s tests -v
   ```

6. **Run Deployment Verification**:
   ```bash
   python scripts/verify_deployment.py
   ```

---

## Architectural Guidelines

- **Maintain Layer Separation**:
  - Keep route controllers and HTTP request/session handling inside `cms_app/__init__.py`.
  - Place domain logic, validation, and database operations in `cms_app/services.py`. Services should remain framework-agnostic and avoid importing Flask globals (`request`, `session`).
  - Read-models and dashboard analytics belong in `cms_app/insights.py`.
- **Database Migrations**:
  - If adding tables or columns, update `cms_app/schema.sql` cleanly with appropriate foreign keys and constraints.
- **Security**:
  - Never disable CSRF protection in production views.
  - Never log credit card numbers or store raw passwords. Passwords must always be hashed.

---

## Submitting Pull Requests

1. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat(reviewer): add keyword filtering for volunteer queue"
   ```
2. Push your branch to GitHub:
   ```bash
   git push origin feature/my-new-feature
   ```
3. Open a Pull Request against the `main` branch. Describe what changed, why, and reference any relevant issue numbers.
