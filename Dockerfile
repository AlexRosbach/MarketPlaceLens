FROM python:3.12-slim

ARG MARKETPLACELENS_BUILD_CODE=20260701.1230
ARG MARKETPLACELENS_BUILD_COMMIT=dev
ARG MARKETPLACELENS_BUILD_BRANCH=main
ARG MARKETPLACELENS_BUILD_CREATED=

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MARKETPLACELENS_DB_PATH=/data/marketplacelens.db \
    MARKETPLACELENS_BUILD_CODE=${MARKETPLACELENS_BUILD_CODE} \
    MARKETPLACELENS_BUILD_COMMIT=${MARKETPLACELENS_BUILD_COMMIT} \
    MARKETPLACELENS_BUILD_BRANCH=${MARKETPLACELENS_BUILD_BRANCH} \
    MARKETPLACELENS_BUILD_CREATED=${MARKETPLACELENS_BUILD_CREATED}

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN printf '#!/bin/sh\nexec python -m app.cli.reset_password "$@"\n' \
    > /usr/local/bin/reset-password \
  && chmod +x /usr/local/bin/reset-password

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
