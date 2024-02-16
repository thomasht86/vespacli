import os
import platform
import subprocess
import sys

from vespacli._version_generated import vespa_version


def get_binary_path():
    base_path = os.path.abspath(os.path.dirname(__file__))
    go_binaries_path = os.path.join(base_path, "go-binaries")

    os_name = platform.system().lower()
    arch = platform.machine().lower()

    if os_name == "darwin":
        arch = "arm64" if arch == "arm64" else "amd64"
    elif os_name == "linux":
        arch = "arm64" if arch == "aarch64" else "amd64"
    elif os_name == "windows":
        os_name = "windows"
        arch = "386" if arch == "x86" else "amd64"
    else:
        raise OSError("Unsupported operating system")

    binary_dir_name = f"vespa-cli_{vespa_version}_{os_name}_{arch}"
    binary_path = os.path.join(go_binaries_path, binary_dir_name, "bin")

    # Assuming the executable name is consistent and known
    executable_name = "vespa" if os_name != "windows" else "vespa.exe"
    full_executable_path = os.path.join(binary_path, executable_name)

    if not os.path.exists(full_executable_path):
        raise FileNotFoundError("Binary executable not found: " + full_executable_path)

    return full_executable_path


def run_vespa_cli():
    args = sys.argv[1:]
    binary_path = get_binary_path()
    full_cmd = [binary_path, *args]
    result = subprocess.run(full_cmd)
    return


__version__ = vespa_version
