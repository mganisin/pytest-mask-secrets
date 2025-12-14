"""pytest plugin to mask/remove secrets from test reports."""
import os
import re

import pytest


mask_secrets_key = pytest.StashKey[set]()

_stash = None


def pytest_configure(config):
    """pytest stash as global variable to gain access."""
    global _stash
    _stash = config.stash
    _stash[mask_secrets_key] = set()


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

    secrets |= _stash[mask_secrets_key]

    if len(secrets) == 0:
        return

    secrets = [re.escape(i) for i in secrets]
    secrets = re.compile(f"({'|'.join(secrets)})")
    mask = "*****"

    report.sections = [(header, secrets.sub(mask, content)) for header, content in report.sections]
    if hasattr(report.longrepr, "chain"):
        for tracebacks, location, _ in report.longrepr.chain:
            for entry in getattr(tracebacks, "reprentries", []):
                entry.lines = [secrets.sub(mask, l) for l in entry.lines]
                if getattr(entry, "reprlocals", None) is not None:
                    entry.reprlocals.lines = [secrets.sub(mask, l) for l in entry.reprlocals.lines]
                if getattr(entry, "reprfuncargs", None) is not None:
                    entry.reprfuncargs.args = [(k, secrets.sub(mask, v)) for k,v in entry.reprfuncargs.args]
            if hasattr(location, "message"):
                location.message = secrets.sub(mask, location.message)
