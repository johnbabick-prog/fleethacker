# Demo deployment candidate. Iron Bank requires rebasing through its own pipeline.
ARG BASE_IMAGE=python:3.13-slim@sha256:ae14d4ce8771606477a81446e7ef429edd6762305fc50c84507c1041fa8285d1
FROM ${BASE_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HATCH_DATA=/data
WORKDIR /app
COPY requirements.lock /app/requirements.lock
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.lock \
    && mkdir /data && chown 10001:10001 /data
COPY hatch /app/hatch
COPY config /app/config
COPY static /app/static
USER 10001:10001
EXPOSE 8765
HEALTHCHECK --interval=15s --timeout=3s --start-period=15s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/healthz', timeout=2)"]
CMD ["python", "-m", "uvicorn", "hatch.app:app", "--host", "0.0.0.0", "--port", "8765"]
