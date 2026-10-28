# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
# Optional public CA bundle mount for managed proxy environments; never persisted in image.
RUN --mount=type=secret,id=proxy_ca \
    if [ -s /run/secrets/proxy_ca ]; then \
      pip install --no-cache-dir --cert /run/secrets/proxy_ca -r requirements.txt; \
    else pip install --no-cache-dir -r requirements.txt; fi
COPY . .
RUN useradd --uid 10001 --create-home turnolab && \
    mkdir -p .data artifacts reports && chown -R turnolab:turnolab /app
USER turnolab
ENV OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONUNBUFFERED=1
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/ready',timeout=3)"
CMD ["python", "scripts/entrypoint.py"]
