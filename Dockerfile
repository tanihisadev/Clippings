FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ ./src/
COPY config.yaml ./config.yaml

RUN mkdir -p /app/data && \
    groupadd -r digest && \
    useradd -r -g digest -d /app -s /sbin/nologin digest && \
    chown -R digest:digest /app

USER digest

EXPOSE 8000

CMD ["digest", "serve"]
