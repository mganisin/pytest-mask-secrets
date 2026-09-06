import os
import pytest


# Use pytest's Pytester fixture to create an isolated test run
@pytest.mark.parametrize("auto", [False, True])
def test_masks_function_args_in_report(pytester: pytest.Pytester, auto: bool):
    # Arrange: create a test file that fails and leaks a secret via a function argument
    body = (
        "import os\n"
        "def test_leak_arg(secret_value='TOPSECRET'):\n"
        "    # Configure masking env inside test module\n"
        + ("    os.environ['MASK_SECRETS_AUTO'] = '1'\n" if auto else "    os.environ['MASK_SECRETS'] = 'MY_SECRET'\n") +
        "    os.environ['MY_SECRET'] = 'TOPSECRET'\n"
        "    # Secret flows through a function argument; failure should show func args in report\n"
        "    assert secret_value == 'NOTSECRET'\n"
    )
    pytester.makepyfile(**{"test_leak_args.py": body})

    # Act: run pytest and capture output
    result = pytester.runpytest()

    # Assert: the raw secret should not appear, but masked value should
    stdout = result.stdout.str()
    stderr = result.stderr.str()

    # Ensure test failed so we have a report to inspect
    result.assert_outcomes(failed=1)

    # The secret value should be masked everywhere
    assert "TOPSECRET" not in stdout
    assert "TOPSECRET" not in stderr
    assert "*****" in stdout or "*****" in stderr


def test_masks_function_args_with_multiple_args(pytester: pytest.Pytester):
    # Arrange: failing test with multiple function args including secret value
    pytester.makepyfile(
        **{
            "test_multi_args.py": (
                "import os\n"
                "os.environ['MASK_SECRETS'] = 'MY_SECRET'\n"
                "os.environ['MY_SECRET'] = 'TOPSECRET'\n"
                "def test_multi_args(a='VISIBLE', b='TOPSECRET'):\n"
                "    # Fails to expose function args in report\n"
                "    assert a == b\n"
            )
        }
    )

    result = pytester.runpytest()
    result.assert_outcomes(failed=1)

    out = result.stdout.str() + result.stderr.str()

    # Secret should be masked, non-secret arg should remain
    assert "TOPSECRET" not in out
    assert "VISIBLE" in out
    assert "*****" in out


def test_masks_logging_output(pytester: pytest.Pytester):
    # Arrange: a passing test leaking a secret through a non-root logger, both inline and via args
    pytester.makepyfile(
        **{
            "test_leak_log.py": (
                "import logging\n"
                "import os\n"
                "os.environ['MASK_SECRETS'] = 'MY_SECRET'\n"
                "os.environ['MY_SECRET'] = 'TOPSECRET'\n"
                "log = logging.getLogger('some.child.logger')\n"
                "def test_leak_log(caplog):\n"
                "    log.warning('inline TOPSECRET and VISIBLE')\n"
                "    log.warning('formatted %s and %s', 'TOPSECRET', 'VISIBLE')\n"
                "    assert 'TOPSECRET' not in caplog.text\n"
            )
        }
    )

    # Act: run with live logging and a log file, the sinks the report hook cannot reach
    log_file = pytester.path / "pytest.log"
    result = pytester.runpytest("--log-cli-level=WARNING", f"--log-file={log_file}", "--log-file-level=WARNING")

    # Assert: masked in caplog (the in-test assert), in live log output and in the log file
    result.assert_outcomes(passed=1)

    out = result.stdout.str() + result.stderr.str() + log_file.read_text()

    assert "TOPSECRET" not in out
    assert "VISIBLE" in out
    assert "*****" in out
