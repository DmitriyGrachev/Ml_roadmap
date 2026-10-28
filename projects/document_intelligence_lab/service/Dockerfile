# Configuration only: build/run NOT_RUN. Tags checked in official docs 2026-10-11.
FROM ghcr.io/astral-sh/uv:0.12.17 AS uv
FROM python:3.12.15-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PYTHONPATH=/app/src:/app \
    PATH="/opt/venv/bin:${PATH}" \
    ROADMAP_SERVICE_CONFIG=/config/service.json

COPY --from=uv /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
# Reuse root CPU lock. No training/tracking/dev groups and no editable project.
RUN uv sync --frozen --no-default-groups --no-install-project \
    && useradd --create-home --uid 10001 appuser

# Copy an exact runtime allowlist; no teacher/student output or private config.
# A namespace package for the checksum helper avoids test-only roadmap_tools.__init__.
COPY src/roadmap_tools/experiment_evidence.py /app/src/roadmap_tools/experiment_evidence.py
COPY projects/document_intelligence_lab/__init__.py projects/document_intelligence_lab/artifacts.py projects/document_intelligence_lab/contracts.py /app/projects/document_intelligence_lab/
COPY projects/document_intelligence_lab/service/__init__.py projects/document_intelligence_lab/service/app.py /app/projects/document_intelligence_lab/service/

USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=2).close()"]
CMD ["python", "-m", "uvicorn", "projects.document_intelligence_lab.service.app:factory", "--factory", "--host", "0.0.0.0", "--port", "8000"]
