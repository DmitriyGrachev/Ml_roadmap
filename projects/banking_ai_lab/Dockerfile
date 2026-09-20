FROM ghcr.io/astral-sh/uv:0.8.22-python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY projects/banking_ai_lab/banking_ai_lab projects/banking_ai_lab/banking_ai_lab

RUN useradd --create-home --uid 10001 banking \
    && chown -R banking:banking /app
USER banking

EXPOSE 8000
CMD ["uv", "run", "--no-sync", "uvicorn", "banking_ai_lab.app:app", "--app-dir", "projects/banking_ai_lab", "--host", "0.0.0.0", "--port", "8000"]
