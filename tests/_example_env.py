# tests._example_env
#
# MIT License
#
# Copyright (c) 2026 Mr. Walls
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""
tests._example_env

Hardened helpers for example runners.
"""

import os
from typing import Optional

_CONTEXT_VARS = {
    # Locale and formatting
    "LANG",
    "LANGUAGE",
    "LC_ALL",
    "LC_CTYPE",
    "LC_COLLATE",
    "LC_MESSAGES",
    # Time and terminal behavior
    "TZ",
    "TERM",
    "COLORTERM",
    "NO_COLOR",
    # User/session identity as informational context
    "USER",
    "LOGNAME",
    "USERNAME",
    "SHELL",
    # Useful path context, if your test needs it
    # "HOME",  # not needed for now?
    "PWD",
}


# Variables that commonly contain credentials, routing controls, or
# execution-changing behavior. Remove these even if they happen to be
# present in the parent environment.
_DENY_PREFIXES = (
    "AWS_",
    "AZURE_",
    "GOOGLE_",
    "GCP_",
    "GH_",
    "GITLAB_",
    "NPM_",
    "PIP_",
    "POETRY_",
    "DOCKER_",
    "KUBECONFIG",
    "SSH_",
    "GIT_",
    "DATABASE_",
    "REDIS_",
    "POSTGRES_",
    "MYSQL_",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "LD_",
    "DYLD_",
)

_DENY_EXACT = {
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AZURE_CLIENT_SECRET",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "CI_JOB_TOKEN",
    "NPM_TOKEN",
    "PYPI_TOKEN",
    "PIP_INDEX_URL",
    "PIP_EXTRA_INDEX_URL",
    "PYTHONSTARTUP",
    "PYTHONPATH",
    "PYTHONHOME",
    "VIRTUAL_ENV",
}


def sanitized_environment(*, extra: Optional[dict] = None) -> dict:
    parent = os.environ.copy()  # copy caller env

    env = {key: value for key, value in parent.items() if key in _CONTEXT_VARS}

    # Preserve the actual current directory as an explicit value.
    env["PWD"] = os.getcwd()

    # Use a predictable, minimal executable search path. Prefer absolute
    # executable paths when invoking subprocesses.
    # env["PATH"] = "/usr/bin:/bin"

    # These are useful defaults if the parent process did not define them.
    env.setdefault("LANG", "C.UTF-8")
    env.setdefault("LC_ALL", "C.UTF-8")
    env.setdefault("TZ", "UTC")

    # Remove anything dangerous that may have been added via extra values.
    for key in list(env):
        if key in _DENY_EXACT or key.startswith(_DENY_PREFIXES):
            env.pop(key, None)

    if extra:
        env.update(extra)

    # Apply the denylist again after merging explicit additions.
    for key in list(env):
        if key in _DENY_EXACT or key.startswith(_DENY_PREFIXES):
            env.pop(key, None)

    return env


def examples_env() -> dict:
    return sanitized_environment()
