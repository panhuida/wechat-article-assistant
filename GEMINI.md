# Gemini CLI Project Mandates: WeChat Article Assistant

This document defines the foundational mandates, technical standards, and operational workflows for Gemini CLI within the `wechat-article-assistant` project. These instructions take absolute precedence over general defaults.

## 🎯 Project Core Objectives
A Python-based assistant for managing WeChat Public Accounts and downloading articles using Playwright for automation and Flask for the web interface.
Key features include:
- **Web Interface:** Flask-based UI for managing accounts and articles.
- **CLI Interface:** Command-line tools for headless operation.
- **Automation:** Playwright for WeChat login (QR code) and article scraping.
- **Data Management:** SQLAlchemy ORM for storage (SQLite local, PostgreSQL production-ready).

## 🛠️ Technical Stack & Tooling
- **Language:** Python 3.12+ (Strictly adhere to Python 3.12 features).
- **Web Framework:** Flask 3.0+.
- **Database:** SQLAlchemy 2.0+ (PostgreSQL for production/migration, SQLite for local).
- **Browser Automation:** Playwright 1.40+.
- **Package Manager:** `uv` (Prefer `uv run`, `uv sync`, `uv add` over `pip`).
- **Linting/Formatting:** `ruff` (Mandatory).
- **Type Checking:** `mypy` and `pyright` (Basic mode).
- **Testing:** `pytest` (unit, integration, contract, e2e).

## 📜 Coding Standards & Conventions
- **Language for Documentation:** **All comments and docstrings MUST be in Chinese.**
- **Docstrings:** Required for all classes and functions. Follow the format:
  ```python
  def function_name(param: type) -> return_type:
      """
      简短描述

      Args:
          param: 参数说明

      Returns:
          返回值说明
      """
  ```
- **Path Handling:** Use `pathlib` instead of `os.path` (Enforced by Ruff `PTH`).
- **Type Hints:** Use static type hints for all function signatures and variable declarations where possible.
- **Naming:** Follow PEP 8 (snake_case for functions/variables, PascalCase for classes).
- **Imports:** Organized by Ruff (isort). First-party imports from `wechat_article_assistant`.

## 🏗️ Architectural Patterns
- **Routes (`src/.../routes/`):** Handle HTTP requests and Blueprint definitions.
  - **Responsibility:** Parameter parsing, service invocation, response formatting.
  - **Restriction:** NO business logic in routes. Delegate to Services.
- **Services (`src/.../services/`):** Contain core business logic.
  - **Responsibility:** Database transactions, complex processing, external API calls.
- **Models (`src/.../models.py`):** SQLAlchemy ORM definitions.
- **Browser (`src/.../browser/`):** Playwright-specific automation logic and session management.
- **Utils (`src/.../utils/`):** Generic helper functions (logger, file_helper, etc.).

## 🧪 Testing & Validation Mandates
- **Test-Driven Fixes:** ALWAYS reproduce a reported bug with a new test case in `tests/` before applying a fix.
- **Testing Strategy:**
    - `unit`: Fast, isolated tests.
    - `integration`: Database and service interaction tests.
    - `contract`: Fixture-driven tests for external data/responses.
    - `e2e`: Full system flow (exclude `tests/e2e/manual` from CI).
- **Coverage:** Maintain at least **60%** code coverage.
- **Validation Command:** Before completing any task, run:
  ```bash
  uv run ruff check . --fix
  uv run ruff format .
  uv run pytest
  ```

## 🗄️ Database Mandates
- **PostgreSQL Consistency:** When generating SQL or using database tools, ALWAYS use the full table name format: `DATABASE_NAME.SCHEMA_NAME.TABLE_NAME` (Default schema is `public`).
- **Migrations:** Currently manual. When modifying `models.py`, inform the user that database recreation or manual migration is required.
- **Table Names:** `wechat_list` (Accounts), `wechat_article_list` (Articles).

## 🚀 Workflow Mandates
1. **Dependency Management:** Use `uv` exclusively. If a new library is needed, use `uv add`.
2. **Environment:** Ensure `.env` is configured. Refer to `.env.example`.
3. **Execution:**
   - Web: `uv run python run.py`
   - CLI: `uv run python wechat-cli.py`
4. **Clean Code:** Use `ruff` to auto-fix linting issues and format code before every commit.

## ⚠️ Security & Safety
- **Credentials:** Never hardcode `SECRET_KEY` or `DATABASE_URL`. Use `.env`.
- **Session Data:** Protect `data/wechat_session.json` and other sensitive session files.
- **Path Traversal:** Validate all user-provided URLs and file paths using `utils/validators.py`.
