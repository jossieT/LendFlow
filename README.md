# Lendflow: Production-Grade Cash Lending Application

A modular, secure, and production-ready cash lending application built with Django and Django REST Framework.

## Architectual Overview

This project follows a **Senior fintech architect's** approach to modularity and security:

- **Apps Directory**: All domain logic resides in the `apps/` directory to maintain a clean root.
- **Service Layer**: Business logic is decoupled from Django views and encapsulated in dedicated services (e.g., `LoanService`, `LedgerService`, `AuthService`).
- **Modular Settings**: Configuration is split into `base`, `local` (development), and `production` environments.
- **Security-First**: Integrated `django-environ` for secret management and pre-configured security headers for production deployment.

## Tech Stack

- **Backend**: Django 4.2+
- **API**: Django REST Framework
- **Environment**: `django-environ`
- **Frontend**: HTMX (integrated via templates)
- **Database**: SQLite (Local Dev) / PostgreSQL ready (Production)

## Getting Started

### 1. Prerequisites

- Python 3.10+
- Virtualenv

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd lendflow

# Create and activate virtual environment
python -m venv venv
source venv/bin/scripts/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup

Create a `.env` file in the root directory:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
```

### 4. Running the App

```bash
python manage.py migrate
python manage.py runserver
```

## Project Structure

```text
lendflow/
├── apps/               # Domain applications (accounts, core)
│   ├── core/           # Lending and Transaction logic
│   │   └── services/   # Business logic layer
│   └── accounts/       # User IAM and Auth profiles
├── config/             # Project configuration
│   └── settings/       # Modular settings (base, local, production)
├── static/             # Static assets
├── templates/          # Global templates
└── manage.py           # Entry point
```

## Security & Auditability

- **Lifecycle Integrity**: Loan states are managed via serialized services.
- **Audit Ready**: All financial events are recorded as immutable transactions.
- **Production Hardened**: HSTS, SSL Redirection, and CORS headers are pre-configured in `production.py`.
