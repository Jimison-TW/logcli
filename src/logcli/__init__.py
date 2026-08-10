import importlib.metadata
import platform

from . import parser


def main() -> None:  # pragma: no cover
    print(f"project version {importlib.metadata.version('logcli')}")
    print(f"python version {platform.python_version()}")
    print(f"Log level: {parser.extract_level('2026-07-17 ERROR failed to connect')}")
