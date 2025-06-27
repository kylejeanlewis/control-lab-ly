FROM python:3.10-slim AS builder

WORKDIR /app

RUN pip install -U pip setuptools wheel

# Install controllably dependencies
COPY pyproject.toml dev/requirements.txt ./
RUN pip wheel --no-cache-dir --no-deps --wheel-dir wheels -r requirements.txt

# Install your local package (controllably)
COPY controllably controllably
RUN pip wheel --no-cache-dir --no-deps --wheel-dir wheels .

FROM python:3.10-slim AS runner

WORKDIR /app

# Install app dependencies
COPY dev/requirements_app.txt . 
RUN pip install --no-cache-dir -r requirements_app.txt

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

EXPOSE 8000

CMD ["python", "-m", "controllably.examples.control.fastapi.server"]
