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
