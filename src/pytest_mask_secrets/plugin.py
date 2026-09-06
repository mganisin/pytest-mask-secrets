"""pytest plugin to mask/remove secrets from test reports."""
import logging
import os
import re

import pytest


mask_secrets_key = pytest.StashKey[set]()

_stash = None
_record_factory = None
_mask = "*****"


def pytest_configure(config):
    """pytest stash as global variable to gain access."""
    global _stash, _record_factory
    _stash = config.stash
    _stash[mask_secrets_key] = set()

    # masking at record creation covers every sink: log_cli, log_file, caplog and own handlers
    if _record_factory is None:
        _record_factory = logging.getLogRecordFactory()
        logging.setLogRecordFactory(_masking_record_factory)


def _get_secrets():
    """collect secrets and compile them into a single pattern, None when there is nothing to mask."""
    secrets = set()

    if os.environ.get("MASK_SECRETS_AUTO", "") not in ("0", ""):
        candidates = "(TOKEN|PASSWORD|PASSWD|SECRET)"
        candidates = re.compile(candidates)
        mine = re.compile(r"MASK_SECRETS(_AUTO)?\b")
        secrets |= {os.environ[k] for k in os.environ if candidates.search(k) and not mine.match(k)}

    if "MASK_SECRETS" in os.environ:
        vars_ = os.environ["MASK_SECRETS"].split(",")
        secrets |= {os.environ[k] for k in vars_ if os.getenv(k)}

    secrets |= _stash[mask_secrets_key]

    if len(secrets) == 0:
        return None

    secrets = [re.escape(i) for i in secrets]
    return re.compile(f"({'|'.join(secrets)})")


def _masking_record_factory(*args, **kwargs):
    """log record factory removing secrets from log messages."""
    record = _record_factory(*args, **kwargs)

    secrets = _get_secrets()
    if secrets is None:
        return record

    try:
        message = record.getMessage()
    except Exception:  # broken format string, leave it for logging to complain about
        return record

    masked = secrets.sub(_mask, message)
    if masked != message:
        record.msg = masked
        record.args = None

    return record


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_logreport(report):
    """pytest hook to remove sensitive data aka secrets from report output."""
    secrets = _get_secrets()

    if secrets is None:
        return

    report.sections = [(header, secrets.sub(_mask, content)) for header, content in report.sections]
    if hasattr(report.longrepr, "chain"):
        for tracebacks, location, _ in report.longrepr.chain:
            for entry in getattr(tracebacks, "reprentries", []):
                entry.lines = [secrets.sub(_mask, l) for l in entry.lines]
                if getattr(entry, "reprlocals", None) is not None:
                    entry.reprlocals.lines = [secrets.sub(_mask, l) for l in entry.reprlocals.lines]
                if getattr(entry, "reprfuncargs", None) is not None:
                    entry.reprfuncargs.args = [(k, secrets.sub(_mask, v)) for k,v in entry.reprfuncargs.args]
            if hasattr(location, "message"):
                location.message = secrets.sub(_mask, location.message)
