import os
import platform
import pytest
import tempfile

from vespa_client.cli.installer import VespaCLIInstaller  # Adjust the import based on your project structure


def test_get_os_and_architecture():
    """Test OS and Architecture detection logic."""
    os_name, arch = VespaCLIInstaller.get_os_and_architecture()
    assert os_name in ["windows", "darwin", "linux"], "OS should be one of 'windows', 'darwin', or 'linux'."
    assert arch in ["amd64", "arm64", "386"], "Architecture should be 'amd64', 'arm64', or '386'."


@pytest.mark.skip(reason="Requires a real archive file for testing")
def test_extract_file():
    """Assumes a test archive is available in the same directory as the script."""
    # This test is skipped by default. To enable it, provide a real archive and remove the skip decorator.


@pytest.mark.skipif(
    platform.system().lower() == "windows", reason="Executable permission test not applicable to Windows"
)
def test_set_executable_permission():
    """Test setting executable permission on Unix-like OS."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        file_path = tmp_file.name
    VespaCLIInstaller.set_executable_permission(file_path)
    assert os.stat(file_path).st_mode & 0o111, "File should have executable permissions set."
    os.remove(file_path)  # Cleanup after test
