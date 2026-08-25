#  Government School Management System (Nepal CEHRD Standard)

[![Django Version](https://img.shields.io/badge/Django-5.2+-092E20?style=flat&logo=django)](https://djangoproject.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python)](https://python.org)
[![Security Audited](https://img.shields.io/badge/Audit_Trail-django--simple--history-blue)](#)

A government-grade, high-security School Management System tailored for public schools in Nepal. Designed for CEHRD/IEMIS compliance, CDC grading rules, and strict auditability.

---

## Security Architecture Highlights
- **Role-Based Access Control (RBAC):** Object-level permissions for teachers and administrators.
- **Immutable Audit Logging:** Full record-keeping of mark edits and profile changes.
- **Brute-Force Defense:** Automated IP throttling and failed-login lockouts.
- **Local Date Logic:** Pure Gregorian storage with seamless BS (Bikram Sambat) rendering.

---

## Quickstart (Local Development)

### 1. Prerequisites
- Python 3.12+
- Git

### 2. Installation
```bash
git clone [https://github.com/your-username/gov-school-management-nepal.git](https://github.com/your-username/gov-school-management-nepal.git)
cd gov-school-management-nepal

# Environment Setup
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure Secrets
cp .env.example .env

# Database Migrations
python manage.py migrate
python manage.py runserver

📁 Repository Layout
Plaintext
├── config/              # Central project settings & WSGI/ASGI
├── apps/                # Modular Django applications (Users, Academics, IEMIS)
├── templates/           # Global HTML templates
├── static/              # CSS, JS, and static assets
├── .env.example         # Template for environment variables
├── .gitignore           # Git exclusion rules
└── manage.py            # Django CLI utility