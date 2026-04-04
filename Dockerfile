FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install trafilatura

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /install /usr/local
COPY src/ ./src/

RUN mkdir -p /app/data

CMD ["python", "-m", "src.main", "serve"]
