import importlib.metadata
import platform

def main() -> None:
    print(f"project version {importlib.metadata.version('logcli')}")
    print(f"python version {platform.python_version()}")
