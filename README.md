# pytest-mask-secrets

pytest-mask-secrets is a plugin for pytest that removes sensitive data from
test reports.

Based on the configuration, it searches for specified secrets, passwords, and
tokens in the records and replaces them with asterisks.

While this feature is usually provided by CI tools, it can be insufficient in
many situations as it only strips secrets from the captured output. A common
case of leaking secrets is through generated JUnit files that are not curated
by CI tools. Therefore, it is necessary to have such functionality at the
pytest level.

## Installation

```
pip install pytest-mask-secrets
```

## Usage

pytest-mask-secrets needs to know which values to mask. These values are read
from environment variables. The list of these variables is passed in the
`MASK_SECRETS` environment variable, which contains a comma-separated list of
all environment variables containing secrets. Here is an example:

```
export PYPI_API_TOKEN=mytoken
export SOME_PASSWORD=mypassword
export MASK_SECRETS=PYPI_API_TOKEN,SOME_PASSWORD

pytest
```

With pytest-mask-secrets installed, all occurrences of "mytoken" and
"mypassword" will be eliminated from the report.

### Define Secret Values in the Code

Tests can use `config.stash` to define secret values to be masked. There is a
`mask_secrets_key` available that provides access to a `set()` where additional
secret values can be added. Here is an example:

```
from pytest_mask_secrets.plugin import mask_secrets_key

def test(pytestconfig):
    pytestconfig.stash[mask_secrets_key].add("true-secret")
    ...
```

All occurrences of "true-secret" will be removed from the report.

## Automagic Identification of Variables with Secrets

If `MASK_SECRETS_AUTO` is set to anything other than zero ("0"), all
environment variables containing the words "TOKEN", "SECRET," "PASSWORD," or
"PASSWD" in their names are considered sensitive, and their values are removed
from the report.

This discovery mode should be used with caution. CI workflows, in particular,
should rely on an explicit list of secret variables. Under certain
circumstances, this method can lead to the leakage of other sensitive data (if,
by accident, a secret from an environment variable matches text commonly
present in the test report). Nevertheless, this method can still be useful for
example for local execution to prevent accidental leaks through copy-and-paste.
