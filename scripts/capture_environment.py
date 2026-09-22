#!/usr/bin/env python3
"""Capture the software/runtime environment used for a reproduction run."""

import platform
import sys
from importlib.metadata import version, PackageNotFoundError

PACKAGES = ["numpy", "h5py", "pandas", "thrift"]

print("python_version:", sys.version.replace("\n", " "))
print("python_executable:", sys.executable)
print("platform:", platform.platform())
print("machine:", platform.machine())
print("processor:", platform.processor() or "not reported")

for package in PACKAGES:
    try:
        v = version(package)
    except PackageNotFoundError:
        v = "NOT INSTALLED"
    print(f"{package}_version:", v)
