from __future__ import annotations

import os

APP_VERSION = "0.4.1"
BUILD_CODE = os.getenv("MARKETPLACELENS_BUILD_CODE", "20260701.1230")
BUILD_COMMIT = os.getenv("MARKETPLACELENS_BUILD_COMMIT", "dev")
BUILD_BRANCH = os.getenv("MARKETPLACELENS_BUILD_BRANCH", "main")
BUILD_CREATED = os.getenv("MARKETPLACELENS_BUILD_CREATED", "")


def version_payload() -> dict[str, str]:
    return {
        "version": APP_VERSION,
        "build_code": BUILD_CODE,
        "commit": BUILD_COMMIT,
        "branch": BUILD_BRANCH,
        "created": BUILD_CREATED,
    }
