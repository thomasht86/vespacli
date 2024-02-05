import os
import platform
import pytest
import shutil
import tempfile
from unittest.mock import MagicMock, patch

from vespa_client.cli.installer import VespaCLIInstaller


@pytest.fixture
def installer():
    """Fixture to create a VespaCLIInstaller instance for testing."""
    return VespaCLIInstaller()


@pytest.mark.skipif(
    platform.system().lower() not in VespaCLIInstaller.SUPPORTED_OS, reason="Unsupported OS for this test"
)
class TestVespaCLIInstaller:
    def test_get_os_and_architecture(self, installer):
        """Test if the correct OS and architecture are detected."""
        os_name, arch = installer.get_os_and_architecture()
        assert os_name in VespaCLIInstaller.SUPPORTED_OS
        assert arch in VespaCLIInstaller.ARCH_MAP.values()

    @pytest.mark.skipif(platform.system().lower() == "windows", reason="Non-Windows specific test")
    def test_create_alias_unix(self, installer, mocker):
        # TODO: write this
        pass

    def test_download_and_extract_cli(self, installer, mocker):
        """Test the download and extraction process."""
        mocker.patch("requests.get")
        temp_file = MagicMock(name="tempfile")
        temp_file.__enter__.return_value.name = "tempfile"  # Mocking context manager protocol
        mocker.patch("tempfile.NamedTemporaryFile", return_value=temp_file)
        mocker.patch("tarfile.open")
        mocker.patch("zipfile.ZipFile")
        mocker.patch.object(installer, "extract_file", return_value="/path/to/extracted")
        extract_path = installer.download_and_extract_cli("0.0.1")
        assert extract_path == "/path/to/extracted"

    @pytest.mark.skipif(platform.system().lower() == "windows", reason="Non-Windows specific test")
    def test_set_executable_permission(self, installer, mocker):
        """Test setting executable permission."""
        temp_file = MagicMock()
        temp_file.name = "tempfile"
        mocker.patch("os.chmod")
        installer.set_executable_permission(temp_file.name)
        os.chmod.assert_called_once()

    def test_download_file_failure_handling(self, installer, mocker):
        """Test download file handling when a network error occurs."""
        mocker.patch("requests.get", side_effect=Exception("Network error"))
        with pytest.raises(Exception) as exc_info:
            installer.download_file("http://example.com/vespa-cli.tar.gz", "tar.gz")
        assert "Network error" in str(exc_info.value)

    def test_extract_file_failure_handling_and_cleanup(self, installer, mocker):
        # TODO: fix
        pass

    @pytest.mark.skip(reason="Integration test that requires network access")
    def test_get_latest_version(self, installer):
        """Test retrieval of the latest version from GitHub."""
        version = installer.get_latest_version()
        assert version, "Should retrieve a version string"
