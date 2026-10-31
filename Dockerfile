FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv
COPY pyproject.toml README.md ./
COPY app ./app
COPY evals ./evals
COPY samples ./samples
RUN pip install --no-cache-dir -e ".[all]" \
    && useradd --create-home rag \
    && mkdir -p /data /srv/app/assets/files && chown -R rag /data /srv/app/assets

USER rag
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
