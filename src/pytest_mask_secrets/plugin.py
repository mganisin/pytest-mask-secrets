"""pytest plugin to mask/remove secrets from test reports."""
import os
import re

import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    """pytest hook to remove sensitive data aka secrets from report output."""
    secrets = set()

    if os.environ.get("MASK_SECRETS_AUTO", "") not in ("0", ""):
        candidates = "(TOKEN|PASSWORD|PASSWD|SECRET)"
        candidates = re.compile(candidates)
        mine = re.compile(r"MASK_SECRETS(_AUTO)?\b")
        secrets |= {os.environ[k] for k in os.environ if candidates.search(k) and not mine.match(k)}

    if "MASK_SECRETS" in os.environ:
        vars_ = os.environ["MASK_SECRETS"].split(",")
        secrets |= {os.environ[k] for k in vars_ if k in os.environ}

    if len(secrets) == 0:
        return

    secrets = [re.escape(i) for i in secrets]
    secrets = re.compile(f"({'|'.join(secrets)})")
    mask = "*****"

    report.sections = [(header, secrets.sub(mask, content)) for header, content in report.sections]
    if report.longrepr:
        for tracebacks, location, _ in report.longrepr.chain:
            for entry in tracebacks.reprentries:
                entry.lines = [secrets.sub(mask, l) for l in entry.lines]
                if hasattr(entry, "reprlocals"):
                    entry.reprlocals.lines = [secrets.sub(mask, l) for l in entry.reprlocals.lines]
            location.message = secrets.sub(mask, location.message)
