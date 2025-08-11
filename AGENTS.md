# AGENTS.md - Guide for AI Agents

This document provides guidance for AI agents working on the StratLogic Scraping System repository.

## 🎯 Project Overview

The StratLogic Scraping System is a comprehensive web scraping platform designed to collect, process, and store data from various sources, including web content, academic papers, and government documents. The system uses a microservices-based architecture with a Python backend, a React/Next.js frontend, and various storage and data processing technologies.

For a detailed project overview, system architecture, and data flow, please refer to the `README.md` file.

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, FastAPI
- **Frontend**: React/Next.js, TypeScript
- **Storage**: MinIO, PostgreSQL, Redis
- **Web Scraping**: Playwright, BeautifulSoup4, Scrapy
- **AI/ML**: OpenRouter, Google Gemini, LangChain
- **DevOps**: Docker, Celery

## 🚀 Getting Started

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd stratlogic-scrape
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables**:
    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

5.  **Start services**:
    ```bash
    docker-compose up -d
    ```

6.  **Run migrations**:
    ```bash
    python scripts/migrate.py
    ```

7.  **Start the application**:
    ```bash
    python src/main.py
    ```

## 📁 Project Structure

The project follows a standard structure for a web application with separate backend and frontend directories.

```
stratlogic-scrape/
├── src/
│   ├── scrapers/
│   ├── storage/
│   ├── api/
│   ├── core/
│   └── services/
├── frontend/
├── tests/
├── docs/
├── docker/
├── scripts/
└── todo/
```

-   `src/`: Contains the Python backend code.
-   `frontend/`: Contains the React/Next.js frontend code.
-   `tests/`: Contains tests for the backend.
-   `docs/`: Contains project documentation.
-   `todo/`: Contains the project's task list and roadmap.

## 📝 Development Guidelines

-   **Coding Style**: Follow standard Python conventions (PEP 8). The project uses Python 3.11+.
-   **Testing**: All new features and bug fixes should be accompanied by tests. The tests are located in the `tests/` directory. To run the tests, you will likely use `pytest`.
-   **Dependencies**: All Python dependencies are managed in `requirements.txt`.
-   **Task Management**: The project's roadmap and task list are managed in the `todo/` directory. The main file to consult is `todo/00-master-todo.md`. Before starting any work, please consult this file to understand the current priorities and task dependencies.

## 🤝 Contributing

1.  Fork the repository.
2.  Create a feature branch for your changes.
3.  Make your changes, including adding tests.
4.  Ensure all tests pass.
5.  Submit a pull request with a clear description of your changes.

## 📄 Key Files to Read

-   `README.md`: For a high-level understanding of the project.
-   `todo/00-master-todo.md`: For the project's roadmap, tasks, and priorities.

## ⚠️ Known Issues

### Docker Permissions in Sandbox Environment

When running `docker compose` or other Docker commands, you may encounter a "permission denied" error related to the Docker daemon socket (`/var/run/docker.sock`). This is a limitation of some sandboxed execution environments and cannot be resolved by the agent.

**Workaround:**
If you encounter this issue, you will not be able to build or run the Docker containers to verify the full application stack. In this case:
1.  Complete all other setup steps: creating files, populating them with code, and installing dependencies.
2.  Instead of running `docker compose up` for verification, ensure that all project files and configurations are correct.
3.  When submitting your work, note that the final verification step was blocked by the environment's Docker permissions.
