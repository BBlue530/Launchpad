import os
import re

def expand_env(value: str):
    if not isinstance(value, str):
        return value

    value = re.sub(
        r"\$\{([^}]+)\}",
        lambda m: os.environ.get(m.group(1), ""),
        value
    )

    value = os.path.expandvars(value)

    return value
