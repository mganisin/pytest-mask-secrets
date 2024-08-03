"""pytest plugin to mask/remove secrets from test reports."""
import os
import re

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    """pytest hook to remove sensitive data aka secrets from report output."""
    if "MASK_SECRETS" not in os.environ:
        return

    secrets = os.environ["MASK_SECRETS"].split(",")
    secrets = [os.environ[k] for k in secrets if k in os.environ]
    if len(secrets) == 0:
        return

    secrets = re.compile(f"({'|'.join(secrets)})")
    mask = "*****"

    report.sections = [(header, secrets.sub(mask, content)) for header, content in report.sections]
    if report.longrepr:
        for tracebacks, location, _ in report.longrepr.chain:
            for entry in tracebacks.reprentries:
                entry.lines = [secrets.sub(mask, l) for l in entry.lines]
            location.message = secrets.sub(mask, location.message)
